# ============================================================
# config.py — Configuration globale de l'application
# ============================================================

DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "jeanchristian",
    "password": "ChristiaN12.",
    "database": "cave_A_Vin",
    "charset":  "utf8mb4",
    "autocommit": False,
}

APP_NAME    = "CAVE OUEDRAOGO"
APP_VERSION = "1.0.0"
WINDOW_SIZE = "1280x780"

# Palette visuelle
COLORS = {
    "bg_dark":    "#1A0A0A",   # Fond principal (bordeaux très sombre)
    "bg_card":    "#2A1010",   # Cartes / panneaux
    "bg_sidebar": "#120606",   # Sidebar
    "accent":     "#C0392B",   # Rouge vin principal
    "accent2":    "#922B21",   # Rouge vin foncé
    "gold":       "#D4AC0D",   # Or (prix, bénéfices)
    "text":       "#F5E6D3",   # Texte principal (crème)
    "text_muted": "#9E8B7A",   # Texte secondaire
    "success":    "#27AE60",   # Vert (bénéfice positif)
    "danger":     "#E74C3C",   # Rouge (manquant / perte)
    "border":     "#3D1515",   # Bordures
    "white":      "#FFFFFF",
}

FONTS = {
    "title":   ("Georgia", 32, "bold"),
    "heading": ("Georgia", 28, "bold"),
    "body":    ("Helvetica", 22),
    "small":   ("Helvetica", 16),
    "mono":    ("Courier New", 22),
    "badge":   ("Helvetica", 20, "bold"),
}

# Rôles utilisateurs
ROLES = {
    "admin":    "Administrateur",
    "caissier": "Caissier",
    "serveur":  "Serveur",
}
