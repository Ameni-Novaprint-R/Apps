#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'analyse pour comprendre pourquoi PAPIERS_ARTICLES et PAPIERS_IMPRIMEURS
ne se synchronisent pas correctement dans le Projet 21
"""

import pyodbc
from datetime import datetime

SOURCE_CONFIG = {
    'server': 'SageSRV\\Graphisoft',
    'database': 'Novaprint',
    'username': 'sa',
    'password': 'Graphis0ft'
}

TARGET_CONFIG = {
    'server': '192.168.10.225',
    'database': 'novaprint_restored',
    'username': 'sa',
    'password': 'bA8ALvct9QtX',
    'trusted_connection': False
}

def get_connection(config, readonly=False):
    """Connexion SQL Server"""
    if config.get('trusted_connection'):
        driver_candidates = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"]
        last_err = None
        conn = None
        for drv in driver_candidates:
            try:
                conn_str = (
                    f"DRIVER={{{drv}}};"
                    f"SERVER={config['server']};"
                    f"DATABASE={config['database']};"
                    f"Trusted_Connection=yes;"
                    f"TrustServerCertificate=yes"
                )
                conn = pyodbc.connect(conn_str)
                break
            except Exception as e:
                last_err = e
                conn = None
        if conn is None:
            raise last_err
    else:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={config['server']};"
            f"DATABASE={config['database']};"
            f"UID={config['username']};"
            f"PWD={config['password']}"
        )
        conn = pyodbc.connect(conn_str)
    if readonly:
        conn.execute("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
    return conn

def get_primary_keys(cursor, table_name):
    """Récupère les colonnes de clé primaire"""
    cursor.execute("""
        SELECT c.name
        FROM sys.indexes i
        INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        INNER JOIN sys.tables t ON i.object_id = t.object_id
        WHERE i.is_primary_key = 1
        AND t.name = ?
        ORDER BY ic.key_ordinal
    """, (table_name,))
    result = [row[0] for row in cursor.fetchall()]
    if not result:
        cursor.execute("""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = ? AND COLUMN_NAME = 'ID'
        """, (table_name,))
        row = cursor.fetchone()
        if row:
            return [row[0]]
    return result

def get_foreign_keys(cursor, table_name):
    """Récupère les contraintes FK d'une table"""
    cursor.execute("""
        SELECT 
            fk.name AS FK_Name,
            tp.name AS Parent_Table,
            cp.name AS Parent_Column,
            tr.name AS Referenced_Table,
            cr.name AS Referenced_Column,
            fk.is_disabled,
            fk.is_not_trusted
        FROM sys.foreign_keys AS fk
        INNER JOIN sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
        INNER JOIN sys.tables AS tp ON fkc.parent_object_id = tp.object_id
        INNER JOIN sys.columns AS cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
        INNER JOIN sys.tables AS tr ON fkc.referenced_object_id = tr.object_id
        INNER JOIN sys.columns AS cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
        WHERE tp.name = ?
    """, (table_name,))
    return cursor.fetchall()

