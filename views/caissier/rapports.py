# ============================================================
# views/caissier/rapports.py — Bénéfices journaliers/mensuels + manquants

import customtkinter as ctk
from tkinter import messagebox
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import COLORS, FONTS
from database.db import db
from utils.pdf_ticket import generer_ticket_pdf, ouvrir_pdf

TICKETS_DIR = os.path.join(os.path.expanduser("~"), "CaveVin_Tickets")
os.makedirs(TICKETS_DIR, exist_ok=True)


class RapportsView(ctk.CTkFrame):
    def __init__(self, parent, user, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self.user = user
        self._build()
        self._load()

    def _build(self):
        C = COLORS
        # Titre + bouton actualiser
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20,0))
        ctk.CTkLabel(hdr, text="📊  Rapports & Manquants",
                     font=FONTS["heading"], text_color=C["gold"]).pack(side="left")
        ctk.CTkButton(hdr, text="🔄 Actualiser", width=130, height=34,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=FONTS["badge"], command=self._load).pack(side="right")

        # Filtre mois / semestre
        flt = ctk.CTkFrame(self, fg_color="transparent")
        flt.pack(fill="x", padx=24, pady=10)
        ctk.CTkLabel(flt, text="Mois (YYYY-MM) :", font=FONTS["small"],
                     text_color=C["text_muted"]).pack(side="left")
        self.e_mois = ctk.CTkEntry(flt, width=110, height=32,
                                    fg_color=C["bg_card"], border_color=C["border"],
                                    text_color=C["text"], font=FONTS["body"])
        self.e_mois.insert(0, date.today().strftime("%Y-%m"))
        self.e_mois.pack(side="left", padx=8)
        ctk.CTkButton(flt, text="Filtrer", width=80, height=32,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=FONTS["badge"], command=self._load).pack(side="left")

        # KPI row
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.pack(fill="x", padx=24, pady=(4,0))

        # Tabs
        tabs = ctk.CTkTabview(self, fg_color=C["bg_card"],
                               segmented_button_fg_color=C["bg_sidebar"],
                               segmented_button_selected_color=C["accent"],
                               segmented_button_unselected_color=C["bg_sidebar"],
                               segmented_button_selected_hover_color=C["accent2"],
                               text_color=C["text"])
        tabs.pack(fill="both", expand=True, padx=24, pady=12)
        self.tab_manquants = tabs.add("⚠ Manquants")
        self.tab_ventes    = tabs.add("💰 Ventes détaillées")
        self.tab_deductions= tabs.add("💸 Déductions salaires")

        self._build_tab_manquants()
        self._build_tab_ventes()
        self._build_tab_deductions()

    # ----------- Tabs construction -----------
    def _build_tab_manquants(self):
        C = COLORS
        t = self.tab_manquants
        hdrs   = ["Serveur", "Ticket", "Montant", "Date", "Remboursé", "Action"]
        widths = [140, 130, 100, 100, 90, 110]
        hrow = ctk.CTkFrame(t, fg_color=C["bg_sidebar"], corner_radius=0)
        hrow.pack(fill="x", padx=1, pady=(1,0))
        for h, w in zip(hdrs, widths):
            ctk.CTkLabel(hrow, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=6, pady=8)
        self.scroll_mq = ctk.CTkScrollableFrame(t, fg_color="transparent")
        self.scroll_mq.pack(fill="both", expand=True)

    def _build_tab_ventes(self):
        C = COLORS
        t = self.tab_ventes
        hdrs   = ["N° Ticket", "Serveur", "Date", "Total", "Reçu", "Manquant", "Statut"]
        widths = [130, 140, 100, 100, 100, 100, 90]
        hrow = ctk.CTkFrame(t, fg_color=C["bg_sidebar"], corner_radius=0)
        hrow.pack(fill="x", padx=1, pady=(1,0))
        for h, w in zip(hdrs, widths):
            ctk.CTkLabel(hrow, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=6, pady=8)
        self.scroll_vt = ctk.CTkScrollableFrame(t, fg_color="transparent")
        self.scroll_vt.pack(fill="both", expand=True)

    def _build_tab_deductions(self):
        C = COLORS
        t = self.tab_deductions
        hdrs   = ["Employé", "Mois", "Montant déduit", "Motif"]
        widths = [160, 90, 130, 300]
        hrow = ctk.CTkFrame(t, fg_color=C["bg_sidebar"], corner_radius=0)
        hrow.pack(fill="x", padx=1, pady=(1,0))
        for h, w in zip(hdrs, widths):
            ctk.CTkLabel(hrow, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=6, pady=8)
        self.scroll_dd = ctk.CTkScrollableFrame(t, fg_color="transparent")
        self.scroll_dd.pack(fill="both", expand=True)

    # ----------- Data load -----------
    def _load(self):
        mois = self.e_mois.get().strip()
        self._load_kpis(mois)
        self._load_manquants(mois)
        self._load_ventes(mois)
        self._load_deductions(mois)

    def _load_kpis(self, mois):
        C = COLORS
        for w in self.kpi_frame.winfo_children():
            w.destroy()

        today = date.today()
        year  = mois[:4] if mois else str(today.year)

        jour  = db.fetchone(
            "SELECT COALESCE(SUM(total),0) AS v FROM tickets WHERE date_vente=%s AND statut='valide'",
            (today,)) or {"v":0}
        mois_ = db.fetchone(
            "SELECT COALESCE(SUM(total),0) AS v FROM tickets WHERE DATE_FORMAT(date_vente,'%%Y-%%m')=%s AND statut='valide'",
            (mois,)) or {"v":0}
        semestre = db.fetchone(
            "SELECT COALESCE(SUM(total),0) AS v FROM tickets WHERE YEAR(date_vente)=%s AND MONTH(date_vente) BETWEEN 1 AND 6 AND statut='valide'",
            (year,)) or {"v":0}
        manq = db.fetchone(
            "SELECT COALESCE(SUM(montant),0) AS v FROM manquants WHERE rembourse=0") or {"v":0}

        kpis = [
            ("Ventes aujourd'hui",  f"{float(jour['v']):,.0f}", "💰", C["gold"]),
            ("Ventes ce mois",      f"{float(mois_['v']):,.0f}", "📅", C["success"]),
            ("Ventes S1 "+year,     f"{float(semestre['v']):,.0f}", "📈", C["text"]),
            ("Manquants actifs",    f"{float(manq['v']):,.0f}", "⚠️",  C["danger"]),
        ]
        for title, val, icon, color in kpis:
            card = ctk.CTkFrame(self.kpi_frame, fg_color=C["bg_card"], corner_radius=10,
                                 border_width=1, border_color=C["border"], width=170, height=88)
            card.pack(side="left", padx=(0,10))
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=icon+"  "+val+" FCFA", font=("Georgia",13,"bold"),
                         text_color=color, wraplength=160).pack(pady=(16,2))
            ctk.CTkLabel(card, text=title, font=FONTS["small"],
                         text_color=C["text_muted"]).pack()

    def _load_manquants(self, mois):
        for w in self.scroll_mq.winfo_children():
            w.destroy()
        rows = db.fetchall("""
            SELECT m.id, CONCAT(u.prenom,' ',u.nom) AS serveur,
                   t.numero AS ticket, m.montant, m.date_manquant, m.rembourse
            FROM manquants m
            JOIN utilisateurs u ON m.serveur_id=u.id
            LEFT JOIN tickets t ON m.ticket_id=t.id
            WHERE DATE_FORMAT(m.date_manquant,'%%Y-%%m')=%s
            ORDER BY m.date_manquant DESC
        """, (mois,))
        C = COLORS
        for i, r in enumerate(rows):
            bg = C["bg_card"] if i%2==0 else C["bg_dark"]
            rf = ctk.CTkFrame(self.scroll_mq, fg_color=bg, corner_radius=0)
            rf.pack(fill="x")
            rembourse = "✅ Oui" if r["rembourse"] else "❌ Non"
            vals  = [r["serveur"], r["ticket"] or "—", f"{r['montant']:,.0f}", str(r["date_manquant"]), rembourse]
            widths= [140, 130, 100, 100, 90]
            for v, w in zip(vals, widths):
                tc = C["success"] if v == "✅ Oui" else (C["danger"] if v == "❌ Non" else C["text"])
                ctk.CTkLabel(rf, text=str(v), font=FONTS["small"],
                             text_color=tc, width=w, anchor="w").pack(side="left", padx=6, pady=7)
            # Bouton déduire
            mid = r["id"]
            ctk.CTkButton(rf, text="💸 Déduire", width=90, height=28,
                          fg_color=C["accent2"], hover_color=C["accent"],
                          font=FONTS["small"],
                          command=lambda mid=mid: self._deduire(mid)).pack(side="left", padx=4)

    def _load_ventes(self, mois):
        for w in self.scroll_vt.winfo_children():
            w.destroy()
        rows = db.fetchall("""
            SELECT t.numero, CONCAT(u.prenom,' ',u.nom) AS serveur,
                   t.date_vente, t.total, t.montant_recu, t.statut,
                   (t.total - t.montant_recu) AS diff
            FROM tickets t
            LEFT JOIN utilisateurs u ON t.serveur_id=u.id
            WHERE DATE_FORMAT(t.date_vente,'%%Y-%%m')=%s
            ORDER BY t.date_vente DESC
        """, (mois,))
        C = COLORS
        for i, r in enumerate(rows):
            bg = C["bg_card"] if i%2==0 else C["bg_dark"]
            rf = ctk.CTkFrame(self.scroll_vt, fg_color=bg, corner_radius=0)
            rf.pack(fill="x")
            diff = float(r["diff"] or 0)
            diff_txt = f"{diff:,.0f}" if diff != 0 else "—"
            vals  = [r["numero"], r["serveur"] or "—", str(r["date_vente"]),
                     f"{r['total']:,.0f}", f"{r['montant_recu']:,.0f}", diff_txt,
                     r["statut"].replace("_"," ").title()]
            widths= [130,140,100,100,100,100,90]
            for v, w in zip(vals, widths):
                tc = C["danger"] if v == diff_txt and diff > 0 else C["text"]
                ctk.CTkLabel(rf, text=str(v), font=FONTS["small"],
                             text_color=tc, width=w, anchor="w").pack(side="left", padx=6, pady=7)

    def _load_deductions(self, mois):
        for w in self.scroll_dd.winfo_children():
            w.destroy()
        rows = db.fetchall("""
            SELECT CONCAT(u.prenom,' ',u.nom) AS employe, d.mois, d.montant, d.motif
            FROM deductions d
            JOIN utilisateurs u ON d.employe_id=u.id
            WHERE d.mois=%s
            ORDER BY d.created_at DESC
        """, (mois,))
        C = COLORS
        for i, r in enumerate(rows):
            bg = C["bg_card"] if i%2==0 else C["bg_dark"]
            rf = ctk.CTkFrame(self.scroll_dd, fg_color=bg, corner_radius=0)
            rf.pack(fill="x")
            vals  = [r["employe"], r["mois"] or "—", f"{r['montant']:,.0f}", r["motif"] or "—"]
            widths= [160, 90, 130, 300]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(rf, text=str(v), font=FONTS["small"],
                             text_color=C["text"], width=w, anchor="w").pack(side="left", padx=6, pady=7)

    def _deduire(self, manquant_id):
        mq = db.fetchone("""
            SELECT m.*, CONCAT(u.prenom,' ',u.nom) AS snom, u.id AS uid
            FROM manquants m JOIN utilisateurs u ON m.serveur_id=u.id
            WHERE m.id=%s
        """, (manquant_id,))
        if not mq:
            messagebox.showerror("Erreur","Manquant introuvable."); return
        if mq["rembourse"]:
            messagebox.showinfo("Info","Ce manquant a déjà été soldé."); return

        mois = date.today().strftime("%Y-%m")
        if messagebox.askyesno("Déduire du salaire",
            f"Déduire {float(mq['montant']):,.0f} FCFA du salaire de {mq['snom']} ({mois}) ?"):
            db.execute(
                "INSERT INTO deductions (employe_id,manquant_id,montant,motif,mois) VALUES (%s,%s,%s,%s,%s)",
                (mq["uid"], manquant_id, mq["montant"],
                 f"Manquant ticket {mq.get('ticket_id','N/A')}", mois), commit=True
            )
            db.execute("UPDATE manquants SET rembourse=1 WHERE id=%s",(manquant_id,),commit=True)
            messagebox.showinfo("Succès",f"Déduction enregistrée pour {mq['snom']}.")
            self._load()
