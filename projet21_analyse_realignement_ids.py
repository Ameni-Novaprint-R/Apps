#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projet 21 - Analyse de faisabilité du réalignement des IDs
Analyse technique approfondie pour PAPIERS_ARTICLES et PAPIERS_IMPRIMEURS

Objectif: Évaluer si le réalignement des identifiants (ID) de ces tables
vers les identifiants de référence de la base Novaprint est techniquement
possible sans risque de perte de données ni de rupture d'intégrité référentielle.
"""

import pyodbc
from collections import defaultdict
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

def get_connection(config, readonly=True):
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

def get_primary_key_info(cursor, table_name):
    """Récupère les informations sur la clé primaire d'une table"""
    cursor.execute("""
        SELECT 
            c.name AS column_name,
            t.name AS data_type,
            c.max_length,
            c.precision,
            c.scale,
            c.is_identity,
            CAST(ISNULL(id_col.seed_value, 0) AS bigint) AS seed_value,
            CAST(ISNULL(id_col.increment_value, 0) AS bigint) AS increment_value
        FROM sys.tables AS tbl
        INNER JOIN sys.indexes AS idx ON tbl.object_id = idx.object_id AND idx.is_primary_key = 1
        INNER JOIN sys.index_columns AS ic ON idx.object_id = ic.object_id AND idx.index_id = ic.index_id
        INNER JOIN sys.columns AS c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        INNER JOIN sys.types AS t ON c.user_type_id = t.user_type_id
        LEFT JOIN sys.identity_columns AS id_col ON c.object_id = id_col.object_id AND c.column_id = id_col.column_id
        WHERE tbl.name = ?
        ORDER BY ic.key_ordinal
    """, (table_name,))
    
    pk_info = []
    for row in cursor.fetchall():
        pk_info.append({
            'column_name': row.column_name,
            'data_type': row.data_type,
            'max_length': row.max_length,
            'precision': row.precision,
            'scale': row.scale,
            'is_identity': bool(row.is_identity),
            'seed_value': int(row.seed_value) if row.seed_value is not None else 0,
            'increment_value': int(row.increment_value) if row.increment_value is not None else 0
        })
    return pk_info

def get_direct_foreign_keys_outgoing(cursor, table_name):
    """Récupère les FK sortantes (tables référencées par cette table)"""
    cursor.execute("""
        SELECT DISTINCT
            fk.name AS FK_Name,
            tr.name AS Referenced_Table,
            cp.name AS Parent_Column,
            cr.name AS Referenced_Column,
            fk.is_disabled,
            fk.is_not_trusted,
            fk.delete_referential_action,
            fk.update_referential_action
        FROM sys.foreign_keys AS fk
        INNER JOIN sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
        INNER JOIN sys.tables AS tp ON fkc.parent_object_id = tp.object_id
        INNER JOIN sys.columns AS cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
        INNER JOIN sys.tables AS tr ON fkc.referenced_object_id = tr.object_id
        INNER JOIN sys.columns AS cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
        WHERE tp.name = ?
        ORDER BY tr.name, fk.name
    """, (table_name,))
    
    fks = []
    for row in cursor.fetchall():
        fks.append({
            'fk_name': row.FK_Name,
            'referenced_table': row.Referenced_Table,
            'parent_column': row.Parent_Column,
            'referenced_column': row.Referenced_Column,
            'is_disabled': row.is_disabled,
            'is_not_trusted': row.is_not_trusted,
            'delete_action': row.delete_referential_action,
            'update_action': row.update_referential_action
        })
    return fks

