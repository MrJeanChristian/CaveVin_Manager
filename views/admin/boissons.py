# ============================================================
# views/admin/boissons.py — Gestion des boissons (Admin)
# ============================================================

import customtkinter as ctk
from tkinter import messagebox, filedialog
import sys, os, shutil, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import COLORS, FONTS
from database.db import db

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Dossier de stockage des photos (local, persistant)
PHOTOS_DIR = os.path.join(os.path.expanduser("~"), "CaveVin_Photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)

# Catégories prédéfinies (extensibles via "+ Autre...")
CATEGORIES = [
    "Vin", "Whisky", "Alcool fort", "Bière", "Champagne",
    "Jus", "Sucrerie / Soda", "Eau", "Cocktail", "Autre",
]

EXTENSIONS_IMG = [("Images", "*.jpg *.jpeg *.png *.webp"), ("Tous fichiers", "*.*")]


class BoissonsView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self._selected_id   = None
        self._photo_path    = None   # chemin local (déjà copié) de la boisson sélectionnée
        self._photo_tmp     = None   # chemin temporaire choisi par l'utilisateur (pas encore copié)
        self._photo_ctk_img = None   # référence forte pour éviter le garbage collector
        self._build()
        self._load()

    # ---------------------------------------------------------------- UI --
    def _build(self):
        C = COLORS
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 0))
        ctk.CTkLabel(hdr, text="🍾 Gestion des Boissons",
                     font=FONTS["heading"], text_color=C["gold"]).pack(side="left")
        ctk.CTkButton(hdr, text="+ Nouvelle boisson", width=160, height=36,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=FONTS["badge"], command=self._new).pack(side="right")

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

        headers = ["", "Nom", "Catégorie", "Prix vente", "Prix achat", "Stock", "Unité"]
        widths  = [40, 160, 110, 90, 90, 55, 75]
        head_row = ctk.CTkFrame(tbl_frame, fg_color=C["bg_sidebar"], corner_radius=0)
        head_row.pack(fill="x", padx=1, pady=(1, 0))
        for h, w in zip(headers, widths):
            ctk.CTkLabel(head_row, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=6, pady=8)

        self.scroll = ctk.CTkScrollableFrame(tbl_frame, fg_color="transparent", corner_radius=0)
        self.scroll.pack(fill="both", expand=True)

        # -- Formulaire --
        form = ctk.CTkFrame(body, fg_color=C["bg_card"], corner_radius=10,
                             border_width=1, border_color=C["border"])
        form.grid(row=0, column=1, sticky="nsew")

        scroll_form = ctk.CTkScrollableFrame(form, fg_color="transparent")
        scroll_form.pack(fill="both", expand=True, padx=2, pady=2)

        ctk.CTkLabel(scroll_form, text="Détail / Édition",
                     font=FONTS["heading"], text_color=C["gold"]).pack(pady=(14, 10))

        # ---- Photo ----
        photo_card = ctk.CTkFrame(scroll_form, fg_color=C["bg_dark"], corner_radius=10,
                                   border_width=1, border_color=C["border"])
        photo_card.pack(padx=16, pady=(0, 12), fill="x")

        self.photo_preview = ctk.CTkLabel(
            photo_card, text="🍷\nAucune photo", font=("Helvetica", 13),
            text_color=C["text_muted"], width=140, height=140,
            fg_color=C["bg_card"], corner_radius=8
        )
        self.photo_preview.pack(pady=12)

        photo_btn_row = ctk.CTkFrame(photo_card, fg_color="transparent")
        photo_btn_row.pack(pady=(0, 12), fill="x", padx=12)
        ctk.CTkButton(photo_btn_row, text="📷 Choisir une photo", height=32,
                      fg_color=C["accent2"], hover_color=C["accent"],
                      font=FONTS["small"], command=self._choisir_photo).pack(fill="x", pady=(0, 4))
        ctk.CTkButton(photo_btn_row, text="✕ Retirer la photo", height=28,
                      fg_color="transparent", hover_color=C["bg_sidebar"],
                      text_color=C["text_muted"], font=FONTS["small"],
                      command=self._retirer_photo).pack(fill="x")

        # ---- Nom ----
        ctk.CTkLabel(scroll_form, text="Nom de la boisson", font=FONTS["small"],
                     text_color=C["text_muted"], anchor="w").pack(fill="x", padx=16, pady=(6, 1))
        self.entry_nom = ctk.CTkEntry(scroll_form, height=36, fg_color=C["bg_dark"],
                                       border_color=C["border"], text_color=C["text"],
                                       font=FONTS["body"])
        self.entry_nom.pack(fill="x", padx=16)

        # ---- Catégorie (dropdown) ----
        ctk.CTkLabel(scroll_form, text="Catégorie", font=FONTS["small"],
                     text_color=C["text_muted"], anchor="w").pack(fill="x", padx=16, pady=(6, 1))
        self.cat_var = ctk.StringVar(value=CATEGORIES[0])
        self.cb_cat  = ctk.CTkComboBox(scroll_form, variable=self.cat_var,
                                        values=CATEGORIES, height=36,
                                        fg_color=C["bg_dark"], border_color=C["border"],
                                        button_color=C["accent"], button_hover_color=C["accent2"],
                                        text_color=C["text"], font=FONTS["body"],
                                        command=self._on_categorie_change)
        self.cb_cat.pack(fill="x", padx=16)

        # Champ catégorie custom (caché par défaut, visible si "Autre")
        self.entry_cat_custom = ctk.CTkEntry(scroll_form, height=36, fg_color=C["bg_dark"],
                                              border_color=C["border"], text_color=C["text"],
                                              font=FONTS["body"],
                                              placeholder_text="Préciser la catégorie...")

        # ---- Autres champs ----
        fields = [
            ("Prix de vente (FCFA)", "entry_prix_vente"),
            ("Prix d'achat (FCFA)", "entry_prix_achat"),
            ("Stock initial", "entry_stock"),
            ("Unité (bouteille, verre…)", "entry_unite"),
        ]
        for label, attr in fields:
            ctk.CTkLabel(scroll_form, text=label, font=FONTS["small"],
                         text_color=C["text_muted"], anchor="w").pack(fill="x", padx=16, pady=(6, 1))
            e = ctk.CTkEntry(scroll_form, height=36, fg_color=C["bg_dark"],
                              border_color=C["border"], text_color=C["text"],
                              font=FONTS["body"])
            e.pack(fill="x", padx=16)
            setattr(self, attr, e)

        # Boutons formulaire
        btn_row = ctk.CTkFrame(scroll_form, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=16)
        ctk.CTkButton(btn_row, text="💾 Enregistrer", fg_color=C["accent"],
                      hover_color=C["accent2"], font=FONTS["badge"],
                      command=self._save).pack(side="left", expand=True, padx=(0, 4))
        ctk.CTkButton(btn_row, text="🗑 Supprimer", fg_color="#5D0000",
                      hover_color="#3D0000", font=FONTS["badge"],
                      command=self._delete).pack(side="right", expand=True, padx=(4, 0))
        ctk.CTkButton(scroll_form, text="✖ Vider le formulaire", fg_color="transparent",
                      hover_color=C["bg_sidebar"], text_color=C["text_muted"],
                      font=FONTS["small"], command=self._clear).pack(pady=(0, 8))

    # -------------------------------------------------------------- Photo --
    def _on_categorie_change(self, value=None):
        if self.cat_var.get() == "Autre":
            self.entry_cat_custom.pack(fill="x", padx=16, pady=(4, 0))
        else:
            self.entry_cat_custom.pack_forget()

    def _choisir_photo(self):
        chemin = filedialog.askopenfilename(
            title="Choisir une photo de la boisson",
            filetypes=EXTENSIONS_IMG
        )
        if not chemin:
            return
        self._photo_tmp = chemin
        self._afficher_apercu(chemin)

    def _retirer_photo(self):
        self._photo_tmp  = "__REMOVE__"
        self._photo_path = None
        self.photo_preview.configure(image=None, text="🍷\nAucune photo")
        self._photo_ctk_img = None

    def _afficher_apercu(self, chemin: str):
        """Affiche un aperçu de l'image choisie (depuis fichier local ou tmp)."""
        if not HAS_PIL or not chemin or not os.path.exists(chemin):
            self.photo_preview.configure(image=None, text="🍷\nAperçu indisponible")
            return
        try:
            img = Image.open(chemin)
            img.thumbnail((130, 130))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self._photo_ctk_img = ctk_img  # garder une référence forte
            self.photo_preview.configure(image=ctk_img, text="")
        except Exception:
            self.photo_preview.configure(image=None, text="🍷\nErreur image")

    def _enregistrer_photo_locale(self, chemin_source: str) -> str:
        """Copie la photo choisie dans le dossier persistant et retourne le nouveau chemin."""
        ext = os.path.splitext(chemin_source)[1].lower() or ".jpg"
        nom_fichier = f"{uuid.uuid4().hex}{ext}"
        dest = os.path.join(PHOTOS_DIR, nom_fichier)
        try:
            if HAS_PIL:
                img = Image.open(chemin_source)
                img.thumbnail((500, 500))   # redimensionner pour ne pas stocker des photos énormes
                if img.mode in ("RGBA", "P") and ext in (".jpg", ".jpeg"):
                    img = img.convert("RGB")
                img.save(dest)
            else:
                shutil.copy2(chemin_source, dest)
            return dest
        except Exception as e:
            print(f"[PHOTO] Erreur enregistrement : {e}")
            return None

    # ---------------------------------------------------------------- Data --
    def _load(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        rows = db.fetchall("SELECT * FROM boissons WHERE actif=1 ORDER BY nom")
        C = COLORS
        for i, r in enumerate(rows):
            bg = C["bg_card"] if i % 2 == 0 else C["bg_dark"]
            row_f = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=0)
            row_f.pack(fill="x")

            # Vignette miniature
            thumb_lbl = ctk.CTkLabel(row_f, text="🍾", font=("Helvetica", 16),
                                      width=40, anchor="center")
            photo = r.get("photo_path")
            if photo and os.path.exists(photo) and HAS_PIL:
                try:
                    img = Image.open(photo)
                    img.thumbnail((28, 28))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    thumb_lbl.configure(image=ctk_img, text="")
                    thumb_lbl.image = ctk_img  # référence forte
                except Exception:
                    pass
            thumb_lbl.pack(side="left", padx=6, pady=5)

            vals   = [r["nom"], r["categorie"],
                      f"{r['prix_vente']:,.0f}", f"{r['prix_achat']:,.0f}",
                      r["stock"], r["unite"]]
            widths = [160, 110, 90, 90, 55, 75]
            for v, w in zip(vals, widths):
                lbl = ctk.CTkLabel(row_f, text=str(v), font=FONTS["small"],
                             text_color=C["text"], width=w, anchor="w")
                lbl.pack(side="left", padx=6, pady=7)
                lbl.bind("<Button-1>", lambda e, row=r: self._select_row(row))
            row_f.bind("<Button-1>", lambda e, row=r: self._select_row(row))
            thumb_lbl.bind("<Button-1>", lambda e, row=r: self._select_row(row))

    def _select_row(self, row):
        self._selected_id = row["id"]
        self._photo_tmp    = None
        self._photo_path   = row.get("photo_path")

        self.entry_nom.delete(0, "end"); self.entry_nom.insert(0, row["nom"])

        cat = row["categorie"] or "Boisson"
        if cat in CATEGORIES:
            self.cat_var.set(cat)
            self.entry_cat_custom.pack_forget()
        else:
            self.cat_var.set("Autre")
            self.entry_cat_custom.delete(0, "end")
            self.entry_cat_custom.insert(0, cat)
            self.entry_cat_custom.pack(fill="x", padx=16, pady=(4, 0))

        self.entry_prix_vente.delete(0, "end"); self.entry_prix_vente.insert(0, str(row["prix_vente"]))
        self.entry_prix_achat.delete(0, "end"); self.entry_prix_achat.insert(0, str(row["prix_achat"]))
        self.entry_stock.delete(0, "end"); self.entry_stock.insert(0, str(row["stock"]))
        self.entry_unite.delete(0, "end"); self.entry_unite.insert(0, row["unite"] or "bouteille")

        if self._photo_path and os.path.exists(self._photo_path):
            self._afficher_apercu(self._photo_path)
        else:
            self.photo_preview.configure(image=None, text="🍷\nAucune photo")
            self._photo_ctk_img = None

    def _new(self):
        self._selected_id = None
        self._clear()

    def _clear(self):
        self._selected_id   = None
        self._photo_tmp      = None
        self._photo_path     = None
        self._photo_ctk_img  = None
        for attr in ["entry_nom","entry_prix_vente","entry_prix_achat","entry_stock","entry_unite"]:
            getattr(self, attr).delete(0, "end")
        self.cat_var.set(CATEGORIES[0])
        self.entry_cat_custom.delete(0, "end")
        self.entry_cat_custom.pack_forget()
        self.photo_preview.configure(image=None, text="🍷\nAucune photo")

    def _save(self):
        nom   = self.entry_nom.get().strip()
        cat   = self.entry_cat_custom.get().strip() if self.cat_var.get() == "Autre" else self.cat_var.get()
        cat   = cat or "Boisson"
        unite = self.entry_unite.get().strip() or "bouteille"
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

        # Gestion de la photo
        photo_final = self._photo_path  # valeur par défaut : inchangée
        if self._photo_tmp == "__REMOVE__":
            photo_final = None
        elif self._photo_tmp:
            nouveau = self._enregistrer_photo_locale(self._photo_tmp)
            if nouveau:
                photo_final = nouveau

        if self._selected_id:
            db.execute(
                "UPDATE boissons SET nom=%s,categorie=%s,prix_vente=%s,prix_achat=%s,stock=%s,unite=%s,photo_path=%s WHERE id=%s",
                (nom, cat, pv, pa, st, unite, photo_final, self._selected_id), commit=True
            )
            messagebox.showinfo("Succès", "Boisson mise à jour.")
        else:
            db.execute(
                "INSERT INTO boissons (nom,categorie,prix_vente,prix_achat,stock,unite,photo_path) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (nom, cat, pv, pa, st, unite, photo_final), commit=True
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
