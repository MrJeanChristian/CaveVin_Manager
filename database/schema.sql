-- ============================================================
--  Cave à Vin - Schéma MySQL
-- ============================================================

CREATE DATABASE IF NOT EXISTS cave_vin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cave_vin;

-- ── Utilisateurs / Employés ─────────────────────────────────
CREATE TABLE IF NOT EXISTS utilisateurs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nom         VARCHAR(100) NOT NULL,
    prenom      VARCHAR(100) NOT NULL,
    username    VARCHAR(50)  NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,          -- SHA-256 hashé
    role        ENUM('admin','caissier','serveur') NOT NULL,
    salaire_base DECIMAL(10,2) DEFAULT 0.00,
    actif       BOOLEAN DEFAULT TRUE,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── Boissons / Produits ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS boissons (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nom         VARCHAR(150) NOT NULL,
    categorie   VARCHAR(100) DEFAULT 'Vin',
    prix_vente  DECIMAL(10,2) NOT NULL,
    prix_achat  DECIMAL(10,2) DEFAULT 0.00,
    stock       INT DEFAULT 0,
    unite       VARCHAR(20) DEFAULT 'bouteille',
    actif       BOOLEAN DEFAULT TRUE,
    date_ajout  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── Tickets de vente ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tickets (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    numero          VARCHAR(20) NOT NULL UNIQUE,
    serveur_id      INT,
    caissier_id     INT,
    date_vente      DATETIME DEFAULT CURRENT_TIMESTAMP,
    montant_total   DECIMAL(10,2) DEFAULT 0.00,
    statut          ENUM('ouvert','validé','annulé') DEFAULT 'ouvert',
    FOREIGN KEY (serveur_id)  REFERENCES utilisateurs(id) ON DELETE SET NULL,
    FOREIGN KEY (caissier_id) REFERENCES utilisateurs(id) ON DELETE SET NULL
);

-- ── Lignes de ticket ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ticket_lignes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id   INT NOT NULL,
    boisson_id  INT NOT NULL,
    quantite    INT NOT NULL DEFAULT 1,
    prix_unitaire DECIMAL(10,2) NOT NULL,
    sous_total  DECIMAL(10,2) GENERATED ALWAYS AS (quantite * prix_unitaire) STORED,
    FOREIGN KEY (ticket_id)  REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (boisson_id) REFERENCES boissons(id) ON DELETE RESTRICT
);

-- ── Manquants (écarts de stock imputés aux serveurs) ────────
CREATE TABLE IF NOT EXISTS manquants (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    serveur_id      INT NOT NULL,
    boisson_id      INT NOT NULL,
    quantite        INT NOT NULL,
    montant         DECIMAL(10,2) NOT NULL,
    date_constat    DATE NOT NULL,
    description     TEXT,
    deduit          BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (serveur_id)  REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (boisson_id)  REFERENCES boissons(id) ON DELETE RESTRICT
);

-- ── Déductions sur salaires ─────────────────────────────────
CREATE TABLE IF NOT EXISTS deductions_salaires (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    employe_id      INT NOT NULL,
    manquant_id     INT,
    montant         DECIMAL(10,2) NOT NULL,
    motif           TEXT,
    date_deduction  DATE NOT NULL,
    FOREIGN KEY (employe_id)  REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (manquant_id) REFERENCES manquants(id) ON DELETE SET NULL
);

-- ── Compte journalier (clôture caissier) ────────────────────
CREATE TABLE IF NOT EXISTS comptes_journaliers (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    caissier_id     INT NOT NULL,
    date_compte     DATE NOT NULL UNIQUE,
    recettes        DECIMAL(10,2) DEFAULT 0.00,
    depenses        DECIMAL(10,2) DEFAULT 0.00,
    benefice        DECIMAL(10,2) DEFAULT 0.00,
    nb_tickets      INT DEFAULT 0,
    notes           TEXT,
    cloture         BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (caissier_id) REFERENCES utilisateurs(id)
);

-- ── Admin par défaut (mot de passe : Admin@2024) ────────────
INSERT IGNORE INTO utilisateurs (nom, prenom, username, password, role)
VALUES ('Administrateur', 'Système', 'admin',
        SHA2('Admin@2024', 256), 'admin');
