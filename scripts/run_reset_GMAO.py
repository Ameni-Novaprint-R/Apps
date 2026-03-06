#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exécute le script de vidage des fiches GMAO (demandes + réparations) et reset des ID."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_cursor

def main():
    print("Exécution du vidage des fiches GMAO...")
    try:
        with get_db_cursor() as cursor:
            # 1. Supprimer les articles
            cursor.execute("DELETE FROM dbo.WEB_GMAO_ARTICLES")
            print("  - WEB_GMAO_ARTICLES : vidé")
            # 2. Supprimer les réparations
            cursor.execute("DELETE FROM dbo.WEB_GMAO_REPARATION")
            print("  - WEB_GMAO_REPARATION : vidé")
            # 3. Supprimer les demandes
            cursor.execute("DELETE FROM dbo.WEB_GMAO")
            print("  - WEB_GMAO : vidé")
            # 4. Reset IDENTITY
            cursor.execute("DBCC CHECKIDENT ('dbo.WEB_GMAO', RESEED, 0)")
            print("  - IDENTITY WEB_GMAO réinitialisé")
            cursor.execute("DBCC CHECKIDENT ('dbo.WEB_GMAO_REPARATION', RESEED, 0)")
            print("  - IDENTITY WEB_GMAO_REPARATION réinitialisé")
            cursor.connection.commit()
        print("Vidage terminé : les deux listes sont vides et les ID repartiront à 1.")
    except Exception as e:
        print(f"ERREUR : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
