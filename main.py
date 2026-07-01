# ============================================================
# main.py — Point d'entrée CaveVin Manager v2.0
# ============================================================

import customtkinter as ctk
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from config import APP_NAME, WINDOW_SIZE, COLORS, FONTS
from database.db import db
from database.models import initialize
from auth.login import LoginWindow
from utils.mailer import charger_config_mail

# Vues
from components.sidebar import Sidebar
from views.admin.dashboard   import AdminDashboard
from views.admin.boissons    import BoissonsView
from views.admin.employes    import EmployesView
from views.admin.graphiques  import GraphiquesView
from views.admin.outils      import OutilsView
from views.admin.config_mail import ConfigMailView
from views.admin.imprimante  import ImprimanteView
from views.caissier.dashboard  import CaissierDashboard
from views.caissier.tickets    import TicketsView
from views.caissier.rapports   import RapportsView
from views.caissier.historique import HistoriqueView
from views.serveur.dashboard   import ServeurDashboard
from views.profil              import ProfilView

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class MainWindow(ctk.CTk):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.title(f"{APP_NAME}  —  {user['prenom']} {user['nom']}  [{user['role'].upper()}]")
        self.geometry(WINDOW_SIZE)
        self.minsize(960, 640)
        self.configure(fg_color=COLORS["bg_dark"])
        self._center()
        self._build()

    def _center(self):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h   = 1280, 780
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        role = self.user["role"]

        if role == "admin":
            menu = [
                ("Dashboard",   "🏠", self._show_admin_home),
                ("Boisson&Prix","🍾", self._show_boissons),
                ("Employés",    "👥", self._show_employes),
                ("Saisie ticket", "🧾", self._show_tickets),
                ("Graphiques",  "📈", self._show_graphiques),
                ("Exports",     "💾", self._show_outils),
                # ("Imprimante",  "🖨", self._show_imprimante),
                ("Config Mail", "📧", self._show_config_mail),
                ("Mon profil",  "🔑", self._show_profil),
            ]
        elif role == "caissier":
            menu = [
                ("Accueil",      "🏠", self._show_caissier_home),
                ("Saisie ticket","🧾", self._show_tickets),
                ("Rapports",     "📊", self._show_rapports),
                ("Graphiques",   "📈", self._show_graphiques),
                ("Mon profil",   "🔑", self._show_profil),
            ]
        else:  # serveur
            menu = [
                ("Mon espace", "🍷", self._show_serveur_home),
                ("Mon profil", "🔑", self._show_profil),
            ]

        self.content = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0)

        self.sidebar = Sidebar(self, self.user, menu, self._logout)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkFrame(self, fg_color=COLORS["border"], width=1).pack(side="left", fill="y")

        self.content.pack(side="left", fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        if self.user["role"] == "caissier":
            self._envoyer_rapport_et_quitter(action="close")
        else:
            self.destroy()

    # ---------------------------------------------------------------- Vues --
    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _show_admin_home(self):
        self._clear_content()
        AdminDashboard(self.content, self.user).pack(fill="both", expand=True)

    def _show_boissons(self):
        self._clear_content()
        BoissonsView(self.content).pack(fill="both", expand=True)

    def _show_employes(self):
        self._clear_content()
        EmployesView(self.content).pack(fill="both", expand=True)

    def _show_graphiques(self):
        self._clear_content()
        GraphiquesView(self.content).pack(fill="both", expand=True)

    def _show_outils(self):
        self._clear_content()
        OutilsView(self.content).pack(fill="both", expand=True)

    def _show_imprimante(self):
        self._clear_content()
        ImprimanteView(self.content).pack(fill="both", expand=True)

    def _show_caissier_home(self):
        self._clear_content()
        CaissierDashboard(self.content, self.user).pack(fill="both", expand=True)

    def _show_tickets(self):
        self._clear_content()
        TicketsView(self.content, self.user).pack(fill="both", expand=True)

    def _show_rapports(self):
        self._clear_content()
        RapportsView(self.content, self.user).pack(fill="both", expand=True)

    def _show_historique(self):
        self._clear_content()
        HistoriqueView(self.content, self.user).pack(fill="both", expand=True)

    def _show_serveur_home(self):
        self._clear_content()
        ServeurDashboard(self.content, self.user).pack(fill="both", expand=True)

    def _show_config_mail(self):
        self._clear_content()
        ConfigMailView(self.content).pack(fill="both", expand=True)

    def _show_profil(self):
        self._clear_content()
        ProfilView(self.content, self.user).pack(fill="both", expand=True)

    def _logout(self):
        if self.user["role"] == "caissier":
            self._envoyer_rapport_et_quitter(action="logout")
        else:
            self.destroy()
            start()

    def _envoyer_rapport_et_quitter(self, action="logout"):
        """
        Génère DEUX fichiers Excel en pièce jointe :
          1. Rapport journalier  (ventes du jour uniquement)
          2. Rapport mensuel     (cumul du mois en cours)
        Puis envoie le tout par mail en arrière-plan.
        """
        import threading, os, tempfile
        from datetime import date
        from utils.mailer import envoyer_rapport_journalier, MAIL_CONFIG
        from utils.export_excel import (exporter_rapport_journalier,
                                        exporter_rapport_mensuel)
        from database.db import db

        caissier_nom = f"{self.user['prenom']} {self.user['nom']}"
        aujourd_hui  = date.today()
        jour_str     = str(aujourd_hui)           # "YYYY-MM-DD"
        mois_str     = aujourd_hui.strftime("%Y-%m")  # "YYYY-MM"

        def _do():
            tmp = tempfile.mkdtemp()
            xlsx_journalier = None
            xlsx_mensuel    = None

            # ── 1. Rapport journalier du jour ──────────────────────────
            try:
                xlsx_journalier = os.path.join(
                    tmp, f"rapport_journalier_{jour_str}.xlsx")
                exporter_rapport_journalier(db, jour_str, xlsx_journalier)
                print(f"[MAIL] Excel journalier généré : {xlsx_journalier}")
            except Exception as e:
                print(f"[MAIL] Erreur Excel journalier : {e}")

            # ── 2. Envoi mail avec la pièce jointe ─────────────
            envoyer_rapport_journalier(
                db, caissier_nom,
                xlsx_path=xlsx_journalier,
            )

        if MAIL_CONFIG.get("actif"):
            t = threading.Thread(target=_do, daemon=True)
            t.start()
            t.join(timeout=5)   # 5s max avant de fermer

        self.destroy()
        if action == "logout":
            start()


def on_login_success(user: dict):
    app = MainWindow(user)
    app.mainloop()

def start():
    login = LoginWindow(on_success=on_login_success)
    login.mainloop()

if __name__ == "__main__":
    print(f"[{APP_NAME}] Initialisation de la base de données...")
    if db.connect():
        db.init_tables()        # Crée la table parametres si absente
        charger_config_mail(db) # Charge la config mail depuis la BdD
    initialize()
    print(f"[{APP_NAME}] Lancement de l'interface...")
    start()


