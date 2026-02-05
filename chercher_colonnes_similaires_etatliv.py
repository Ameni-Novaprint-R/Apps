#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script pour trouver toutes les colonnes similaires a EtatLiv avec d'autres noms"""

from db import get_db_cursor

print("=" * 80)
print("RECHERCHE DE COLONNES SIMILAIRES A EtatLiv AVEC D'AUTRES NOMS")
print("=" * 80)

with get_db_cursor() as cursor:
    # Rechercher des colonnes avec des noms similaires
    print("\n1. RECHERCHE DE COLONNES CONTENANT 'ETAT' ET 'LIV':")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE (
            COLUMN_NAME LIKE '%ETAT%' AND COLUMN_NAME LIKE '%LIV%'
            OR COLUMN_NAME LIKE '%LIV%' AND COLUMN_NAME LIKE '%ETAT%'
            OR COLUMN_NAME LIKE '%STATUT%' AND COLUMN_NAME LIKE '%LIV%'
            OR COLUMN_NAME LIKE '%LIV%' AND COLUMN_NAME LIKE '%STATUT%'
        )
        ORDER BY TABLE_NAME, COLUMN_NAME
    """)
    
    colonnes_etat_liv = cursor.fetchall()
    
    if colonnes_etat_liv:
        print(f"   Total de colonnes trouvees: {len(colonnes_etat_liv)}\n")
        for col in colonnes_etat_liv:
            print(f"   - {col[0]}.{col[1]} (Type: {col[2]}, Nullable: {col[3]}, Default: {col[4]})")
    else:
        print("   Aucune colonne trouvee")
    
    # Rechercher des colonnes contenant "ETAT" dans les tables de livraison
    print("\n2. RECHERCHE DE COLONNES 'ETAT' DANS LES TABLES DE LIVRAISON:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE (
            TABLE_NAME LIKE '%LIV%' AND COLUMN_NAME LIKE '%ETAT%'
            OR TABLE_NAME LIKE '%LIVRAISON%' AND COLUMN_NAME LIKE '%ETAT%'
        )
        ORDER BY TABLE_NAME, COLUMN_NAME
    """)
    
    colonnes_liv_etat = cursor.fetchall()
    
    if colonnes_liv_etat:
        print(f"   Total de colonnes trouvees: {len(colonnes_liv_etat)}\n")
        for col in colonnes_liv_etat:
            print(f"   - {col[0]}.{col[1]} (Type: {col[2]}, Nullable: {col[3]}, Default: {col[4]})")
    else:
        print("   Aucune colonne trouvee")
    
    # Rechercher des colonnes contenant "STATUT" dans les tables de livraison
    print("\n3. RECHERCHE DE COLONNES 'STATUT' DANS LES TABLES DE LIVRAISON:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE (
            TABLE_NAME LIKE '%LIV%' AND COLUMN_NAME LIKE '%STATUT%'
            OR TABLE_NAME LIKE '%LIVRAISON%' AND COLUMN_NAME LIKE '%STATUT%'
        )
        ORDER BY TABLE_NAME, COLUMN_NAME
    """)
    
    colonnes_liv_statut = cursor.fetchall()
    
    if colonnes_liv_statut:
        print(f"   Total de colonnes trouvees: {len(colonnes_liv_statut)}\n")
        for col in colonnes_liv_statut:
            print(f"   - {col[0]}.{col[1]} (Type: {col[2]}, Nullable: {col[3]}, Default: {col[4]})")
    else:
        print("   Aucune colonne trouvee")
    
    # Rechercher toutes les tables contenant "LIV" dans leur nom
    print("\n4. TOUTES LES TABLES CONTENANT 'LIV' DANS LEUR NOM:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT DISTINCT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME LIKE '%LIV%'
        ORDER BY TABLE_NAME
    """)
    
    tables_liv = cursor.fetchall()
    
    if tables_liv:
        print(f"   Total de tables trouvees: {len(tables_liv)}\n")
        for table in tables_liv:
            table_name = table[0]
            print(f"   - {table_name}")
            
            # Lister toutes les colonnes de cette table
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """, (table_name,))
            
            colonnes = cursor.fetchall()
            print(f"     Colonnes: {', '.join([f'{c[0]} ({c[1]})' for c in colonnes[:10]])}")
            if len(colonnes) > 10:
                print(f"     ... et {len(colonnes) - 10} autres colonnes")
            print()
    
    # Rechercher des colonnes avec des valeurs similaires (0-3) qui pourraient être des états
    print("\n5. RECHERCHE DE COLONNES NUMERIQUES AVEC VALEURS 0-3:")
    print("-" * 80)
    print("   (Colonnes qui pourraient representer des etats similaires)")
    
    cursor.execute("""
        SELECT DISTINCT 
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE DATA_TYPE IN ('tinyint', 'smallint', 'int', 'bigint')
        AND TABLE_NAME LIKE '%LIV%'
        AND COLUMN_NAME NOT LIKE '%ID%'
        AND COLUMN_NAME NOT LIKE '%NUM%'
        AND COLUMN_NAME NOT LIKE '%QTE%'
        AND COLUMN_NAME NOT LIKE '%PRIX%'
        AND COLUMN_NAME NOT LIKE '%MONTANT%'
        ORDER BY TABLE_NAME, COLUMN_NAME
    """)
    
    colonnes_numeriques = cursor.fetchall()
    
    if colonnes_numeriques:
        print(f"   Total de colonnes numeriques trouvees: {len(colonnes_numeriques)}\n")
        for col in colonnes_numeriques[:20]:  # Limiter à 20 pour ne pas surcharger
            table_name = col[0]
            col_name = col[1]
            data_type = col[2]
            
            # Vérifier les valeurs distinctes
            try:
                cursor.execute(f"""
                    SELECT DISTINCT [{col_name}], COUNT(*) as count
                    FROM [{table_name}]
                    WHERE [{col_name}] IS NOT NULL
                    GROUP BY [{col_name}]
                    ORDER BY [{col_name}]
                """)
                valeurs = cursor.fetchall()
                
                # Filtrer celles qui ont des valeurs entre 0 et 3
                valeurs_0_3 = [v for v, c in valeurs if isinstance(v, (int, type(None))) and v is not None and 0 <= v <= 3]
                
                if valeurs_0_3 and len(valeurs_0_3) <= 4:  # Maximum 4 valeurs distinctes (0,1,2,3)
                    print(f"   - {table_name}.{col_name} ({data_type})")
                    print(f"     Valeurs: {sorted(valeurs_0_3)}")
                    print(f"     Total valeurs distinctes: {len(valeurs)}")
            except:
                pass
    
    # Recherche spécifique de colonnes avec des noms alternatifs
    print("\n6. RECHERCHE DE COLONNES AVEC NOMS ALTERNATIFS POSSIBLES:")
    print("-" * 80)
    
    noms_alternatifs = [
        'Etat_Liv', 'EtatLivraison', 'Etat_Livraison',
        'StatutLiv', 'Statut_Liv', 'StatutLivraison', 'Statut_Livraison',
        'LivEtat', 'Liv_Etat', 'LivraisonEtat', 'Livraison_Etat',
        'LivStatut', 'Liv_Statut', 'LivraisonStatut', 'Livraison_Statut',
        'Etat', 'Statut'
    ]
    
    for nom in noms_alternatifs:
        cursor.execute("""
            SELECT 
                TABLE_NAME,
                COLUMN_NAME,
                DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE COLUMN_NAME = ?
            ORDER BY TABLE_NAME
        """, (nom,))
        
        resultats = cursor.fetchall()
        if resultats:
            print(f"\n   Colonne '{nom}' trouvee dans:")
            for res in resultats:
                print(f"   - {res[0]}.{res[1]} (Type: {res[2]})")

print("\n" + "=" * 80)
print("RECHERCHE TERMINEE")
print("=" * 80)
