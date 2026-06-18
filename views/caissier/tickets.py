# ============================================================
# views/caissier/tickets.py — Saisie des tickets de vente
# ============================================================

import customtkinter as ctk
from tkinter import messagebox, filedialog
import sys, os, uuid
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import COLORS, FONTS
from database.db import db
from utils.pdf_ticket import generer_ticket_pdf, ouvrir_pdf

TICKETS_DIR = os.path.join(os.path.expanduser("~"), "CaveVin_Tickets")
os.makedirs(TICKETS_DIR, exist_ok=True)


class TicketsView(ctk.CTkFrame):
    def __init__(self, parent, user, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self.user    = user
        self._lignes = []
        self._build()
        self._refresh_boissons()

    # ------------------------------------------------------------------ UI --
    def _build(self):
        C = COLORS
        ctk.CTkLabel(self, text="  Saisie de Ticket de Vente",
                     font=FONTS["heading"], text_color=C["gold"]).pack(anchor="w", padx=24, pady=(20,16))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        # ---- Panneau gauche ----
        left = ctk.CTkFrame(body, fg_color=C["bg_card"], corner_radius=10,
                             border_width=1, border_color=C["border"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0,10))

        ctk.CTkLabel(left, text="Ajouter un article",
                     font=FONTS["body"], text_color=C["text_muted"]).pack(pady=(14,8))

        ctk.CTkLabel(left, text="Serveur", font=FONTS["small"],
                     text_color=C["text_muted"], anchor="w").pack(fill="x", padx=14)
        self.serveur_var = ctk.StringVar()
        self.cb_serveur  = ctk.CTkComboBox(left, variable=self.serveur_var,
                                            fg_color=C["bg_dark"], border_color=C["border"],
                                            button_color=C["accent"], text_color=C["text"],
                                            font=FONTS["body"])
        self.cb_serveur.pack(fill="x", padx=14, pady=(2,10))
        self._load_serveurs()

        ctk.CTkLabel(left, text="Date de vente", font=FONTS["small"],
                     text_color=C["text_muted"], anchor="w").pack(fill="x", padx=14)
        self.e_date = ctk.CTkEntry(left, height=36, fg_color=C["bg_dark"],
                                    border_color=C["border"], text_color=C["text"],
                                    font=FONTS["body"])
        self.e_date.insert(0, str(date.today()))
        self.e_date.pack(fill="x", padx=14, pady=(2,10))

        ctk.CTkLabel(left, text="Boisson", font=FONTS["small"],
                     text_color=C["text_muted"], anchor="w").pack(fill="x", padx=14)
        self.boisson_var = ctk.StringVar()
        self.cb_boisson  = ctk.CTkComboBox(left, variable=self.boisson_var,
                                            fg_color=C["bg_dark"], border_color=C["border"],
                                            button_color=C["accent"], text_color=C["text"],
                                            font=FONTS["body"])
        self.cb_boisson.pack(fill="x", padx=14, pady=(2,10))

        ctk.CTkLabel(left, text="Quantite", font=FONTS["small"],
                     text_color=C["text_muted"], anchor="w").pack(fill="x", padx=14)
        self.e_qte = ctk.CTkEntry(left, height=36, fg_color=C["bg_dark"],
                                   border_color=C["border"], text_color=C["text"],
                                   font=FONTS["body"])
        self.e_qte.insert(0, "1")
        self.e_qte.pack(fill="x", padx=14, pady=(2,14))

        ctk.CTkButton(left, text="+ Ajouter au ticket", height=40,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=FONTS["badge"], command=self._add_ligne).pack(fill="x", padx=14, pady=(0,10))

        ctk.CTkLabel(left, text="Montant recu (FCFA)", font=FONTS["small"],
                     text_color=C["text_muted"], anchor="w").pack(fill="x", padx=14)
        self.e_recu = ctk.CTkEntry(left, height=36, fg_color=C["bg_dark"],
                                    border_color=C["border"], text_color=C["text"],
                                    font=FONTS["body"])
        self.e_recu.pack(fill="x", padx=14, pady=(2,10))

        ctk.CTkLabel(left, text="Notes (optionnel)", font=FONTS["small"],
                     text_color=C["text_muted"], anchor="w").pack(fill="x", padx=14)
        self.e_notes = ctk.CTkEntry(left, height=36, fg_color=C["bg_dark"],
                                     border_color=C["border"], text_color=C["text"],
                                     font=FONTS["body"])
        self.e_notes.pack(fill="x", padx=14, pady=(2,14))

        # Boutons d'action finaux
        ctk.CTkButton(left, text="  Valider + Imprimer PDF", height=44,
                      fg_color=C["success"], hover_color="#1E8449",
                      text_color=C["white"], font=("Helvetica", 13, "bold"),
                      command=lambda: self._valider(imprimer=True)).pack(fill="x", padx=14, pady=(0,6))
        ctk.CTkButton(left, text="Valider sans impression", height=36,
                      fg_color="transparent", hover_color=C["bg_sidebar"],
                      text_color=C["text_muted"], font=FONTS["small"],
                      command=lambda: self._valider(imprimer=False)).pack(fill="x", padx=14, pady=(0,14))

        # ---- Panneau droit ----
        right = ctk.CTkFrame(body, fg_color=C["bg_card"], corner_radius=10,
                              border_width=1, border_color=C["border"])
        right.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(right, text="Lignes du ticket courant",
                     font=FONTS["body"], text_color=C["text_muted"]).pack(pady=(14,4))

        hdrs   = ["Boisson", "Qte", "Prix unit.", "Sous-total", ""]
        widths = [200, 60, 100, 110, 60]
        hrow = ctk.CTkFrame(right, fg_color=C["bg_sidebar"], corner_radius=0)
        hrow.pack(fill="x", padx=1)
        for h, w in zip(hdrs, widths):
            ctk.CTkLabel(hrow, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=6, pady=8)

        self.lignes_scroll = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self.lignes_scroll.pack(fill="both", expand=True, padx=1)

        self.lbl_total = ctk.CTkLabel(right, text="TOTAL : 0 FCFA",
                                       font=("Georgia", 18, "bold"), text_color=C["gold"])
        self.lbl_total.pack(pady=10)

        ctk.CTkButton(right, text="Vider le ticket", height=36,
                      fg_color="transparent", hover_color="#5D0000",
                      text_color=C["danger"], font=FONTS["badge"],
                      command=self._clear_ticket).pack(pady=(0,10))

    # ---------------------------------------------------------------- Data --
    def _load_serveurs(self):
        rows = db.fetchall(
            "SELECT id, CONCAT(prenom,' ',nom) AS nom FROM utilisateurs WHERE role='serveur' AND actif=1"
        )
        self._serveurs = {r["nom"]: r["id"] for r in rows}
        self.cb_serveur.configure(values=list(self._serveurs.keys()))
        if self._serveurs:
            self.serveur_var.set(list(self._serveurs.keys())[0])

    def _refresh_boissons(self):
        rows = db.fetchall("SELECT id, nom, prix_vente FROM boissons WHERE actif=1 ORDER BY nom")
        self._boissons = {r["nom"]: r for r in rows}
        self.cb_boisson.configure(values=list(self._boissons.keys()))
        if self._boissons:
            self.boisson_var.set(list(self._boissons.keys())[0])

    def _add_ligne(self):
        bname = self.boisson_var.get()
        if bname not in self._boissons:
            messagebox.showerror("Erreur", "Boisson invalide."); return
        try: qte = int(self.e_qte.get())
        except ValueError:
            messagebox.showerror("Erreur", "Quantite invalide."); return
        if qte <= 0:
            messagebox.showerror("Erreur", "Quantite doit etre > 0."); return
        b = self._boissons[bname]
        for l in self._lignes:
            if l["boisson_id"] == b["id"]:
                l["qte"] += qte
                self._render_lignes(); return
        self._lignes.append({"boisson_id": b["id"], "nom": bname,
                              "qte": qte, "prix": float(b["prix_vente"])})
        self._render_lignes()

    def _render_lignes(self):
        C = COLORS
        for w in self.lignes_scroll.winfo_children():
            w.destroy()
        total = 0
        for i, l in enumerate(self._lignes):
            sous = l["qte"] * l["prix"]
            total += sous
            bg = C["bg_card"] if i % 2 == 0 else C["bg_dark"]
            rf = ctk.CTkFrame(self.lignes_scroll, fg_color=bg, corner_radius=0)
            rf.pack(fill="x")
            vals   = [l["nom"], str(l["qte"]), f"{l['prix']:,.0f}", f"{sous:,.0f}"]
            widths = [200, 60, 100, 110]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(rf, text=v, font=FONTS["small"], text_color=C["text"],
                             width=w, anchor="w").pack(side="left", padx=6, pady=6)
            idx = i
            ctk.CTkButton(rf, text="x", width=40, height=28,
                          fg_color="transparent", hover_color="#5D0000",
                          text_color=C["danger"], font=FONTS["small"],
                          command=lambda i=idx: self._del_ligne(i)).pack(side="left")
        self.lbl_total.configure(text=f"TOTAL : {total:,.0f} FCFA")

    def _del_ligne(self, idx):
        self._lignes.pop(idx); self._render_lignes()

    def _clear_ticket(self):
        self._lignes.clear(); self._render_lignes()

    # ----------------------------------------------------------- Valider ---
    def _valider(self, imprimer=True):
        if not self._lignes:
            messagebox.showwarning("Attention", "Ajoutez au moins une ligne."); return
        serv_name = self.serveur_var.get()
        if serv_name not in self._serveurs:
            messagebox.showerror("Erreur", "Selectionnez un serveur."); return
        try: recu = float(self.e_recu.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Montant recu invalide."); return

        date_v   = self.e_date.get().strip() or str(date.today())
        serv_id  = self._serveurs[serv_name]
        caiss_id = self.user["id"]
        notes    = self.e_notes.get().strip()
        total    = sum(l["qte"] * l["prix"] for l in self._lignes)
        numero   = f"T{date.today().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

        # Insertion ticket
        db.execute(
            """INSERT INTO tickets (numero,serveur_id,caissier_id,date_vente,total,montant_recu,statut,notes)
               VALUES (%s,%s,%s,%s,%s,%s,'valide',%s)""",
            (numero, serv_id, caiss_id, date_v, total, recu, notes), commit=True
        )
        tid = db.lastrowid()
        for l in self._lignes:
            db.execute(
                "INSERT INTO ticket_lignes (ticket_id,boisson_id,quantite,prix_unit) VALUES (%s,%s,%s,%s)",
                (tid, l["boisson_id"], l["qte"], l["prix"]), commit=True
            )
            db.execute("UPDATE boissons SET stock=stock-%s WHERE id=%s",
                       (l["qte"], l["boisson_id"]), commit=True)

        manquant = total - recu
        if manquant > 0:
            db.execute(
                "INSERT INTO manquants (serveur_id,ticket_id,montant,description,date_manquant) VALUES (%s,%s,%s,%s,%s)",
                (serv_id, tid, manquant, f"Manquant ticket {numero}", date_v), commit=True
            )

        # Impression PDF
        if imprimer:
            caissier_row = db.fetchone(
                "SELECT CONCAT(prenom,' ',nom) AS nom FROM utilisateurs WHERE id=%s", (caiss_id,)
            )
            ticket_data = {
                "numero":       numero,
                "date_vente":   date_v,
                "total":        total,
                "montant_recu": recu,
                "serveur_nom":  serv_name,
                "caissier_nom": caissier_row["nom"] if caissier_row else "—",
                "notes":        notes,
            }
            pdf_lignes = [
                {"nom": l["nom"], "quantite": l["qte"],
                 "prix_unit": l["prix"], "sous_total": l["qte"] * l["prix"]}
                for l in self._lignes
            ]
            pdf_path = os.path.join(TICKETS_DIR, f"{numero}.pdf")
            try:
                generer_ticket_pdf(ticket_data, pdf_lignes, pdf_path)
                ouvrir_pdf(pdf_path)
            except Exception as e:
                messagebox.showerror("Erreur PDF", f"Impossible de generer le PDF:\n{e}")

        if manquant > 0:
            messagebox.showwarning("Manquant detecte",
                f"Ticket {numero} valide.\nManquant de {manquant:,.0f} FCFA pour {serv_name}.")
        else:
            messagebox.showinfo("Succes", f"Ticket {numero} valide !\nTotal : {total:,.0f} FCFA")

        self._clear_ticket()
        self.e_recu.delete(0, "end")
        self.e_notes.delete(0, "end")
