# ============================================================
# utils/mailer.py — Envoi de rapport journalier par Gmail SMTP
# Config mail persistante en base de données (table parametres)
# ============================================================

import smtplib
import os
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.base      import MIMEBase
from email                import encoders
from datetime             import date, datetime

MAIL_CONFIG = {
    "smtp_host":    "smtp.gmail.com",
    "smtp_port":    587,
    "expediteur":   "",
    "app_password": "",
    "destinataire": "",
    "actif":        False,
}


# ============================================================
# Persistance BdD
# ============================================================

def charger_config_mail(db) -> bool:
    """
    Charge la config mail depuis la table `parametres` en BdD.
    À appeler une fois au démarrage de l'application.
    """
    global MAIL_CONFIG
    try:
        rows = db.fetchall(
            "SELECT cle, valeur FROM parametres WHERE cle LIKE 'mail_%'"
        )
        if not rows:
            return False
        mapping = {r["cle"]: r["valeur"] for r in rows}
        MAIL_CONFIG["expediteur"]   = mapping.get("mail_expediteur",   "")
        MAIL_CONFIG["app_password"] = mapping.get("mail_app_password", "")
        MAIL_CONFIG["destinataire"] = mapping.get("mail_destinataire", "")
        MAIL_CONFIG["actif"]        = mapping.get("mail_actif", "0") == "1"
        print(f"[MAIL] Config chargée — actif={MAIL_CONFIG['actif']} "
              f"— expéditeur={MAIL_CONFIG['expediteur']}")
        return MAIL_CONFIG["actif"]
    except Exception as e:
        print(f"[MAIL] Erreur chargement config : {e}")
        return False


def sauvegarder_config_mail(db, expediteur: str, app_password: str,
                             destinataire: str, actif: bool) -> bool:
    """Sauvegarde la config mail en BdD (INSERT OR UPDATE)."""
    global MAIL_CONFIG
    try:
        paires = [
            ("mail_expediteur",   expediteur),
            ("mail_app_password", app_password),
            ("mail_destinataire", destinataire),
            ("mail_actif",        "1" if actif else "0"),
        ]
        for cle, valeur in paires:
            db.execute("""
                INSERT INTO parametres (cle, valeur)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE valeur = VALUES(valeur)
            """, (cle, valeur))
        MAIL_CONFIG["expediteur"]   = expediteur
        MAIL_CONFIG["app_password"] = app_password
        MAIL_CONFIG["destinataire"] = destinataire
        MAIL_CONFIG["actif"]        = actif
        print("[MAIL] Config sauvegardée en BdD.")
        return True
    except Exception as e:
        print(f"[MAIL] Erreur sauvegarde config : {e}")
        return False


def get_config_mail(db) -> dict:
    """Retourne la config mail actuelle depuis la BdD."""
    try:
        rows = db.fetchall(
            "SELECT cle, valeur FROM parametres WHERE cle LIKE 'mail_%'"
        )
        mapping = {r["cle"]: r["valeur"] for r in rows}
        return {
            "expediteur":   mapping.get("mail_expediteur",   ""),
            "app_password": mapping.get("mail_app_password", ""),
            "destinataire": mapping.get("mail_destinataire", ""),
            "actif":        mapping.get("mail_actif", "0") == "1",
        }
    except Exception as e:
        print(f"[MAIL] Erreur lecture config : {e}")
        return {"expediteur": "", "app_password": "",
                "destinataire": "", "actif": False}


# ============================================================
# Construction du rapport HTML
# ============================================================

