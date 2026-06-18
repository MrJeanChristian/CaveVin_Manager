# 🍷 CaveVin Manager

Logiciel de gestion de cave à vin — CustomTkinter + MySQL

---

## 📦 Installation

```bash
# 1. Cloner / placer le dossier cave_vin/
cd cave_vin

# 2. Créer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer la base de données
#    → Ouvrir config.py et renseigner vos identifiants MySQL :
#      DB_CONFIG = { "user": "root", "password": "votre_mdp", ... }

# 5. Lancer l'application (crée la BDD automatiquement)
python main.py
```

---

## 🔐 Compte par défaut

| Username | Mot de passe | Rôle          |
|----------|-------------|---------------|
| `admin`  | `admin123`  | Administrateur |

> ⚠️ Changez ce mot de passe dès la première connexion via la gestion des employés.

---

## 🗂 Structure du projet

```
cave_vin/
├── main.py                  # Point d'entrée
├── config.py                # Palette, DB config, constantes
├── requirements.txt
├── database/
│   ├── db.py               # Singleton MySQL
│   └── models.py           # Tables + initialisation
├── auth/
│   └── login.py            # Fenêtre de connexion
├── views/
│   ├── admin/
│   │   ├── dashboard.py    # KPIs globaux
│   │   ├── boissons.py     # CRUD boissons + prix
│   │   └── employes.py     # CRUD employés (caissiers, serveurs)
│   ├── caissier/
│   │   ├── dashboard.py    # Accueil caissier
│   │   ├── tickets.py      # Saisie des tickets de vente
│   │   └── rapports.py     # Bénéfices jour/mois/S1 + manquants + déductions
│   └── serveur/
│       └── dashboard.py    # Espace personnel serveur
└── components/
    └── sidebar.py          # Sidebar réutilisable
```

---

## 👥 Rôles & Fonctionnalités

### 🔴 Admin
- Vue d'ensemble (KPIs globaux, derniers tickets)
- Gestion des boissons : ajout, modification, prix de vente/achat, stock
- Gestion des employés : création, modification, désactivation, salaires

### 🟡 Caissier
- Dashboard : ventes du jour, du mois, manquants actifs
- Saisie de ticket : sélection du serveur, ajout de lignes, calcul automatique
  → Détection automatique du manquant si montant reçu < total
- Rapports :
  - 💰 Ventes détaillées par mois
  - ⚠ Manquants par serveur
  - 💸 Déductions sur salaires (avec un clic)
  - 📈 Bénéfices journaliers, mensuels, semestriels

### 🟢 Serveur
- Son tableau de bord personnel : tickets, manquants, déductions, salaire net estimé

---

## 🔧 Configuration MySQL

Modifier `config.py` :

```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "votre_mot_de_passe",
    "database": "cave_vin",
}
```

La base et les tables sont créées **automatiquement** au premier lancement.
