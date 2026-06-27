# ============================================================
# views/admin/config_mail.py — Configuration Gmail SMTP (Admin)
# ============================================================

import customtkinter as ctk
from tkinter import messagebox
import threading, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import COLORS, FONTS


class ConfigMailView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self._build()
        self._load()

    def _build(self):
        C = COLORS

        ctk.CTkLabel(self, text="  Configuration Mail — Rapport journalier",
                     font=FONTS["heading"], text_color=C["gold"]).pack(
                     anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(self,
                     text="Le rapport est envoyé automatiquement quand le caissier se déconnecte.",
                     font=FONTS["small"], text_color=C["text_muted"]).pack(
                     anchor="w", padx=24, pady=(0, 16))

        card = ctk.CTkFrame(self, fg_color=C["bg_card"], corner_radius=10,
                             border_width=1, border_color=C["border"])
        card.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        # Activation
        act_row = ctk.CTkFrame(card, fg_color="transparent")
        act_row.pack(fill="x", padx=20, pady=(20, 8))
        ctk.CTkLabel(act_row, text="Activer l'envoi automatique",
                     font=FONTS["body"], text_color=C["text"]).pack(side="left")
        self.actif_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(act_row, text="", variable=self.actif_var,
                       progress_color=C["accent"],
                       width=52).pack(side="left", padx=12)

        ctk.CTkFrame(card, fg_color=C["border"], height=1).pack(
            fill="x", padx=20, pady=(0, 16))

        # Champs
        fields = [
            ("Adresse Gmail expéditeur",     "e_from",   False,
             "ex: cavevin.manager@gmail.com"),
            ("Mot de passe d'application",   "e_pass",   True,
             "16 caractères — voir guide ci-dessous"),
            ("Adresse admin (destinataire)", "e_to",     False,
             "ex: patron@gmail.com"),
        ]
        for label, attr, secret, placeholder in fields:
            ctk.CTkLabel(card, text=label, font=FONTS["small"],
                         text_color=C["text_muted"], anchor="w").pack(
                         fill="x", padx=20, pady=(0, 2))
            e = ctk.CTkEntry(card, height=38, show="●" if secret else "",
                              fg_color=C["bg_dark"], border_color=C["border"],
                              text_color=C["text"], font=FONTS["body"],
                              placeholder_text=placeholder)
            e.pack(fill="x", padx=20, pady=(0, 12))
            setattr(self, attr, e)

        # Guide Gmail
        guide = ctk.CTkFrame(card, fg_color=C["bg_dark"], corner_radius=8)
        guide.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkLabel(guide,
                     text=(
                         "  Comment obtenir un mot de passe d'application Gmail :\n\n"
                         "  1. Ouvre myaccount.google.com\n"
                         "  2. Sécurité → Validation en 2 étapes (activer si pas encore fait)\n"
                         "  3. Sécurité → Mots de passe des applications\n"
                         "  4. Sélectionner 'Autre' → taper 'CaveVin' → Générer\n"
                         "  5. Copier le mot de passe de 16 caractères ici"
                     ),
                     font=FONTS["small"], text_color=C["text_muted"],
                     justify="left").pack(anchor="w", padx=14, pady=12)

        # Boutons
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkButton(btn_row, text="  Enregistrer", height=42,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      text_color=C["white"], font=("Helvetica", 12, "bold"),
                      command=self._save).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_row, text="  Envoyer un mail test", height=42,
                      fg_color=C["bg_dark"], hover_color=C["bg_sidebar"],
                      border_width=1, border_color=C["border"],
                      text_color=C["text"], font=FONTS["body"],
                      command=self._test).pack(side="left")

        self.lbl_status = ctk.CTkLabel(card, text="", font=FONTS["body"])
        self.lbl_status.pack(pady=(4, 20))

    def _load(self):
        from utils.mailer import MAIL_CONFIG as MC
        self.actif_var.set(MC.get("actif", False))
        self.e_from.delete(0, "end")
        self.e_from.insert(0, MC.get("expediteur", ""))
        self.e_pass.delete(0, "end")
        self.e_pass.insert(0, MC.get("app_password", ""))
        self.e_to.delete(0, "end")
        self.e_to.insert(0, MC.get("destinataire", ""))

    def _save(self):
        from utils import mailer
        mailer.MAIL_CONFIG["actif"]        = self.actif_var.get()
        mailer.MAIL_CONFIG["expediteur"]   = self.e_from.get().strip()
        mailer.MAIL_CONFIG["app_password"] = self.e_pass.get().strip()
        mailer.MAIL_CONFIG["destinataire"] = self.e_to.get().strip()
        self.lbl_status.configure(
            text="  Configuration enregistrée !",
            text_color=COLORS["success"])

    def _test(self):
        self._save()
        from utils.mailer import MAIL_CONFIG as MC
        if not MC["expediteur"] or not MC["app_password"] or not MC["destinataire"]:
            self.lbl_status.configure(
                text="Remplissez tous les champs avant de tester.",
                text_color=COLORS["danger"])
            return

        self.lbl_status.configure(text="Envoi en cours...", text_color=COLORS["gold"])
        self.update()

        def do():
            import smtplib
            from email.mime.text import MIMEText
            try:
                msg = MIMEText(
                    "<h2 style='color:#C0392B'>CaveVin Manager</h2>"
                    "<p>✅ La configuration mail fonctionne correctement !</p>",
                    "html", "utf-8"
                )
                msg["From"]    = MC["expediteur"]
                msg["To"]      = MC["destinataire"]
                msg["Subject"] = "[CaveVin] Test de configuration mail"
                with smtplib.SMTP(MC["smtp_host"], MC["smtp_port"]) as s:
                    s.ehlo(); s.starttls()
                    s.login(MC["expediteur"], MC["app_password"])
                    s.sendmail(MC["expediteur"], MC["destinataire"], msg.as_string())
                self.after(0, lambda: self.lbl_status.configure(
                    text="  Mail test envoyé avec succès !",
                    text_color=COLORS["success"]))
            except Exception as e:
                err = str(e)
                self.after(0, lambda m=err: self.lbl_status.configure(
                    text=f"Erreur : {m}", text_color=COLORS["danger"]))

        threading.Thread(target=do, daemon=True).start()
