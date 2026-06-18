# ============================================================
# views/admin/boissons.py — Gestion des boissons (Admin)
# ============================================================

import customtkinter as ctk
from tkinter import messagebox
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import COLORS, FONTS
from database.db import db


class BoissonsView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self._selected_id = None
        self._build()
        self._load()

    def _build(self):
        C = COLORS
        # ---- Titre ----
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 0))
        ctk.CTkLabel(hdr, text="🍾 Gestion des Boissons",
                     font=FONTS["heading"], text_color=C["gold"]).pack(side="left")
        ctk.CTkButton(hdr, text="+ Nouvelle boisson", width=160, height=36,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=FONTS["badge"], command=self._new).pack(side="right")

        # ---- Corps ----
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # -- Tableau --
        tbl_frame = ctk.CTkFrame(body, fg_color=C["bg_card"],
                                  corner_radius=10, border_width=1,
                                  border_color=C["border"])
        tbl_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # En-têtes
        headers = ["ID", "Nom", "Catégorie", "Prix vente", "Prix achat", "Stock", "Unité"]
        widths  = [40, 180, 100, 90, 90, 60, 80]
        head_row = ctk.CTkFrame(tbl_frame, fg_color=C["bg_sidebar"], corner_radius=0)
        head_row.pack(fill="x", padx=1, pady=(1, 0))
        for h, w in zip(headers, widths):
            ctk.CTkLabel(head_row, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=6, pady=8)

        # Zone scrollable
        self.scroll = ctk.CTkScrollableFrame(tbl_frame, fg_color="transparent", corner_radius=0)
        self.scroll.pack(fill="both", expand=True)

        # -- Formulaire --
        form = ctk.CTkFrame(body, fg_color=C["bg_card"], corner_radius=10,
                             border_width=1, border_color=C["border"])
        form.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(form, text="Détail / Édition",
                     font=FONTS["heading"], text_color=C["gold"]).pack(pady=(16, 10))

        fields = [
            ("Nom de la boisson", "entry_nom"),
            ("Catégorie", "entry_cat"),
            ("Prix de vente (FCFA)", "entry_prix_vente"),
            ("Prix d'achat (FCFA)", "entry_prix_achat"),
            ("Stock initial", "entry_stock"),
            ("Unité (bouteille, verre…)", "entry_unite"),
        ]
        for label, attr in fields:
            ctk.CTkLabel(form, text=label, font=FONTS["small"],
                         text_color=C["text_muted"], anchor="w").pack(fill="x", padx=16, pady=(6, 1))
            e = ctk.CTkEntry(form, height=36, fg_color=C["bg_dark"],
                              border_color=C["border"], text_color=C["text"],
                              font=FONTS["body"])
            e.pack(fill="x", padx=16)
            setattr(self, attr, e)

        # Boutons formulaire
        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=16)
        ctk.CTkButton(btn_row, text="💾 Enregistrer", fg_color=C["accent"],
                      hover_color=C["accent2"], font=FONTS["badge"],
                      command=self._save).pack(side="left", expand=True, padx=(0, 4))
        ctk.CTkButton(btn_row, text="🗑 Supprimer", fg_color="#5D0000",
                      hover_color="#3D0000", font=FONTS["badge"],
                      command=self._delete).pack(side="right", expand=True, padx=(4, 0))
        ctk.CTkButton(form, text="✖ Vider le formulaire", fg_color="transparent",
                      hover_color=C["bg_sidebar"], text_color=C["text_muted"],
                      font=FONTS["small"], command=self._clear).pack(pady=(0, 8))

    def _load(self):
        """Recharge la liste des boissons."""
        for w in self.scroll.winfo_children():
            w.destroy()
        rows = db.fetchall("SELECT * FROM boissons WHERE actif=1 ORDER BY nom")
        C = COLORS
        for i, r in enumerate(rows):
            bg = C["bg_card"] if i % 2 == 0 else C["bg_dark"]
            row_f = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=0)
            row_f.pack(fill="x")
            vals   = [r["id"], r["nom"], r["categorie"],
                      f"{r['prix_vente']:,.0f}", f"{r['prix_achat']:,.0f}",
                      r["stock"], r["unite"]]
            widths = [40, 180, 100, 90, 90, 60, 80]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(row_f, text=str(v), font=FONTS["small"],
                             text_color=C["text"], width=w, anchor="w").pack(side="left", padx=6, pady=7)
            row_f.bind("<Button-1>", lambda e, row=r: self._select_row(row))
            for child in row_f.winfo_children():
                child.bind("<Button-1>", lambda e, row=r: self._select_row(row))

    def _select_row(self, row):
        self._selected_id = row["id"]
        self.entry_nom.delete(0, "end");   self.entry_nom.insert(0, row["nom"])
        self.entry_cat.delete(0, "end");   self.entry_cat.insert(0, row["categorie"] or "")
        self.entry_prix_vente.delete(0, "end"); self.entry_prix_vente.insert(0, str(row["prix_vente"]))
        self.entry_prix_achat.delete(0, "end"); self.entry_prix_achat.insert(0, str(row["prix_achat"]))
        self.entry_stock.delete(0, "end"); self.entry_stock.insert(0, str(row["stock"]))
        self.entry_unite.delete(0, "end"); self.entry_unite.insert(0, row["unite"] or "bouteille")

    def _new(self):
        self._selected_id = None
        self._clear()

    def _clear(self):
        self._selected_id = None
        for attr in ["entry_nom","entry_cat","entry_prix_vente","entry_prix_achat","entry_stock","entry_unite"]:
            getattr(self, attr).delete(0, "end")

    def _save(self):
        nom        = self.entry_nom.get().strip()
        cat        = self.entry_cat.get().strip() or "Boisson"
        unite      = self.entry_unite.get().strip() or "bouteille"
        try:
            pv = float(self.entry_prix_vente.get())
            pa = float(self.entry_prix_achat.get() or 0)
            st = int(self.entry_stock.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Prix et stock doivent être des nombres.")
            return
        if not nom:
            messagebox.showerror("Erreur", "Le nom est obligatoire.")
            return

        if self._selected_id:
            db.execute(
                "UPDATE boissons SET nom=%s,categorie=%s,prix_vente=%s,prix_achat=%s,stock=%s,unite=%s WHERE id=%s",
                (nom, cat, pv, pa, st, unite, self._selected_id), commit=True
            )
            messagebox.showinfo("Succès", "Boisson mise à jour.")
        else:
            db.execute(
                "INSERT INTO boissons (nom,categorie,prix_vente,prix_achat,stock,unite) VALUES (%s,%s,%s,%s,%s,%s)",
                (nom, cat, pv, pa, st, unite), commit=True
            )
            messagebox.showinfo("Succès", "Boisson ajoutée.")
        self._clear()
        self._load()

    def _delete(self):
        if not self._selected_id:
            messagebox.showwarning("Attention", "Sélectionnez une boisson.")
            return
        if messagebox.askyesno("Confirmer", "Supprimer cette boisson ?"):
            db.execute("UPDATE boissons SET actif=0 WHERE id=%s", (self._selected_id,), commit=True)
            self._clear()
            self._load()
