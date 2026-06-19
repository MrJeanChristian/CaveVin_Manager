# ============================================================
# views/profil.py — Changement de mot de passe (tous rôles)
# ============================================================

import customtkinter as ctk
from tkinter import messagebox
import hashlib, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import COLORS, FONTS
from database.db import db


def _hash(p): return hashlib.sha256(p.encode()).hexdigest()


class ProfilView(ctk.CTkFrame):
    def __init__(self, parent, user, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self.user = user
        self._build()

    def _build(self):
        C = COLORS
        ctk.CTkLabel(self, text="  Mon Profil",
                     font=FONTS["heading"], text_color=C["gold"]).pack(anchor="w", padx=24, pady=(20, 16))

        # Carte infos
        card = ctk.CTkFrame(self, fg_color=C["bg_card"], corner_radius=10,
                             border_width=1, border_color=C["border"])
        card.pack(fill="x", padx=24, pady=(0, 16))
        card.columnconfigure(1, weight=1)

        infos = [
            ("Prénom",   self.user.get("prenom","")),
            ("Nom",      self.user.get("nom","")),
            ("Username", self.user.get("username","")),
            ("Rôle",     self.user.get("role","").capitalize()),
            ("Salaire",  f"{float(self.user.get('salaire',0)):,.0f} FCFA"),
        ]
        for i, (label, val) in enumerate(infos):
            ctk.CTkLabel(card, text=label, font=FONTS["body"],
                         text_color=C["text_muted"], anchor="w").grid(
                row=i, column=0, padx=(20, 8), pady=8, sticky="w")
            ctk.CTkLabel(card, text=val, font=("Georgia", 13, "bold"),
                         text_color=C["text"], anchor="w").grid(
                row=i, column=1, padx=8, pady=8, sticky="w")

        # Carte changement mdp
        mdp_card = ctk.CTkFrame(self, fg_color=C["bg_card"], corner_radius=10,
                                 border_width=1, border_color=C["border"])
        mdp_card.pack(fill="x", padx=24, pady=(0, 16))

        ctk.CTkLabel(mdp_card, text="Changer le mot de passe",
                     font=FONTS["heading"], text_color=C["gold"]).pack(anchor="w", padx=20, pady=(16, 8))

        for label, attr, show in [
            ("Mot de passe actuel",      "e_old",   "●"),
            ("Nouveau mot de passe",     "e_new1",  "●"),
            ("Confirmer nouveau mot de passe", "e_new2", "●"),
        ]:
            ctk.CTkLabel(mdp_card, text=label, font=FONTS["small"],
                         text_color=C["text_muted"], anchor="w").pack(fill="x", padx=20, pady=(6, 1))
            e = ctk.CTkEntry(mdp_card, height=38, show=show,
                              fg_color=C["bg_dark"], border_color=C["border"],
                              text_color=C["text"], font=FONTS["body"])
            e.pack(fill="x", padx=20, pady=(0, 4))
            setattr(self, attr, e)

        # Indicateur force mdp
        self.lbl_force = ctk.CTkLabel(mdp_card, text="", font=FONTS["small"])
        self.lbl_force.pack(padx=20, anchor="w")
        self.e_new1.bind("<KeyRelease>", self._check_strength)

        self.lbl_status = ctk.CTkLabel(mdp_card, text="", font=FONTS["body"])
        self.lbl_status.pack(pady=(4, 8))

        ctk.CTkButton(mdp_card, text="  Enregistrer le nouveau mot de passe",
                      height=42, fg_color=C["accent"], hover_color=C["accent2"],
                      text_color=C["white"], font=("Helvetica", 12, "bold"),
                      command=self._changer_mdp).pack(fill="x", padx=20, pady=(0, 20))

    def _check_strength(self, event=None):
        C = COLORS
        mdp = self.e_new1.get()
        if len(mdp) == 0:
            self.lbl_force.configure(text="", text_color=C["text_muted"]); return
        score = 0
        if len(mdp) >= 8:    score += 1
        if any(c.isupper() for c in mdp): score += 1
        if any(c.isdigit() for c in mdp): score += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in mdp): score += 1

        niveaux = [
            (0, "Trop court",  C["danger"]),
            (1, "Faible",      C["danger"]),
            (2, "Moyen",       C["gold"]),
            (3, "Fort",        C["success"]),
            (4, "Très fort",   C["success"]),
        ]
        txt, color = niveaux[score][1], niveaux[score][2]
        self.lbl_force.configure(text=f"Force : {txt}", text_color=color)

    def _changer_mdp(self):
        C = COLORS
        old  = self.e_old.get()
        new1 = self.e_new1.get()
        new2 = self.e_new2.get()

        if not old or not new1 or not new2:
            self.lbl_status.configure(text="Remplissez tous les champs.", text_color=C["danger"]); return
        if len(new1) < 6:
            self.lbl_status.configure(text="Le nouveau mot de passe doit faire au moins 6 caractères.", text_color=C["danger"]); return
        if new1 != new2:
            self.lbl_status.configure(text="Les deux nouveaux mots de passe ne correspondent pas.", text_color=C["danger"]); return

        # Vérification de l'ancien
        user = db.fetchone(
            "SELECT id FROM utilisateurs WHERE id=%s AND password=%s",
            (self.user["id"], _hash(old))
        )
        if not user:
            self.lbl_status.configure(text="Mot de passe actuel incorrect.", text_color=C["danger"]); return

        db.execute(
            "UPDATE utilisateurs SET password=%s WHERE id=%s",
            (_hash(new1), self.user["id"]), commit=True
        )
        self.lbl_status.configure(text="  Mot de passe mis à jour avec succès !", text_color=C["success"])
        for e in [self.e_old, self.e_new1, self.e_new2]:
            e.delete(0, "end")
        self.lbl_force.configure(text="")
