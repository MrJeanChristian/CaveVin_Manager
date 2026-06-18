# ============================================================
# views/caissier/dashboard.py — Accueil caissier
# ============================================================

import customtkinter as ctk
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import COLORS, FONTS
from database.db import db


class CaissierDashboard(ctk.CTkFrame):
    def __init__(self, parent, user, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self.user = user
        self._build()

    def _build(self):
        C = COLORS
        ctk.CTkLabel(self, text=f"👋  Bonjour {self.user['prenom']} — Caissier",
                     font=FONTS["heading"], text_color=C["gold"]).pack(anchor="w", padx=24, pady=(20,6))
        ctk.CTkLabel(self, text=f"📅 {date.today().strftime('%A %d %B %Y').capitalize()}",
                     font=FONTS["body"], text_color=C["text_muted"]).pack(anchor="w", padx=24, pady=(0,16))

        kpis = self._get_kpis()
        kpi_row = ctk.CTkFrame(self, fg_color="transparent")
        kpi_row.pack(fill="x", padx=24)
        for title, val, icon, color in kpis:
            card = ctk.CTkFrame(kpi_row, fg_color=C["bg_card"], corner_radius=10,
                                 border_width=1, border_color=C["border"], width=190, height=100)
            card.pack(side="left", padx=(0,12))
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=icon, font=("Helvetica", 26)).pack(pady=(14,0))
            ctk.CTkLabel(card, text=val, font=("Georgia",15,"bold"), text_color=color).pack()
            ctk.CTkLabel(card, text=title, font=FONTS["small"], text_color=C["text_muted"]).pack()

        # Derniers manquants
        ctk.CTkLabel(self, text="⚠  Manquants non soldés",
                     font=FONTS["body"], text_color=C["danger"]).pack(anchor="w", padx=24, pady=(24,8))

        tbl = ctk.CTkFrame(self, fg_color=C["bg_card"], corner_radius=10,
                            border_width=1, border_color=C["border"])
        tbl.pack(fill="both", expand=True, padx=24, pady=(0,16))

        hdrs  = ["Serveur", "Montant", "Date", "Ticket"]
        widths= [200, 120, 120, 160]
        hrow = ctk.CTkFrame(tbl, fg_color=C["bg_sidebar"], corner_radius=0)
        hrow.pack(fill="x", padx=1, pady=(1,0))
        for h, w in zip(hdrs, widths):
            ctk.CTkLabel(hrow, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=8, pady=8)

        scroll = ctk.CTkScrollableFrame(tbl, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        rows = db.fetchall("""
            SELECT CONCAT(u.prenom,' ',u.nom) AS serveur, m.montant,
                   m.date_manquant, t.numero
            FROM manquants m
            JOIN utilisateurs u ON m.serveur_id=u.id
            LEFT JOIN tickets t ON m.ticket_id=t.id
            WHERE m.rembourse=0
            ORDER BY m.date_manquant DESC
            LIMIT 30
        """)
        for i, r in enumerate(rows):
            bg = C["bg_card"] if i%2==0 else C["bg_dark"]
            rf = ctk.CTkFrame(scroll, fg_color=bg, corner_radius=0)
            rf.pack(fill="x")
            for v, w in zip([r["serveur"], f"{r['montant']:,.0f} FCFA",
                              str(r["date_manquant"]), r["numero"] or "—"], widths):
                ctk.CTkLabel(rf, text=str(v), font=FONTS["small"],
                             text_color=C["text"], width=w, anchor="w").pack(side="left", padx=8, pady=7)

    def _get_kpis(self):
        C = COLORS; today = date.today()
        mois = today.strftime("%Y-%m")
        j = db.fetchone("SELECT COALESCE(SUM(total),0) AS v FROM tickets WHERE date_vente=%s AND statut='valide'",(today,)) or {"v":0}
        m = db.fetchone("SELECT COALESCE(SUM(total),0) AS v FROM tickets WHERE DATE_FORMAT(date_vente,'%%Y-%%m')=%s AND statut='valide'",(mois,)) or {"v":0}
        mq= db.fetchone("SELECT COALESCE(SUM(montant),0) AS v FROM manquants WHERE rembourse=0") or {"v":0}
        nt= db.fetchone("SELECT COUNT(*) AS v FROM tickets WHERE date_vente=%s AND statut='valide'",(today,)) or {"v":0}
        return [
            ("Ventes aujourd'hui",  f"{float(j['v']):,.0f} F", "💰", C["gold"]),
            ("Ventes ce mois",      f"{float(m['v']):,.0f} F", "📅", C["success"]),
            ("Tickets du jour",     str(nt["v"]),               "🧾", C["text"]),
            ("Manquants actifs",    f"{float(mq['v']):,.0f} F","⚠️", C["danger"]),
        ]
