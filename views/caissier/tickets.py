
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
    """Vue principale : onglets Nouveau ticket | Tickets ouverts"""

    def __init__(self, parent, user, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self.user    = user
        self._lignes = []          # lignes du ticket en cours de saisie
        self._ticket_edit_id = None  # id du ticket ouvert en cours d'édition
        self._build()
        self._refresh_boissons()
        self._load_tickets_ouverts()

    # ============================================================ UI =====
    def _build(self):
        C = COLORS

        # Tabs
        self.tabs = ctk.CTkTabview(
            self,
            fg_color=C["bg_card"],
            segmented_button_fg_color=C["bg_sidebar"],
            segmented_button_selected_color=C["accent"],
            segmented_button_unselected_color=C["bg_sidebar"],
            segmented_button_selected_hover_color=C["accent2"],
            text_color=C["text"],
        )
        self.tabs.pack(fill="both", expand=True, padx=24, pady=16)

        tab_new  = self.tabs.add("🧾  Nouveau ticket")
        tab_open = self.tabs.add("📋  Tickets ouverts")

        self._build_tab_new(tab_new)
        self._build_tab_open(tab_open)

    # ------------------------------------------------- Tab Nouveau -------
    def _build_tab_new(self, parent):
        C = COLORS
        parent.columnconfigure(0, weight=2)
        parent.columnconfigure(1, weight=3)
        parent.rowconfigure(0, weight=1)

        # ---- Panneau gauche : saisie ----
        left = ctk.CTkFrame(parent, fg_color=C["bg_card"], corner_radius=10,
                             border_width=1, border_color=C["border"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=8)

        scroll_left = ctk.CTkScrollableFrame(left, fg_color="transparent")
        scroll_left.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll_left, text="Informations du ticket",
                     font=FONTS["body"], text_color=C["text_muted"]).pack(pady=(14, 8))

        # Indicateur édition
        self.lbl_edit_mode = ctk.CTkLabel(scroll_left, text="",
                                           font=FONTS["badge"], text_color=C["gold"])
        self.lbl_edit_mode.pack()

        # Serveur
        ctk.CTkLabel(scroll_left, text="Serveur", font=FONTS["small"],
                     text_color=C["text_muted"], anchor="w").pack(fill="x", padx=14)
        self.serveur_var = ctk.StringVar()
        self.cb_serveur  = ctk.CTkComboBox(scroll_left, variable=self.serveur_var,
                                            fg_color=C["bg_dark"], border_color=C["border"],
                                            button_color=C["accent"], text_color=C["text"],
                                            font=FONTS["body"])
        self.cb_serveur.pack(fill="x", padx=14, pady=(2, 10))
        self._load_serveurs()

        # Date
        ctk.CTkLabel(scroll_left, text="Date de vente", font=FONTS["small"],
                     text_color=C["text_muted"], anchor="w").pack(fill="x", padx=14)
        self.e_date = ctk.CTkEntry(scroll_left, height=36, fg_color=C["bg_dark"],
                                    border_color=C["border"], text_color=C["text"],
                                    font=FONTS["body"])
        self.e_date.insert(0, str(date.today()))
        self.e_date.pack(fill="x", padx=14, pady=(2, 10))

        # Boisson
        ctk.CTkLabel(scroll_left, text="Boisson", font=FONTS["small"],
                     text_color=C["text_muted"], anchor="w").pack(fill="x", padx=14)
        self.boisson_var = ctk.StringVar()
        self.cb_boisson  = ctk.CTkComboBox(scroll_left, variable=self.boisson_var,
                                            fg_color=C["bg_dark"], border_color=C["border"],
                                            button_color=C["accent"], text_color=C["text"],
                                            font=FONTS["body"])
        self.cb_boisson.pack(fill="x", padx=14, pady=(2, 10))

        # Quantité
        ctk.CTkLabel(scroll_left, text="Quantité", font=FONTS["small"],
                     text_color=C["text_muted"], anchor="w").pack(fill="x", padx=14)
        self.e_qte = ctk.CTkEntry(scroll_left, height=36, fg_color=C["bg_dark"],
                                   border_color=C["border"], text_color=C["text"],
                                   font=FONTS["body"])
        self.e_qte.insert(0, "1")
        self.e_qte.pack(fill="x", padx=14, pady=(2, 14))

        ctk.CTkButton(scroll_left, text="➕ Ajouter au ticket", height=40,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=FONTS["badge"], command=self._add_ligne).pack(fill="x", padx=14, pady=(0, 10))

        # Notes
        ctk.CTkLabel(scroll_left, text="Notes (optionnel)", font=FONTS["small"],
                     text_color=C["text_muted"], anchor="w").pack(fill="x", padx=14)
        self.e_notes = ctk.CTkEntry(scroll_left, height=36, fg_color=C["bg_dark"],
                                     border_color=C["border"], text_color=C["text"],
                                     font=FONTS["body"])
        self.e_notes.pack(fill="x", padx=14, pady=(2, 14))

        # Boutons finaux
        ctk.CTkButton(scroll_left, text="📂 Ouvrir (payer plus tard)", height=44,
                      fg_color=C["bg_dark"], hover_color=C["bg_sidebar"],
                      border_width=1, border_color=C["accent"],
                      text_color=C["gold"], font=("Helvetica", 12, "bold"),
                      command=lambda: self._soumettre(cloturer=False)).pack(
                      fill="x", padx=14, pady=(0, 6))

        ctk.CTkButton(scroll_left, text="✅ Encaisser maintenant", height=44,
                      fg_color=C["success"], hover_color="#1E8449",
                      text_color=C["white"], font=("Helvetica", 12, "bold"),
                      command=lambda: self._soumettre(cloturer=True)).pack(
                      fill="x", padx=14, pady=(0, 6))

        ctk.CTkButton(scroll_left, text="✖ Annuler / Nouveau", height=34,
                      fg_color="transparent", hover_color=C["bg_sidebar"],
                      text_color=C["text_muted"], font=FONTS["small"],
                      command=self._reset_form).pack(fill="x", padx=14, pady=(0, 14))

        # ---- Panneau droit : lignes ----
        right = ctk.CTkFrame(parent, fg_color=C["bg_card"], corner_radius=10,
                              border_width=1, border_color=C["border"])
        right.grid(row=0, column=1, sticky="nsew", pady=8)

        ctk.CTkLabel(right, text="Lignes du ticket",
                     font=FONTS["body"], text_color=C["text_muted"]).pack(pady=(14, 4))

        hdrs   = ["Boisson", "Qté", "Prix unit.", "Sous-total", ""]
        widths = [200, 55, 100, 110, 55]
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

        # Champ montant reçu (visible seulement pour encaissement)
        self.frame_encaissement = ctk.CTkFrame(right, fg_color="transparent")
        self.frame_encaissement.pack(fill="x", padx=14, pady=(0, 6))
        ctk.CTkLabel(self.frame_encaissement, text="Montant reçu (FCFA)",
                     font=FONTS["small"], text_color=C["text_muted"], anchor="w").pack(fill="x")
        self.e_recu = ctk.CTkEntry(self.frame_encaissement, height=36,
                                    fg_color=C["bg_dark"], border_color=C["border"],
                                    text_color=C["text"], font=FONTS["body"])
        self.e_recu.pack(fill="x")

        ctk.CTkButton(right, text="🗑 Vider le ticket", height=34,
                      fg_color="transparent", hover_color="#5D0000",
                      text_color=C["danger"], font=FONTS["badge"],
                      command=self._clear_lignes).pack(pady=(0, 10))

    # ------------------------------------------------- Tab Ouverts -------
    def _build_tab_open(self, parent):
        C = COLORS
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # Header
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", pady=(8, 4))
        ctk.CTkLabel(hdr, text="Tickets en attente de paiement",
                     font=FONTS["body"], text_color=C["text_muted"]).pack(side="left")
        ctk.CTkButton(hdr, text="🔄 Actualiser", width=120, height=32,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=FONTS["badge"],
                      command=self._load_tickets_ouverts).pack(side="right")

        # Tableau
        tbl = ctk.CTkFrame(parent, fg_color=C["bg_card"], corner_radius=10,
                            border_width=1, border_color=C["border"])
        tbl.grid(row=1, column=0, sticky="nsew", pady=(0, 8))

        hdrs   = ["N° Ticket", "Serveur", "Date", "Total", "Lignes", "Actions"]
        widths = [160, 160, 100, 120, 60, 280]
        hrow = ctk.CTkFrame(tbl, fg_color=C["bg_sidebar"], corner_radius=0)
        hrow.pack(fill="x", padx=1, pady=(1, 0))
        for h, w in zip(hdrs, widths):
            ctk.CTkLabel(hrow, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=6, pady=8)

        self.scroll_ouverts = ctk.CTkScrollableFrame(tbl, fg_color="transparent")
        self.scroll_ouverts.pack(fill="both", expand=True)

    # ============================================================ Data ===
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

    def _load_tickets_ouverts(self):
        for w in self.scroll_ouverts.winfo_children():
            w.destroy()
        C = COLORS

        rows = db.fetchall("""
            SELECT t.id, t.numero, CONCAT(u.prenom,' ',u.nom) AS serveur,
                   t.date_vente, t.total,
                   (SELECT COUNT(*) FROM ticket_lignes tl WHERE tl.ticket_id=t.id) AS nb_lignes
            FROM tickets t
            LEFT JOIN utilisateurs u ON u.id=t.serveur_id
            WHERE t.statut='en_attente'
            ORDER BY t.created_at DESC
        """)

        if not rows:
            ctk.CTkLabel(self.scroll_ouverts,
                         text="Aucun ticket ouvert pour le moment.",
                         font=FONTS["body"], text_color=C["text_muted"]).pack(pady=24)
            return

        for i, r in enumerate(rows):
            bg = C["bg_card"] if i % 2 == 0 else C["bg_dark"]
            rf = ctk.CTkFrame(self.scroll_ouverts, fg_color=bg, corner_radius=0)
            rf.pack(fill="x", pady=1)

            vals   = [r["numero"], r["serveur"] or "—",
                      str(r["date_vente"]), f"{float(r['total']):,.0f} FCFA",
                      str(r["nb_lignes"])]
            widths = [160, 160, 100, 120, 60]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(rf, text=str(v), font=FONTS["small"],
                             text_color=C["text"], width=w, anchor="w").pack(side="left", padx=6, pady=8)

            # Boutons actions
            tid = r["id"]
            btn_frame = ctk.CTkFrame(rf, fg_color="transparent")
            btn_frame.pack(side="left", padx=4)

            ctk.CTkButton(btn_frame, text="➕ Ajouter", width=90, height=28,
                          fg_color=C["accent2"], hover_color=C["accent"],
                          font=FONTS["small"],
                          command=lambda t=r: self._charger_ticket_pour_edition(t)
                          ).pack(side="left", padx=(0, 4))

            ctk.CTkButton(btn_frame, text="✅ Encaisser", width=100, height=28,
                          fg_color=C["success"], hover_color="#1E8449",
                          text_color=C["white"], font=FONTS["small"],
                          command=lambda t=r: self._encaisser_ticket(t)
                          ).pack(side="left", padx=(0, 4))

            ctk.CTkButton(btn_frame, text="🗑 Annuler", width=85, height=28,
                          fg_color="#5D0000", hover_color="#3D0000",
                          text_color=C["text"], font=FONTS["small"],
                          command=lambda t=r: self._annuler_ticket(t)
                          ).pack(side="left")

    # ============================================================ Actions =
    def _add_ligne(self):
        bname = self.boisson_var.get()
        if bname not in self._boissons:
            messagebox.showerror("Erreur", "Boisson invalide."); return
        try: qte = int(self.e_qte.get())
        except ValueError:
            messagebox.showerror("Erreur", "Quantité invalide."); return
        if qte <= 0:
            messagebox.showerror("Erreur", "Quantité doit être > 0."); return
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
            widths = [200, 55, 100, 110]
            for v, w in zip(vals, widths):
                ctk.CTkLabel(rf, text=v, font=FONTS["small"], text_color=C["text"],
                             width=w, anchor="w").pack(side="left", padx=6, pady=6)
            idx = i
            ctk.CTkButton(rf, text="✕", width=40, height=28,
                          fg_color="transparent", hover_color="#5D0000",
                          text_color=C["danger"], font=FONTS["small"],
                          command=lambda i=idx: self._del_ligne(i)).pack(side="left")
        self.lbl_total.configure(text=f"TOTAL : {total:,.0f} FCFA")

    def _del_ligne(self, idx):
        self._lignes.pop(idx); self._render_lignes()

    def _clear_lignes(self):
        self._lignes.clear(); self._render_lignes()

    def _reset_form(self):
        self._ticket_edit_id = None
        self._lignes.clear()
        self._render_lignes()
        self.e_notes.delete(0, "end")
        self.e_recu.delete(0, "end")
        self.lbl_edit_mode.configure(text="")

    # ---- Ouvrir ticket existant pour ajout de lignes ----
    def _charger_ticket_pour_edition(self, ticket_row):
        """Charge un ticket ouvert dans le formulaire pour ajouter des lignes."""
        self._ticket_edit_id = ticket_row["id"]
        self.lbl_edit_mode.configure(
            text=f"✏ Ajout sur ticket {ticket_row['numero']}",
            text_color=COLORS["gold"])
        # Charger les lignes existantes
        lignes_db = db.fetchall("""
            SELECT b.nom, b.id AS bid, tl.quantite, tl.prix_unit
            FROM ticket_lignes tl
            JOIN boissons b ON b.id=tl.boisson_id
            WHERE tl.ticket_id=%s
        """, (ticket_row["id"],))
        self._lignes = [
            {"boisson_id": l["bid"], "nom": l["nom"],
             "qte": l["quantite"], "prix": float(l["prix_unit"])}
            for l in lignes_db
        ]
        self._render_lignes()
        # Basculer sur l'onglet saisie
        self.tabs.set("🧾  Nouveau ticket")

    # ---- Soumettre (ouvrir ou encaisser) ----
    def _soumettre(self, cloturer: bool):
        if not self._lignes:
            messagebox.showwarning("Attention", "Ajoutez au moins une ligne."); return
        serv_name = self.serveur_var.get()
        if serv_name not in self._serveurs:
            messagebox.showerror("Erreur", "Sélectionnez un serveur."); return

        recu = 0.0
        if cloturer:
            try: recu = float(self.e_recu.get() or 0)
            except ValueError:
                messagebox.showerror("Erreur", "Montant reçu invalide."); return

        date_v   = self.e_date.get().strip() or str(date.today())
        serv_id  = self._serveurs[serv_name]
        caiss_id = self.user["id"]
        notes    = self.e_notes.get().strip()
        total    = sum(l["qte"] * l["prix"] for l in self._lignes)
        statut   = "valide" if cloturer else "en_attente"

        if self._ticket_edit_id:
            # Mise à jour d'un ticket existant
            db.execute(
                "UPDATE tickets SET total=%s, montant_recu=%s, statut=%s, notes=%s WHERE id=%s",
                (total, recu if cloturer else 0, statut, notes, self._ticket_edit_id), commit=True
            )
            # Supprimer les anciennes lignes et réinsérer
            db.execute("DELETE FROM ticket_lignes WHERE ticket_id=%s",
                       (self._ticket_edit_id,), commit=True)
            for l in self._lignes:
                db.execute(
                    "INSERT INTO ticket_lignes (ticket_id,boisson_id,quantite,prix_unit) VALUES (%s,%s,%s,%s)",
                    (self._ticket_edit_id, l["boisson_id"], l["qte"], l["prix"]), commit=True
                )
                if cloturer:
                    db.execute("UPDATE boissons SET stock=stock-%s WHERE id=%s",
                               (l["qte"], l["boisson_id"]), commit=True)
            tid    = self._ticket_edit_id
            numero = db.fetchone("SELECT numero FROM tickets WHERE id=%s", (tid,))["numero"]

        else:
            # Nouveau ticket
            numero = f"T{date.today().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
            db.execute(
                """INSERT INTO tickets
                   (numero,serveur_id,caissier_id,date_vente,total,montant_recu,statut,notes)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (numero, serv_id, caiss_id, date_v, total,
                 recu if cloturer else 0, statut, notes), commit=True
            )
            tid = db.lastrowid()
            for l in self._lignes:
                db.execute(
                    "INSERT INTO ticket_lignes (ticket_id,boisson_id,quantite,prix_unit) VALUES (%s,%s,%s,%s)",
                    (tid, l["boisson_id"], l["qte"], l["prix"]), commit=True
                )
                if cloturer:
                    db.execute("UPDATE boissons SET stock=stock-%s WHERE id=%s",
                               (l["qte"], l["boisson_id"]), commit=True)

        # Manquant seulement à la clôture
        if cloturer:
            manquant = total - recu
            if manquant > 0:
                db.execute(
                    "INSERT INTO manquants (serveur_id,ticket_id,montant,description,date_manquant) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    (serv_id, tid, manquant, f"Manquant ticket {numero}", date_v), commit=True
                )
            # Impression PDF
            caissier_row = db.fetchone(
                "SELECT CONCAT(prenom,' ',nom) AS nom FROM utilisateurs WHERE id=%s", (caiss_id,)
            )
            ticket_data = {
                "numero": numero, "date_vente": date_v,
                "total": total, "montant_recu": recu,
                "serveur_nom": serv_name,
                "caissier_nom": caissier_row["nom"] if caissier_row else "—",
                "notes": notes,
            }
            pdf_lignes = [{"nom": l["nom"], "quantite": l["qte"],
                           "prix_unit": l["prix"], "sous_total": l["qte"]*l["prix"]}
                          for l in self._lignes]
            pdf_path = os.path.join(TICKETS_DIR, f"{numero}.pdf")
            try:
                generer_ticket_pdf(ticket_data, pdf_lignes, pdf_path)
                ouvrir_pdf(pdf_path)
            except Exception as e:
                print(f"[PDF] Erreur : {e}")

            if manquant > 0:
                messagebox.showwarning("Manquant détecté",
                    f"Ticket {numero} encaissé.\n⚠ Manquant de {manquant:,.0f} FCFA.")
            else:
                messagebox.showinfo("Encaissé ✅",
                    f"Ticket {numero} encaissé !\nTotal : {total:,.0f} FCFA")
        else:
            messagebox.showinfo("Ticket ouvert 📂",
                f"Ticket {numero} ouvert.\nLe client pourra payer plus tard.")

        self._reset_form()
        self._load_tickets_ouverts()

    # ---- Encaisser depuis la liste des tickets ouverts ----
    def _encaisser_ticket(self, ticket_row):
        """Ouvre une fenêtre modale pour encaisser un ticket ouvert."""
        C = COLORS
        win = ctk.CTkToplevel(self)
        win.title(f"Encaisser — {ticket_row['numero']}")
        win.geometry("450x350")
        win.configure(fg_color=C["bg_dark"])

        # Center the window BEFORE setting grab
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 420) // 2
        y = (win.winfo_screenheight() - 320) // 2
        win.geometry(f"450x350+{x}+{y}")

        # Wait for the window to be fully mapped/visible
        win.wait_visibility()

        # Now set the grab
        win.grab_set()
        win.focus()

        total = float(ticket_row["total"])
        ctk.CTkLabel(win, text=f"Ticket  {ticket_row['numero']}",
                     font=FONTS["heading"], text_color=C["gold"]).pack(pady=(20, 4))
        ctk.CTkLabel(win, text=f"Serveur : {ticket_row['serveur'] or '—'}",
                     font=FONTS["body"], text_color=C["text_muted"]).pack()
        ctk.CTkLabel(win, text=f"TOTAL À PAYER : {total:,.0f} FCFA",
                     font=("Georgia", 16, "bold"), text_color=C["gold"]).pack(pady=12)

        ctk.CTkLabel(win, text="Montant reçu (FCFA) :",
                     font=FONTS["body"], text_color=C["text_muted"]).pack()
        e_recu = ctk.CTkEntry(win, height=42, width=260,
                               fg_color=C["bg_card"], border_color=C["border"],
                               text_color=C["text"], font=("Georgia", 16))
        e_recu.insert(0, str(int(total)))
        e_recu.pack(pady=8)
        e_recu.focus()
        e_recu.select_range(0, "end")

        lbl_err = ctk.CTkLabel(win, text="", font=FONTS["small"], text_color=C["danger"])
        lbl_err.pack()

        def confirmer():
            try: recu = float(e_recu.get())
            except ValueError:
                lbl_err.configure(text="Montant invalide."); return

            date_v   = str(ticket_row["date_vente"])
            serv_row = db.fetchone("SELECT serveur_id FROM tickets WHERE id=%s",
                                   (ticket_row["id"],))
            serv_id  = serv_row["serveur_id"] if serv_row else None

            # Mettre à jour le ticket
            db.execute(
                "UPDATE tickets SET montant_recu=%s, statut='valide' WHERE id=%s",
                (recu, ticket_row["id"]), commit=True
            )

            # Déduire le stock
            lignes_db = db.fetchall(
                "SELECT boisson_id, quantite FROM ticket_lignes WHERE ticket_id=%s",
                (ticket_row["id"],)
            )
            for l in lignes_db:
                db.execute("UPDATE boissons SET stock=stock-%s WHERE id=%s",
                           (l["quantite"], l["boisson_id"]), commit=True)

            # Manquant éventuel
            manquant = total - recu
            if manquant > 0 and serv_id:
                db.execute(
                    "INSERT INTO manquants (serveur_id,ticket_id,montant,description,date_manquant) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    (serv_id, ticket_row["id"], manquant,
                     f"Manquant ticket {ticket_row['numero']}", date_v), commit=True
                )

            # Impression PDF
            lignes_pdf = db.fetchall("""
                SELECT b.nom, tl.quantite, tl.prix_unit, tl.sous_total
                FROM ticket_lignes tl JOIN boissons b ON b.id=tl.boisson_id
                WHERE tl.ticket_id=%s
            """, (ticket_row["id"],))
            caissier_row = db.fetchone(
                "SELECT CONCAT(prenom,' ',nom) AS nom FROM utilisateurs WHERE id=%s",
                (self.user["id"],)
            )
            ticket_data = {
                "numero": ticket_row["numero"], "date_vente": date_v,
                "total": total, "montant_recu": recu,
                "serveur_nom": ticket_row["serveur"] or "—",
                "caissier_nom": caissier_row["nom"] if caissier_row else "—",
                "notes": "",
            }
            pdf_lignes = [{"nom": l["nom"], "quantite": l["quantite"],
                           "prix_unit": float(l["prix_unit"]),
                           "sous_total": float(l["sous_total"])}
                          for l in lignes_pdf]
            pdf_path = os.path.join(TICKETS_DIR, f"{ticket_row['numero']}.pdf")
            try:
                generer_ticket_pdf(ticket_data, pdf_lignes, pdf_path)
                ouvrir_pdf(pdf_path)
            except Exception as e:
                print(f"[PDF] Erreur : {e}")

            win.destroy()
            self._load_tickets_ouverts()

            monnaie = recu - total
            if manquant > 0:
                messagebox.showwarning("Encaissé avec manquant",
                    f"✅ Ticket {ticket_row['numero']} clôturé.\n"
                    f"⚠ Manquant de {manquant:,.0f} FCFA enregistré.")
            elif monnaie > 0:
                messagebox.showinfo("Encaissé ✅",
                    f"Ticket {ticket_row['numero']} clôturé !\n"
                    f"Monnaie à rendre : {monnaie:,.0f} FCFA")
            else:
                messagebox.showinfo("Encaissé ✅",
                    f"Ticket {ticket_row['numero']} clôturé !")

        e_recu.bind("<Return>", lambda e: confirmer())
        ctk.CTkButton(win, text="✅ Confirmer l'encaissement", height=44,
                      fg_color=C["success"], hover_color="#1E8449",
                      text_color=C["white"], font=("Helvetica", 13, "bold"),
                      command=confirmer).pack(fill="x", padx=30, pady=(8, 6))
        ctk.CTkButton(win, text="Annuler", height=34,
                      fg_color="transparent", hover_color=C["bg_sidebar"],
                      text_color=C["text_muted"], font=FONTS["small"],
                      command=win.destroy).pack(fill="x", padx=30)

    # ---- Annuler un ticket ouvert ----
    def _annuler_ticket(self, ticket_row):
        if not messagebox.askyesno("Confirmer",
            f"Annuler le ticket {ticket_row['numero']} ?\nCette action est irréversible."):
            return
        db.execute("UPDATE tickets SET statut='annule' WHERE id=%s",
                   (ticket_row["id"],), commit=True)
        self._load_tickets_ouverts()
        messagebox.showinfo("Annulé", f"Ticket {ticket_row['numero']} annulé.")


    def _encaisser_ticket_depuis_dashboard(self, parent_widget, ticket_row, on_done=None):
        """Méthode appelable depuis le dashboard pour encaisser un ticket."""
        self._encaisser_ticket_impl(parent_widget, ticket_row, on_done)

    def _encaisser_ticket_impl(self, parent_widget, ticket_row, on_done=None):
        """Popup d'encaissement réutilisable."""
        C = COLORS
        win = ctk.CTkToplevel(parent_widget)
        win.title(f"Encaisser — {ticket_row['numero']}")
        win.geometry("420x320")
        win.configure(fg_color=C["bg_dark"])
        win.grab_set(); win.focus()
        win.update_idletasks()
        x = (win.winfo_screenwidth()  - 420) // 2
        y = (win.winfo_screenheight() - 320) // 2
        win.geometry(f"420x320+{x}+{y}")

        total = float(ticket_row["total"])
        ctk.CTkLabel(win, text=f"Ticket  {ticket_row['numero']}",
                     font=FONTS["heading"], text_color=C["gold"]).pack(pady=(20, 4))
        ctk.CTkLabel(win, text=f"TOTAL : {total:,.0f} FCFA",
                     font=("Georgia", 16, "bold"), text_color=C["gold"]).pack(pady=8)
        ctk.CTkLabel(win, text="Montant reçu (FCFA) :",
                     font=FONTS["body"], text_color=C["text_muted"]).pack()
        e_recu = ctk.CTkEntry(win, height=42, width=260,
                               fg_color=C["bg_card"], border_color=C["border"],
                               text_color=C["text"], font=("Georgia", 16))
        e_recu.insert(0, str(int(total)))
        e_recu.pack(pady=8); e_recu.focus(); e_recu.select_range(0, "end")
        lbl_err = ctk.CTkLabel(win, text="", font=FONTS["small"], text_color=C["danger"])
        lbl_err.pack()

        def confirmer():
            try: recu = float(e_recu.get())
            except ValueError:
                lbl_err.configure(text="Montant invalide."); return
            date_v  = str(ticket_row["date_vente"])
            serv_row= db.fetchone("SELECT serveur_id FROM tickets WHERE id=%s",(ticket_row["id"],))
            serv_id = serv_row["serveur_id"] if serv_row else None
            db.execute("UPDATE tickets SET montant_recu=%s,statut='valide' WHERE id=%s",
                       (recu, ticket_row["id"]), commit=True)
            lignes_db = db.fetchall("SELECT boisson_id,quantite FROM ticket_lignes WHERE ticket_id=%s",
                                    (ticket_row["id"],))
            for l in lignes_db:
                db.execute("UPDATE boissons SET stock=stock-%s WHERE id=%s",
                           (l["quantite"],l["boisson_id"]), commit=True)
            manquant = total - recu
            if manquant > 0 and serv_id:
                db.execute(
                    "INSERT INTO manquants (serveur_id,ticket_id,montant,description,date_manquant) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    (serv_id,ticket_row["id"],manquant,
                     f"Manquant ticket {ticket_row['numero']}",date_v), commit=True)
            win.destroy()
            if on_done: on_done()
            monnaie = recu - total
            if manquant > 0:
                messagebox.showwarning("Encaissé avec manquant",
                    f"✅ Ticket clôturé.\n⚠ Manquant de {manquant:,.0f} FCFA.")
            elif monnaie > 0:
                messagebox.showinfo("Encaissé ✅",
                    f"Monnaie à rendre : {monnaie:,.0f} FCFA")
            else:
                messagebox.showinfo("Encaissé ✅","Ticket clôturé avec succès !")

        e_recu.bind("<Return>", lambda e: confirmer())
        ctk.CTkButton(win, text="✅ Confirmer", height=44,
                      fg_color=C["success"], hover_color="#1E8449",
                      text_color=C["white"], font=("Helvetica",13,"bold"),
                      command=confirmer).pack(fill="x", padx=30, pady=(8,6))
        ctk.CTkButton(win, text="Annuler", height=34,
                      fg_color="transparent", hover_color=C["bg_sidebar"],
                      text_color=C["text_muted"], font=FONTS["small"],
                      command=win.destroy).pack(fill="x", padx=30)