def get_direct_foreign_keys_incoming(cursor, table_name):
    """Récupère les FK entrantes (tables qui référencent cette table)"""
    cursor.execute("""
        SELECT DISTINCT
            fk.name AS FK_Name,
            tp.name AS Parent_Table,
            cp.name AS Parent_Column,
            cr.name AS Referenced_Column,
            fk.is_disabled,
            fk.is_not_trusted,
            fk.delete_referential_action,
            fk.update_referential_action
        FROM sys.foreign_keys AS fk
        INNER JOIN sys.foreign_key_columns AS fkc ON fk.object_id = fkc.constraint_object_id
        INNER JOIN sys.tables AS tp ON fkc.parent_object_id = tp.object_id
        INNER JOIN sys.columns AS cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
        INNER JOIN sys.tables AS tr ON fkc.referenced_object_id = tr.object_id
        INNER JOIN sys.columns AS cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
        WHERE tr.name = ?
        ORDER BY tp.name, fk.name
    """, (table_name,))
    
    fks = []
    for row in cursor.fetchall():
        fks.append({
            'fk_name': row.FK_Name,
            'parent_table': row.Parent_Table,
            'parent_column': row.Parent_Column,
            'referenced_column': row.Referenced_Column,
            'is_disabled': row.is_disabled,
            'is_not_trusted': row.is_not_trusted,
            'delete_action': row.delete_referential_action,
            'update_action': row.update_referential_action
        })
    return fks

def get_table_row_count(cursor, table_name):
    """Récupère le nombre de lignes d'une table"""
    try:
        cursor.execute(f"SELECT COUNT(*) AS cnt FROM [{table_name}]")
        row = cursor.fetchone()
        return row.cnt if row else 0
    except Exception as e:
        return None

def analyze_id_overlap(cursor, source_table, target_table, pk_column):
    """Analyse les chevauchements d'IDs entre source et cible"""
    try:
        # IDs dans la source (Novaprint)
        cursor.execute(f"SELECT DISTINCT [{pk_column}] FROM [{source_table}] ORDER BY [{pk_column}]")
        source_ids = set(row[0] for row in cursor.fetchall())
        
        # IDs dans la cible (novaprint_restored)
        cursor.execute(f"SELECT DISTINCT [{pk_column}] FROM [{target_table}] ORDER BY [{pk_column}]")
        target_ids = set(row[0] for row in cursor.fetchall())
        
        overlap = source_ids & target_ids
        source_only = source_ids - target_ids
        target_only = target_ids - source_ids
        
        return {
            'source_count': len(source_ids),
            'target_count': len(target_ids),
            'overlap_count': len(overlap),
            'source_only_count': len(source_only),
            'target_only_count': len(target_only),
            'overlap_percentage': (len(overlap) / len(target_ids) * 100) if target_ids else 0
        }
    except Exception as e:
        return {'error': str(e)}

def analyze_fk_references(cursor, table_name, pk_column, fk_tables):
    """Analyse les références FK vers cette table"""
    results = {}
    
    for fk_info in fk_tables:
        parent_table = fk_info['parent_table']
        parent_column = fk_info['parent_column']
        
        try:
            # Compter les références distinctes
            cursor.execute(f"""
                SELECT COUNT(DISTINCT [{parent_column}]) AS distinct_refs,
                       COUNT(*) AS total_refs
                FROM [{parent_table}]
                WHERE [{parent_column}] IS NOT NULL
            """)
            row = cursor.fetchone()
            
            # Vérifier les valeurs orphelines (références vers des IDs inexistants)
            cursor.execute(f"""
                SELECT COUNT(*) AS orphan_count
                FROM [{parent_table}] p
                LEFT JOIN [{table_name}] t ON p.[{parent_column}] = t.[{pk_column}]
                WHERE p.[{parent_column}] IS NOT NULL AND t.[{pk_column}] IS NULL
            """)
            orphan_row = cursor.fetchone()
            
            results[parent_table] = {
                'fk_name': fk_info['fk_name'],
                'parent_column': parent_column,
                'distinct_references': row.distinct_refs if row else 0,
                'total_references': row.total_refs if row else 0,
                'orphan_references': orphan_row.orphan_count if orphan_row else 0,
                'update_action': fk_info['update_action'],
                'delete_action': fk_info['delete_action']
            }
        except Exception as e:
            results[parent_table] = {'error': str(e)}
    
    return results

