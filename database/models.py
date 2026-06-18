# ============================================================
# database/models.py — Création des tables + données initiales
# ============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database.db import db
import hashlib


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


TABLES = [
    # 1. Utilisateurs
    """
    CREATE TABLE IF NOT EXISTS utilisateurs (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        nom         VARCHAR(100) NOT NULL,
        prenom      VARCHAR(100) NOT NULL,
        username    VARCHAR(50)  NOT NULL UNIQUE,
        password    VARCHAR(256) NOT NULL,
        role        ENUM('admin','caissier','serveur') NOT NULL,
        salaire     DECIMAL(10,2) DEFAULT 0.00,
        actif       TINYINT(1)   DEFAULT 1,
        created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 2. Boissons
    """
    CREATE TABLE IF NOT EXISTS boissons (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        nom         VARCHAR(150) NOT NULL,
        categorie   VARCHAR(80)  DEFAULT 'Boisson',
        prix_vente  DECIMAL(10,2) NOT NULL,
        prix_achat  DECIMAL(10,2) DEFAULT 0.00,
        stock       INT          DEFAULT 0,
        unite       VARCHAR(30)  DEFAULT 'bouteille',
        actif       TINYINT(1)   DEFAULT 1,
        created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 3. Tickets de vente
    """
    CREATE TABLE IF NOT EXISTS tickets (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        numero       VARCHAR(30)  NOT NULL UNIQUE,
        serveur_id   INT          REFERENCES utilisateurs(id),
        caissier_id  INT          REFERENCES utilisateurs(id),
        date_vente   DATE         NOT NULL,
        total        DECIMAL(10,2) DEFAULT 0.00,
        montant_recu DECIMAL(10,2) DEFAULT 0.00,
        statut       ENUM('en_attente','valide','annule') DEFAULT 'en_attente',
        notes        TEXT,
        created_at   DATETIME     DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 4. Lignes de ticket (détail des ventes)
    """
    CREATE TABLE IF NOT EXISTS ticket_lignes (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        ticket_id   INT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
        boisson_id  INT NOT NULL REFERENCES boissons(id),
        quantite    INT NOT NULL DEFAULT 1,
        prix_unit   DECIMAL(10,2) NOT NULL,
        sous_total  DECIMAL(10,2) GENERATED ALWAYS AS (quantite * prix_unit) STORED
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 5. Manquants (différence entre ce qui a été vendu et ce qui est encaissé)
    """
    CREATE TABLE IF NOT EXISTS manquants (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        serveur_id   INT  NOT NULL REFERENCES utilisateurs(id),
        ticket_id    INT  REFERENCES tickets(id),
        montant      DECIMAL(10,2) NOT NULL,
        description  TEXT,
        rembourse    TINYINT(1) DEFAULT 0,
        date_manquant DATE DEFAULT (CURRENT_DATE),
        created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 6. Déductions salaire
    """
    CREATE TABLE IF NOT EXISTS deductions (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        employe_id   INT  NOT NULL REFERENCES utilisateurs(id),
        manquant_id  INT  REFERENCES manquants(id),
        montant      DECIMAL(10,2) NOT NULL,
        motif        TEXT,
        mois         VARCHAR(7),   -- FORMAT: YYYY-MM
        created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # 7. Journées de caisse
    """
    CREATE TABLE IF NOT EXISTS journees (
        id              INT AUTO_INCREMENT PRIMARY KEY,
        date_journee    DATE NOT NULL UNIQUE,
        caissier_id     INT  REFERENCES utilisateurs(id),
        total_ventes    DECIMAL(10,2) DEFAULT 0.00,
        total_manquants DECIMAL(10,2) DEFAULT 0.00,
        benefice_net    DECIMAL(10,2) DEFAULT 0.00,
        cloturee        TINYINT(1) DEFAULT 0,
        created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
]


def create_database():
    """Crée la base de données si elle n'existe pas."""
    import mysql.connector
    from config import DB_CONFIG
    cfg = dict(DB_CONFIG)
    dbname = cfg.pop("database")
    cfg.pop("autocommit", None)
    try:
        tmp = mysql.connector.connect(**cfg)
        cur = tmp.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{dbname}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        tmp.commit()
        cur.close()
        tmp.close()
        return True
    except Exception as e:
        print(f"[DB] Impossible de créer la base : {e}")
        return False


def initialize():
    """Crée les tables et insère l'admin par défaut."""
    create_database()
    db.connect()
    for sql in TABLES:
        db.execute(sql, commit=True)

    # Admin par défaut : admin / admin123
    existing = db.fetchone("SELECT id FROM utilisateurs WHERE username='admin'")
    if not existing:
        db.execute(
            """INSERT INTO utilisateurs (nom, prenom, username, password, role, salaire)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            ("Super", "Admin", "admin", hash_password("admin123"), "admin", 0),
            commit=True,
        )
        print("[DB] Admin créé → username: admin | password: admin123")

    print("[DB] Base initialisée avec succès.")
