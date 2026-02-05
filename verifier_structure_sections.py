#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script pour verifier la structure de WEB_SECTIONS"""

from db import get_db_cursor

with get_db_cursor() as cursor:
    # Vérifier les colonnes de WEB_SECTIONS
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'WEB_SECTIONS'
        ORDER BY ORDINAL_POSITION
    """)
    
    print("Colonnes de WEB_SECTIONS:")
    for col in cursor.fetchall():
        print(f"  - {col[0]} ({col[1]}, Nullable: {col[2]})")
    
    # Exemples de sections
    cursor.execute("""
        SELECT TOP 5 WS.ID, WS.Nom, WS.ID_Proj, WP.NumProj, WP.Nom as NomProjet
        FROM WEB_SECTIONS WS
        INNER JOIN WEB_PROJETS WP ON WP.ID = WS.ID_Proj
        ORDER BY WS.ID
    """)
    
    print("\nExemples de sections:")
    for row in cursor.fetchall():
        print(f"  - ID: {row[0]}, Nom: {row[1]}, Projet: {row[4]} (Num: {row[3]})")
