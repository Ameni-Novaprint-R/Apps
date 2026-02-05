#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script pour trouver toutes les tables contenant la colonne EtatLiv"""

from db import get_db_cursor

print("=" * 80)
print("RECHERCHE DE LA COLONNE EtatLiv DANS TOUTES LES TABLES")
print("=" * 80)

with get_db_cursor() as cursor:
    # Rechercher toutes les tables contenant EtatLiv
    print("\n1. TOUTES LES TABLES CONTENANT LA COLONNE EtatLiv:")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            CHARACTER_MAXIMUM_LENGTH,
            NUMERIC_PRECISION,
            NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE COLUMN_NAME = 'EtatLiv'
        ORDER BY TABLE_NAME
    """)
    
    tables = cursor.fetchall()
    
    if tables:
        print(f"   Total de tables trouvees: {len(tables)}\n")
        
        for table_info in tables:
            table_name = table_info[0]
            col_name = table_info[1]
            data_type = table_info[2]
            nullable = table_info[3]
            default = table_info[4]
            max_length = table_info[5]
            precision = table_info[6]
            scale = table_info[7]
            
            print(f"   Table: {table_name}")
            print(f"   - Colonne: {col_name}")
            print(f"   - Type: {data_type}", end="")
            if max_length:
                print(f"({max_length})", end="")
            elif precision:
                print(f"({precision},{scale})", end="")
            print()
            print(f"   - Nullable: {nullable}")
            print(f"   - Valeur par defaut: {default}")
            
            # Analyser les valeurs distinctes dans chaque table
            try:
                cursor.execute(f"""
                    SELECT DISTINCT EtatLiv, COUNT(*) as count
                    FROM [{table_name}]
                    WHERE EtatLiv IS NOT NULL
                    GROUP BY EtatLiv
                    ORDER BY EtatLiv
                """)
                valeurs = cursor.fetchall()
                
                if valeurs:
                    print(f"   - Valeurs distinctes:")
                    for val, count in valeurs:
                        print(f"     * EtatLiv = {val}: {count} occurrences")
                else:
                    print(f"   - Aucune valeur non-NULL trouvee")
                    
                # Compter le total d'enregistrements
                cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                total = cursor.fetchone()[0]
                print(f"   - Total d'enregistrements dans la table: {total}")
                
            except Exception as e:
                print(f"   - Erreur lors de l'analyse: {str(e)}")
            
            print()
    else:
        print("   Aucune table trouvee avec la colonne EtatLiv")
    
    # Vérifier les clés étrangères pour chaque table
    print("\n2. VERIFICATION DES CLES ETRANGERES:")
    print("-" * 80)
    
    for table_info in tables:
        table_name = table_info[0]
        print(f"\n   Table: {table_name}")
        
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
            WHERE tp.name = ? AND cp.name = 'EtatLiv'
        """, (table_name,))
        
        fks = cursor.fetchall()
        if fks:
            print(f"   [OK] Cle(s) etrangere(s) trouvee(s):")
            for fk in fks:
                print(f"   - Nom FK: {fk[0]}")
                print(f"   - Table parente: {fk[1]}.{fk[2]}")
                print(f"   - Table referencee: {fk[3]}.{fk[4]}")
        else:
            print(f"   [INFO] Aucune cle etrangere trouvee")
    
    # Comparaison des valeurs entre les tables
    print("\n3. COMPARAISON DES VALEURS ENTRE LES TABLES:")
    print("-" * 80)
    
    if len(tables) > 1:
        print("   Valeurs communes et differences:")
        valeurs_par_table = {}
        
        for table_info in tables:
            table_name = table_info[0]
            try:
                cursor.execute(f"""
                    SELECT DISTINCT EtatLiv
                    FROM [{table_name}]
                    WHERE EtatLiv IS NOT NULL
                    ORDER BY EtatLiv
                """)
                valeurs = [row[0] for row in cursor.fetchall()]
                valeurs_par_table[table_name] = set(valeurs)
                print(f"   - {table_name}: {sorted(valeurs)}")
            except Exception as e:
                print(f"   - {table_name}: Erreur - {str(e)}")
        
        # Trouver les valeurs communes
        if len(valeurs_par_table) > 1:
            valeurs_communes = set.intersection(*valeurs_par_table.values())
            if valeurs_communes:
                print(f"\n   Valeurs communes a toutes les tables: {sorted(valeurs_communes)}")
            
            # Valeurs uniques par table
            for table_name, valeurs in valeurs_par_table.items():
                autres_tables = [v for k, v in valeurs_par_table.items() if k != table_name]
                if autres_tables:
                    valeurs_uniques = valeurs - set.union(*autres_tables)
                    if valeurs_uniques:
                        print(f"   Valeurs uniques a {table_name}: {sorted(valeurs_uniques)}")

print("\n" + "=" * 80)
print("RECHERCHE TERMINEE")
print("=" * 80)
