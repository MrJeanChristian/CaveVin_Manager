# ============================================================
# utils/pdf_ticket.py — Génération de ticket PDF (format reçu)
# ============================================================

import os, tempfile, subprocess, platform
from datetime import datetime
from io import BytesIO

from reportlab.lib.units import mm as MM
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

try:
    import qrcode
    HAS_QR = True
except ImportError:
    HAS_QR = False


TICKET_W = 80 * MM
MARGIN   = 5 * MM

ROUGE_VIN = colors.HexColor("#C0392B")
OR        = colors.HexColor("#D4AC0D")
NOIR      = colors.black
GRIS      = colors.HexColor("#555555")
BLANC     = colors.white


def generer_ticket_pdf(ticket: dict, lignes: list, output_path: str = None) -> str:
    if output_path is None:
        tmp_dir     = tempfile.mkdtemp()
        output_path = os.path.join(tmp_dir, f"ticket_{ticket['numero']}.pdf")

    n_lignes = len(lignes)
    ticket_h = (
        35 * MM
        + 8  * MM
        + 10 * MM
        + n_lignes * 9 * MM
        + 30 * MM
        + (18 * MM if HAS_QR else 0)
        + 18 * MM
    )

    c = canvas.Canvas(output_path, pagesize=(TICKET_W, ticket_h))
    y = ticket_h

    def line(x1, y1, x2, y2, color=GRIS, width=0.5):
        c.setStrokeColor(color)
        c.setLineWidth(width)
        c.line(x1, y1, x2, y2)

    def text(txt, x, y_, font="Helvetica", size=8, color=NOIR, align="left"):
        c.setFont(font, size)
        c.setFillColor(color)
        if align == "center":
            c.drawCentredString(x, y_, txt)
        elif align == "right":
            c.drawRightString(x, y_, txt)
        else:
            c.drawString(x, y_, txt)

    # -- EN-TETE --
    y -= 6 * MM
    text("CAVE A VIN", TICKET_W / 2, y, "Helvetica-Bold", 13, ROUGE_VIN, "center")
    y -= 5 * MM
    text("CaveVin Manager", TICKET_W / 2, y, "Helvetica", 7, GRIS, "center")
    y -= 5 * MM
    line(MARGIN, y, TICKET_W - MARGIN, y, ROUGE_VIN, 1.2)

    # -- INFOS --
    y -= 5 * MM
    text(f"Ticket : {ticket['numero']}", MARGIN, y, "Helvetica-Bold", 8)
    y -= 4 * MM
    date_str = str(ticket.get("date_vente", "")).split(" ")[0]
    heure    = datetime.now().strftime("%H:%M")
    text(f"Date   : {date_str}  {heure}", MARGIN, y, size=7, color=GRIS)
    y -= 4 * MM
    text(f"Serveur  : {ticket.get('serveur_nom', '-')}", MARGIN, y, size=7, color=GRIS)
    y -= 4 * MM
    text(f"Caissier : {ticket.get('caissier_nom', '-')}", MARGIN, y, size=7, color=GRIS)
    y -= 2 * MM
    line(MARGIN, y, TICKET_W - MARGIN, y)

    # -- EN-TETE TABLEAU --
    y -= 6 * MM
    text("ARTICLE",   MARGIN,          y, "Helvetica-Bold", 7.5)
    text("QTE",       42 * MM,         y, "Helvetica-Bold", 7.5, align="center")
    text("P.U.",      54 * MM,         y, "Helvetica-Bold", 7.5, align="right")
    text("TOTAL",     TICKET_W-MARGIN, y, "Helvetica-Bold", 7.5, align="right")
    y -= 1.5 * MM
    line(MARGIN, y, TICKET_W - MARGIN, y, NOIR, 0.8)

    # -- LIGNES --
    for i, l in enumerate(lignes):
        y -= 7 * MM
        bg = colors.HexColor("#FFF8F8") if i % 2 == 0 else BLANC
        c.setFillColor(bg)
        c.rect(MARGIN, y - 1*MM, TICKET_W - 2*MARGIN, 7*MM, fill=1, stroke=0)
        nom = str(l["nom"])
        if len(nom) > 20:
            nom = nom[:18] + ".."
        pv = float(l["prix_unit"])
        st = float(l["sous_total"])
        text(nom,               MARGIN + 1*MM,   y + 1.5*MM, size=7.5, color=NOIR)
        text(str(l["quantite"]),42 * MM,          y + 1.5*MM, size=7.5, align="center")
        text(f"{pv:,.0f}",      54 * MM,          y + 1.5*MM, size=7.5, align="right")
        text(f"{st:,.0f}",      TICKET_W-MARGIN,  y + 1.5*MM, size=7.5, align="right")

    y -= 1.5 * MM
    line(MARGIN, y, TICKET_W - MARGIN, y, NOIR, 0.8)

    # -- TOTAUX --
    total    = float(ticket.get("total", 0))
    recu     = float(ticket.get("montant_recu", 0))
    manquant = total - recu if recu < total else 0
    monnaie  = recu - total if recu > total else 0

    y -= 6 * MM
    text("TOTAL",      MARGIN,          y, "Helvetica-Bold", 9)
    text(f"{total:,.0f} FCFA", TICKET_W-MARGIN, y, "Helvetica-Bold", 9, align="right")
    y -= 5 * MM
    text("Montant recu", MARGIN, y, size=8, color=GRIS)
    text(f"{recu:,.0f} FCFA", TICKET_W-MARGIN, y, size=8, color=GRIS, align="right")
    if monnaie > 0:
        y -= 4.5 * MM
        text("Monnaie rendue", MARGIN, y, size=8, color=GRIS)
        text(f"{monnaie:,.0f} FCFA", TICKET_W-MARGIN, y, size=8, color=GRIS, align="right")
    if manquant > 0:
        y -= 5 * MM
        c.setFillColor(colors.HexColor("#FFF0F0"))
        c.roundRect(MARGIN, y - 2*MM, TICKET_W - 2*MARGIN, 8*MM, 2*MM, fill=1, stroke=0)
        text("MANQUANT",     MARGIN + 2*MM,       y + 1.5*MM, "Helvetica-Bold", 8, ROUGE_VIN)
        text(f"{manquant:,.0f} FCFA", TICKET_W-MARGIN-2*MM, y+1.5*MM,
             "Helvetica-Bold", 8, ROUGE_VIN, align="right")

    notes = ticket.get("notes", "")
    if notes and notes.strip():
        y -= 5 * MM
        text(f"Note : {notes.strip()}", MARGIN, y, size=7, color=GRIS)

    # -- QR CODE --
    if HAS_QR:
        y -= 3 * MM
        line(MARGIN, y, TICKET_W - MARGIN, y)
        y -= 1 * MM
        qr_data = (
            f"TICKET:{ticket['numero']}\n"
            f"DATE:{date_str}\n"
            f"TOTAL:{total:.0f} FCFA\n"
            f"SERVEUR:{ticket.get('serveur_nom','')}"
        )
        qr     = qrcode.make(qr_data)
        qr_size= 18 * MM
        buf    = BytesIO()
        qr.save(buf, format="PNG")
        buf.seek(0)
        y -= qr_size
        c.drawImage(ImageReader(buf), (TICKET_W - qr_size) / 2, y, qr_size, qr_size)
        y -= 3 * MM
        text("Scannez pour verifier", TICKET_W/2, y, size=6, color=GRIS, align="center")

    # -- PIED --
    y -= 4 * MM
    line(MARGIN, y, TICKET_W - MARGIN, y, ROUGE_VIN, 1.2)
    y -= 5 * MM
    text("Merci pour votre confiance !", TICKET_W/2, y, "Helvetica-Bold", 8, OR, "center")
    y -= 4 * MM
    text("CaveVin Manager v1.0.0", TICKET_W/2, y, size=6, color=GRIS, align="center")

    c.save()
    return output_path


def ouvrir_pdf(path: str):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        print(f"[PDF] Impossible d'ouvrir : {e}")
