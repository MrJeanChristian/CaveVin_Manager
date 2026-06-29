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
        self._auto_refresh()   # actualisation automatique toutes les 30s

    def _build(self):
        C = COLORS
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 6))
        ctk.CTkLabel(hdr, text=f"👋  Bienvenue {self.user['prenom']} — Caissier",
                     font=FONTS["heading"], text_color=C["gold"]).pack(side="left")
        ctk.CTkButton(hdr, text="🔄 Actualiser", width=110, height=32,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=FONTS["badge"], command=self._refresh).pack(side="right")

        ctk.CTkLabel(self, text=f"📅 {date.today().strftime('%A %d %B %Y').capitalize()}",
                     font=FONTS["body"], text_color=C["text_muted"]).pack(anchor="w", padx=24)

        # KPIs
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.pack(fill="x", padx=24, pady=(12, 0))

        # Tickets ouverts
        ctk.CTkLabel(self, text="📂  Tickets ouverts (en attente de paiement)",
                     font=FONTS["body"], text_color=C["gold"]).pack(
                     anchor="w", padx=24, pady=(18, 6))

        tbl_open = ctk.CTkFrame(self, fg_color=C["bg_card"], corner_radius=10,
                                 border_width=1, border_color=C["border"])
        tbl_open.pack(fill="x", padx=24, pady=(0, 12))

        hdrs   = ["N° Ticket", "Serveur", "Date", "Total", "Lignes", ""]
        widths = [160, 160, 100, 120, 60, 120]
        hrow = ctk.CTkFrame(tbl_open, fg_color=C["bg_sidebar"], corner_radius=0)
        hrow.pack(fill="x", padx=1, pady=(1, 0))
        for h, w in zip(hdrs, widths):
            ctk.CTkLabel(hrow, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=6, pady=8)

        self.scroll_open = ctk.CTkScrollableFrame(tbl_open, fg_color="transparent", height=160)
        self.scroll_open.pack(fill="x")

        # Manquants actifs
        ctk.CTkLabel(self, text="⚠  Manquants non soldés",
                     font=FONTS["body"], text_color=C["danger"]).pack(
                     anchor="w", padx=24, pady=(8, 6))

        tbl_mq = ctk.CTkFrame(self, fg_color=C["bg_card"], corner_radius=10,
                               border_width=1, border_color=C["border"])
        tbl_mq.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        hdrs2  = ["Serveur", "Montant", "Date", "Ticket"]
        widths2= [200, 120, 120, 160]
        hrow2 = ctk.CTkFrame(tbl_mq, fg_color=C["bg_sidebar"], corner_radius=0)
        hrow2.pack(fill="x", padx=1, pady=(1, 0))
        for h, w in zip(hdrs2, widths2):
            ctk.CTkLabel(hrow2, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=8, pady=8)

        self.scroll_mq = ctk.CTkScrollableFrame(tbl_mq, fg_color="transparent")
        self.scroll_mq.pack(fill="both", expand=True)

        self._refresh()

    def _refresh(self):
        self._load_kpis()
        self._load_tickets_ouverts()
        self._load_manquants()

    def _load_kpis(self):
        C = COLORS
        for w in self.kpi_frame.winfo_children():
            w.destroy()
        today = date.today()
        mois  = today.strftime("%Y-%m")

        j  = db.fetchone("SELECT COALESCE(SUM(total),0) AS v FROM tickets WHERE date_vente=%s AND statut='valide'",(today,)) or {"v":0}
        m  = db.fetchone("SELECT COALESCE(SUM(total),0) AS v FROM tickets WHERE DATE_FORMAT(date_vente,'%%Y-%%m')=%s AND statut='valide'",(mois,)) or {"v":0}
        mq = db.fetchone("SELECT COALESCE(SUM(montant),0) AS v FROM manquants WHERE rembourse=0") or {"v":0}
        nt = db.fetchone("SELECT COUNT(*) AS v FROM tickets WHERE date_vente=%s AND statut='valide'",(today,)) or {"v":0}
        no = db.fetchone("SELECT COUNT(*) AS v FROM tickets WHERE statut='en_attente'") or {"v":0}

        kpis = [
            ("Ventes aujourd'hui",  f"{float(j['v']):,.0f} F",  "💰", C["gold"]),
            ("Ventes ce mois",      f"{float(m['v']):,.0f} F",  "📅", C["success"]),
            ("Tickets du jour",     str(nt["v"]),                "🧾", C["text"]),
            ("Tickets ouverts",     str(no["v"]),                "📂", C["gold"]),
            ("Manquants actifs",    f"{float(mq['v']):,.0f} F", "⚠️", C["danger"]),
        ]
        for title, val, icon, color in kpis:
            card = ctk.CTkFrame(self.kpi_frame, fg_color=C["bg_card"], corner_radius=10,
                                 border_width=1, border_color=C["border"], width=176, height=88)
            card.pack(side="left", padx=(0,10))
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=icon, font=("Helvetica",22)).pack(pady=(12,0))
            ctk.CTkLabel(card, text=val, font=("Georgia",13,"bold"), text_color=color).pack()
            ctk.CTkLabel(card, text=title, font=FONTS["small"],
                         text_color=C["text_muted"], wraplength=165).pack()

    def _load_tickets_ouverts(self):
        for w in self.scroll_open.winfo_children():
            w.destroy()
        C = COLORS
        rows = db.fetchall("""
            SELECT t.id, t.numero, CONCAT(u.prenom,' ',u.nom) AS serveur,
                   t.date_vente, t.total,
                   (SELECT COUNT(*) FROM ticket_lignes tl WHERE tl.ticket_id=t.id) AS nb_lignes
            FROM tickets t
            LEFT JOIN utilisateurs u ON u.id=t.serveur_id
            WHERE t.statut='en_attente'
            ORDER BY t.created_at DESC LIMIT 20
        """)

        if not rows:
            ctk.CTkLabel(self.scroll_open, text="Aucun ticket ouvert.",
                         font=FONTS["small"], text_color=C["text_muted"]).pack(pady=10)
            return

        for i, r in enumerate(rows):
            bg = C["bg_card"] if i % 2 == 0 else C["bg_dark"]
            rf = ctk.CTkFrame(self.scroll_open, fg_color=bg, corner_radius=0)
            rf.pack(fill="x", pady=1)
            vals   = [r["numero"], r["serveur"] or "—",
                      str(r["date_vente"]), f"{float(r['total']):,.0f} FCFA",
                      str(r["nb_lignes"])]
            widths = [160, 160, 100, 120, 60]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(rf, text=str(v), font=FONTS["small"],
                             text_color=C["text"], width=w, anchor="w").pack(
                             side="left", padx=6, pady=7)
            # Badge payé
            ctk.CTkButton(rf, text="✅ Encaissé", width=110, height=26,
                          fg_color=C["success"], hover_color="#1E8449",
                          text_color=C["white"], font=FONTS["small"],
                          command=lambda row=r: self._encaisser_rapide(row)
                          ).pack(side="left", padx=4)

    def _encaisser_rapide(self, ticket_row):
        """Encaissement rapide depuis le dashboard — ouvre la popup."""
        from views.caissier.tickets import TicketsView
        # Réutiliser la même popup d'encaissement
        tmp = TicketsView.__new__(TicketsView)
        tmp.user = self.user
        tmp._encaisser_ticket_depuis_dashboard(self, ticket_row, self._refresh)

    def _load_manquants(self):
        for w in self.scroll_mq.winfo_children():
            w.destroy()
        C = COLORS
        rows = db.fetchall("""
            SELECT CONCAT(u.prenom,' ',u.nom) AS serveur, m.montant,
                   m.date_manquant, t.numero
            FROM manquants m
            JOIN utilisateurs u ON m.serveur_id=u.id
            LEFT JOIN tickets t ON m.ticket_id=t.id
            WHERE m.rembourse=0
            ORDER BY m.date_manquant DESC LIMIT 30
        """)
        for i, r in enumerate(rows):
            bg = C["bg_card"] if i%2==0 else C["bg_dark"]
            rf = ctk.CTkFrame(self.scroll_mq, fg_color=bg, corner_radius=0)
            rf.pack(fill="x")
            for v, w in zip([r["serveur"], f"{float(r['montant']):,.0f} FCFA",
                              str(r["date_manquant"]), r["numero"] or "—"],
                             [200, 120, 120, 160]):
                ctk.CTkLabel(rf, text=str(v), font=FONTS["small"],
                             text_color=C["text"], width=w, anchor="w").pack(
                             side="left", padx=8, pady=7)

    def _auto_refresh(self):
        """Actualisation automatique toutes les 30 secondes."""
        self._refresh()
        self._refresh_job = self.after(30000, self._auto_refresh)

    def destroy(self):
        if hasattr(self, '_refresh_job'):
            self.after_cancel(self._refresh_job)
        super().destroy()