def generate_analysis_report(table_name, source_conn, target_conn):
    """Génère un rapport d'analyse complet pour une table"""
    print(f"\n{'='*80}")
    print(f"ANALYSE: {table_name}")
    print(f"{'='*80}\n")
    
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    report = {
        'table_name': table_name,
        'analysis_date': datetime.now().isoformat(),
        'primary_key': {},
        'direct_relations': {
            'outgoing': [],
            'incoming': []
        },
        'data_analysis': {},
        'risk_assessment': {},
        'feasibility': {}
    }
    
    # 1. Analyse de la clé primaire
    print("1. ANALYSE DE LA CLÉ PRIMAIRE")
    print("-" * 80)
    pk_info = get_primary_key_info(target_cursor, table_name)
    if pk_info:
        pk_col = pk_info[0]['column_name']
        report['primary_key'] = {
            'column': pk_col,
            'is_identity': pk_info[0]['is_identity'],
            'data_type': pk_info[0]['data_type'],
            'seed_value': pk_info[0]['seed_value'],
            'increment_value': pk_info[0]['increment_value']
        }
        print(f"   Colonne PK: {pk_col}")
        print(f"   Type: {pk_info[0]['data_type']}")
        print(f"   Identity: {'Oui' if pk_info[0]['is_identity'] else 'Non'}")
        if pk_info[0]['is_identity']:
            print(f"   Seed: {pk_info[0]['seed_value']}, Increment: {pk_info[0]['increment_value']}")
    else:
        print("   [ATTENTION] Aucune cle primaire trouvee!")
        return None
    
    # 2. Analyse des relations directes
    print(f"\n2. RELATIONS DIRECTES")
    print("-" * 80)
    
    # FK sortantes (tables référencées)
    outgoing_fks = get_direct_foreign_keys_outgoing(target_cursor, table_name)
    report['direct_relations']['outgoing'] = outgoing_fks
    print(f"   FK Sortantes (tables référencées): {len(outgoing_fks)}")
    for fk in outgoing_fks:
        print(f"      -> {fk['referenced_table']} via {fk['fk_name']} ({fk['parent_column']} -> {fk['referenced_column']})")
    
    # FK entrantes (tables qui référencent)
    incoming_fks = get_direct_foreign_keys_incoming(target_cursor, table_name)
    report['direct_relations']['incoming'] = incoming_fks
    print(f"   FK Entrantes (tables référencent): {len(incoming_fks)}")
    for fk in incoming_fks:
        print(f"      <- {fk['parent_table']} via {fk['fk_name']} ({fk['parent_column']} -> {fk['referenced_column']})")
    
    total_direct_relations = len(outgoing_fks) + len(incoming_fks)
    print(f"\n   TOTAL RELATIONS DIRECTES: {total_direct_relations}")
    
    # 3. Analyse des données
    print(f"\n3. ANALYSE DES DONNÉES")
    print("-" * 80)
    
    # Nombre de lignes
    source_count = get_table_row_count(source_cursor, table_name)
    target_count = get_table_row_count(target_cursor, table_name)
    print(f"   Lignes dans Novaprint (source): {source_count:,}" if source_count is not None else "   Lignes dans Novaprint (source): N/A")
    print(f"   Lignes dans novaprint_restored (cible): {target_count:,}" if target_count is not None else "   Lignes dans novaprint_restored (cible): N/A")
    
    # Analyse des chevauchements d'IDs
    print(f"\n   Analyse des chevauchements d'IDs:")
    id_overlap = analyze_id_overlap(source_cursor, table_name, table_name, pk_col)
    if 'error' not in id_overlap:
        report['data_analysis']['id_overlap'] = id_overlap
        print(f"      IDs dans source: {id_overlap['source_count']:,}")
        print(f"      IDs dans cible: {id_overlap['target_count']:,}")
        print(f"      Chevauchement: {id_overlap['overlap_count']:,} ({id_overlap['overlap_percentage']:.2f}%)")
        print(f"      Uniquement source: {id_overlap['source_only_count']:,}")
        print(f"      Uniquement cible: {id_overlap['target_only_count']:,}")
    
    # Analyse des références FK entrantes
    if incoming_fks:
        print(f"\n   Analyse des références FK entrantes:")
        fk_refs = analyze_fk_references(target_cursor, table_name, pk_col, incoming_fks)
        report['data_analysis']['fk_references'] = fk_refs
        for ref_table, ref_info in fk_refs.items():
            if 'error' not in ref_info:
                print(f"      {ref_table}:")
                print(f"         Références distinctes: {ref_info['distinct_references']:,}")
                print(f"         Total références: {ref_info['total_references']:,}")
                print(f"         Références orphelines: {ref_info['orphan_references']:,}")
                print(f"         Action UPDATE: {ref_info['update_action']}")
                print(f"         Action DELETE: {ref_info['delete_action']}")
    
    # 4. Évaluation des risques
    print(f"\n4. ÉVALUATION DES RISQUES")
    print("-" * 80)
    
    risks = []
    warnings = []
    safe_points = []
    
    # Risque 1: Nombre de relations directes
    if total_direct_relations > 3:
        risks.append({
            'level': 'HIGH',
            'category': 'Complexité des relations',
            'description': f'Nombre de relations directes ({total_direct_relations}) dépasse le seuil recommandé (3)',
            'impact': 'Augmente la complexité et les risques de rupture d\'intégrité'
        })
        print(f"   [ATTENTION] RISQUE ELEVE: {total_direct_relations} relations directes (> 3)")
    else:
        safe_points.append({
            'category': 'Complexité des relations',
            'description': f'Nombre de relations directes ({total_direct_relations}) <= 3',
            'impact': 'Complexité gérable pour le réalignement'
        })
        print(f"   [OK] Complexite acceptable: {total_direct_relations} relations directes")
    
    # Risque 2: Chevauchement d'IDs
    if 'id_overlap' in report['data_analysis']:
        overlap = report['data_analysis']['id_overlap']
        if overlap['overlap_percentage'] < 50:
            risks.append({
                'level': 'MEDIUM',
                'category': 'Chevauchement d\'IDs',
                'description': f'Seulement {overlap["overlap_percentage"]:.2f}% de chevauchement',
                'impact': 'Beaucoup d\'IDs à réassigner, risque de conflits'
            })
            print(f"   ⚠️  RISQUE MOYEN: Chevauchement faible ({overlap['overlap_percentage']:.2f}%)")
        elif overlap['target_only_count'] > 0:
            risks.append({
                'level': 'HIGH',
                'category': 'IDs uniques en cible',
                'description': f'{overlap["target_only_count"]:,} IDs existent uniquement en cible',
                'impact': 'Ces IDs doivent être préservés ou réassignés sans conflit'
            })
            print(f"   [ATTENTION] RISQUE ELEVE: {overlap['target_only_count']:,} IDs uniques en cible")
        else:
            safe_points.append({
                'category': 'Chevauchement d\'IDs',
                'description': f'Chevauchement élevé ({overlap["overlap_percentage"]:.2f}%)',
                'impact': 'La plupart des IDs correspondent déjà'
            })
            print(f"   [OK] Chevauchement acceptable: {overlap['overlap_percentage']:.2f}%")
    
    # Risque 3: Références FK entrantes
    if 'fk_references' in report['data_analysis']:
        for ref_table, ref_info in report['data_analysis']['fk_references'].items():
            if 'error' not in ref_info:
                if ref_info['orphan_references'] > 0:
                    warnings.append({
                        'level': 'MEDIUM',
                        'category': 'Intégrité référentielle',
                        'description': f'{ref_info["orphan_references"]:,} références orphelines dans {ref_table}',
                        'impact': 'Données incohérentes existantes'
                    })
                    print(f"   [ATTENTION] AVERTISSEMENT: {ref_info['orphan_references']:,} references orphelines dans {ref_table}")
                
                if ref_info['update_action'] != 1:  # 1 = NO ACTION
                    risks.append({
                        'level': 'HIGH',
                        'category': 'Action CASCADE',
                        'description': f'Action UPDATE CASCADE détectée sur FK {ref_info["fk_name"]}',
                        'impact': 'Modification des IDs propagera automatiquement aux tables enfants'
                    })
                    print(f"   [ATTENTION] RISQUE ELEVE: Action UPDATE CASCADE sur {ref_info['fk_name']}")
                else:
                    safe_points.append({
                        'category': 'Action FK',
                        'description': f'Pas d\'action CASCADE sur {ref_info["fk_name"]}',
                        'impact': 'Contrôle manuel possible'
                    })
    
    # Risque 4: Identity column
    if report['primary_key']['is_identity']:
        risks.append({
            'level': 'MEDIUM',
            'category': 'Colonne Identity',
            'description': 'La clé primaire est une colonne IDENTITY',
            'impact': 'Nécessite de désactiver IDENTITY pendant le réalignement'
        })
        print(f"   [ATTENTION] RISQUE MOYEN: Colonne IDENTITY detectee")
    else:
        safe_points.append({
            'category': 'Type de PK',
            'description': 'PK n\'est pas IDENTITY',
            'impact': 'Plus facile à modifier'
        })
        print(f"   [OK] PK n'est pas IDENTITY")
    
    report['risk_assessment'] = {
        'risks': risks,
        'warnings': warnings,
        'safe_points': safe_points
    }
    
    # 5. Faisabilité
    print(f"\n5. FAISABILITÉ TECHNIQUE")
    print("-" * 80)
    
    feasibility = {
        'technically_possible': True,
        'safety_level': 'UNKNOWN',
        'recommendations': []
    }
    
    # Critères de faisabilité
    if total_direct_relations <= 3:
        feasibility['recommendations'].append('[OK] Nombre de relations directes acceptable (<= 3)')
    else:
        feasibility['technically_possible'] = False
        feasibility['recommendations'].append('✗ Trop de relations directes (> 3)')
    
    if len(risks) == 0:
        feasibility['safety_level'] = 'SAFE'
        feasibility['recommendations'].append('✓ Aucun risque majeur identifié')
    elif len([r for r in risks if r['level'] == 'HIGH']) == 0:
        feasibility['safety_level'] = 'MODERATE'
        feasibility['recommendations'].append('[ATTENTION] Risques moderes identifies')
    else:
        feasibility['safety_level'] = 'RISKY'
        feasibility['recommendations'].append('[NON] Risques eleves identifies')
    
    # Recommandations spécifiques
    if report['primary_key']['is_identity']:
        feasibility['recommendations'].append('-> Desactiver IDENTITY avant realignement')
        feasibility['recommendations'].append('-> Reactiver IDENTITY apres realignement avec nouvelle seed')
    
    if 'fk_references' in report['data_analysis']:
        for ref_table, ref_info in report['data_analysis']['fk_references'].items():
            if 'error' not in ref_info and ref_info['total_references'] > 0:
                feasibility['recommendations'].append(f'-> Mettre a jour {ref_info["total_references"]:,} references dans {ref_table}')
    
    feasibility['recommendations'].append('-> Effectuer une sauvegarde complete avant toute operation')
    feasibility['recommendations'].append('-> Tester sur un environnement de developpement d\'abord')
    feasibility['recommendations'].append('-> Utiliser des transactions avec rollback possible')
    
    report['feasibility'] = feasibility
    
    # Affichage de la conclusion
    print(f"\n   Techniquement possible: {'OUI' if feasibility['technically_possible'] else 'NON'}")
    print(f"   Niveau de sécurité: {feasibility['safety_level']}")
    print(f"\n   Recommandations:")
    for rec in feasibility['recommendations']:
        print(f"      {rec}")
    
    source_cursor.close()
    target_cursor.close()
    
    return report

