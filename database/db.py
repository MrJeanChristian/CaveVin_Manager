# ============================================================
# database/db.py — Connexion MySQL + helpers
# ============================================================

import mysql.connector
from mysql.connector import Error
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DB_CONFIG


class Database:
    _instance = None

    def __init__(self):
        self.conn   = None
        self.cursor = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def connect(self):
        try:
            self.conn   = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(dictionary=True)
            return True
        except Error as e:
            print(f"[DB] Erreur de connexion : {e}")
            return False

    def disconnect(self):
        if self.conn and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()

    def execute(self, query, params=None, commit=False):
        try:
            self.cursor.execute(query, params or ())
            if commit:
                self.conn.commit()
            return True
        except Error as e:
            print(f"[DB] Erreur execute : {e}")
            self.conn.rollback()
            return False

    def fetchone(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchone()
        except Error as e:
            print(f"[DB] Erreur fetchone : {e}")
            return None

    def fetchall(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Error as e:
            print(f"[DB] Erreur fetchall : {e}")
            return []

    def lastrowid(self):
        return self.cursor.lastrowid


# Singleton global
db = Database.get_instance()
