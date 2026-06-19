# ============================================================
# utils/backup.py — Sauvegarde automatique MySQL planifiée
# ============================================================
#
# Pas de dépendance externe — utilise mysqldump (déjà installé
# avec MySQL/MariaDB) + threading + schedule optionnel.
#
# Optionnel : pip install schedule  (pour la planification auto)
# ============================================================

import os, subprocess, threading, time
from datetime import datetime, date

try:
    import schedule
    HAS_SCHEDULE = True
except ImportError:
    HAS_SCHEDULE = False


# ---- Configuration backup ----
BACKUP_CONFIG = {
    "backup_dir":       os.path.join(os.path.expanduser("~"), "CaveVin_Backups"),
    "keep_days":        30,       # Nombre de jours à conserver
    "auto_enabled":     False,    # Sauvegarde auto au démarrage
    "auto_heure":       "23:00",  # Heure de sauvegarde quotidienne
    "compress":         True,     # Compresser avec gzip
}


def _get_db_config():
    """Récupère la config DB depuis config.py."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from config import DB_CONFIG
    return DB_CONFIG


def _nom_fichier(compress: bool) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = ".sql.gz" if compress else ".sql"
    return f"cavevin_backup_{ts}{ext}"


def sauvegarder(backup_dir: str = None, compress: bool = None,
                on_progress=None) -> str:
    """
    Effectue un dump MySQL de la base cave_vin.

    Retourne le chemin du fichier créé.
    on_progress(message: str) : callback optionnel pour l'UI
    """
    cfg      = _get_db_config()
    bdir     = backup_dir or BACKUP_CONFIG["backup_dir"]
    compress = compress if compress is not None else BACKUP_CONFIG["compress"]

    os.makedirs(bdir, exist_ok=True)
    nom      = _nom_fichier(compress)
    chemin   = os.path.join(bdir, nom)

    if on_progress:
        on_progress(f"Démarrage du dump → {nom}")

    cmd_dump = [
        "mysqldump",
        f"--host={cfg['host']}",
        f"--port={cfg.get('port', 3306)}",
        f"--user={cfg['user']}",
        f"--password={cfg.get('password','')}",
        "--single-transaction",
        "--routines",
        "--triggers",
        "--add-drop-table",
        cfg["database"],
    ]

    try:
        if compress:
            # mysqldump | gzip > fichier.sql.gz
            with open(chemin, "wb") as f:
                dump = subprocess.Popen(
                    cmd_dump, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                gzip = subprocess.Popen(
                    ["gzip", "-9"], stdin=dump.stdout, stdout=f, stderr=subprocess.PIPE
                )
                dump.stdout.close()
                gzip_out, gzip_err = gzip.communicate()
                dump.wait()
        else:
            with open(chemin, "w", encoding="utf-8") as f:
                result = subprocess.run(
                    cmd_dump, stdout=f, stderr=subprocess.PIPE, text=True
                )
                if result.returncode != 0:
                    raise RuntimeError(f"mysqldump error: {result.stderr}")

        taille = os.path.getsize(chemin)
        msg = f"Sauvegarde OK : {nom} ({taille/1024:.1f} Ko)"
        if on_progress:
            on_progress(msg)
        print(f"[BACKUP] {msg}")

        # Nettoyage des anciens backups
        _nettoyer_anciens(bdir)
        return chemin

    except Exception as e:
        if on_progress:
            on_progress(f"Erreur : {e}")
        raise


def restaurer(chemin_sql: str, on_progress=None) -> bool:
    """
    Restaure la base depuis un fichier .sql ou .sql.gz.
    ⚠ Écrase les données existantes !
    """
    cfg = _get_db_config()
    if on_progress:
        on_progress(f"Restauration depuis {os.path.basename(chemin_sql)}...")

    cmd_mysql = [
        "mysql",
        f"--host={cfg['host']}",
        f"--port={cfg.get('port', 3306)}",
        f"--user={cfg['user']}",
        f"--password={cfg.get('password','')}",
        cfg["database"],
    ]

    try:
        is_gz = chemin_sql.endswith(".gz")
        if is_gz:
            gunzip = subprocess.Popen(
                ["gunzip", "-c", chemin_sql], stdout=subprocess.PIPE
            )
            mysql  = subprocess.Popen(
                cmd_mysql, stdin=gunzip.stdout, stderr=subprocess.PIPE
            )
            gunzip.stdout.close()
            _, err = mysql.communicate()
            gunzip.wait()
        else:
            with open(chemin_sql, "r", encoding="utf-8") as f:
                result = subprocess.run(cmd_mysql, stdin=f,
                                        stderr=subprocess.PIPE, text=True)
                err = result.stderr

        if on_progress:
            on_progress("Restauration terminée avec succès !")
        return True
    except Exception as e:
        if on_progress:
            on_progress(f"Erreur restauration : {e}")
        return False


def lister_backups(backup_dir: str = None) -> list:
    """Retourne la liste des sauvegardes disponibles (plus récent en premier)."""
    bdir = backup_dir or BACKUP_CONFIG["backup_dir"]
    if not os.path.exists(bdir):
        return []
    fichiers = [
        f for f in os.listdir(bdir)
        if f.startswith("cavevin_backup_") and (f.endswith(".sql") or f.endswith(".sql.gz"))
    ]
    fichiers.sort(reverse=True)
    result = []
    for f in fichiers:
        chemin = os.path.join(bdir, f)
        taille = os.path.getsize(chemin)
        mtime  = datetime.fromtimestamp(os.path.getmtime(chemin))
        result.append({
            "nom":    f,
            "chemin": chemin,
            "taille": taille,
            "date":   mtime,
        })
    return result


def _nettoyer_anciens(bdir: str):
    """Supprime les sauvegardes plus vieilles que keep_days jours."""
    keep = BACKUP_CONFIG["keep_days"]
    now  = datetime.now()
    for b in lister_backups(bdir):
        age = (now - b["date"]).days
        if age > keep:
            try:
                os.remove(b["chemin"])
                print(f"[BACKUP] Supprimé (>{keep}j) : {b['nom']}")
            except Exception:
                pass


# ---- Planification automatique ----
_backup_thread = None
_stop_event    = threading.Event()


def demarrer_sauvegarde_auto(heure: str = None, on_done=None):
    """Lance la sauvegarde automatique quotidienne dans un thread."""
    global _backup_thread, _stop_event

    if not HAS_SCHEDULE:
        print("[BACKUP] 'schedule' non installé. pip install schedule")
        return

    heure = heure or BACKUP_CONFIG["auto_heure"]
    _stop_event.clear()

    def job():
        try:
            path = sauvegarder()
            if on_done:
                on_done(f"Sauvegarde auto OK : {os.path.basename(path)}")
        except Exception as e:
            if on_done:
                on_done(f"Erreur sauvegarde auto : {e}")

    schedule.every().day.at(heure).do(job)

    def run():
        while not _stop_event.is_set():
            schedule.run_pending()
            time.sleep(30)

    _backup_thread = threading.Thread(target=run, daemon=True, name="CaveVin-Backup")
    _backup_thread.start()
    print(f"[BACKUP] Sauvegarde automatique planifiée à {heure}")


def arreter_sauvegarde_auto():
    global _stop_event
    _stop_event.set()
    if HAS_SCHEDULE:
        schedule.clear()
    print("[BACKUP] Sauvegarde automatique arrêtée.")
