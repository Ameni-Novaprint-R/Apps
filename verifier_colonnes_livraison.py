#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script pour verifier les colonnes de date de livraison dans COMMANDES et LIVRAISONS_CMDE"""

from db import get_db_cursor

print("=" * 80)
print("VERIFICATION DES COLONNES DE DATE DE LIVRAISON")
print("=" * 80)

with get_db_cursor() as cursor:
    # 1. Colonnes dans COMMANDES
    print("\n1. COLONNES DANS COMMANDES (relatives a la livraison):")
    print("-" * 80)
    
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'COMMANDES' 
        AND (COLUMN_NAME LIKE '%LIV%' OR COLUMN_NAME LIKE '%Dte%')
        ORDER BY COLUMN_NAME
    """)
    
    colonnes_cmd = cursor.fetchall()
    for col in colonnes_cmd:
        print(f"   - {col[0]} ({col[1]}, Nullable: {col[2]})")
    
    # 2. Colonnes dans LIVRAISONS_CMDE
    print("\n2. COLONNES DANS LIVRAISONS_CMDE:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'LIVRAISONS_CMDE'
        ORDER BY COLUMN_NAME
    """)
    
    colonnes_liv = cursor.fetchall()
    for col in colonnes_liv:
        print(f"   - {col[0]} ({col[1]}, Nullable: {col[2]})")
    
    # 3. Vérifier si COMMANDES.DteLivReelle existe
    print("\n3. VERIFICATION DE LA COLONNE DteLivReelle DANS COMMANDES:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'COMMANDES' AND COLUMN_NAME = 'DteLivReelle'
    """)
    
    dte_liv_reelle_exists = cursor.fetchone()
    if dte_liv_reelle_exists:
        print("   [OK] La colonne DteLivReelle existe dans COMMANDES")
    else:
        print("   [ERREUR] La colonne DteLivReelle n'existe PAS dans COMMANDES")
        print("   La fonction marquer_livraison_reelle essaie de modifier une colonne inexistante!")
    
    # 4. Vérifier la relation entre COMMANDES et LIVRAISONS_CMDE
    print("\n4. RELATION ENTRE COMMANDES ET LIVRAISONS_CMDE:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT TOP 5
            C.Numero,
            C.DteLivPrev,
            L.ID as ID_LIVRAISON,
            L.DteLiv as DteLiv_LIVRAISONS_CMDE,
            L.EtatLiv as EtatLiv_LIVRAISONS_CMDE
        FROM COMMANDES C
        LEFT JOIN LIVRAISONS_CMDE L ON C.ID = L.ID_COMMANDE
        WHERE C.Numero IS NOT NULL
        ORDER BY C.Numero DESC
    """)
    
    exemples = cursor.fetchall()
    print("   Exemples de relations:")
    for ex in exemples:
        print(f"   - Cmd: {ex[0]}, Date Prevue: {ex[1]}, ID_Liv: {ex[2]}, DteLiv: {ex[3]}, EtatLiv: {ex[4]}")

print("\n" + "=" * 80)
print("VERIFICATION TERMINEE")
print("=" * 80)
