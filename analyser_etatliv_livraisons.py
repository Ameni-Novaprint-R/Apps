#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script pour analyser la colonne EtatLiv dans LIVRAISONS_CMDE"""

from db import get_db_cursor

print("=" * 70)
print("ANALYSE DE LA COLONNE EtatLiv DANS LA TABLE LIVRAISONS_CMDE")
print("=" * 70)

with get_db_cursor() as cursor:
    # 1. Vérifier si la table existe
    print("\n1. Vérification de l'existence de la table LIVRAISONS_CMDE:")
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = 'LIVRAISONS_CMDE'
    """)
    table_exists = cursor.fetchone()
    if table_exists:
        print("   [OK] Table LIVRAISONS_CMDE trouvee")
    else:
        print("   [ERREUR] Table LIVRAISONS_CMDE non trouvee")
        exit(1)
    
    # 2. Vérifier si la colonne EtatLiv existe dans LIVRAISONS_CMDE
    print("\n2. Vérification de l'existence de la colonne EtatLiv:")
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'LIVRAISONS_CMDE' AND COLUMN_NAME = 'EtatLiv'
    """)
    col_info = cursor.fetchone()
    if col_info:
        print(f"   [OK] Colonne EtatLiv trouvee")
        print(f"   - Type de donnees: {col_info[1]}")
        print(f"   - Nullable: {col_info[2]}")
        print(f"   - Valeur par defaut: {col_info[3]}")
    else:
        print("   [ERREUR] Colonne EtatLiv non trouvee dans LIVRAISONS_CMDE")
        # Vérifier toutes les colonnes de la table
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'LIVRAISONS_CMDE'
            ORDER BY ORDINAL_POSITION
        """)
        print("\n   Colonnes disponibles dans LIVRAISONS_CMDE:")
        for col in cursor.fetchall():
            print(f"   - {col[0]} ({col[1]})")
        exit(1)
    
    # 3. Valeurs distinctes dans LIVRAISONS_CMDE
    print("\n3. Valeurs distinctes de EtatLiv dans LIVRAISONS_CMDE:")
    cursor.execute("""
        SELECT DISTINCT EtatLiv, COUNT(*) as count
        FROM LIVRAISONS_CMDE
        WHERE EtatLiv IS NOT NULL
        GROUP BY EtatLiv
        ORDER BY EtatLiv
    """)
    valeurs = cursor.fetchall()
    if valeurs:
        print("   Valeurs trouvées:")
        for val, count in valeurs:
            print(f"   - EtatLiv = {val}: {count} occurrences")
    else:
        print("   Aucune valeur trouvée (toutes les valeurs sont NULL)")
    
    # 4. Vérifier si c'est une clé étrangère
    print("\n4. Vérification des clés étrangères:")
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
        WHERE tp.name = 'LIVRAISONS_CMDE' AND cp.name = 'EtatLiv'
    """)
    fks = cursor.fetchall()
    if fks:
        print("   [OK] Cle(s) etrangere(s) trouvee(s):")
        for fk in fks:
            print(f"   - Nom FK: {fk[0]}")
            print(f"   - Table parente: {fk[1]}.{fk[2]}")
            print(f"   - Table referencee: {fk[3]}.{fk[4]}")
    else:
        print("   [INFO] Aucune cle etrangere trouvee pour EtatLiv dans LIVRAISONS_CMDE")
    
    # 5. Chercher des tables de référence possibles avec des colonnes similaires
    print("\n5. Recherche de tables de référence possibles:")
    cursor.execute("""
        SELECT TABLE_NAME, COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE COLUMN_NAME LIKE '%ETAT%' OR COLUMN_NAME LIKE '%LIV%' OR COLUMN_NAME LIKE '%STATUT%'
        ORDER BY TABLE_NAME, COLUMN_NAME
    """)
    tables_ref = cursor.fetchall()
    if tables_ref:
        print("   Tables avec colonnes similaires trouvées:")
        current_table = None
        for table, col in tables_ref:
            if table != current_table:
                if current_table is not None:
                    print()
                print(f"   - {table}:")
                current_table = table
            print(f"     • {col}")
    else:
        print("   Aucune table de référence évidente trouvée")
    
    # 6. Vérifier si EtatLiv existe dans d'autres tables
    print("\n6. Autres tables contenant une colonne EtatLiv:")
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE COLUMN_NAME = 'EtatLiv'
        ORDER BY TABLE_NAME
    """)
    autres_tables = cursor.fetchall()
    if autres_tables:
        for table in autres_tables:
            print(f"   - {table[0]}")
    else:
        print("   Aucune autre table trouvée")
    
    # 7. Exemples de données avec différentes valeurs
    print("\n7. Exemples de données pour chaque valeur d'EtatLiv:")
    cursor.execute("""
        SELECT TOP 3 EtatLiv, ID_COMMANDE, DteLiv
        FROM LIVRAISONS_CMDE
        WHERE EtatLiv IS NOT NULL
        ORDER BY EtatLiv, ID_COMMANDE
    """)
    exemples = cursor.fetchall()
    if exemples:
        print("   Exemples:")
        for ex in exemples:
            print(f"   - EtatLiv={ex[0]}, ID_COMMANDE={ex[1]}, DteLiv={ex[2]}")

print("\n" + "=" * 70)
print("ANALYSE TERMINÉE")
print("=" * 70)
