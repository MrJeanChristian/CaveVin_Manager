#!/usr/bin/env python3
# ============================================================
# main.py — Point d'entrée CaveVin Manager
# ============================================================

import customtkinter as ctk
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from config import APP_NAME, WINDOW_SIZE, COLORS, FONTS
from database.db import db
from database.models import initialize
from auth.login import LoginWindow

# ---- Imports des vues ----
from components.sidebar import Sidebar
from views.admin.dashboard  import AdminDashboard
from views.admin.boissons   import BoissonsView
from views.admin.employes   import EmployesView
from views.caissier.dashboard  import CaissierDashboard
from views.caissier.tickets    import TicketsView
from views.caissier.rapports   import RapportsView
from views.caissier.historique import HistoriqueView
from views.serveur.dashboard  import ServeurDashboard


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


# ============================================================
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

        # ---- Menu selon rôle ----
        if role == "admin":
            menu = [
                ("Tableau de bord", "🏠", self._show_admin_home),
                ("Boissons & Prix",  "🍾", self._show_boissons),
                ("Employés",         "👥", self._show_employes),
            ]
        elif role == "caissier":
            menu = [
                ("Accueil",          "🏠", self._show_caissier_home),
                ("Saisir un ticket", "🧾", self._show_tickets),
                ("Historique",       "📄", self._show_historique),
                ("Rapports",         "📊", self._show_rapports),
            ]
        else:  # serveur
            menu = [
                ("Mon espace", "🍷", self._show_serveur_home),
            ]

        # ---- Layout principal ----
        # IMPORTANT : self.content doit exister AVANT Sidebar car
        # elle appelle le callback du premier item dès __init__.
        self.content = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0)

        self.sidebar = Sidebar(self, self.user, menu, self._logout)
        self.sidebar.pack(side="left", fill="y")

        # Séparateur vertical
        ctk.CTkFrame(self, fg_color=COLORS["border"], width=1).pack(side="left", fill="y")

        self.content.pack(side="left", fill="both", expand=True)

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

    # -------------------------------------------------------------- Auth --
    def _logout(self):
        self.destroy()
        start()


# ============================================================
def on_login_success(user: dict):
    app = MainWindow(user)
    app.mainloop()


def start():
    login = LoginWindow(on_success=on_login_success)
    login.mainloop()


# ============================================================
if __name__ == "__main__":
    print(f"[{APP_NAME}] Initialisation de la base de données...")
    initialize()
    print(f"[{APP_NAME}] Lancement de l'interface...")
    start()
