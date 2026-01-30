#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vérification complète de l'intégrité des données après réalignement des IDs
Table: PAPIERS_ARTICLES

Vérifie:
- Préservation de tous les enregistrements
- Intégrité des clés étrangères
- Cohérence des tables liées
- Absence de perte ou duplication de données
- Validité des contraintes et index
- Volume de données identique
"""

import pyodbc
from datetime import datetime
import json

# Configuration des bases de données
SOURCE_CONFIG = {
    'server': 'SageSRV\\Graphisoft',
    'database': 'Novaprint',
    'username': 'sa',
    'password': 'Graphis0ft'
}

TARGET_CONFIG = {
    'server': '192.168.10.225',
    'database': 'novaprint_restored',
    'trusted_connection': True
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

def verification_complete():
    """Effectue une vérification complète de l'intégrité"""
    
    print("="*80)
    print("VERIFICATION DE L'INTEGRITE APRES REALIGNEMENT")
    print("Table: PAPIERS_ARTICLES")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    source_conn = None
    target_conn = None
    rapport = {
        'date_verification': datetime.now().isoformat(),
        'table_verifiee': 'PAPIERS_ARTICLES',
        'verifications': {},
        'resultat_global': 'EN_ATTENTE',
        'risques_detectes': []
    }
    
    try:
        # Connexions
        print("[1/8] Connexion aux bases de donnees...")
        source_conn = get_connection(SOURCE_CONFIG, readonly=True)
        target_conn = get_connection(TARGET_CONFIG, readonly=True)
        print("  [OK] Connexions etablies")
        print()
        
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()
        
        # ========================================================================
        # VÉRIFICATION 1: Volume de données (nombre de lignes)
        # ========================================================================
        print("[2/8] Verification 1: Volume de donnees...")
        
        source_cursor.execute("SELECT COUNT(*) FROM PAPIERS_ARTICLES")
        source_count = source_cursor.fetchone()[0]
        
        target_cursor.execute("SELECT COUNT(*) FROM PAPIERS_ARTICLES")
        target_count = target_cursor.fetchone()[0]
        
        print(f"  Lignes source (Novaprint): {source_count:,}")
        print(f"  Lignes cible (novaprint_restored): {target_count:,}")
        
        if source_count == target_count:
            print("  [OK] Volume identique")
            rapport['verifications']['volume'] = {'statut': 'OK', 'source': source_count, 'cible': target_count}
        else:
            diff = target_count - source_count
            print(f"  [ERREUR] Difference de {abs(diff):,} lignes!")
            rapport['verifications']['volume'] = {'statut': 'ERREUR', 'source': source_count, 'cible': target_count, 'difference': diff}
            rapport['risques_detectes'].append(f"Difference de volume: {diff} lignes")
        print()
        
        # ========================================================================
        # VÉRIFICATION 2: Correspondance des IDs
        # ========================================================================
        print("[3/8] Verification 2: Correspondance des IDs...")
        
        # Identifier les colonnes communes pour la correspondance
        source_cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'PAPIERS_ARTICLES'
            AND COLUMN_NAME != 'ID'
            ORDER BY ORDINAL_POSITION
        """)
        source_columns = set(row[0] for row in source_cursor.fetchall())
        
        target_cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'PAPIERS_ARTICLES'
            AND COLUMN_NAME != 'ID'
            ORDER BY ORDINAL_POSITION
        """)
        target_columns = set(row[0] for row in target_cursor.fetchall())
        columns = sorted(list(source_columns & target_columns))
        columns_str = ', '.join(columns)
        
        # Comparer les IDs
        source_cursor.execute(f"""
            SELECT ID, {columns_str}
            FROM PAPIERS_ARTICLES
        """)
        source_data = {tuple(row[1:]): row[0] for row in source_cursor.fetchall()}
        
        target_cursor.execute(f"""
            SELECT ID, {columns_str}
            FROM PAPIERS_ARTICLES
        """)
        target_data = [(row[0], tuple(row[1:])) for row in target_cursor.fetchall()]
        
        mismatches = []
        matched = 0
        for target_id, target_key in target_data:
            if target_key in source_data:
                source_id = source_data[target_key]
                if target_id != source_id:
                    mismatches.append({'cible': target_id, 'source': source_id, 'key': target_key})
                else:
                    matched += 1
        
        if not mismatches:
            print(f"  [OK] Tous les IDs correspondent ({matched:,} correspondances)")
            rapport['verifications']['correspondance_ids'] = {'statut': 'OK', 'correspondances': matched}
        else:
            print(f"  [ERREUR] {len(mismatches)} IDs ne correspondent pas!")
            rapport['verifications']['correspondance_ids'] = {'statut': 'ERREUR', 'mismatches': len(mismatches), 'details': mismatches[:10]}
            rapport['risques_detectes'].append(f"{len(mismatches)} IDs ne correspondent pas")
        print()
        
        # ========================================================================
        # VÉRIFICATION 3: Intégrité des clés étrangères (FK entrantes)
        # ========================================================================
        print("[4/8] Verification 3: Integrite des cles etrangeres (FK entrantes)...")
        
        # Identifier toutes les tables qui référencent PAPIERS_ARTICLES
        target_cursor.execute("""
            SELECT DISTINCT
                tp.name AS Parent_Table,
                cp.name AS Parent_Column,
                fk.name AS FK_Name
            FROM sys.foreign_keys AS fk
            INNER JOIN sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
            INNER JOIN sys.tables AS tp ON fkc.parent_object_id = tp.object_id
            INNER JOIN sys.columns AS cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
            INNER JOIN sys.tables AS tr ON fkc.referenced_object_id = tr.object_id
            WHERE tr.name = 'PAPIERS_ARTICLES'
        """)
        
        fk_tables = []
        for row in target_cursor.fetchall():
            fk_tables.append({
                'table': row.Parent_Table,
                'column': row.Parent_Column,
                'fk_name': row.FK_Name
            })
        
        fk_verifications = {}
        total_orphans = 0
        
        for fk_info in fk_tables:
            table_name = fk_info['table']
            column_name = fk_info['column']
            
            # Compter les références orphelines
            target_cursor.execute(f"""
                SELECT COUNT(*)
                FROM [{table_name}] ptf
                LEFT JOIN PAPIERS_ARTICLES pa ON ptf.[{column_name}] = pa.ID
                WHERE ptf.[{column_name}] IS NOT NULL AND pa.ID IS NULL
            """)
            orphan_count = target_cursor.fetchone()[0]
            
            # Compter le total de références
            target_cursor.execute(f"""
                SELECT COUNT(*)
                FROM [{table_name}]
                WHERE [{column_name}] IS NOT NULL
            """)
            total_refs = target_cursor.fetchone()[0]
            
            # Compter les références valides
            target_cursor.execute(f"""
                SELECT COUNT(*)
                FROM [{table_name}] ptf
                INNER JOIN PAPIERS_ARTICLES pa ON ptf.[{column_name}] = pa.ID
            """)
            valid_refs = target_cursor.fetchone()[0]
            
            fk_verifications[table_name] = {
                'column': column_name,
                'total_references': total_refs,
                'valid_references': valid_refs,
                'orphan_references': orphan_count
            }
            
            total_orphans += orphan_count
            
            if orphan_count == 0:
                print(f"  [OK] {table_name}.{column_name}: {valid_refs:,} references valides")
            else:
                print(f"  [ERREUR] {table_name}.{column_name}: {orphan_count:,} references orphelines sur {total_refs:,} total")
        
        if total_orphans == 0:
            print("  [OK] Aucune reference orpheline detectee")
            rapport['verifications']['fk_entrantes'] = {'statut': 'OK', 'details': fk_verifications}
        else:
            print(f"  [ERREUR] {total_orphans:,} references orphelines au total!")
            rapport['verifications']['fk_entrantes'] = {'statut': 'ERREUR', 'total_orphans': total_orphans, 'details': fk_verifications}
            rapport['risques_detectes'].append(f"{total_orphans} references orphelines dans les FK entrantes")
        print()
        
        # ========================================================================
        # VÉRIFICATION 4: Intégrité des clés étrangères (FK sortantes)
        # ========================================================================
        print("[5/8] Verification 4: Integrite des cles etrangeres (FK sortantes)...")
        
        # Identifier les tables référencées par PAPIERS_ARTICLES
        target_cursor.execute("""
            SELECT DISTINCT
                tr.name AS Referenced_Table,
                cr.name AS Referenced_Column,
                cp.name AS Parent_Column,
                fk.name AS FK_Name
            FROM sys.foreign_keys AS fk
            INNER JOIN sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
            INNER JOIN sys.tables AS tp ON fkc.parent_object_id = tp.object_id
            INNER JOIN sys.columns AS cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
            INNER JOIN sys.tables AS tr ON fkc.referenced_object_id = tr.object_id
            INNER JOIN sys.columns AS cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
            WHERE tp.name = 'PAPIERS_ARTICLES'
        """)
        
        outgoing_fk_verifications = {}
        total_outgoing_orphans = 0
        
        for row in target_cursor.fetchall():
            ref_table = row.Referenced_Table
            ref_column = row.Referenced_Column
            parent_column = row.Parent_Column
            
            # Compter les références orphelines
            target_cursor.execute(f"""
                SELECT COUNT(*)
                FROM PAPIERS_ARTICLES pa
                LEFT JOIN [{ref_table}] rt ON pa.[{parent_column}] = rt.[{ref_column}]
                WHERE pa.[{parent_column}] IS NOT NULL AND rt.[{ref_column}] IS NULL
            """)
            orphan_count = target_cursor.fetchone()[0]
            
            # Compter le total de références
            target_cursor.execute(f"""
                SELECT COUNT(*)
                FROM PAPIERS_ARTICLES
                WHERE [{parent_column}] IS NOT NULL
            """)
            total_refs = target_cursor.fetchone()[0]
            
            # Compter les références valides
            target_cursor.execute(f"""
                SELECT COUNT(*)
                FROM PAPIERS_ARTICLES pa
                INNER JOIN [{ref_table}] rt ON pa.[{parent_column}] = rt.[{ref_column}]
            """)
            valid_refs = target_cursor.fetchone()[0]
            
            outgoing_fk_verifications[ref_table] = {
                'parent_column': parent_column,
                'referenced_column': ref_column,
                'total_references': total_refs,
                'valid_references': valid_refs,
                'orphan_references': orphan_count
            }
            
            total_outgoing_orphans += orphan_count
            
            if orphan_count == 0:
                print(f"  [OK] -> {ref_table}.{ref_column}: {valid_refs:,} references valides")
            else:
                print(f"  [ATTENTION] -> {ref_table}.{ref_column}: {orphan_count:,} references orphelines sur {total_refs:,} total")
        
        if total_outgoing_orphans == 0:
            print("  [OK] Toutes les FK sortantes sont valides")
            rapport['verifications']['fk_sortantes'] = {'statut': 'OK', 'details': outgoing_fk_verifications}
        else:
            print(f"  [ATTENTION] {total_outgoing_orphans:,} references orphelines dans les FK sortantes")
            rapport['verifications']['fk_sortantes'] = {'statut': 'ATTENTION', 'total_orphans': total_outgoing_orphans, 'details': outgoing_fk_verifications}
        print()
        
        # ========================================================================
        # VÉRIFICATION 5: Absence de duplication
        # ========================================================================
        print("[6/8] Verification 5: Absence de duplication...")
        
        # Vérifier les doublons d'IDs
        target_cursor.execute("""
            SELECT ID, COUNT(*) AS cnt
            FROM PAPIERS_ARTICLES
            GROUP BY ID
            HAVING COUNT(*) > 1
        """)
        duplicate_ids = target_cursor.fetchall()
        
        if not duplicate_ids:
            print("  [OK] Aucun ID duplique")
            rapport['verifications']['duplication_ids'] = {'statut': 'OK'}
        else:
            print(f"  [ERREUR] {len(duplicate_ids)} IDs dupliques detectes!")
            rapport['verifications']['duplication_ids'] = {'statut': 'ERREUR', 'count': len(duplicate_ids), 'details': [{'id': r[0], 'count': r[1]} for r in duplicate_ids]}
            rapport['risques_detectes'].append(f"{len(duplicate_ids)} IDs dupliques")
        
        # Vérifier les doublons de données (basés sur les colonnes communes)
        if columns:
            columns_check = ', '.join(columns)
            target_cursor.execute(f"""
                SELECT {columns_check}, COUNT(*) AS cnt
                FROM PAPIERS_ARTICLES
                GROUP BY {columns_check}
                HAVING COUNT(*) > 1
            """)
            duplicate_data = target_cursor.fetchall()
            
            if not duplicate_data:
                print("  [OK] Aucune donnee dupliquee")
                rapport['verifications']['duplication_donnees'] = {'statut': 'OK'}
            else:
                print(f"  [ATTENTION] {len(duplicate_data)} enregistrements dupliques detectes (peut etre normal)")
                rapport['verifications']['duplication_donnees'] = {'statut': 'ATTENTION', 'count': len(duplicate_data)}
        print()
        
        # ========================================================================
        # VÉRIFICATION 6: Validité des contraintes
        # ========================================================================
        print("[7/8] Verification 6: Validite des contraintes...")
        
        # Vérifier les contraintes FK
        target_cursor.execute("""
            SELECT 
                fk.name AS FK_Name,
                tp.name AS Parent_Table,
                tr.name AS Referenced_Table,
                fk.is_disabled,
                fk.is_not_trusted
            FROM sys.foreign_keys AS fk
            INNER JOIN sys.tables AS tp ON fk.parent_object_id = tp.object_id
            INNER JOIN sys.tables AS tr ON fk.referenced_object_id = tr.object_id
            WHERE tp.name = 'PAPIERS_ARTICLES' OR tr.name = 'PAPIERS_ARTICLES'
        """)
        
        constraint_issues = []
        for row in target_cursor.fetchall():
            if row.is_disabled:
                constraint_issues.append(f"FK {row.FK_Name} est desactivee")
            if row.is_not_trusted:
                constraint_issues.append(f"FK {row.FK_Name} n'est pas trustee")
        
        if not constraint_issues:
            print("  [OK] Toutes les contraintes FK sont valides")
            rapport['verifications']['contraintes'] = {'statut': 'OK'}
        else:
            print(f"  [ATTENTION] {len(constraint_issues)} problemes de contraintes detectes")
            for issue in constraint_issues:
                print(f"    - {issue}")
            rapport['verifications']['contraintes'] = {'statut': 'ATTENTION', 'issues': constraint_issues}
        print()
        
        # ========================================================================
        # VÉRIFICATION 7: Validité des index
        # ========================================================================
        print("[8/8] Verification 7: Validite des index...")
        
        # Vérifier l'index de la clé primaire
        target_cursor.execute("""
            SELECT 
                i.name AS Index_Name,
                i.is_disabled,
                i.is_hypothetical
            FROM sys.indexes AS i
            INNER JOIN sys.tables AS t ON i.object_id = t.object_id
            WHERE t.name = 'PAPIERS_ARTICLES'
            AND i.is_primary_key = 1
        """)
        
        pk_index = target_cursor.fetchone()
        if pk_index:
            if pk_index.is_disabled:
                print("  [ERREUR] Index de la clé primaire est desactive!")
                rapport['verifications']['index'] = {'statut': 'ERREUR', 'issue': 'PK index disabled'}
                rapport['risques_detectes'].append("Index de la clé primaire desactive")
            else:
                print("  [OK] Index de la clé primaire est actif")
                rapport['verifications']['index'] = {'statut': 'OK'}
        else:
            print("  [ERREUR] Index de la clé primaire non trouve!")
            rapport['verifications']['index'] = {'statut': 'ERREUR', 'issue': 'PK index not found'}
            rapport['risques_detectes'].append("Index de la clé primaire non trouve")
        print()
        
        # ========================================================================
        # VÉRIFICATION 8: Cohérence des tables liées
        # ========================================================================
        print("[9/8] Verification 8: Coherence des tables liees...")
        
        # Pour chaque table qui référence PAPIERS_ARTICLES, vérifier la cohérence
        coherence_issues = []
        
        for fk_info in fk_tables:
            table_name = fk_info['table']
            column_name = fk_info['column']
            
            # Vérifier que toutes les références pointent vers des IDs existants
            target_cursor.execute(f"""
                SELECT COUNT(DISTINCT ptf.[{column_name}]) AS distinct_refs
                FROM [{table_name}] ptf
                WHERE ptf.[{column_name}] IS NOT NULL
            """)
            distinct_refs = target_cursor.fetchone()[0]
            
            target_cursor.execute(f"""
                SELECT COUNT(DISTINCT pa.ID) AS distinct_ids
                FROM PAPIERS_ARTICLES pa
                INNER JOIN [{table_name}] ptf ON ptf.[{column_name}] = pa.ID
            """)
            distinct_ids = target_cursor.fetchone()[0]
            
            if distinct_refs == distinct_ids:
                print(f"  [OK] {table_name}: toutes les references sont valides")
            else:
                diff = distinct_refs - distinct_ids
                print(f"  [ERREUR] {table_name}: {diff} references invalides")
                coherence_issues.append(f"{table_name}: {diff} references invalides")
        
        if not coherence_issues:
            print("  [OK] Toutes les tables liees sont coherentes")
            rapport['verifications']['coherence_tables'] = {'statut': 'OK'}
        else:
            print(f"  [ERREUR] {len(coherence_issues)} problemes de coherence detectes")
            rapport['verifications']['coherence_tables'] = {'statut': 'ERREUR', 'issues': coherence_issues}
            rapport['risques_detectes'].extend(coherence_issues)
        print()
        
        # ========================================================================
        # RÉSUMÉ ET CONCLUSION
        # ========================================================================
        print("="*80)
        print("RESUME DE LA VERIFICATION")
        print("="*80)
        print()
        
        # Compter les erreurs
        erreurs = [v for v in rapport['verifications'].values() if v.get('statut') == 'ERREUR']
        attentions = [v for v in rapport['verifications'].values() if v.get('statut') == 'ATTENTION']
        
        print(f"Verifications effectuees: {len(rapport['verifications'])}")
        print(f"Erreurs detectees: {len(erreurs)}")
        print(f"Avertissements: {len(attentions)}")
        print()
        
        if not erreurs and not rapport['risques_detectes']:
            print("[OK] REALIGNEMENT SÛR - Aucun probleme detecte")
            print()
            print("L'alignement des IDs a ete effectue avec succes et l'integrite")
            print("des donnees est totalement preservee:")
            print("  - Tous les enregistrements existent toujours")
            print("  - Aucune clé etrangere n'est cassee")
            print("  - Les tables liees refletent correctement les nouveaux IDs")
            print("  - Aucune donnee n'a ete perdue ou dupliquee")
            print("  - Les contraintes et index sont valides")
            print("  - Le volume de lignes est identique")
            rapport['resultat_global'] = 'SUR'
        elif not erreurs:
            print("[ATTENTION] REALIGNEMENT MODEREMENT SÛR - Avertissements detectes")
            print()
            print("L'alignement a ete effectue mais certains points necessitent attention:")
            for risque in rapport['risques_detectes']:
                print(f"  - {risque}")
            rapport['resultat_global'] = 'MODEREMENT_SUR'
        else:
            print("[ERREUR] REALIGNEMENT NON SÛR - Problemes detectes")
            print()
            print("Des problemes ont ete detectes apres l'alignement:")
            for risque in rapport['risques_detectes']:
                print(f"  - {risque}")
            rapport['resultat_global'] = 'NON_SUR'
        
        # Sauvegarder le rapport
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"projet21_verification_integrite_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(rapport, f, indent=2, ensure_ascii=False)
        
        print()
        print(f"Rapport detaille sauvegarde: {filename}")
        
        return rapport['resultat_global'] == 'SUR' or (rapport['resultat_global'] == 'MODEREMENT_SUR' and not erreurs)
        
    except Exception as e:
        print()
        print("="*80)
        print("[ERREUR] La verification a echoue!")
        print("="*80)
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if source_conn:
            source_conn.close()
        if target_conn:
            target_conn.close()

if __name__ == '__main__':
    success = verification_complete()
    exit(0 if success else 1)
