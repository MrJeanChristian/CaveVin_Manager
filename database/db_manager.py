"""
Gestionnaire de connexion MySQL - Cave à Vin
"""
import mysql.connector
from mysql.connector import Error
import hashlib
import os


# ── Configuration ────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": "cave_vin",
    "charset":  "utf8mb4",
    "autocommit": False,
}


class DatabaseManager:
    """Singleton de connexion MySQL."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._conn = None
        return cls._instance

    # ── Connexion ────────────────────────────────────────────
    def connect(self, host=None, port=None, user=None, password=None):
        cfg = DB_CONFIG.copy()
        if host:     cfg["host"]     = host
        if port:     cfg["port"]     = port
        if user:     cfg["user"]     = user
        if password: cfg["password"] = password

        # Créer la BDD si elle n'existe pas encore
        init_cfg = {k: v for k, v in cfg.items() if k != "database"}
        init_cfg["autocommit"] = True
        tmp = mysql.connector.connect(**init_cfg)
        cur = tmp.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS cave_vin "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cur.close()
        tmp.close()

        self._conn = mysql.connector.connect(**cfg)
        self._run_schema()
        return True

    def _run_schema(self):
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            raw = f.read()
        cursor = self._conn.cursor()
        for stmt in raw.split(";"):
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--") and stmt.upper() not in ("USE CAVE_VIN", ""):
                try:
                    cursor.execute(stmt)
                except Error:
                    pass
        self._conn.commit()
        cursor.close()

    def disconnect(self):
        if self._conn and self._conn.is_connected():
            self._conn.close()
            self._conn = None

    @property
    def connection(self):
        if self._conn is None or not self._conn.is_connected():
            raise RuntimeError("Non connecté à la base de données.")
        return self._conn

    # ── Helpers CRUD ─────────────────────────────────────────
    def execute(self, query, params=None, commit=True):
        cur = self.connection.cursor()
        cur.execute(query, params or ())
        if commit:
            self._conn.commit()
        last_id = cur.lastrowid
        cur.close()
        return last_id

    def fetchall(self, query, params=None):
        cur = self.connection.cursor(dictionary=True)
        cur.execute(query, params or ())
        rows = cur.fetchall()
        cur.close()
        return rows

    def fetchone(self, query, params=None):
        cur = self.connection.cursor(dictionary=True)
        cur.execute(query, params or ())
        row = cur.fetchone()
        cur.close()
        return row

    # ── Auth ─────────────────────────────────────────────────
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username: str, password: str):
        """Retourne la ligne utilisateur ou None."""
        hashed = self.hash_password(password)
        return self.fetchone(
            "SELECT * FROM utilisateurs WHERE username=%s AND password=%s AND actif=1",
            (username, hashed)
        )


# Instance globale
db = DatabaseManager()
