# ============================================================
# views/admin/dashboard.py — Vue d'ensemble Admin
# ============================================================

import customtkinter as ctk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import COLORS, FONTS
from database.db import db
from datetime import date


class AdminDashboard(ctk.CTkFrame):
    def __init__(self, parent, user, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self.user = user
        self._build()

    def _build(self):
        C = COLORS
        # Titre
        ctk.CTkLabel(self, text=f"🏠  Tableau de bord — Bonjour {self.user['prenom']} !",
                     font=FONTS["heading"], text_color=C["gold"]).pack(anchor="w", padx=24, pady=(20,16))

        # KPI cards
        kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame.pack(fill="x", padx=24)

        kpis = self._get_kpis()
        for title, val, icon, color in kpis:
            self._kpi_card(kpi_frame, title, val, icon, color)

        # Section rapide : derniers tickets
        ctk.CTkLabel(self, text="📋 Derniers tickets saisis",
                     font=FONTS["body"], text_color=C["text_muted"]).pack(anchor="w", padx=24, pady=(24,8))

        tbl = ctk.CTkFrame(self, fg_color=C["bg_card"], corner_radius=10,
                            border_width=1, border_color=C["border"])
        tbl.pack(fill="x", padx=24, pady=(0,16))

        hdrs  = ["N° Ticket", "Serveur", "Date", "Total", "Statut"]
        widths= [120, 160, 110, 110, 100]
        hrow = ctk.CTkFrame(tbl, fg_color=C["bg_sidebar"], corner_radius=0)
        hrow.pack(fill="x", padx=1, pady=(1,0))
        for h, w in zip(hdrs, widths):
            ctk.CTkLabel(hrow, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=8, pady=8)

        scroll = ctk.CTkScrollableFrame(tbl, fg_color="transparent", height=180)
        scroll.pack(fill="x")

        tickets = db.fetchall("""
            SELECT t.numero, CONCAT(u.prenom,' ',u.nom) AS serveur,
                   t.date_vente, t.total, t.statut
            FROM tickets t
            LEFT JOIN utilisateurs u ON t.serveur_id=u.id
            ORDER BY t.created_at DESC LIMIT 20
        """)
        statut_colors = {"en_attente": C["gold"], "valide": C["success"], "annule": C["danger"]}
        for i, r in enumerate(tickets):
            bg = C["bg_card"] if i%2==0 else C["bg_dark"]
            rf = ctk.CTkFrame(scroll, fg_color=bg, corner_radius=0)
            rf.pack(fill="x")
            vals = [r["numero"], r["serveur"] or "—",
                    str(r["date_vente"]), f"{r['total']:,.0f} FCFA", r["statut"].replace("_"," ").title()]
            for v, w in zip(vals, widths):
                sc = statut_colors.get(r["statut"], C["text"]) if v == vals[-1] else C["text"]
                ctk.CTkLabel(rf, text=str(v), font=FONTS["small"],
                             text_color=sc, width=w, anchor="w").pack(side="left", padx=8, pady=7)

    def _kpi_card(self, parent, title, value, icon, color):
        C = COLORS
        card = ctk.CTkFrame(parent, fg_color=C["bg_card"], corner_radius=10,
                             border_width=1, border_color=C["border"], width=180, height=100)
        card.pack(side="left", padx=(0,12), pady=4)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=icon, font=("Helvetica", 26)).pack(pady=(14,0))
        ctk.CTkLabel(card, text=value, font=("Georgia", 16, "bold"),
                     text_color=color).pack()
        ctk.CTkLabel(card, text=title, font=FONTS["small"],
                     text_color=C["text_muted"]).pack()

    def _get_kpis(self):
        today = date.today()
        month = today.strftime("%Y-%m")

        total_jour = db.fetchone(
            "SELECT COALESCE(SUM(total),0) AS v FROM tickets WHERE date_vente=%s AND statut='valide'",
            (today,)) or {"v": 0}
        total_mois = db.fetchone(
            "SELECT COALESCE(SUM(total),0) AS v FROM tickets WHERE DATE_FORMAT(date_vente,'%%Y-%%m')=%s AND statut='valide'",
            (month,)) or {"v": 0}
        nb_employes = db.fetchone(
            "SELECT COUNT(*) AS v FROM utilisateurs WHERE actif=1 AND role!='admin'") or {"v": 0}
        nb_boissons = db.fetchone(
            "SELECT COUNT(*) AS v FROM boissons WHERE actif=1") or {"v": 0}
        manquants = db.fetchone(
            "SELECT COALESCE(SUM(montant),0) AS v FROM manquants WHERE rembourse=0") or {"v": 0}

        return [
            ("Ventes aujourd'hui",  f"{float(total_jour['v']):,.0f} FCFA",  "💰", COLORS["gold"]),
            ("Ventes ce mois",      f"{float(total_mois['v']):,.0f} FCFA",  "📈", COLORS["success"]),
            ("Employés actifs",     str(nb_employes["v"]),                   "👥", COLORS["text"]),
            ("Boissons en catalogue",str(nb_boissons["v"]),                  "🍾", COLORS["accent"]),
            ("Manquants non soldés",f"{float(manquants['v']):,.0f} FCFA",   "⚠️", COLORS["danger"]),
        ]
