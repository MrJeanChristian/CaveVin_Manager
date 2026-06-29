# 🍷 CaveVin Manager — v2.0

Logiciel de gestion complète de cave à vin — CustomTkinter + MySQL

---

## 📦 Installation

```bash
# 1. Extraire le projet
unzip cave_vin_manager.zip -d ~/Applications/
cd ~/Applications/cave_vin

# 2. Créer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 3. Installer toutes les dépendances
pip install -r requirements.txt

# 4. Configurer la base de données
#    → Ouvrir config.py et renseigner vos identifiants MySQL :
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "votre_user",
    "password": "votre_mot_de_passe",
    "database": "cave_vin",
}

# 5. Lancer l'application (crée la BDD automatiquement)
python main.py
```

---

## 🔐 Compte par défaut

| Username | Mot de passe | Rôle           |
|----------|-------------|----------------|
| `admin`  | `admin123`  | Administrateur |

> ⚠️ Changez ce mot de passe dès la première connexion via **Mon profil**.

---

## 📦 Dépendances

```bash
pip install customtkinter        # Interface graphique
pip install mysql-connector-python  # Base de données MySQL
pip install Pillow               # Photos des boissons + aperçu
pip install reportlab            # Génération tickets PDF
pip install qrcode[pil]          # QR code sur les tickets PDF
pip install matplotlib           # Graphiques dashboard admin
pip install openpyxl             # Export rapports Excel
pip install python-escpos        # Impression thermique directe
pip install schedule             # Sauvegarde automatique planifiée (optionnel)
```

Ou en une seule commande :
```bash
pip install -r requirements.txt
```

---

## 🗂 Structure du projet

```
cave_vin/
├── main.py                        # Point d'entrée
├── config.py                      # Palette, DB config, constantes
├── requirements.txt
├── README.md
├── database/
│   ├── db.py                     # Singleton MySQL
│   └── models.py                 # Tables + initialisation BDD
├── auth/
│   └── login.py                  # Fenêtre de connexion (SHA-256)
├── components/
│   └── sidebar.py                # Sidebar réutilisable
├── utils/
│   ├── pdf_ticket.py             # Génération ticket PDF (reportlab)
│   ├── thermal_printer.py        # Impression thermique ESC/POS
│   ├── export_excel.py           # Export Excel journalier/mensuel/annuel
│   ├── backup.py                 # Sauvegarde/restauration MySQL
│   └── mailer.py                 # Envoi rapport journalier par Gmail
└── views/
    ├── profil.py                 # Changement mot de passe (tous rôles)
    ├── admin/
    │   ├── dashboard.py          # KPIs globaux + derniers tickets
    │   ├── boissons.py           # CRUD boissons + photos + catégories
    │   ├── employes.py           # CRUD employés (caissiers, serveurs)
    │   ├── graphiques.py         # Graphiques matplotlib (4 courbes/camemberts)
    │   ├── outils.py             # Export Excel + Sauvegarde MySQL
    │   ├── imprimante.py         # Configuration imprimante thermique
    │   └── config_mail.py        # Configuration Gmail SMTP
    ├── caissier/
    │   ├── dashboard.py          # Accueil caissier + KPIs du jour
    │   ├── tickets.py            # Saisie tickets + impression PDF/thermique
    │   ├── historique.py         # Historique + réimpression PDF
    │   └── rapports.py           # Bénéfices + manquants + déductions
    └── serveur/
        └── dashboard.py          # Espace personnel serveur
```

---

## 👥 Rôles & Fonctionnalités

### 🔴 Administrateur
| Fonctionnalité | Description |
|---|---|
| Tableau de bord | KPIs globaux, derniers tickets en temps réel |
| Boissons & Prix | CRUD complet, photo par boisson, catégories prédéfinies |
| Employés | Création/modification/désactivation, gestion des salaires |
| Graphiques | Ventes mensuelles, CA vs Bénéfice, Top boissons, Manquants par serveur |
| Export & Backup | Rapport Excel journalier/mensuel/annuel + Dump MySQL (gzip) |
| Imprimante | Configuration USB/Réseau/Série + ticket de test |
| Config Mail | Gmail SMTP pour rapport journalier automatique |
| Mon profil | Changement de mot de passe avec indicateur de force |

### 🟡 Caissier
| Fonctionnalité | Description |
|---|---|
| Accueil | KPIs du jour : ventes, tickets, manquants actifs |
| Saisir un ticket | Ajout lignes, calcul auto, détection manquant, impression PDF/thermique |
| Historique | Recherche et réimpression de n'importe quel ticket passé |
| Rapports | Ventes détaillées, manquants par serveur, déductions salaires |
| Mon profil | Changement de mot de passe |
| **Déconnexion** | **Envoi automatique du rapport journalier par mail à l'admin** |