def _build_rapport(db, caissier_nom: str) -> dict:
    """Collecte les données du rapport journalier depuis la BdD."""
    today = date.today()

    total = db.fetchone(
        "SELECT COALESCE(SUM(total),0) AS v FROM tickets "
        "WHERE date_vente=%s AND statut='valide'", (today,)
    ) or {"v": 0}
    nb = db.fetchone(
        "SELECT COUNT(*) AS v FROM tickets "
        "WHERE date_vente=%s AND statut='valide'", (today,)
    ) or {"v": 0}
    manq = db.fetchone(
        "SELECT COALESCE(SUM(montant),0) AS v FROM manquants "
        "WHERE date_manquant=%s", (today,)
    ) or {"v": 0}
    cout = db.fetchone("""
        SELECT COALESCE(SUM(tl.quantite * b.prix_achat),0) AS v
        FROM ticket_lignes tl
        JOIN boissons b ON b.id=tl.boisson_id
        JOIN tickets t  ON t.id=tl.ticket_id
        WHERE t.date_vente=%s AND t.statut='valide'
    """, (today,)) or {"v": 0}
    top = db.fetchall("""
        SELECT b.nom, SUM(tl.quantite) AS qte, SUM(tl.sous_total) AS ca
        FROM ticket_lignes tl
        JOIN boissons b ON b.id=tl.boisson_id
        JOIN tickets t  ON t.id=tl.ticket_id
        WHERE t.date_vente=%s AND t.statut='valide'
        GROUP BY b.id ORDER BY qte DESC LIMIT 5
    """, (today,))
    manq_detail = db.fetchall("""
        SELECT CONCAT(u.prenom,' ',u.nom) AS serveur, SUM(m.montant) AS montant
        FROM manquants m
        JOIN utilisateurs u ON u.id=m.serveur_id
        WHERE m.date_manquant=%s
        GROUP BY m.serveur_id
    """, (today,))

    total_v  = float(total["v"])
    benefice = total_v - float(cout["v"])
    return {
        "caissier":         caissier_nom,
        "date":             str(today),
        "total_ventes":     total_v,
        "nb_tickets":       int(nb["v"]),
        "total_manquants":  float(manq["v"]),
        "benefice_net":     benefice,
        "top_boissons":     top,
        "manquants_detail": manq_detail,
    }


