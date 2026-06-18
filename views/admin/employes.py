# ============================================================
# views/admin/employes.py — Gestion des employés (Admin)
# ============================================================

import customtkinter as ctk
from tkinter import messagebox
import hashlib, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import COLORS, FONTS, ROLES
from database.db import db


def _hash(p): return hashlib.sha256(p.encode()).hexdigest()


class EmployesView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self._selected_id = None
        self._build()
        self._load()

    def _build(self):
        C = COLORS
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 0))
        ctk.CTkLabel(hdr, text="👥 Gestion des Employés",
                     font=FONTS["heading"], text_color=C["gold"]).pack(side="left")
        ctk.CTkButton(hdr, text="+ Nouvel employé", width=160, height=36,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=FONTS["badge"], command=self._new).pack(side="right")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # ---- Tableau ----
        tbl = ctk.CTkFrame(body, fg_color=C["bg_card"], corner_radius=10,
                            border_width=1, border_color=C["border"])
        tbl.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        headers = ["ID", "Prénom", "Nom", "Username", "Rôle", "Salaire", "Statut"]
        widths  = [40, 110, 110, 100, 90, 90, 70]
        head_row = ctk.CTkFrame(tbl, fg_color=C["bg_sidebar"], corner_radius=0)
        head_row.pack(fill="x", padx=1, pady=(1, 0))
        for h, w in zip(headers, widths):
            ctk.CTkLabel(head_row, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=5, pady=8)

        self.scroll = ctk.CTkScrollableFrame(tbl, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        # ---- Formulaire ----
        form = ctk.CTkFrame(body, fg_color=C["bg_card"], corner_radius=10,
                             border_width=1, border_color=C["border"])
        form.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(form, text="Fiche Employé",
                     font=FONTS["heading"], text_color=C["gold"]).pack(pady=(16, 10))

        for label, attr in [("Prénom","e_prenom"),("Nom","e_nom"),("Username","e_user"),("Salaire (FCFA)","e_sal")]:
            ctk.CTkLabel(form, text=label, font=FONTS["small"],
                         text_color=C["text_muted"], anchor="w").pack(fill="x", padx=16, pady=(5, 1))
            e = ctk.CTkEntry(form, height=36, fg_color=C["bg_dark"],
                              border_color=C["border"], text_color=C["text"], font=FONTS["body"])
            e.pack(fill="x", padx=16)
            setattr(self, attr, e)

        # Mot de passe
        ctk.CTkLabel(form, text="Mot de passe (laisser vide = inchangé)",
                     font=FONTS["small"], text_color=C["text_muted"], anchor="w").pack(fill="x", padx=16, pady=(5,1))
        self.e_pass = ctk.CTkEntry(form, height=36, show="●",
                                    fg_color=C["bg_dark"], border_color=C["border"],
                                    text_color=C["text"], font=FONTS["body"])
        self.e_pass.pack(fill="x", padx=16)

        # Rôle
        ctk.CTkLabel(form, text="Rôle", font=FONTS["small"],
                     text_color=C["text_muted"], anchor="w").pack(fill="x", padx=16, pady=(5,1))
        self.role_var = ctk.StringVar(value="serveur")
        role_frame = ctk.CTkFrame(form, fg_color="transparent")
        role_frame.pack(fill="x", padx=16)
        for key, label in ROLES.items():
            if key == "admin": continue
            ctk.CTkRadioButton(role_frame, text=label, variable=self.role_var, value=key,
                                font=FONTS["body"], text_color=C["text"],
                                fg_color=C["accent"]).pack(side="left", padx=6, pady=6)

        # Actif toggle
        self.actif_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(form, text="Compte actif", variable=self.actif_var,
                         font=FONTS["body"], text_color=C["text"],
                         fg_color=C["accent"]).pack(padx=16, pady=8, anchor="w")

        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=8)
        ctk.CTkButton(btn_row, text="💾 Enregistrer", fg_color=C["accent"],
                      hover_color=C["accent2"], font=FONTS["badge"],
                      command=self._save).pack(side="left", expand=True, padx=(0,4))
        ctk.CTkButton(btn_row, text="🗑 Supprimer", fg_color="#5D0000",
                      hover_color="#3D0000", font=FONTS["badge"],
                      command=self._delete).pack(side="right", expand=True, padx=(4,0))
        ctk.CTkButton(form, text="✖ Vider", fg_color="transparent",
                      hover_color=C["bg_sidebar"], text_color=C["text_muted"],
                      font=FONTS["small"], command=self._clear).pack(pady=(0,8))

    def _load(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        rows = db.fetchall(
            "SELECT * FROM utilisateurs WHERE role != 'admin' ORDER BY nom, prenom"
        )
        C = COLORS
        for i, r in enumerate(rows):
            bg = C["bg_card"] if i % 2 == 0 else C["bg_dark"]
            rf = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=0)
            rf.pack(fill="x")
            statut = "✅ Actif" if r["actif"] else "❌ Inactif"
            vals  = [r["id"], r["prenom"], r["nom"], r["username"],
                     ROLES.get(r["role"],"?"), f"{r['salaire']:,.0f}", statut]
            widths= [40, 110, 110, 100, 90, 90, 70]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(rf, text=str(v), font=FONTS["small"],
                             text_color=C["text"], width=w, anchor="w").pack(side="left", padx=5, pady=7)
            rf.bind("<Button-1>", lambda e, row=r: self._select(row))
            for c in rf.winfo_children():
                c.bind("<Button-1>", lambda e, row=r: self._select(row))

    def _select(self, row):
        self._selected_id = row["id"]
        for attr, key in [("e_prenom","prenom"),("e_nom","nom"),("e_user","username"),("e_sal","salaire")]:
            e = getattr(self, attr)
            e.delete(0,"end"); e.insert(0, str(row[key]))
        self.e_pass.delete(0,"end")
        self.role_var.set(row["role"])
        self.actif_var.set(bool(row["actif"]))

    def _new(self): self._selected_id = None; self._clear()
    def _clear(self):
        self._selected_id = None
        for attr in ["e_prenom","e_nom","e_user","e_sal","e_pass"]:
            getattr(self, attr).delete(0,"end")
        self.role_var.set("serveur"); self.actif_var.set(True)

    def _save(self):
        prenom = self.e_prenom.get().strip()
        nom    = self.e_nom.get().strip()
        user   = self.e_user.get().strip()
        passwd = self.e_pass.get().strip()
        role   = self.role_var.get()
        actif  = int(self.actif_var.get())
        try: sal = float(self.e_sal.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur","Salaire invalide."); return
        if not prenom or not nom or not user:
            messagebox.showerror("Erreur","Prénom, nom et username requis."); return

        if self._selected_id:
            if passwd:
                db.execute(
                    "UPDATE utilisateurs SET prenom=%s,nom=%s,username=%s,password=%s,role=%s,salaire=%s,actif=%s WHERE id=%s",
                    (prenom,nom,user,_hash(passwd),role,sal,actif,self._selected_id), commit=True
                )
            else:
                db.execute(
                    "UPDATE utilisateurs SET prenom=%s,nom=%s,username=%s,role=%s,salaire=%s,actif=%s WHERE id=%s",
                    (prenom,nom,user,role,sal,actif,self._selected_id), commit=True
                )
            messagebox.showinfo("Succès","Employé mis à jour.")
        else:
            if not passwd:
                messagebox.showerror("Erreur","Mot de passe requis pour un nouvel employé."); return
            existing = db.fetchone("SELECT id FROM utilisateurs WHERE username=%s",(user,))
            if existing:
                messagebox.showerror("Erreur","Ce username existe déjà."); return
            db.execute(
                "INSERT INTO utilisateurs (prenom,nom,username,password,role,salaire,actif) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (prenom,nom,user,_hash(passwd),role,sal,actif), commit=True
            )
            messagebox.showinfo("Succès","Employé créé.")
        self._clear(); self._load()

    def _delete(self):
        if not self._selected_id:
            messagebox.showwarning("Attention","Sélectionnez un employé."); return
        if messagebox.askyesno("Confirmer","Désactiver cet employé ?"):
            db.execute("UPDATE utilisateurs SET actif=0 WHERE id=%s",(self._selected_id,),commit=True)
            self._clear(); self._load()
