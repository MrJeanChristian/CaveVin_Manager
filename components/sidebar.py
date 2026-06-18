# ============================================================
# components/sidebar.py — Sidebar latérale réutilisable
# ============================================================

import customtkinter as ctk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import COLORS, FONTS, APP_NAME, ROLES


class Sidebar(ctk.CTkFrame):
    """Barre latérale avec navigation, info utilisateur et déconnexion."""

    def __init__(self, parent, user: dict, menu_items: list, on_logout, **kwargs):
        """
        menu_items : liste de tuples (label, icon, callback)
        """
        super().__init__(parent, fg_color=COLORS["bg_sidebar"],
                         corner_radius=0, width=210, **kwargs)
        self.pack_propagate(False)

        self.user       = user
        self.on_logout  = on_logout
        self.menu_items = menu_items
        self._buttons   = {}
        self._active    = None

        self._build()

    def _build(self):
        C = COLORS
        # ---- Logo ----
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(20, 0))
        ctk.CTkLabel(top, text="🍷", font=("Helvetica", 30)).pack()
        ctk.CTkLabel(top, text=APP_NAME, font=("Georgia", 13, "bold"),
                     text_color=C["gold"]).pack()

        # Séparateur
        ctk.CTkFrame(self, fg_color=C["border"], height=1).pack(fill="x", padx=14, pady=10)

        # ---- Info utilisateur ----
        info = ctk.CTkFrame(self, fg_color=C["bg_card"], corner_radius=8)
        info.pack(fill="x", padx=12, pady=(0, 14))
        ctk.CTkLabel(info, text=f"👤 {self.user['prenom']} {self.user['nom']}",
                     font=FONTS["body"], text_color=C["text"], wraplength=160).pack(pady=(8, 2), padx=8)
        role_label = ROLES.get(self.user["role"], self.user["role"])
        ctk.CTkLabel(info, text=role_label, font=FONTS["badge"],
                     text_color=C["gold"]).pack(pady=(0, 8))

        # ---- Menu items ----
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="both", expand=True, padx=8)

        for (label, icon, cb) in self.menu_items:
            btn = ctk.CTkButton(
                nav, text=f"  {icon}  {label}", anchor="w", height=42,
                corner_radius=8,
                fg_color="transparent",
                hover_color=C["bg_card"],
                text_color=C["text_muted"],
                font=FONTS["body"],
                command=lambda c=cb, l=label: self._select(l, c),
            )
            btn.pack(fill="x", pady=3)
            self._buttons[label] = btn

        # Auto-sélection du premier item
        if self.menu_items:
            first_label, _, first_cb = self.menu_items[0]
            self._select(first_label, first_cb)

        # ---- Déconnexion ----
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=8, pady=12)
        ctk.CTkFrame(self, fg_color=C["border"], height=1).pack(fill="x", padx=14, pady=(0, 8))
        ctk.CTkButton(
            bottom, text="  🚪  Déconnexion", anchor="w", height=40,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#3D0000",
            text_color=C["danger"],
            font=FONTS["body"],
            command=self.on_logout,
        ).pack(fill="x")

    def _select(self, label: str, callback):
        C = COLORS
        # Réinitialiser l'ancien bouton actif
        if self._active and self._active in self._buttons:
            self._buttons[self._active].configure(
                fg_color="transparent", text_color=C["text_muted"]
            )
        # Activer le nouveau
        if label in self._buttons:
            self._buttons[label].configure(
                fg_color=C["accent2"], text_color=C["white"]
            )
        self._active = label
        callback()
