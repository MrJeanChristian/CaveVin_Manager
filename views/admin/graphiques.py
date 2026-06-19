# ============================================================
# views/admin/graphiques.py — Graphiques de ventes (matplotlib)
# ============================================================

import customtkinter as ctk
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import COLORS, FONTS
from database.db import db

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


# Palette matplotlib cohérente avec l'appli
MPL_BG      = "#1A0A0A"
MPL_CARD    = "#2A1010"
MPL_ROUGE   = "#C0392B"
MPL_OR      = "#D4AC0D"
MPL_VERT    = "#27AE60"
MPL_GRIS    = "#9E8B7A"
MPL_TEXT    = "#F5E6D3"


class GraphiquesView(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_dark"], **kwargs)
        self._build()
        self._load_all()

    def _build(self):
        C = COLORS
        # ---- Header ----
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 0))
        ctk.CTkLabel(hdr, text="  Graphiques & Statistiques",
                     font=FONTS["heading"], text_color=C["gold"]).pack(side="left")

        ctrl = ctk.CTkFrame(hdr, fg_color="transparent")
        ctrl.pack(side="right")
        ctk.CTkLabel(ctrl, text="Année :", font=FONTS["small"],
                     text_color=C["text_muted"]).pack(side="left")
        self.annee_var = ctk.StringVar(value=str(date.today().year))
        annees = [str(y) for y in range(date.today().year, date.today().year - 4, -1)]
        ctk.CTkComboBox(ctrl, variable=self.annee_var, values=annees,
                         width=90, height=32,
                         fg_color=C["bg_card"], border_color=C["border"],
                         button_color=C["accent"], text_color=C["text"],
                         font=FONTS["body"],
                         command=lambda v: self._load_all()).pack(side="left", padx=8)
        ctk.CTkButton(ctrl, text=" Actualiser", width=110, height=32,
                      fg_color=C["accent"], hover_color=C["accent2"],
                      font=FONTS["badge"], command=self._load_all).pack(side="left")

        # ---- Zone scrollable pour les graphiques ----
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=24, pady=12)

    # ---------------------------------------------------------------- Load --
    def _load_all(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        annee = self.annee_var.get()
        self._chart_ventes_mensuelles(annee)
        self._chart_benefice_mensuel(annee)
        self._chart_top_boissons(annee)
        self._chart_manquants_par_serveur(annee)

    # ---- Graphique 1 : Ventes mensuelles (barres) ----
    def _chart_ventes_mensuelles(self, annee):
        rows = db.fetchall("""
            SELECT MONTH(date_vente) AS mois, SUM(total) AS total
            FROM tickets
            WHERE YEAR(date_vente)=%s AND statut='valide'
            GROUP BY MONTH(date_vente)
            ORDER BY mois
        """, (annee,))

        mois_labels = ["Jan","Fév","Mar","Avr","Mai","Jun",
                       "Jul","Aoû","Sep","Oct","Nov","Déc"]
        valeurs = [0.0] * 12
        for r in rows:
            valeurs[r["mois"] - 1] = float(r["total"])

        fig = Figure(figsize=(9, 3.2), facecolor=MPL_CARD)
        ax  = fig.add_subplot(111, facecolor=MPL_BG)
        bars = ax.bar(mois_labels, valeurs, color=MPL_ROUGE, width=0.6,
                      edgecolor=MPL_OR, linewidth=0.6)

        # Valeur au-dessus de chaque barre
        for bar, val in zip(bars, valeurs):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(valeurs)*0.01,
                        f"{val/1000:.0f}k", ha="center", va="bottom",
                        color=MPL_OR, fontsize=7)

        ax.set_title(f"Ventes mensuelles {annee} (FCFA)", color=MPL_TEXT, fontsize=11, pad=10)
        ax.set_ylabel("FCFA", color=MPL_GRIS, fontsize=9)
        ax.tick_params(colors=MPL_TEXT, labelsize=8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x/1000:.0f}k"))
        for spine in ax.spines.values():
            spine.set_edgecolor(MPL_CARD)
        ax.grid(axis="y", color="#3D1515", linewidth=0.5, linestyle="--")
        fig.tight_layout(pad=1.5)

        self._embed_fig(fig, f"Ventes mensuelles {annee}")

    # ---- Graphique 2 : Bénéfice mensuel (ligne) ----
    def _chart_benefice_mensuel(self, annee):
        rows = db.fetchall("""
            SELECT MONTH(t.date_vente) AS mois,
                   SUM(t.total) AS ca,
                   SUM(tl.quantite * b.prix_achat) AS cout
            FROM tickets t
            JOIN ticket_lignes tl ON tl.ticket_id = t.id
            JOIN boissons b ON b.id = tl.boisson_id
            WHERE YEAR(t.date_vente)=%s AND t.statut='valide'
            GROUP BY MONTH(t.date_vente)
            ORDER BY mois
        """, (annee,))

        mois_labels = ["Jan","Fév","Mar","Avr","Mai","Jun",
                       "Jul","Aoû","Sep","Oct","Nov","Déc"]
        ca_vals  = [0.0] * 12
        ben_vals = [0.0] * 12
        for r in rows:
            m = r["mois"] - 1
            ca  = float(r["ca"] or 0)
            cout= float(r["cout"] or 0)
            ca_vals[m]  = ca
            ben_vals[m] = ca - cout

        fig = Figure(figsize=(9, 3.2), facecolor=MPL_CARD)
        ax  = fig.add_subplot(111, facecolor=MPL_BG)
        x   = range(12)
        ax.plot(mois_labels, ca_vals,  color=MPL_OR,    marker="o", linewidth=2,
                markersize=5, label="Chiffre d'affaires")
        ax.plot(mois_labels, ben_vals, color=MPL_VERT,  marker="s", linewidth=2,
                markersize=5, linestyle="--", label="Bénéfice net")
        ax.fill_between(mois_labels, ben_vals, alpha=0.12, color=MPL_VERT)

        ax.set_title(f"CA vs Bénéfice {annee}", color=MPL_TEXT, fontsize=11, pad=10)
        ax.set_ylabel("FCFA", color=MPL_GRIS, fontsize=9)
        ax.tick_params(colors=MPL_TEXT, labelsize=8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x/1000:.0f}k"))
        ax.legend(facecolor=MPL_CARD, edgecolor=MPL_ROUGE,
                  labelcolor=MPL_TEXT, fontsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor(MPL_CARD)
        ax.grid(color="#3D1515", linewidth=0.5, linestyle="--")
        fig.tight_layout(pad=1.5)

        self._embed_fig(fig, f"CA vs Bénéfice {annee}")

    # ---- Graphique 3 : Top 8 boissons (barres horizontales) ----
    def _chart_top_boissons(self, annee):
        rows = db.fetchall("""
            SELECT b.nom, SUM(tl.quantite) AS qte, SUM(tl.sous_total) AS ca
            FROM ticket_lignes tl
            JOIN boissons b ON b.id = tl.boisson_id
            JOIN tickets t  ON t.id = tl.ticket_id
            WHERE YEAR(t.date_vente)=%s AND t.statut='valide'
            GROUP BY b.id, b.nom
            ORDER BY qte DESC
            LIMIT 8
        """, (annee,))

        if not rows:
            return

        noms = [r["nom"][:22] for r in rows][::-1]
        qtes = [int(r["qte"]) for r in rows][::-1]

        fig = Figure(figsize=(9, 3.2), facecolor=MPL_CARD)
        ax  = fig.add_subplot(111, facecolor=MPL_BG)
        bars = ax.barh(noms, qtes, color=MPL_ROUGE, edgecolor=MPL_OR, linewidth=0.5)
        for bar, val in zip(bars, qtes):
            ax.text(bar.get_width() + max(qtes)*0.01, bar.get_y() + bar.get_height()/2,
                    str(val), va="center", color=MPL_OR, fontsize=8)

        ax.set_title(f"Top boissons par quantité vendue {annee}",
                     color=MPL_TEXT, fontsize=11, pad=10)
        ax.set_xlabel("Quantité", color=MPL_GRIS, fontsize=9)
        ax.tick_params(colors=MPL_TEXT, labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor(MPL_CARD)
        ax.grid(axis="x", color="#3D1515", linewidth=0.5, linestyle="--")
        fig.tight_layout(pad=1.5)

        self._embed_fig(fig, f"Top boissons {annee}")

    # ---- Graphique 4 : Manquants par serveur (camembert) ----
    def _chart_manquants_par_serveur(self, annee):
        rows = db.fetchall("""
            SELECT CONCAT(u.prenom,' ',u.nom) AS nom, SUM(m.montant) AS total
            FROM manquants m
            JOIN utilisateurs u ON u.id = m.serveur_id
            WHERE YEAR(m.date_manquant)=%s
            GROUP BY m.serveur_id
            ORDER BY total DESC
        """, (annee,))

        if not rows:
            return

        noms   = [r["nom"] for r in rows]
        totaux = [float(r["total"]) for r in rows]
        colors_pie = [MPL_ROUGE, MPL_OR, "#922B21", "#D4AC0D",
                      "#7B241C", "#A9770B", "#5B1010", "#8B6508"]

        fig = Figure(figsize=(9, 3.4), facecolor=MPL_CARD)
        ax  = fig.add_subplot(111, facecolor=MPL_CARD)
        wedges, texts, autotexts = ax.pie(
            totaux, labels=noms,
            colors=colors_pie[:len(noms)],
            autopct=lambda p: f"{p:.1f}%\n({p*sum(totaux)/100:,.0f}F)",
            startangle=90,
            textprops={"color": MPL_TEXT, "fontsize": 8},
            wedgeprops={"edgecolor": MPL_BG, "linewidth": 1.5},
        )
        for at in autotexts:
            at.set_color(MPL_BG)
            at.set_fontsize(7)

        ax.set_title(f"Manquants par serveur {annee}",
                     color=MPL_TEXT, fontsize=11, pad=10)
        fig.tight_layout(pad=1.5)

        self._embed_fig(fig, f"Manquants {annee}")

    # ---- Embed matplotlib dans CustomTkinter ----
    def _embed_fig(self, fig, titre: str):
        C = COLORS
        container = ctk.CTkFrame(self.scroll, fg_color=C["bg_card"],
                                  corner_radius=10, border_width=1,
                                  border_color=C["border"])
        container.pack(fill="x", pady=(0, 16))

        canvas = FigureCanvasTkAgg(fig, master=container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=8, pady=8)
        plt.close(fig)