def main():
    """Fonction principale"""
    print("="*80)
    print("ANALYSE DE FAISABILITÉ DU RÉALIGNEMENT DES IDs")
    print("Tables: PAPIERS_ARTICLES et PAPIERS_IMPRIMEURS")
    print("="*80)
    
    try:
        # Connexions
        print("\nConnexion aux bases de données...")
        source_conn = get_connection(SOURCE_CONFIG, readonly=True)
        print("[OK] Connexion a Novaprint (source) etablie")
        
        target_conn = get_connection(TARGET_CONFIG, readonly=True)
        print("[OK] Connexion a novaprint_restored (cible) etablie")
        
        # Analyse des deux tables
        reports = []
        
        for table_name in ['PAPIERS_ARTICLES', 'PAPIERS_IMPRIMEURS']:
            report = generate_analysis_report(table_name, source_conn, target_conn)
            if report:
                reports.append(report)
        
        # Synthèse globale
        print(f"\n{'='*80}")
        print("SYNTHÈSE GLOBALE")
        print(f"{'='*80}\n")
        
        total_relations = sum(
            len(r['direct_relations']['outgoing']) + len(r['direct_relations']['incoming'])
            for r in reports
        )
        
        print(f"Total relations directes (toutes tables): {total_relations}")
        
        all_risks = []
        for r in reports:
            all_risks.extend(r['risk_assessment']['risks'])
        
        high_risks = [r for r in all_risks if r['level'] == 'HIGH']
        medium_risks = [r for r in all_risks if r['level'] == 'MEDIUM']
        
        print(f"\nRisques identifiés:")
        print(f"   Élevés: {len(high_risks)}")
        print(f"   Moyens: {len(medium_risks)}")
        
        # Conclusion finale
        print(f"\n{'='*80}")
        print("CONCLUSION")
        print(f"{'='*80}\n")
        
        if all(r['feasibility']['technically_possible'] for r in reports):
            if all(r['feasibility']['safety_level'] == 'SAFE' for r in reports):
                print("[OK] OPERATION SURE")
                print("\nLe realignement des IDs est techniquement possible et sur.")
                print("Les deux tables ont <= 3 relations directes et aucun risque majeur n'a ete identifie.")
            elif any(r['feasibility']['safety_level'] == 'RISKY' for r in reports):
                print("[ATTENTION] OPERATION RISQUEE")
                print("\nLe realignement est techniquement possible mais presente des risques eleves.")
                print("Une planification minutieuse et des tests approfondis sont essentiels.")
            else:
                print("[ATTENTION] OPERATION MODEREMENT SURE")
                print("\nLe realignement est techniquement possible avec des precautions.")
        else:
            print("[NON] OPERATION NON RECOMMANDEE")
            print("\nLe realignement presente trop de risques ou de complexite.")
        
        # Sauvegarde du rapport JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"projet21_analyse_realignement_ids_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'analysis_date': datetime.now().isoformat(),
                'tables_analyzed': [r['table_name'] for r in reports],
                'reports': reports,
                'summary': {
                    'total_direct_relations': total_relations,
                    'high_risks_count': len(high_risks),
                    'medium_risks_count': len(medium_risks),
                    'feasible': all(r['feasibility']['technically_possible'] for r in reports)
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\nRapport détaillé sauvegardé: {filename}")
        
        source_conn.close()
        target_conn.close()
        
    except Exception as e:
        print(f"\n[ERREUR] ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