### 🟢 Serveur
| Fonctionnalité | Description |
|---|---|
| Mon espace | Tickets du mois, manquants, déductions, salaire net estimé |
| Mon profil | Changement de mot de passe |

---

## 🖨 Imprimante thermique

```bash
# Trouver les IDs USB de l'imprimante
lsusb
# → ex: ID 0416:5011  →  idVendor=0416  idProduct=5011

# Ajouter les droits USB
sudo usermod -aG lp $USER
sudo usermod -aG plugdev $USER

# Règle udev (remplacer les IDs)
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="0416", ATTRS{idProduct}=="5011", MODE="0666", GROUP="plugdev"' \
  | sudo tee /etc/udev/rules.d/99-escpos.rules
sudo udevadm control --reload-rules && sudo udevadm trigger

# Rebrancher l'imprimante + redémarrer la session
```

Configurer ensuite dans **Admin → Imprimante** : entrer `idVendor` et `idProduct`, cliquer "Imprimer ticket test".

---

## 📧 Rapport journalier par mail (Gmail)

1. Activer la **validation en 2 étapes** sur le compte Gmail expéditeur
2. Aller sur [myaccount.google.com](https://myaccount.google.com) → Sécurité → **Mots de passe des applications**
3. Créer un mot de passe pour "CaveVin" → copier les **16 caractères sans espaces**
4. Dans l'appli : **Admin → Config Mail** → renseigner expéditeur, mot de passe d'application, destinataire
5. Cliquer "Envoyer un mail test" pour vérifier
6. Dès que le caissier se déconnecte ou ferme l'appli → **rapport Excel du jour envoyé automatiquement**

> 💡 Si le mail arrive en spam la première fois, le marquer "Pas un spam" — les suivants arriveront en boîte de réception.

---

## 💾 Sauvegarde MySQL

- **Manuelle** : Admin → Export & Backup → "Sauvegarder maintenant"
- **Automatique** : activer le switch + définir l'heure (ex: 23:00)
- Fichiers stockés dans `~/CaveVin_Backups/` (`.sql.gz` compressé)
- Conservation automatique des 30 derniers jours
- **Restauration** : Admin → Export & Backup → "Restaurer..." → choisir le fichier

---

## 📊 Export Excel

Trois types de rapports disponibles dans **Admin → Export & Backup** :

| Type | Saisir | Contenu |
|------|--------|---------|
| Journalier | `2026-06-27` | Résumé KPIs, tickets du jour, boissons vendues, manquants |
| Mensuel | `2026-06` | Résumé, ventes détaillées, boissons, manquants, déductions |
| Annuel | `2026` | Tableau mois par mois + CA, coût, bénéfice, tickets, manquants |

---

## 📸 Photos des boissons

- Formats acceptés : JPG, PNG, WEBP
- Stockées dans `~/CaveVin_Photos/` (redimensionnées automatiquement à 500×500 max)
- Vignette miniature affichée dans la liste des boissons
- Aperçu instantané dans le formulaire d'édition

---

## 🔄 Mise à jour

```bash
# 1. Sauvegarder la base AVANT toute mise à jour
#    Admin → Export & Backup → Sauvegarder maintenant

# 2. Remplacer les fichiers .py (ne pas toucher config.py !)
# 3. Relancer
source .venv/bin/activate
python main.py
```

---

## 🚀 Démarrage rapide (raccourci Linux)

```bash
# Créer un script de lancement
cat > ~/Applications/cave_vin/lancer.sh << 'SCRIPT'
#!/bin/bash
cd ~/Applications/cave_vin
source .venv/bin/activate
python main.py
SCRIPT
chmod +x ~/Applications/cave_vin/lancer.sh

# Raccourci bureau
cat > ~/.local/share/applications/cavevin.desktop << 'DESKTOP'
[Desktop Entry]
Name=CaveVin Manager
Exec=/bin/bash -c "cd ~/Applications/cave_vin && source .venv/bin/activate && python main.py"
Terminal=false
Type=Application
Categories=Office;
DESKTOP
```

---

## ✅ Checklist déploiement

```
☐ Python 3.10+ installé
☐ MySQL/MariaDB installé et démarré
☐ Utilisateur MySQL dédié créé avec droits sur cave_vin
☐ config.py mis à jour avec les bons identifiants
☐ pip install -r requirements.txt exécuté
☐ python main.py → BDD créée automatiquement
☐ Connexion admin / admin123 → changer le mot de passe !
☐ Boissons ajoutées avec photos et catégories
☐ Employés créés (caissiers + serveurs)
☐ Imprimante branchée + configurée + ticket test OK
☐ Config Mail renseignée + mail test reçu
☐ Premier rapport Excel généré et vérifié
☐ Sauvegarde automatique activée
```

---

*CaveVin Manager v2.0 — Développé avec Python + CustomTkinter + MySQL*
