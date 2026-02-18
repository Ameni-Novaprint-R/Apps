#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Vérifie si la colonne TempsEcouleAffichageSec existe dans WEB_TRAITEMENTS.
Si elle n'existe pas, l'ajoute (migration).
"""
from db import get_db_cursor


def verifier_et_ajouter():
    with get_db_cursor() as cursor:
        # 1. Vérifier l'existence de la colonne
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo'
              AND TABLE_NAME = 'WEB_TRAITEMENTS'
              AND COLUMN_NAME = 'TempsEcouleAffichageSec'
        """)
        row = cursor.fetchone()
        if row:
            print("La colonne TempsEcouleAffichageSec EXISTE dans WEB_TRAITEMENTS.")
            print(f"  Type: {row.DATA_TYPE}")
            return True

        print("La colonne TempsEcouleAffichageSec N'EXISTE PAS. Ajout en cours...")

        # 2. Ajouter la colonne
        try:
            cursor.execute("""
                ALTER TABLE [dbo].[WEB_TRAITEMENTS]
                ADD [TempsEcouleAffichageSec] INT NULL
            """)
            cursor.connection.commit()
            print("Colonne TempsEcouleAffichageSec ajoutée avec succès.")
        except Exception as e:
            print("Erreur lors de l'ajout:", e)
            cursor.connection.rollback()
            return False

        # 3. Revérifier
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo'
              AND TABLE_NAME = 'WEB_TRAITEMENTS'
              AND COLUMN_NAME = 'TempsEcouleAffichageSec'
        """)
        row2 = cursor.fetchone()
        if row2:
            print("Vérification OK: la colonne est bien présente.")
            return True
        print("Avertissement: la colonne n'apparaît pas après ajout.")
        return False


if __name__ == "__main__":
    verifier_et_ajouter()
