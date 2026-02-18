#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Liste toutes les colonnes de la table WEB_TRAITEMENTS (base utilisée par db.py).
"""
from db import get_db_cursor, DB_CONFIG


def lister():
    print("Connexion à:", DB_CONFIG.get("SERVER"), "/", DB_CONFIG.get("DATABASE"))
    print()
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo'
              AND TABLE_NAME = 'WEB_TRAITEMENTS'
            ORDER BY ORDINAL_POSITION
        """)
        rows = cursor.fetchall()
        print("Colonnes de WEB_TRAITEMENTS :")
        print("-" * 50)
        for r in rows:
            print("  ", r.COLUMN_NAME, "  ", r.DATA_TYPE, "  ", r.IS_NULLABLE)
        print("-" * 50)
        print("Total:", len(rows), "colonnes")
        if any(r.COLUMN_NAME == 'TempsEcouleAffichageSec' for r in rows):
            print("\n>>> TempsEcouleAffichageSec : PRESENTE")
        else:
            print("\n>>> TempsEcouleAffichageSec : ABSENTE")


if __name__ == "__main__":
    lister()