def _build_corps_html(rapport: dict) -> str:
    today      = date.today().strftime("%d/%m/%Y")
    caissier   = rapport.get("caissier", "—")
    total      = rapport.get("total_ventes", 0)
    nb_tickets = rapport.get("nb_tickets", 0)
    manquants  = rapport.get("total_manquants", 0)
    benefice   = rapport.get("benefice_net", 0)

    lignes_html = ""
    for r in rapport.get("top_boissons", []):
        lignes_html += f"""
        <tr>
          <td style="padding:6px 12px;border-bottom:1px solid #3D1515;">{r['nom']}</td>
          <td style="padding:6px 12px;border-bottom:1px solid #3D1515;text-align:center;">{r['qte']}</td>
          <td style="padding:6px 12px;border-bottom:1px solid #3D1515;text-align:right;">{float(r['ca']):,.0f} FCFA</td>
        </tr>"""

    manquants_html = ""
    for m in rapport.get("manquants_detail", []):
        manquants_html += f"""
        <tr>
          <td style="padding:6px 12px;border-bottom:1px solid #3D1515;">{m['serveur']}</td>
          <td style="padding:6px 12px;border-bottom:1px solid #3D1515;text-align:right;color:#E74C3C;">
            {float(m['montant']):,.0f} FCFA
          </td>
        </tr>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Georgia,serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:24px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#1A0A0A;border-radius:12px;overflow:hidden;">
        <tr>
          <td style="background:#C0392B;padding:24px;text-align:center;">
            <h1 style="margin:0;color:#D4AC0D;font-size:22px;">🍷 CaveVin Manager</h1>
            <p style="margin:6px 0 0;color:#F5E6D3;font-size:13px;">
              Rapport de ventes journalier — {today}
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 24px;">
            <p style="color:#9E8B7A;font-size:12px;margin:0;">
              Rapport généré par <strong style="color:#F5E6D3;">{caissier}</strong>
              le {datetime.now().strftime('%d/%m/%Y à %H:%M')}
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:0 24px 16px;">
            <table width="100%" cellpadding="0" cellspacing="8">
              <tr>
                <td width="25%" style="background:#2A1010;border-radius:8px;
                    padding:14px;text-align:center;border:1px solid #3D1515;">
                  <div style="font-size:22px;">💰</div>
                  <div style="color:#D4AC0D;font-size:16px;font-weight:bold;">{total:,.0f}</div>
                  <div style="color:#9E8B7A;font-size:10px;">Total ventes (FCFA)</div>
                </td>
                <td width="25%" style="background:#2A1010;border-radius:8px;
                    padding:14px;text-align:center;border:1px solid #3D1515;">
                  <div style="font-size:22px;">🧾</div>
                  <div style="color:#F5E6D3;font-size:16px;font-weight:bold;">{nb_tickets}</div>
                  <div style="color:#9E8B7A;font-size:10px;">Tickets validés</div>
                </td>
                <td width="25%" style="background:#2A1010;border-radius:8px;
                    padding:14px;text-align:center;border:1px solid #3D1515;">
                  <div style="font-size:22px;">📈</div>
                  <div style="color:#27AE60;font-size:16px;font-weight:bold;">{benefice:,.0f}</div>
                  <div style="color:#9E8B7A;font-size:10px;">Bénéfice net (FCFA)</div>
                </td>
                <td width="25%" style="background:#2A1010;border-radius:8px;
                    padding:14px;text-align:center;border:1px solid #3D1515;">
                  <div style="font-size:22px;">⚠️</div>
                  <div style="color:#E74C3C;font-size:16px;font-weight:bold;">{manquants:,.0f}</div>
                  <div style="color:#9E8B7A;font-size:10px;">Manquants (FCFA)</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        {"" if not lignes_html else f'''
        <tr><td style="padding:0 24px 16px;">
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="background:#2A1010;border-radius:8px;border:1px solid #3D1515;overflow:hidden;">
            <tr style="background:#3D1515;">
              <th style="padding:10px 12px;text-align:left;color:#D4AC0D;font-size:12px;">Boisson</th>
              <th style="padding:10px 12px;text-align:center;color:#D4AC0D;font-size:12px;">Qté</th>
              <th style="padding:10px 12px;text-align:right;color:#D4AC0D;font-size:12px;">CA</th>
            </tr>
            {lignes_html}
          </table>
        </td></tr>'''}
        {"" if not manquants_html else f'''
        <tr><td style="padding:0 24px 16px;">
          <p style="color:#E74C3C;font-size:13px;font-weight:bold;margin:0 0 8px;">
            ⚠ Manquants du jour
          </p>
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="background:#2A1010;border-radius:8px;border:1px solid #3D1515;overflow:hidden;">
            <tr style="background:#3D1515;">
              <th style="padding:10px 12px;text-align:left;color:#D4AC0D;font-size:12px;">Serveur</th>
              <th style="padding:10px 12px;text-align:right;color:#D4AC0D;font-size:12px;">Montant</th>
            </tr>
            {manquants_html}
          </table>
        </td></tr>'''}
        <tr>
          <td style="background:#120606;padding:16px 24px;text-align:center;
              border-top:1px solid #3D1515;">
            <p style="color:#9E8B7A;font-size:11px;margin:0;">
              📎 Pièces jointes : rapport journalier + cumul mensuel en Excel
            </p>
            <p style="color:#9E8B7A;font-size:11px;margin:4px 0 0;">
              CaveVin Manager v1.0.0 — Rapport automatique
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ============================================================
# Envoi du rapport
# ============================================================

def _attacher_xlsx(msg, path: str):
    """Attache un fichier Excel au message mail."""
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            part = MIMEBase("application",
                            "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition",
                        f'attachment; filename="{os.path.basename(path)}"')
        msg.attach(part)


def envoyer_rapport_journalier(db, caissier_nom: str,
                                xlsx_path: str = None,
                                xlsx_path_mensuel: str = None,
                                on_done=None):
    """
    Envoie le rapport journalier par mail en arrière-plan.

    db                : instance Database
    caissier_nom      : nom complet du caissier connecté
    xlsx_path         : rapport Excel JOURNALIER à joindre
    xlsx_path_mensuel : rapport Excel MENSUEL (cumul) à joindre
    on_done(ok, msg)  : callback appelé à la fin (optionnel)
    """
    if not MAIL_CONFIG.get("actif"):
        if on_done:
            on_done(False, "Mail non configuré — envoi ignoré.")
        return

    def _send():
        try:
            rapport = _build_rapport(db, caissier_nom)
            corps   = _build_corps_html(rapport)
            today   = date.today().strftime("%d/%m/%Y")

            msg = MIMEMultipart("mixed")
            msg["From"]    = MAIL_CONFIG["expediteur"]
            msg["To"]      = MAIL_CONFIG["destinataire"]
            msg["Subject"] = f"[CaveVin] Rapport journalier {today} — {caissier_nom}"

            msg.attach(MIMEText(corps, "html", "utf-8"))

            # PJ 1 : rapport journalier
            _attacher_xlsx(msg, xlsx_path)

            # PJ 2 : cumul mensuel
            _attacher_xlsx(msg, xlsx_path_mensuel)

            with smtplib.SMTP(MAIL_CONFIG["smtp_host"],
                              MAIL_CONFIG["smtp_port"]) as server:
                server.ehlo()
                server.starttls()
                server.login(MAIL_CONFIG["expediteur"],
                             MAIL_CONFIG["app_password"])
                server.sendmail(MAIL_CONFIG["expediteur"],
                                MAIL_CONFIG["destinataire"],
                                msg.as_string())

            print(f"[MAIL] Rapport envoyé à {MAIL_CONFIG['destinataire']}")
            if on_done:
                on_done(True, "Rapport envoyé avec succès.")

        except Exception as e:
            print(f"[MAIL] Erreur envoi : {e}")
            if on_done:
                on_done(False, str(e))

    threading.Thread(target=_send, daemon=True, name="CaveVin-Mailer").start()
