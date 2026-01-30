#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour vérifier les colonnes des tables PAPIERS et IMPRIMEURS
"""

from db import get_db_cursor

def main():
    print("=" * 80)
    print("VERIFICATION DES COLONNES - PAPIERS et IMPRIMEURS")
    print("=" * 80)
    print()
    
    with get_db_cursor() as cursor:
        # Colonnes de PAPIERS
        print("Colonnes de PAPIERS:")
        print("-" * 80)
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'PAPIERS'
            ORDER BY ORDINAL_POSITION
        """)
        for row in cursor.fetchall():
            print(f"  {row.COLUMN_NAME} ({row.DATA_TYPE})")
        print()
        
        # Colonnes de IMPRIMEURS
        print("Colonnes de IMPRIMEURS:")
        print("-" * 80)
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'IMPRIMEURS'
            ORDER BY ORDINAL_POSITION
        """)
        for row in cursor.fetchall():
            print(f"  {row.COLUMN_NAME} ({row.DATA_TYPE})")
        print()
        
        # Exemple de données pour voir les noms de colonnes
        print("Exemple de données PAPIERS (première ligne):")
        print("-" * 80)
        cursor.execute("SELECT TOP 1 * FROM PAPIERS")
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            for i, col in enumerate(columns):
                print(f"  {col}: {row[i]}")
        print()
        
        print("Exemple de données IMPRIMEURS (première ligne):")
        print("-" * 80)
        cursor.execute("SELECT TOP 1 * FROM IMPRIMEURS")
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            for i, col in enumerate(columns):
                print(f"  {col}: {row[i]}")

if __name__ == "__main__":
    main()
