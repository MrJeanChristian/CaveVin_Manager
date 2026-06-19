# ============================================================
# views/admin/outils.py — Export Excel + Sauvegarde MySQL (Admin)
# ============================================================

import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading, os, sys
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import COLORS, FONTS
from database.db import db


class OutilsView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self._build()
        self._load_backups()

    def _build(self):
        C = COLORS
        ctk.CTkLabel(self, text="  Outils — Export & Sauvegarde",
                     font=FONTS["heading"], text_color=C["gold"]).pack(anchor="w", padx=24, pady=(20, 16))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ---- Colonne gauche : Export Excel ----
        excel_card = ctk.CTkFrame(body, fg_color=C["bg_card"], corner_radius=10,
                                   border_width=1, border_color=C["border"])
        excel_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(excel_card, text="  Export Excel",
                     font=FONTS["heading"], text_color=C["gold"]).pack(anchor="w", padx=20, pady=(18, 4))
        ctk.CTkLabel(excel_card, text="Génère un rapport complet mensuel en .xlsx\navec 5 feuilles : Résumé, Ventes, Boissons, Manquants, Déductions.",
                     font=FONTS["small"], text_color=C["text_muted"], justify="left").pack(anchor="w", padx=20, pady=(0, 16))

        ctk.CTkLabel(excel_card, text="Mois (YYYY-MM) :", font=FONTS["body"],
                     text_color=C["text_muted"], anchor="w").pack(fill="x", padx=20)
        self.e_mois_excel = ctk.CTkEntry(excel_card, height=36,
                                          fg_color=C["bg_dark"], border_color=C["border"],
                                          text_color=C["text"], font=FONTS["body"])
        self.e_mois_excel.insert(0, date.today().strftime("%Y-%m"))
        self.e_mois_excel.pack(fill="x", padx=20, pady=(4, 12))

        ctk.CTkButton(excel_card, text="  Générer et enregistrer...", height=42,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      text_color=C["white"], font=("Helvetica", 12, "bold"),
                      command=self._export_excel).pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkButton(excel_card, text="  Ouvrir dossier exports", height=36,
                      fg_color="transparent", hover_color=C["bg_sidebar"],
                      border_width=1, border_color=C["border"],
                      text_color=C["text"], font=FONTS["body"],
                      command=self._ouvrir_dossier_exports).pack(fill="x", padx=20)

        self.lbl_excel_status = ctk.CTkLabel(excel_card, text="", font=FONTS["body"])
        self.lbl_excel_status.pack(pady=12)

        # ---- Colonne droite : Sauvegarde MySQL ----
        bk_card = ctk.CTkFrame(body, fg_color=C["bg_card"], corner_radius=10,
                                border_width=1, border_color=C["border"])
        bk_card.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(bk_card, text="  Sauvegarde MySQL",
                     font=FONTS["heading"], text_color=C["gold"]).pack(anchor="w", padx=20, pady=(18, 4))
        ctk.CTkLabel(bk_card, text="Dump complet de la base cave_vin via mysqldump.\nFichiers compressés (.sql.gz) stockés localement.",
                     font=FONTS["small"], text_color=C["text_muted"], justify="left").pack(anchor="w", padx=20, pady=(0, 12))

        # Options
        opt_row = ctk.CTkFrame(bk_card, fg_color="transparent")
        opt_row.pack(fill="x", padx=20, pady=(0, 12))
        self.compress_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opt_row, text="Compresser (gzip)", variable=self.compress_var,
                         font=FONTS["body"], text_color=C["text"],
                         fg_color=C["accent"]).pack(side="left")

        ctk.CTkButton(bk_card, text="  Sauvegarder maintenant", height=42,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      text_color=C["white"], font=("Helvetica", 12, "bold"),
                      command=self._sauvegarder).pack(fill="x", padx=20, pady=(0, 8))

        # Sauvegarde auto
        auto_card = ctk.CTkFrame(bk_card, fg_color=C["bg_dark"], corner_radius=8)
        auto_card.pack(fill="x", padx=20, pady=(0, 10))
        ctk.CTkLabel(auto_card, text="Sauvegarde automatique quotidienne :",
                     font=FONTS["badge"], text_color=C["text_muted"]).pack(anchor="w", padx=12, pady=(10, 4))
        auto_row = ctk.CTkFrame(auto_card, fg_color="transparent")
        auto_row.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(auto_row, text="À :", font=FONTS["small"],
                     text_color=C["text_muted"]).pack(side="left")
        self.e_heure = ctk.CTkEntry(auto_row, width=70, height=32,
                                     fg_color=C["bg_card"], border_color=C["border"],
                                     text_color=C["text"], font=FONTS["mono"])
        self.e_heure.insert(0, "23:00")
        self.e_heure.pack(side="left", padx=8)
        self.auto_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(auto_row, text="Activer", variable=self.auto_var,
                       font=FONTS["body"], text_color=C["text"],
                       progress_color=C["accent"],
                       command=self._toggle_auto).pack(side="left", padx=8)

        self.lbl_bk_status = ctk.CTkLabel(bk_card, text="", font=FONTS["small"],
                                            text_color=C["text_muted"])
        self.lbl_bk_status.pack(pady=4)

        # Liste des sauvegardes
        ctk.CTkLabel(bk_card, text="Sauvegardes disponibles :",
                     font=FONTS["badge"], text_color=C["text_muted"]).pack(anchor="w", padx=20, pady=(4, 2))

        self.scroll_bk = ctk.CTkScrollableFrame(bk_card, fg_color="transparent", height=160)
        self.scroll_bk.pack(fill="x", padx=20, pady=(0, 8))

        btn_row = ctk.CTkFrame(bk_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(btn_row, text=" Restaurer...", height=34,
                      fg_color="#5D0000", hover_color="#3D0000",
                      text_color=C["text"], font=FONTS["body"],
                      command=self._restaurer).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text=" Ouvrir dossier", height=34,
                      fg_color="transparent", hover_color=C["bg_sidebar"],
                      border_width=1, border_color=C["border"],
                      text_color=C["text"], font=FONTS["body"],
                      command=self._ouvrir_dossier_bk).pack(side="left")

    # ---- Export Excel ----
    def _export_excel(self):
        mois = self.e_mois_excel.get().strip()
        if not mois:
            self.lbl_excel_status.configure(text="Entrez un mois (YYYY-MM).",
                                             text_color=COLORS["danger"]); return
        chemin = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"rapport_{mois}.xlsx",
            title="Enregistrer le rapport Excel"
        )
        if not chemin: return

        self.lbl_excel_status.configure(text="Génération en cours...", text_color=COLORS["gold"])
        self.update()
        def do():
            try:
                from utils.export_excel import exporter_rapport_mensuel
                exporter_rapport_mensuel(db, mois, chemin)
                nom = os.path.basename(chemin)
                self.after(0, lambda n=nom: self.lbl_excel_status.configure(
                    text=f"  Exporte : {n}",
                    text_color=COLORS["success"]))
                import subprocess, platform
                if platform.system() == "Linux":
                    subprocess.Popen(["xdg-open", chemin])
            except Exception as e:
                msg = str(e)
                self.after(0, lambda m=msg: self.lbl_excel_status.configure(
                    text=f"Erreur : {m}", text_color=COLORS["danger"]))
        threading.Thread(target=do, daemon=True).start()

    def _ouvrir_dossier_exports(self):
        import subprocess
        d = os.path.join(os.path.expanduser("~"), "CaveVin_Exports")
        os.makedirs(d, exist_ok=True)
        subprocess.Popen(["xdg-open", d])

    # ---- Backup ----
    def _sauvegarder(self):
        self.lbl_bk_status.configure(text="Sauvegarde en cours...", text_color=COLORS["gold"])
        self.update()
        compress = self.compress_var.get()
        def do():
            try:
                from utils.backup import sauvegarder
                path = sauvegarder(compress=compress,
                                   on_progress=lambda m: self.after(
                                       0, lambda msg=m: self.lbl_bk_status.configure(
                                           text=msg, text_color=COLORS["text_muted"])))
                nom_bk = os.path.basename(path)
                self.after(0, lambda n=nom_bk: [
                    self.lbl_bk_status.configure(
                        text=f"  {n}",
                        text_color=COLORS["success"]),
                    self._load_backups()
                ])
            except Exception as e:
                msg = str(e)
                self.after(0, lambda m=msg: self.lbl_bk_status.configure(
                    text=f"Erreur : {m}", text_color=COLORS["danger"]))
        threading.Thread(target=do, daemon=True).start()

    def _toggle_auto(self):
        from utils.backup import demarrer_sauvegarde_auto, arreter_sauvegarde_auto
        if self.auto_var.get():
            heure = self.e_heure.get().strip() or "23:00"
            demarrer_sauvegarde_auto(heure, on_done=lambda m: self.after(
                0, lambda msg=m: self.lbl_bk_status.configure(
                    text=msg, text_color=COLORS["success"])))
            self.lbl_bk_status.configure(
                text=f"Sauvegarde auto activée à {heure}",
                text_color=COLORS["success"])
        else:
            arreter_sauvegarde_auto()
            self.lbl_bk_status.configure(text="Sauvegarde auto désactivée.",
                                          text_color=COLORS["text_muted"])

    def _load_backups(self):
        from utils.backup import lister_backups
        for w in self.scroll_bk.winfo_children():
            w.destroy()
        C = COLORS
        backups = lister_backups()
        if not backups:
            ctk.CTkLabel(self.scroll_bk, text="Aucune sauvegarde disponible.",
                         font=FONTS["small"], text_color=C["text_muted"]).pack(pady=8)
            return
        for i, b in enumerate(backups):
            bg  = C["bg_card"] if i % 2 == 0 else C["bg_dark"]
            rf  = ctk.CTkFrame(self.scroll_bk, fg_color=bg, corner_radius=0)
            rf.pack(fill="x")
            ctk.CTkLabel(rf, text=b["nom"], font=FONTS["small"],
                         text_color=C["text"], anchor="w").pack(side="left", padx=8, pady=5)
            ctk.CTkLabel(rf, text=f"{b['taille']/1024:.0f} Ko  {b['date'].strftime('%d/%m %H:%M')}",
                         font=FONTS["small"], text_color=C["text_muted"]).pack(side="right", padx=8)

    def _restaurer(self):
        chemin = filedialog.askopenfilename(
            filetypes=[("SQL", "*.sql *.sql.gz")],
            title="Sélectionner une sauvegarde"
        )
        if not chemin: return
        if not messagebox.askyesno("Confirmer restauration",
            f"ATTENTION : ceci écrasera toutes les données actuelles !\n\nRestaurer depuis :\n{os.path.basename(chemin)} ?"):
            return
        self.lbl_bk_status.configure(text="Restauration en cours...", text_color=COLORS["gold"])
        def do():
            from utils.backup import restaurer
            ok = restaurer(chemin, on_progress=lambda m: self.after(
                0, lambda msg=m: self.lbl_bk_status.configure(
                    text=msg, text_color=COLORS["text_muted"])))
            color = COLORS["success"] if ok else COLORS["danger"]
            msg   = "Restauration terminee !" if ok else "Echec de la restauration."
            self.after(0, lambda m=msg, c=color: self.lbl_bk_status.configure(text=m, text_color=c))
        threading.Thread(target=do, daemon=True).start()

    def _ouvrir_dossier_bk(self):
        import subprocess
        from utils.backup import BACKUP_CONFIG
        d = BACKUP_CONFIG["backup_dir"]
        os.makedirs(d, exist_ok=True)
        subprocess.Popen(["xdg-open", d])