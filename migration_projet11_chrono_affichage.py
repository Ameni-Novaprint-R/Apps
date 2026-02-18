#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Migration Projet 11 : ajouter la colonne TempsEcouleAffichageSec à WEB_TRAITEMENTS.
Cette colonne stocke le temps affiché du chronomètre (en secondes) lorsque l'utilisateur
a mis en pause puis fermé la fenêtre, pour réafficher le même temps à la réouverture.
"""
from db import get_db_cursor


def run():
    with get_db_cursor() as cursor:
        try:
            cursor.execute("""
                IF NOT EXISTS (
                    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_TRAITEMENTS'
                    AND COLUMN_NAME = 'TempsEcouleAffichageSec'
                )
                BEGIN
                    ALTER TABLE [dbo].[WEB_TRAITEMENTS] ADD [TempsEcouleAffichageSec] INT NULL;
                END
            """)
            cursor.connection.commit()
            print("Colonne WEB_TRAITEMENTS.TempsEcouleAffichageSec : OK")
        except Exception as e:
            print("Erreur:", e)
            cursor.connection.rollback()
            return False
    return True


if __name__ == "__main__":
    run()
