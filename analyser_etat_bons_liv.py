#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script pour analyser la colonne Etat dans BONS_LIV"""

from db import get_db_cursor

print("=" * 80)
print("ANALYSE DE LA COLONNE Etat DANS BONS_LIV")
print("=" * 80)

with get_db_cursor() as cursor:
    # 1. Informations sur la colonne
    print("\n1. INFORMATIONS SUR LA COLONNE:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'BONS_LIV' AND COLUMN_NAME = 'Etat'
    """)
    
    col_info = cursor.fetchone()
    if col_info:
        print(f"   Colonne: {col_info[0]}")
        print(f"   Type: {col_info[1]}")
        print(f"   Nullable: {col_info[2]}")
        print(f"   Valeur par defaut: {col_info[3]}")
    
    # 2. Valeurs distinctes
    print("\n2. VALEURS DISTINCTES:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT DISTINCT Etat, COUNT(*) as count
        FROM BONS_LIV
        WHERE Etat IS NOT NULL
        GROUP BY Etat
        ORDER BY Etat
    """)
    
    valeurs = cursor.fetchall()
    for val, count in valeurs:
        print(f"   - Etat = {val}: {count} occurrences")
    
    # 3. Relation avec LIVRAISONS_CMDE
    print("\n3. RELATION AVEC LIVRAISONS_CMDE:")
    print("-" * 80)
    
    # Chercher une clé de liaison possible
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'BONS_LIV' 
        AND (COLUMN_NAME LIKE '%LIV%' OR COLUMN_NAME LIKE '%CMDE%' OR COLUMN_NAME LIKE '%COMMANDE%')
    """)
    
    colonnes_liaison = cursor.fetchall()
    print("   Colonnes potentielles de liaison dans BONS_LIV:")
    for col in colonnes_liaison:
        print(f"   - {col[0]}")
    
    # 4. Exemples de données
    print("\n4. EXEMPLES DE DONNEES:")
    print("-" * 80)
    
    for etat in [1, 2, 3]:
        cursor.execute("""
            SELECT TOP 3 
                ID,
                Numero,
                DateBl,
                Etat,
                Edite
            FROM BONS_LIV
            WHERE Etat = ?
            ORDER BY ID
        """, (etat,))
        
        exemples = cursor.fetchall()
        print(f"\n   Exemples pour Etat = {etat}:")
        for ex in exemples:
            print(f"   - ID={ex[0]}, Numero={ex[1]}, DateBl={ex[2]}, Etat={ex[3]}, Edite={ex[4]}")
    
    # 5. Vérifier si c'est une clé étrangère
    print("\n5. VERIFICATION DES CLES ETRANGERES:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            fk.name AS FK_Name,
            tp.name AS Parent_Table,
            cp.name AS Parent_Column,
            tr.name AS Referenced_Table,
            cr.name AS Referenced_Column
        FROM sys.foreign_keys AS fk
        INNER JOIN sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
        INNER JOIN sys.tables AS tp ON fkc.parent_object_id = tp.object_id
        INNER JOIN sys.columns AS cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
        INNER JOIN sys.tables AS tr ON fkc.referenced_object_id = tr.object_id
        INNER JOIN sys.columns AS cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
        WHERE tp.name = 'BONS_LIV' AND cp.name = 'Etat'
    """)
    
    fks = cursor.fetchall()
    if fks:
        print("   [OK] Cle(s) etrangere(s) trouvee(s):")
        for fk in fks:
            print(f"   - Nom FK: {fk[0]}")
            print(f"   - Table parente: {fk[1]}.{fk[2]}")
            print(f"   - Table referencee: {fk[3]}.{fk[4]}")
    else:
        print("   [INFO] Aucune cle etrangere trouvee")
    
    # 6. Comparaison avec EtatLiv
    print("\n6. COMPARAISON AVEC EtatLiv:")
    print("-" * 80)
    print("   BONS_LIV.Etat utilise les valeurs: 1, 2, 3")
    print("   LIVRAISONS_CMDE.EtatLiv utilise les valeurs: 0, 1, 2, 3")
    print("   COMMANDES.EtatLiv utilise les valeurs: 0, 1, 2, 3")
    print("\n   Note: BONS_LIV.Etat n'utilise pas la valeur 0")

print("\n" + "=" * 80)
print("ANALYSE TERMINEE")
print("=" * 80)
