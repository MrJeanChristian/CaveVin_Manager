# ============================================================
# utils/thermal_printer.py — Impression thermique directe (ESC/POS)
# ============================================================
#
# Dépendance : pip install python-escpos
#
# Connexions supportées :
#   - USB  (le plus courant sous Linux)
#   - Réseau (IP)
#   - Série (/dev/ttyUSB0)
#
# Pour trouver ton imprimante USB sous Linux :
#   lsusb
#   → ex: Bus 001 Device 003: ID 0416:5011 Winbond Electronics Corp.
#         idVendor=0416  idProduct=5011
#
# Droits USB : sudo usermod -aG lp $USER  puis redémarrer la session
# ============================================================

from datetime import datetime

try:
    from escpos.printer import Usb, Network, Serial, File
    HAS_ESCPOS = True
except ImportError:
    HAS_ESCPOS = False


# ---- Configuration imprimante (à adapter) ----
PRINTER_CONFIG = {
    "type":       "usb",        # "usb" | "network" | "serial" | "file"
    # USB
    "usb_vendor":  0x0416,      # idVendor  (lsusb)
    "usb_product": 0x5011,      # idProduct (lsusb)
    # Réseau
    "network_host": "192.168.1.100",
    "network_port": 9100,
    # Série
    "serial_port": "/dev/ttyUSB0",
    "serial_baud": 9600,
    # Fichier (test sans imprimante)
    "file_path":  "/tmp/ticket_escpos.txt",
    # Largeur en caractères (57mm=32, 80mm=42 ou 48)
    "columns": 42,
}


def _get_printer():
    """Retourne une instance d'imprimante selon la config."""
    if not HAS_ESCPOS:
        raise ImportError("python-escpos n'est pas installé.\nLancez : pip install python-escpos")

    t = PRINTER_CONFIG["type"]
    if t == "usb":
        return Usb(
            PRINTER_CONFIG["usb_vendor"],
            PRINTER_CONFIG["usb_product"],
        )
    elif t == "network":
        return Network(
            PRINTER_CONFIG["network_host"],
            PRINTER_CONFIG["network_port"],
        )
    elif t == "serial":
        return Serial(
            devfile=PRINTER_CONFIG["serial_port"],
            baudrate=PRINTER_CONFIG["serial_baud"],
        )
    elif t == "file":
        return File(PRINTER_CONFIG["file_path"])
    else:
        raise ValueError(f"Type d'imprimante inconnu : {t}")


def _sep(p, cols, char="-"):
    """Ligne de séparation."""
    p.text(char * cols + "\n")


def _ligne_2col(p, left: str, right: str, cols: int):
    """Texte aligné gauche/droite sur une ligne."""
    space = cols - len(left) - len(right)
    if space < 1:
        space = 1
    p.text(left + " " * space + right + "\n")


def imprimer_ticket(ticket: dict, lignes: list) -> bool:
    """
    Imprime un ticket sur l'imprimante thermique.

    ticket  : dict {numero, date_vente, total, montant_recu,
                    serveur_nom, caissier_nom, notes}
    lignes  : list de dicts {nom, quantite, prix_unit, sous_total}

    Retourne True si succès, False sinon.
    """
    cols = PRINTER_CONFIG["columns"]

    try:
        p = _get_printer()

        # ---- EN-TETE ----
        p.set(align="center", bold=True, double_height=True, double_width=True)
        p.text("CAVE A VIN\n")
        p.set(align="center", bold=False, double_height=False, double_width=False)
        p.text("CaveVin Manager\n")
        _sep(p, cols, "=")

        # ---- INFOS TICKET ----
        p.set(align="left", bold=False)
        date_str = str(ticket.get("date_vente", "")).split(" ")[0]
        heure    = datetime.now().strftime("%H:%M")
        p.text(f"Ticket  : {ticket['numero']}\n")
        p.text(f"Date    : {date_str}  {heure}\n")
        p.text(f"Serveur : {ticket.get('serveur_nom', '-')}\n")
        p.text(f"Caissier: {ticket.get('caissier_nom', '-')}\n")
        _sep(p, cols)

        # ---- EN-TETE TABLEAU ----
        p.set(bold=True)
        col_nom  = cols - 6 - 10 - 10 - 3  # qte(6) pu(10) total(10) spaces(3)
        header   = f"{'ARTICLE':<{col_nom}} {'QTE':>5} {'P.U.':>9} {'TOTAL':>9}"
        p.text(header[:cols] + "\n")
        p.set(bold=False)
        _sep(p, cols)

        # ---- LIGNES ----
        total_calc = 0
        for l in lignes:
            nom   = str(l["nom"])
            qte   = int(l["quantite"])
            pu    = float(l["prix_unit"])
            st    = float(l["sous_total"])
            total_calc += st

            # Si nom trop long, tronquer
            max_nom = col_nom
            if len(nom) > max_nom:
                nom = nom[:max_nom - 1] + "."

            ligne_str = f"{nom:<{col_nom}} {qte:>5} {pu:>9,.0f} {st:>9,.0f}"
            p.text(ligne_str[:cols] + "\n")

        _sep(p, cols)

        # ---- TOTAUX ----
        total    = float(ticket.get("total", 0))
        recu     = float(ticket.get("montant_recu", 0))
        manquant = total - recu if recu < total else 0
        monnaie  = recu - total if recu > total else 0

        p.set(bold=True, double_height=True)
        _ligne_2col(p, "TOTAL", f"{total:,.0f} FCFA", cols)
        p.set(bold=False, double_height=False)
        _ligne_2col(p, "Montant recu", f"{recu:,.0f} FCFA", cols)

        if monnaie > 0:
            _ligne_2col(p, "Monnaie rendue", f"{monnaie:,.0f} FCFA", cols)

        if manquant > 0:
            _sep(p, cols, "*")
            p.set(bold=True)
            _ligne_2col(p, "!! MANQUANT !!", f"{manquant:,.0f} FCFA", cols)
            p.set(bold=False)
            _sep(p, cols, "*")

        notes = ticket.get("notes", "")
        if notes and notes.strip():
            p.text(f"\nNote : {notes.strip()}\n")

        # ---- PIED ----
        _sep(p, cols, "=")
        p.set(align="center", bold=True)
        p.text("Merci pour votre confiance !\n")
        p.set(align="center", bold=False)
        p.text("CaveVin Manager v1.0.0\n")
        _sep(p, cols, "=")

        # Couper le papier + avancer
        p.text("\n\n\n")
        try:
            p.cut()
        except Exception:
            pass  # Pas toutes les imprimantes supportent la coupe

        p.close()
        return True

    except Exception as e:
        print(f"[THERMAL] Erreur impression : {e}")
        raise


def tester_imprimante() -> bool:
    """Imprime un ticket de test pour vérifier la connexion."""
    ticket_test = {
        "numero":       "TEST-001",
        "date_vente":   datetime.now().strftime("%Y-%m-%d"),
        "total":        5000,
        "montant_recu": 5000,
        "serveur_nom":  "Test Serveur",
        "caissier_nom": "Test Caissier",
        "notes":        "Ticket de test",
    }
    lignes_test = [
        {"nom": "Article Test 1", "quantite": 2, "prix_unit": 1500, "sous_total": 3000},
        {"nom": "Article Test 2", "quantite": 1, "prix_unit": 2000, "sous_total": 2000},
    ]
    return imprimer_ticket(ticket_test, lignes_test)
