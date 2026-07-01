# ============================================================
# views/caissier/dashboard.py — Accueil caissier
# ============================================================

import customtkinter as ctk
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import COLORS, FONTS
from database.db import db
from tkinter import messagebox, filedialog
import sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.pdf_ticket import generer_ticket_pdf, ouvrir_pdf

TICKETS_DIR = os.path.join(os.path.expanduser("~"), "CaveVin_Tickets")
os.makedirs(TICKETS_DIR, exist_ok=True)


class CaissierDashboard(ctk.CTkFrame):
    def __init__(self, parent, user, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self.user = user
        self._build()
        self._auto_refresh()

    def _build(self):
        C = COLORS
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 6))
        ctk.CTkLabel(hdr, text=f"👋  Bienvenue {self.user['prenom']} — Caissier",
                     font=FONTS["heading"], text_color=C["gold"]).pack(side="left")
        ctk.CTkButton(hdr, text="🔄 Actualiser", width=110, height=32,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=FONTS["badge"], command=self._refresh).pack(side="right")

        ctk.CTkLabel(self, text=f"📅 {date.today().strftime('%A %d %B %Y').capitalize()}",
                     font=FONTS["body"], text_color=C["text_muted"]).pack(anchor="w", padx=24)

        # KPIs
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.pack(fill="x", padx=24, pady=(12, 0))

        # Tickets ouverts
        ctk.CTkLabel(self, text="📂  Tickets ouverts (en attente de paiement)",
                     font=FONTS["body"], text_color=C["gold"]).pack(
                     anchor="w", padx=24, pady=(18, 6))

        tbl_open = ctk.CTkFrame(self, fg_color=C["bg_card"], corner_radius=10,
                                 border_width=1, border_color=C["border"])
        tbl_open.pack(fill="x", padx=24, pady=(0, 12))

        # Largeurs réduites pour que les 2 boutons soient visibles
        hdrs   = ["N° Ticket", "Serveur", "Date", "Total", "Lignes", "Encaisser", "Imprimer"]
        widths = [130, 130, 90,  110,  50,  110,  100]
        # Total ≈ 720px — raisonnable sur tous les écrans

        hrow = ctk.CTkFrame(tbl_open, fg_color=C["bg_sidebar"], corner_radius=0)
        hrow.pack(fill="x", padx=1, pady=(1, 0))
        for h, w in zip(hdrs, widths):
            ctk.CTkLabel(hrow, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=6, pady=8)

        self.scroll_open = ctk.CTkScrollableFrame(tbl_open, fg_color="transparent", height=160)
        self.scroll_open.pack(fill="x")

        # Manquants actifs
        ctk.CTkLabel(self, text="⚠  Manquants non soldés",
                     font=FONTS["body"], text_color=C["danger"]).pack(
                     anchor="w", padx=24, pady=(8, 6))

        tbl_mq = ctk.CTkFrame(self, fg_color=C["bg_card"], corner_radius=10,
                               border_width=1, border_color=C["border"])
        tbl_mq.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        hdrs2   = ["Serveur", "Montant", "Date", "Ticket"]
        widths2 = [200, 120, 120, 160]
        hrow2 = ctk.CTkFrame(tbl_mq, fg_color=C["bg_sidebar"], corner_radius=0)
        hrow2.pack(fill="x", padx=1, pady=(1, 0))
        for h, w in zip(hdrs2, widths2):
            ctk.CTkLabel(hrow2, text=h, font=FONTS["badge"],
                         text_color=C["gold"], width=w, anchor="w").pack(side="left", padx=8, pady=8)

        self.scroll_mq = ctk.CTkScrollableFrame(tbl_mq, fg_color="transparent")
        self.scroll_mq.pack(fill="both", expand=True)

        self._refresh()

    def _refresh(self):
        self._load_kpis()
        self._load_tickets_ouverts()
        self._load_manquants()

    def _load_kpis(self):
        C = COLORS
        for w in self.kpi_frame.winfo_children():
            w.destroy()
        today = date.today()
        mois  = today.strftime("%Y-%m")

        j  = db.fetchone("SELECT COALESCE(SUM(total),0) AS v FROM tickets WHERE date_vente=%s AND statut='valide'",(today,)) or {"v":0}
        m  = db.fetchone("SELECT COALESCE(SUM(total),0) AS v FROM tickets WHERE DATE_FORMAT(date_vente,'%%Y-%%m')=%s AND statut='valide'",(mois,)) or {"v":0}
        mq = db.fetchone("SELECT COALESCE(SUM(montant),0) AS v FROM manquants WHERE rembourse=0") or {"v":0}
        nt = db.fetchone("SELECT COUNT(*) AS v FROM tickets WHERE date_vente=%s AND statut='valide'",(today,)) or {"v":0}
        no = db.fetchone("SELECT COUNT(*) AS v FROM tickets WHERE statut='en_attente'") or {"v":0}

        kpis = [
            ("Ventes aujourd'hui",  f"{float(j['v']):,.0f} F",  "💰", C["gold"]),
            ("Ventes ce mois",      f"{float(m['v']):,.0f} F",  "📅", C["success"]),
            ("Tickets du jour",     str(nt["v"]),                "🧾", C["text"]),
            ("Tickets ouverts",     str(no["v"]),                "📂", C["gold"]),
            ("Manquants actifs",    f"{float(mq['v']):,.0f} F", "⚠️", C["danger"]),
        ]
        for title, val, icon, color in kpis:
            card = ctk.CTkFrame(self.kpi_frame, fg_color=C["bg_card"], corner_radius=10,
                                 border_width=1, border_color=C["border"], width=176, height=88)
            card.pack(side="left", padx=(0,10))
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=icon, font=("Helvetica",22)).pack(pady=(12,0))
            ctk.CTkLabel(card, text=val, font=("Georgia",13,"bold"), text_color=color).pack()
            ctk.CTkLabel(card, text=title, font=FONTS["small"],
                         text_color=C["text_muted"], wraplength=165).pack()

    def _load_tickets_ouverts(self):
        for w in self.scroll_open.winfo_children():
            w.destroy()
        C = COLORS
        rows = db.fetchall("""
            SELECT t.id, t.numero, CONCAT(u.prenom,' ',u.nom) AS serveur,
                   t.date_vente, t.total,
                   (SELECT COUNT(*) FROM ticket_lignes tl WHERE tl.ticket_id=t.id) AS nb_lignes
            FROM tickets t
            LEFT JOIN utilisateurs u ON u.id=t.serveur_id
            WHERE t.statut='en_attente'
            ORDER BY t.created_at DESC LIMIT 20
        """)

        if not rows:
            ctk.CTkLabel(self.scroll_open, text="Aucun ticket ouvert.",
                         font=FONTS["small"], text_color=C["text_muted"]).pack(pady=10)
            return

        for i, r in enumerate(rows):
            bg = C["bg_card"] if i % 2 == 0 else C["bg_dark"]

            # Frame principal avec largeur fixe pour éviter le débordement
            rf = ctk.CTkFrame(self.scroll_open, fg_color=bg, corner_radius=0, width=800)
            rf.pack(fill="x", pady=1)
            rf.pack_propagate(False)  # Empêche le frame de se rétrécir

            # Configuration des colonnes avec grid pour un meilleur contrôle
            # Colonnes: Numéro, Serveur, Date, Total, Lignes, Actions
            rf.columnconfigure(0, weight=0, minsize=120)  # Numéro
            rf.columnconfigure(1, weight=0, minsize=140)  # Serveur
            rf.columnconfigure(2, weight=0, minsize=100)  # Date
            rf.columnconfigure(3, weight=0, minsize=120)  # Total
            rf.columnconfigure(4, weight=0, minsize=60)  # Lignes
            rf.columnconfigure(5, weight=1)  # Actions (prend le reste)

            # Données
            vals = [
                r["numero"],
                r["serveur"] or "—",
                str(r["date_vente"]),
                f"{float(r['total']):,.0f} FCFA",
                str(r["nb_lignes"])
            ]

            for col, (v) in enumerate(vals):
                ctk.CTkLabel(rf, text=str(v), font=FONTS["small"],
                             text_color=C["text"], anchor="w").grid(
                    row=0, column=col, padx=6, pady=7, sticky="w")

            # Frame pour les boutons dans la colonne Actions
            btn_frame = ctk.CTkFrame(rf, fg_color="transparent")
            btn_frame.grid(row=0, column=5, padx=6, pady=4, sticky="e")

            # Bouton Encaisser
            ctk.CTkButton(btn_frame, text="✅ Encaissé", width=90, height=28,
                          fg_color=C["success"], hover_color="#1E8449",
                          text_color=C["white"], font=FONTS["small"],
                          command=lambda row=r: self._encaisser_ticket(row)
                          ).pack(side="left", padx=2)

            # Bouton Imprimer
            ctk.CTkButton(btn_frame, text="🖨️ Imprimer", width=90, height=28,
                          fg_color=C["accent"], hover_color=C["accent2"],
                          text_color=C["white"], font=FONTS["small"],
                          command=lambda row=r: self._imprimer_ticket(row)
                          ).pack(side="left", padx=2)

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

    def _encaisser_rapide(self, ticket_row):
        """Encaissement rapide depuis le dashboard — ouvre la popup."""
        from views.caissier.tickets import TicketsView
        tmp = TicketsView.__new__(TicketsView)
        tmp.user = self.user
        tmp._encaisser_ticket_depuis_dashboard(self, ticket_row, self._refresh)

    def _imprimer_ticket(self, ticket_row):
        """
        Impression directe du ticket ouvert sur l'imprimante thermique.
        - Ne change PAS le statut du ticket (reste 'en_attente')
        - Ne crée PAS de manquant
        - Appelle imprimer_ticket() depuis utils/thermal_printer.py
        """
        try:
            from utils.thermal_printer import imprimer_ticket

            # Récupérer les lignes du ticket depuis la BdD
            lignes = db.fetchall("""
                SELECT tl.quantite,
                       tl.prix_unitaire AS prix_unit,
                       tl.sous_total,
                       b.nom            AS nom
                FROM ticket_lignes tl
                JOIN boissons b ON b.id = tl.boisson_id
                WHERE tl.ticket_id = %s
            """, (ticket_row["id"],))

            # montant_recu = 0 → ticket pas encore encaissé
            # → pas de monnaie rendue ni manquant affiché sur le ticket
            ticket_data = {
                "numero":       ticket_row["numero"],
                "date_vente":   str(ticket_row["date_vente"]),
                "serveur_nom":  ticket_row["serveur"] or "—",
                "caissier_nom": f"{self.user.get('prenom', '')} {self.user.get('nom', '')}".strip(),
                "total":        float(ticket_row["total"]),
                "montant_recu": 0,
                "notes":        "",
            }

            imprimer_ticket(ticket_data, lignes)

        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("Erreur impression", f"Impossible d'imprimer le ticket :\n{e}")

    def _load_manquants(self):
        for w in self.scroll_mq.winfo_children():
            w.destroy()
        C = COLORS
        rows = db.fetchall("""
            SELECT CONCAT(u.prenom,' ',u.nom) AS serveur, m.montant,
                   m.date_manquant, t.numero
            FROM manquants m
            JOIN utilisateurs u ON m.serveur_id=u.id
            LEFT JOIN tickets t ON m.ticket_id=t.id
            WHERE m.rembourse=0
            ORDER BY m.date_manquant DESC LIMIT 30
        """)
        for i, r in enumerate(rows):
            bg = C["bg_card"] if i%2==0 else C["bg_dark"]
            rf = ctk.CTkFrame(self.scroll_mq, fg_color=bg, corner_radius=0)
            rf.pack(fill="x")
            for v, w in zip([r["serveur"], f"{float(r['montant']):,.0f} FCFA",
                              str(r["date_manquant"]), r["numero"] or "—"],
                             [200, 120, 120, 160]):
                ctk.CTkLabel(rf, text=str(v), font=FONTS["small"],
                             text_color=C["text"], width=w, anchor="w").pack(
                             side="left", padx=8, pady=7)

    def _auto_refresh(self):
        """Actualisation automatique toutes les 30 secondes."""
        self._refresh()
        self._refresh_job = self.after(30000, self._auto_refresh)

    def destroy(self):
        if hasattr(self, '_refresh_job'):
            self.after_cancel(self._refresh_job)
        super().destroy()