# ============================================================
# auth/login.py — Fenêtre de connexion
# ============================================================

import customtkinter as ctk
import hashlib, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import COLORS, FONTS, APP_NAME
from database.db import db


def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()


class LoginWindow(ctk.CTk):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.title(f"{APP_NAME} — Connexion")
        self.geometry("480x560")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_dark"])

        # Centrer la fenêtre
        self.after(10, self._center)
        self._build_ui()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 480) // 2
        y = (self.winfo_screenheight() - 560) // 2
        self.geometry(f"480x560+{x}+{y}")

    def _build_ui(self):
        C = COLORS
        # Conteneur carte
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"],
                            corner_radius=16, border_width=1,
                            border_color=COLORS["border"])
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.82, relheight=0.92)

        # Logo / icône vin
        lbl_icon = ctk.CTkLabel(card, text="🍷", font=("Helvetica", 52))
        lbl_icon.pack(pady=(32, 4))

        lbl_title = ctk.CTkLabel(card, text=APP_NAME,
                                  font=FONTS["title"], text_color=COLORS["gold"])
        lbl_title.pack()

        lbl_sub = ctk.CTkLabel(card, text="Gestion de cave à vin",
                                font=FONTS["small"], text_color=COLORS["text_muted"])
        lbl_sub.pack(pady=(2, 24))

        # Champ username
        ctk.CTkLabel(card, text="Nom d'utilisateur",
                     font=FONTS["body"], text_color=COLORS["text"],
                     anchor="w").pack(fill="x", padx=32)
        self.entry_user = ctk.CTkEntry(card, height=40, corner_radius=8,
                                        fg_color=COLORS["bg_dark"],
                                        border_color=COLORS["border"],
                                        text_color=COLORS["text"],
                                        font=FONTS["body"])
        self.entry_user.pack(fill="x", padx=32, pady=(4, 14))
        self.entry_user.focus()

        # Champ password
        ctk.CTkLabel(card, text="Mot de passe",
                     font=FONTS["body"], text_color=COLORS["text"],
                     anchor="w").pack(fill="x", padx=32)
        self.entry_pass = ctk.CTkEntry(card, height=40, corner_radius=8,
                                        fg_color=COLORS["bg_dark"],
                                        border_color=COLORS["border"],
                                        text_color=COLORS["text"],
                                        font=FONTS["body"], show="●")
        self.entry_pass.pack(fill="x", padx=32, pady=(4, 6))
        self.entry_pass.bind("<Return>", lambda e: self._login())

        # Message d'erreur
        self.lbl_error = ctk.CTkLabel(card, text="", font=FONTS["small"],
                                       text_color=COLORS["danger"])
        self.lbl_error.pack(pady=(2, 8))

        # Bouton connexion
        btn = ctk.CTkButton(card, text="Se connecter", height=44,
                             corner_radius=8,
                             fg_color=COLORS["accent"],
                             hover_color=COLORS["accent2"],
                             text_color=COLORS["white"],
                             font=("Helvetica", 18, "bold"),
                             command=self._login)
        btn.pack(fill="x", padx=32, pady=(0, 24))

        # Footer
        ctk.CTkLabel(card, text=f"v1.0.0 — ©2026 Cave-Manager by Jean Christian",
                     font=FONTS["small"], text_color=COLORS["text_muted"]).pack(side="bottom", pady=12)

    def _login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        if not username or not password:
            self.lbl_error.configure(text="⚠ Remplissez tous les champs.")
            return

        user = db.fetchone(
            "SELECT * FROM utilisateurs WHERE username=%s AND password=%s AND actif=1",
            (username, hash_password(password))
        )
        if user:
            self.destroy()
            self.on_success(user)
        else:
            self.lbl_error.configure(text="✗ Identifiants incorrects.")
            self.entry_pass.delete(0, "end")
