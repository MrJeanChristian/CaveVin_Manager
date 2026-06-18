# ============================================================
# views/serveur/dashboard.py — Espace Serveur
# ============================================================

import customtkinter as ctk
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import COLORS, FONTS
from database.db import db


class ServeurDashboard(ctk.CTkFrame):
    def __init__(self, parent, user, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self.user = user
        self._build()

    def _build(self):
        C = COLORS
        uid = self.user["id"]

        ctk.CTkLabel(self, text=f"🍷  Mon espace — {self.user['prenom']} {self.user['nom']}",
                     font=FONTS["heading"], text_color=C["gold"]).pack(anchor="w", padx=24, pady=(20,6))

        # KPIs personnels
        mois  = date.today().strftime("%Y-%m")
        mq_tot= db.fetchone("SELECT COALESCE(SUM(montant),0) AS v FROM manquants WHERE serveur_id=%s AND rembourse=0",(uid,)) or {"v":0}
        mq_mo = db.fetchone("SELECT COALESCE(SUM(montant),0) AS v FROM manquants WHERE serveur_id=%s AND DATE_FORMAT(date_manquant,'%%Y-%%m')=%s",(uid,mois)) or {"v":0}
        ded   = db.fetchone("SELECT COALESCE(SUM(montant),0) AS v FROM deductions WHERE employe_id=%s AND mois=%s",(uid,mois)) or {"v":0}
        tkt   = db.fetchone("SELECT COUNT(*) AS v FROM tickets WHERE serveur_id=%s AND DATE_FORMAT(date_vente,'%%Y-%%m')=%s AND statut='valide'",(uid,mois)) or {"v":0}
        sal   = float(self.user.get("salaire",0))
        net   = sal - float(ded["v"])

        kpis = [
            ("Mes tickets ce mois",    str(tkt["v"]),                   "🧾", C["text"]),
            ("Manquants non soldés",   f"{float(mq_tot['v']):,.0f} F", "⚠️", C["danger"]),
            ("Manquants ce mois",      f"{float(mq_mo['v']):,.0f} F",  "📋", C["gold"]),
            ("Déductions ce mois",     f"{float(ded['v']):,.0f} F",    "💸", C["danger"]),
            ("Salaire net estimé",     f"{net:,.0f} F",                 "💰", C["success"]),
        ]
        kpi_row = ctk.CTkFrame(self, fg_color="transparent")
        kpi_row.pack(fill="x", padx=24, pady=10)
        for title, val, icon, color in kpis:
            card = ctk.CTkFrame(kpi_row, fg_color=C["bg_card"], corner_radius=10,
                                 border_width=1, border_color=C["border"], width=176, height=96)
            card.pack(side="left", padx=(0,10))
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=icon, font=("Helvetica",24)).pack(pady=(12,0))
            ctk.CTkLabel(card, text=val, font=("Georgia",13,"bold"), text_color=color).pack()
            ctk.CTkLabel(card, text=title, font=FONTS["small"],
                         text_color=C["text_muted"], wraplength=165).pack()

        # Mes manquants
        ctk.CTkLabel(self, text="📋 Mes manquants",
                     font=FONTS["body"], text_color=C["text_muted"]).pack(anchor="w", padx=24, pady=(16,6))

        tbl = ctk.CTkFrame(self, fg_color=C["bg_card"], corner_radius=10,
                            border_width=1, border_color=C["border"])
        tbl.pack(fill="both", expand=True, padx=24, pady=(0,16))

        hdrs  = ["Date", "Ticket", "Montant", "Remboursé"]
        widths= [110, 160, 120, 110]
        hrow = ctk.CTkFrame(tbl, fg_color=C["bg_sidebar"], corner_radius=0)
        hrow.pack(fill="x", padx=1, pady=(1,0))
        for h, w in zip(hdrs, widths):
            ctk.CTkLabel(hrow, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=8, pady=8)

        scroll = ctk.CTkScrollableFrame(tbl, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        rows = db.fetchall("""
            SELECT m.date_manquant, t.numero, m.montant, m.rembourse
            FROM manquants m
            LEFT JOIN tickets t ON m.ticket_id=t.id
            WHERE m.serveur_id=%s
            ORDER BY m.date_manquant DESC
            LIMIT 50
        """, (uid,))
        for i, r in enumerate(rows):
            bg = C["bg_card"] if i%2==0 else C["bg_dark"]
            rf = ctk.CTkFrame(scroll, fg_color=bg, corner_radius=0)
            rf.pack(fill="x")
            remb = "✅ Oui" if r["rembourse"] else "❌ Non"
            vals = [str(r["date_manquant"]), r["numero"] or "—",
                    f"{r['montant']:,.0f} FCFA", remb]
            for v, w in zip(vals, widths):
                tc = C["success"] if v == "✅ Oui" else (C["danger"] if v == "❌ Non" else C["text"])
                ctk.CTkLabel(rf, text=str(v), font=FONTS["small"],
                             text_color=tc, width=w, anchor="w").pack(side="left", padx=8, pady=7)
