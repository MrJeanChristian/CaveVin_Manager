# ============================================================
# views/caissier/historique.py — Historique + Reimpression PDF
# ============================================================

import customtkinter as ctk
from tkinter import messagebox, filedialog
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import COLORS, FONTS
from database.db import db
from utils.pdf_ticket import generer_ticket_pdf, ouvrir_pdf

TICKETS_DIR = os.path.join(os.path.expanduser("~"), "CaveVin_Tickets")
os.makedirs(TICKETS_DIR, exist_ok=True)


class HistoriqueView(ctk.CTkFrame):
    def __init__(self, parent, user, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self.user = user
        self._build()
        self._load()

    def _build(self):
        C = COLORS
        # ---- Header ----
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 0))
        ctk.CTkLabel(hdr, text="  Historique des Tickets",
                     font=FONTS["heading"], text_color=C["gold"]).pack(side="left")
        ctk.CTkButton(hdr, text=" Actualiser", width=120, height=34,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=FONTS["badge"], command=self._load).pack(side="right")

        # ---- Filtres ----
        flt = ctk.CTkFrame(self, fg_color=C["bg_card"], corner_radius=10,
                            border_width=1, border_color=C["border"])
        flt.pack(fill="x", padx=24, pady=12)

        ctk.CTkLabel(flt, text="Filtres :", font=FONTS["body"],
                     text_color=C["text_muted"]).pack(side="left", padx=12, pady=10)

        ctk.CTkLabel(flt, text="Mois", font=FONTS["small"],
                     text_color=C["text_muted"]).pack(side="left", padx=(8, 2))
        self.e_mois = ctk.CTkEntry(flt, width=100, height=32,
                                    fg_color=C["bg_dark"], border_color=C["border"],
                                    text_color=C["text"], font=FONTS["body"])
        self.e_mois.insert(0, date.today().strftime("%Y-%m"))
        self.e_mois.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(flt, text="Serveur", font=FONTS["small"],
                     text_color=C["text_muted"]).pack(side="left", padx=(0, 2))
        self.serveur_var = ctk.StringVar(value="Tous")
        self.cb_serveur  = ctk.CTkComboBox(flt, variable=self.serveur_var,
                                            width=160, height=32,
                                            fg_color=C["bg_dark"], border_color=C["border"],
                                            button_color=C["accent"], text_color=C["text"],
                                            font=FONTS["body"])
        self.cb_serveur.pack(side="left", padx=(0, 12))
        self._load_serveurs()

        ctk.CTkLabel(flt, text="N° ticket", font=FONTS["small"],
                     text_color=C["text_muted"]).pack(side="left", padx=(0, 2))
        self.e_search = ctk.CTkEntry(flt, width=140, height=32,
                                      fg_color=C["bg_dark"], border_color=C["border"],
                                      text_color=C["text"], font=FONTS["body"],
                                      placeholder_text="Rechercher...")
        self.e_search.pack(side="left", padx=(0, 12))
        self.e_search.bind("<Return>", lambda e: self._load())

        ctk.CTkButton(flt, text="Filtrer", width=80, height=32,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=FONTS["badge"], command=self._load).pack(side="left")

        # ---- Corps : liste + detail ----
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # -- Liste tickets --
        lst = ctk.CTkFrame(body, fg_color=C["bg_card"], corner_radius=10,
                            border_width=1, border_color=C["border"])
        lst.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        hdrs   = ["N° Ticket", "Serveur", "Date", "Total", "Recu", "Statut"]
        widths = [150, 150, 100, 110, 110, 90]
        hrow = ctk.CTkFrame(lst, fg_color=C["bg_sidebar"], corner_radius=0)
        hrow.pack(fill="x", padx=1, pady=(1, 0))
        for h, w in zip(hdrs, widths):
            ctk.CTkLabel(hrow, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=6, pady=8)

        self.scroll_list = ctk.CTkScrollableFrame(lst, fg_color="transparent")
        self.scroll_list.pack(fill="both", expand=True)

        # -- Detail + actions --
        detail = ctk.CTkFrame(body, fg_color=C["bg_card"], corner_radius=10,
                               border_width=1, border_color=C["border"])
        detail.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(detail, text="Detail du ticket",
                     font=FONTS["heading"], text_color=C["gold"]).pack(pady=(16, 8))

        self.lbl_info = ctk.CTkLabel(detail, text="Cliquez sur un ticket",
                                      font=FONTS["body"], text_color=C["text_muted"],
                                      wraplength=280, justify="left")
        self.lbl_info.pack(padx=14, pady=4, anchor="w")

        # Sous-tableau lignes
        detail_hdrs   = ["Article", "Qte", "P.U.", "S.Total"]
        detail_widths = [130, 40, 80, 80]
        dhrow = ctk.CTkFrame(detail, fg_color=C["bg_sidebar"], corner_radius=0)
        dhrow.pack(fill="x", padx=1, pady=(8, 0))
        for h, w in zip(detail_hdrs, detail_widths):
            ctk.CTkLabel(dhrow, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=4, pady=6)

        self.scroll_detail = ctk.CTkScrollableFrame(detail, fg_color="transparent", height=160)
        self.scroll_detail.pack(fill="x", padx=1)

        self.lbl_total_detail = ctk.CTkLabel(detail, text="",
                                              font=("Georgia", 14, "bold"), text_color=C["gold"])
        self.lbl_total_detail.pack(pady=8)

        # Boutons actions
        ctk.CTkButton(detail, text="  Imprimer PDF", height=42,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      text_color=C["white"], font=("Helvetica", 12, "bold"),
                      command=self._imprimer).pack(fill="x", padx=14, pady=(0, 6))
        ctk.CTkButton(detail, text="  Enregistrer PDF...", height=36,
                      fg_color=C["bg_dark"], hover_color=C["bg_sidebar"],
                      text_color=C["text"], font=FONTS["body"],
                      command=self._enregistrer_sous).pack(fill="x", padx=14, pady=(0, 6))
        ctk.CTkButton(detail, text="  Dossier tickets", height=34,
                      fg_color="transparent", hover_color=C["bg_sidebar"],
                      text_color=C["text_muted"], font=FONTS["small"],
                      command=lambda: ouvrir_pdf(TICKETS_DIR)).pack(fill="x", padx=14, pady=(0, 14))

        self._selected_ticket = None

    # ---------------------------------------------------------------- Data --
    def _load_serveurs(self):
        rows = db.fetchall(
            "SELECT CONCAT(prenom,' ',nom) AS nom FROM utilisateurs WHERE role='serveur' AND actif=1"
        )
        vals = ["Tous"] + [r["nom"] for r in rows]
        self.cb_serveur.configure(values=vals)
        self.serveur_var.set("Tous")

    def _load(self):
        mois    = self.e_mois.get().strip()
        serveur = self.serveur_var.get()
        search  = self.e_search.get().strip()

        query  = """
            SELECT t.id, t.numero, CONCAT(u.prenom,' ',u.nom) AS serveur_nom,
                   t.date_vente, t.total, t.montant_recu, t.statut, t.notes,
                   t.caissier_id
            FROM tickets t
            LEFT JOIN utilisateurs u ON t.serveur_id=u.id
            WHERE DATE_FORMAT(t.date_vente,'%%Y-%%m') = %s
        """
        params = [mois]

        if serveur != "Tous":
            query  += " AND CONCAT(u.prenom,' ',u.nom) = %s"
            params.append(serveur)
        if search:
            query  += " AND t.numero LIKE %s"
            params.append(f"%{search}%")

        query += " ORDER BY t.date_vente DESC, t.id DESC LIMIT 200"
        rows   = db.fetchall(query, params)

        C = COLORS
        for w in self.scroll_list.winfo_children():
            w.destroy()

        statut_col = {"en_attente": C["gold"], "valide": C["success"], "annule": C["danger"]}
        for i, r in enumerate(rows):
            bg = C["bg_card"] if i % 2 == 0 else C["bg_dark"]
            rf = ctk.CTkFrame(self.scroll_list, fg_color=bg, corner_radius=0)
            rf.pack(fill="x")
            vals   = [r["numero"], r["serveur_nom"] or "—", str(r["date_vente"]),
                      f"{r['total']:,.0f}", f"{r['montant_recu']:,.0f}",
                      r["statut"].replace("_"," ").title()]
            widths = [150, 150, 100, 110, 110, 90]
            for v, w in zip(vals, widths):
                tc = statut_col.get(r["statut"], C["text"]) if v == vals[-1] else C["text"]
                ctk.CTkLabel(rf, text=str(v), font=FONTS["small"],
                             text_color=tc, width=w, anchor="w").pack(side="left", padx=6, pady=7)
            rf.bind("<Button-1>", lambda e, row=r: self._select(row))
            for child in rf.winfo_children():
                child.bind("<Button-1>", lambda e, row=r: self._select(row))

    def _select(self, row):
        C = COLORS
        self._selected_ticket = row
        manquant = float(row["total"]) - float(row["montant_recu"])

        info = (
            f"N° : {row['numero']}\n"
            f"Serveur  : {row['serveur_nom'] or '-'}\n"
            f"Date     : {row['date_vente']}\n"
            f"Total    : {float(row['total']):,.0f} FCFA\n"
            f"Recu     : {float(row['montant_recu']):,.0f} FCFA\n"
        )
        if manquant > 0:
            info += f"Manquant : {manquant:,.0f} FCFA\n"
        if row.get("notes"):
            info += f"Note     : {row['notes']}\n"

        self.lbl_info.configure(text=info, text_color=C["text"])

        # Charger les lignes
        lignes = db.fetchall("""
            SELECT b.nom, tl.quantite, tl.prix_unit, tl.sous_total
            FROM ticket_lignes tl
            JOIN boissons b ON tl.boisson_id=b.id
            WHERE tl.ticket_id=%s
        """, (row["id"],))

        for w in self.scroll_detail.winfo_children():
            w.destroy()

        total = 0
        for i, l in enumerate(lignes):
            bg = C["bg_card"] if i % 2 == 0 else C["bg_dark"]
            rf = ctk.CTkFrame(self.scroll_detail, fg_color=bg, corner_radius=0)
            rf.pack(fill="x")
            st = float(l["sous_total"])
            total += st
            nom = l["nom"]
            if len(nom) > 18: nom = nom[:16] + ".."
            vals   = [nom, str(l["quantite"]), f"{float(l['prix_unit']):,.0f}", f"{st:,.0f}"]
            widths = [130, 40, 80, 80]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(rf, text=str(v), font=FONTS["small"],
                             text_color=C["text"], width=w, anchor="w").pack(side="left", padx=4, pady=5)

        self.lbl_total_detail.configure(text=f"TOTAL : {total:,.0f} FCFA")
        self._lignes_cache = lignes

    def _get_ticket_data_and_lignes(self):
        if not self._selected_ticket:
            messagebox.showwarning("Attention", "Selectionnez un ticket d'abord.")
            return None, None
        row = self._selected_ticket
        caissier_row = db.fetchone(
            "SELECT CONCAT(prenom,' ',nom) AS nom FROM utilisateurs WHERE id=%s",
            (row["caissier_id"],)
        )
        ticket_data = {
            "numero":       row["numero"],
            "date_vente":   row["date_vente"],
            "total":        float(row["total"]),
            "montant_recu": float(row["montant_recu"]),
            "serveur_nom":  row["serveur_nom"] or "—",
            "caissier_nom": caissier_row["nom"] if caissier_row else "—",
            "notes":        row.get("notes", ""),
        }
        pdf_lignes = [
            {"nom": l["nom"], "quantite": l["quantite"],
             "prix_unit": float(l["prix_unit"]), "sous_total": float(l["sous_total"])}
            for l in self._lignes_cache
        ]
        return ticket_data, pdf_lignes

    def _imprimer(self):
        ticket_data, pdf_lignes = self._get_ticket_data_and_lignes()
        if not ticket_data: return
        pdf_path = os.path.join(TICKETS_DIR, f"{ticket_data['numero']}.pdf")
        try:
            generer_ticket_pdf(ticket_data, pdf_lignes, pdf_path)
            ouvrir_pdf(pdf_path)
        except Exception as e:
            messagebox.showerror("Erreur PDF", f"Erreur lors de la generation :\n{e}")

    def _enregistrer_sous(self):
        ticket_data, pdf_lignes = self._get_ticket_data_and_lignes()
        if not ticket_data: return
        chemin = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"ticket_{ticket_data['numero']}.pdf",
            title="Enregistrer le ticket PDF"
        )
        if not chemin: return
        try:
            generer_ticket_pdf(ticket_data, pdf_lignes, chemin)
            messagebox.showinfo("Enregistre", f"PDF sauvegarde :\n{chemin}")
            ouvrir_pdf(chemin)
        except Exception as e:
            messagebox.showerror("Erreur PDF", str(e))