def analyze_table_sync(table_name):
    """Analyse la synchronisation d'une table spécifique"""
    print(f"\n{'='*80}")
    print(f"ANALYSE DE LA TABLE: {table_name}")
    print(f"{'='*80}")
    
    source_conn = get_connection(SOURCE_CONFIG, readonly=True)
    source_cursor = source_conn.cursor()
    target_conn = get_connection(TARGET_CONFIG)
    target_cursor = target_conn.cursor()
    
    try:
        # 1. Vérifier l'existence des tables
        print(f"\n1. VÉRIFICATION D'EXISTENCE:")
        source_cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
        """, (table_name,))
        source_exists = source_cursor.fetchone()[0] > 0
        
        target_cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
        """, (table_name,))
        target_exists = target_cursor.fetchone()[0] > 0
        
        source_status = "EXISTE" if source_exists else "N'EXISTE PAS"
        target_status = "EXISTE" if target_exists else "N'EXISTE PAS"
        print(f"   Source (Novaprint): {source_status}")
        print(f"   Cible (novaprint_restored): {target_status}")
        
        if not source_exists:
            print(f"   ATTENTION: Table absente de la source - ne peut pas etre synchronisee")
            return
        if not target_exists:
            print(f"   ATTENTION: Table absente de la cible - doit etre creee lors de la synchronisation")
            return
        
        # 2. Compter les enregistrements
        print(f"\n2. COMPTAGE DES ENREGISTREMENTS:")
        source_cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
        source_count = source_cursor.fetchone()[0]
        
        target_cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
        target_count = target_cursor.fetchone()[0]
        
        print(f"   Source: {source_count:,} enregistrements")
        print(f"   Cible: {target_count:,} enregistrements")
        print(f"   Écart: {source_count - target_count:,} enregistrements")
        
        if source_count == target_count:
            print(f"   OK: Les comptes correspondent")
        else:
            print(f"   ATTENTION: ECART DETECTE: {abs(source_count - target_count):,} enregistrements")
        
        # 3. Comparer par clé primaire
        print(f"\n3. COMPARAISON PAR CLÉ PRIMAIRE:")
        pk_columns = get_primary_keys(source_cursor, table_name)
        
        if not pk_columns:
            print(f"   ATTENTION: Pas de cle primaire detectee")
            pk_columns = ['ID']  # Fallback
        
        print(f"   Clé primaire: {', '.join(pk_columns)}")
        
        pk_list = ", ".join([f"[{pk}]" for pk in pk_columns])
        
        # Récupérer les PKs de la source
        source_cursor.execute(f"SELECT {pk_list} FROM [{table_name}]")
        source_pks = set()
        for row in source_cursor.fetchall():
            if len(pk_columns) == 1:
                source_pks.add(row[0])
            else:
                source_pks.add(tuple(row))
        
        # Récupérer les PKs de la cible
        target_cursor.execute(f"SELECT {pk_list} FROM [{table_name}]")
        target_pks = set()
        for row in target_cursor.fetchall():
            if len(pk_columns) == 1:
                target_pks.add(row[0])
            else:
                target_pks.add(tuple(row))
        
        missing_pks = source_pks - target_pks
        extra_pks = target_pks - source_pks
        
        print(f"   Source: {len(source_pks):,} clés primaires")
        print(f"   Cible: {len(target_pks):,} clés primaires")
        print(f"   Manquantes dans cible: {len(missing_pks):,}")
        print(f"   Supplémentaires dans cible: {len(extra_pks):,}")
        
        if missing_pks:
            print(f"\n   Exemples de clés manquantes (max 10):")
            for i, pk in enumerate(list(missing_pks)[:10]):
                print(f"     - {pk}")
        
        # 4. Analyser les clés étrangères
        print(f"\n4. ANALYSE DES CLÉS ÉTRANGÈRES:")
        fks = get_foreign_keys(source_cursor, table_name)
        
        if not fks:
            print(f"   OK: Aucune cle etrangere")
        else:
            print(f"   {len(fks)} clé(s) étrangère(s) trouvée(s):")
            for fk in fks:
                fk_name, parent_table, parent_col, ref_table, ref_col, is_disabled, is_not_trusted = fk
                print(f"\n   FK: {fk_name}")
                print(f"      Colonne: {parent_col} -> {ref_table}.{ref_col}")
                print(f"      Désactivée: {'Oui' if is_disabled else 'Non'}")
                print(f"      Non vérifiée: {'Oui' if is_not_trusted else 'Non'}")
                
                # Vérifier si la table référencée existe dans la cible
                target_cursor.execute("""
                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = ? AND TABLE_TYPE = 'BASE TABLE'
                """, (ref_table,))
                ref_exists = target_cursor.fetchone()[0] > 0
                
                if not ref_exists:
                    print(f"      ATTENTION: Table referencee '{ref_table}' N'EXISTE PAS dans la cible")
                else:
                    # Compter les valeurs FK dans la source
                    source_cursor.execute(f"""
                        SELECT COUNT(DISTINCT [{parent_col}]) 
                        FROM [{table_name}] 
                        WHERE [{parent_col}] IS NOT NULL
                    """)
                    source_fk_count = source_cursor.fetchone()[0]
                    
                    # Compter les valeurs FK valides dans la cible
                    target_cursor.execute(f"""
                        SELECT COUNT(DISTINCT [{parent_col}]) 
                        FROM [{table_name}] 
                        WHERE [{parent_col}] IS NOT NULL
                        AND [{parent_col}] IN (SELECT [{ref_col}] FROM [{ref_table}])
                    """)
                    valid_fk_count = target_cursor.fetchone()[0]
                    
                    # Trouver les valeurs FK invalides
                    source_cursor.execute(f"""
                        SELECT DISTINCT [{parent_col}]
                        FROM [{table_name}]
                        WHERE [{parent_col}] IS NOT NULL
                    """)
                    source_fk_values = {row[0] for row in source_cursor.fetchall()}
                    
                    target_cursor.execute(f"SELECT DISTINCT [{ref_col}] FROM [{ref_table}]")
                    valid_fk_values = {row[0] for row in target_cursor.fetchall()}
                    
                    invalid_fk_values = source_fk_values - valid_fk_values
                    
                    print(f"      Valeurs FK dans source: {source_fk_count}")
                    print(f"      Valeurs FK valides dans cible: {valid_fk_count}")
                    print(f"      Valeurs FK invalides: {len(invalid_fk_values)}")
                    
                    if invalid_fk_values:
                        print(f"      ATTENTION: PROBLEME DETECTE: {len(invalid_fk_values)} valeur(s) FK invalide(s)")
                        print(f"      Exemples de valeurs FK invalides (max 10):")
                        for i, val in enumerate(list(invalid_fk_values)[:10]):
                            print(f"        - {val}")
        
        # 5. Vérifier les contraintes dans la cible
        print(f"\n5. ÉTAT DES CONTRAINTES DANS LA CIBLE:")
        target_fks = get_foreign_keys(target_cursor, table_name)
        
        if not target_fks:
            print(f"   OK: Aucune contrainte FK dans la cible")
        else:
            for fk in target_fks:
                fk_name, parent_table, parent_col, ref_table, ref_col, is_disabled, is_not_trusted = fk
                status = []
                if is_disabled:
                    status.append("DÉSACTIVÉE")
                if is_not_trusted:
                    status.append("NON VÉRIFIÉE")
                if not status:
                    status.append("ACTIVE")
                
                print(f"   {fk_name}: {', '.join(status)}")
        
        # 6. Analyser les enregistrements manquants
        if missing_pks:
            print(f"\n6. ANALYSE DES ENREGISTREMENTS MANQUANTS:")
            print(f"   Analyse de {min(5, len(missing_pks))} enregistrement(s) manquant(s)...")
            
            source_cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
            columns = [desc[0] for desc in source_cursor.description]
            
            for i, missing_pk in enumerate(list(missing_pks)[:5]):
                print(f"\n   Enregistrement {i+1} (PK: {missing_pk}):")
                
                # Récupérer l'enregistrement source
                if len(pk_columns) == 1:
                    where_clause = f"[{pk_columns[0]}] = ?"
                    source_cursor.execute(f"SELECT * FROM [{table_name}] WHERE {where_clause}", (missing_pk,))
                else:
                    where_parts = [f"[{pk}] = ?" for pk in pk_columns]
                    where_clause = " AND ".join(where_parts)
                    source_cursor.execute(f"SELECT * FROM [{table_name}] WHERE {where_clause}", missing_pk)
                
                source_row = source_cursor.fetchone()
                if source_row:
                    row_dict = {columns[j]: source_row[j] for j in range(len(columns))}
                    
                    # Vérifier les FK de cet enregistrement
                    for fk in fks:
                        fk_name, parent_table, parent_col, ref_table, ref_col, is_disabled, is_not_trusted = fk
                        if parent_col in row_dict:
                            fk_value = row_dict[parent_col]
                            if fk_value is not None:
                                # Vérifier si la valeur FK existe dans la cible
                                target_cursor.execute(f"""
                                    SELECT COUNT(*) FROM [{ref_table}] WHERE [{ref_col}] = ?
                                """, (fk_value,))
                                fk_exists = target_cursor.fetchone()[0] > 0
                                
                                if not fk_exists:
                                    print(f"      ATTENTION: FK '{parent_col}' = {fk_value} -> '{ref_table}.{ref_col}' N'EXISTE PAS dans la cible")
                                else:
                                    print(f"      OK: FK '{parent_col}' = {fk_value} -> '{ref_table}.{ref_col}' existe")
        
    except Exception as e:
        print(f"\nERREUR lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()
    finally:
        source_conn.close()
        target_conn.close()

if __name__ == '__main__':
    print("="*80)
    print("ANALYSE DE SYNCHRONISATION - PAPIERS_ARTICLES et PAPIERS_IMPRIMEURS")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    for table_name in ['PAPIERS_ARTICLES', 'PAPIERS_IMPRIMEURS']:
        analyze_table_sync(table_name)
    
    print(f"\n{'='*80}")
    print("ANALYSE TERMINÉE")
    print(f"{'='*80}")
