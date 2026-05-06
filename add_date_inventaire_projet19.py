"""
Script pour ajouter la colonne DateInventaire (DATE) à WEB_S_DOS_ENCOURS.

Ce script utilise la connexion SQL définie dans `db.py` (get_db_connection).
"""

from db import get_db_connection


def add_date_inventaire_column() -> None:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) AS col_exists
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS'
              AND COLUMN_NAME = 'DateInventaire'
        """)
        row = cursor.fetchone()
        exists = bool(row and getattr(row, "col_exists", 0) > 0)

        if exists:
            print("[OK] La colonne DateInventaire existe deja.")
            return

        cursor.execute("""
            ALTER TABLE WEB_S_DOS_ENCOURS
            ADD DateInventaire DATE NULL
        """)
        conn.commit()
        print("[OK] Colonne DateInventaire ajoutee avec succes.")
    except Exception as exc:
        print(f"[ERREUR] {exc}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    add_date_inventaire_column()
