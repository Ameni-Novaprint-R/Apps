#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Projet 21 - Analyse du schéma de la base de données
Génère un rapport détaillé listant toutes les tables ayant une relation
directe ou indirecte avec PAPIERS_ARTICLES et PAPIERS_IMPRIMEURS
"""

import pyodbc
from collections import defaultdict, deque
from datetime import datetime
import json

# Configuration de la base de données cible
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

def get_all_foreign_keys(cursor):
    """Récupère toutes les clés étrangères de la base de données"""
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
        INNER JOIN sys.columns AS cp ON fkc.parent_object_id = cp.object_id 
            AND fkc.parent_column_id = cp.column_id
        INNER JOIN sys.tables AS tr ON fkc.referenced_object_id = tr.object_id
        INNER JOIN sys.columns AS cr ON fkc.referenced_object_id = cr.object_id 
            AND fkc.referenced_column_id = cr.column_id
        ORDER BY tp.name, fk.name, fkc.constraint_column_id
    """)
    
    fk_dict = defaultdict(list)
    for row in cursor.fetchall():
        parent_table = row.Parent_Table
        referenced_table = row.Referenced_Table
        fk_info = {
            'fk_name': row.FK_Name,
            'parent_column': row.Parent_Column,
            'referenced_column': row.Referenced_Column,
            'is_disabled': row.is_disabled,
            'is_not_trusted': row.is_not_trusted
        }
        fk_dict[parent_table].append({
            'referenced_table': referenced_table,
            'details': fk_info
        })
    
    return fk_dict

def build_reverse_fk_graph(fk_dict):
    """Construit un graphe inversé: table -> tables qui la référencent"""
    reverse_graph = defaultdict(set)
    for parent_table, fks in fk_dict.items():
        for fk in fks:
            referenced_table = fk['referenced_table']
            reverse_graph[referenced_table].add(parent_table)
    return reverse_graph

def find_all_related_tables(start_tables, fk_dict, reverse_graph):
    """
    Trouve toutes les tables liées directement ou indirectement aux tables de départ
    Utilise BFS pour parcourir le graphe de dépendances
    """
    related_tables = set()
    visited = set()
    queue = deque()
    
    # Initialiser avec les tables de départ
    for table in start_tables:
        if table not in visited:
            visited.add(table)
            queue.append((table, 0, 'start'))  # (table, niveau, type_relation)
            related_tables.add(table)
    
    # Parcourir les tables qui référencent les tables de départ (enfants)
    for table in start_tables:
        if table in reverse_graph:
            for child_table in reverse_graph[table]:
                if child_table not in visited:
                    visited.add(child_table)
                    queue.append((child_table, 1, 'child'))
                    related_tables.add(child_table)
    
    # Parcourir les tables référencées par les tables de départ (parents)
    for table in start_tables:
        if table in fk_dict:
            for fk in fk_dict[table]:
                parent_table = fk['referenced_table']
                if parent_table not in visited:
                    visited.add(parent_table)
                    queue.append((parent_table, 1, 'parent'))
                    related_tables.add(parent_table)
    
    # BFS pour trouver toutes les relations indirectes
    while queue:
        current_table, level, relation_type = queue.popleft()
        
        # Trouver les enfants (tables qui référencent cette table)
        if current_table in reverse_graph:
            for child_table in reverse_graph[current_table]:
                if child_table not in visited:
                    visited.add(child_table)
                    queue.append((child_table, level + 1, 'child'))
                    related_tables.add(child_table)
        
        # Trouver les parents (tables référencées par cette table)
        if current_table in fk_dict:
            for fk in fk_dict[current_table]:
                parent_table = fk['referenced_table']
                if parent_table not in visited:
                    visited.add(parent_table)
                    queue.append((parent_table, level + 1, 'parent'))
                    related_tables.add(parent_table)
    
    return related_tables

def get_table_info(cursor, table_name):
    """Récupère les informations sur une table"""
    cursor.execute("""
        SELECT 
            COUNT(*) AS row_count
        FROM INFORMATION_SCHEMA.TABLES t
        WHERE t.TABLE_NAME = ? AND t.TABLE_TYPE = 'BASE TABLE'
    """, (table_name,))
    
    exists = cursor.fetchone()
    if not exists:
        return None
    
    # Compter les lignes (peut être lent sur grandes tables)
    try:
        cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
        row_count = cursor.fetchone()[0]
    except:
        row_count = "N/A"
    
    # Récupérer les colonnes
    cursor.execute("""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """, (table_name,))
    
    columns = []
    for row in cursor.fetchall():
        columns.append({
            'name': row.COLUMN_NAME,
            'type': row.DATA_TYPE,
            'nullable': row.IS_NULLABLE,
            'default': row.COLUMN_DEFAULT
        })
    
    return {
        'row_count': row_count,
        'columns': columns
    }

def generate_report(start_tables, fk_dict, reverse_graph, cursor):
    """Génère le rapport détaillé"""
    print("=" * 80)
    print("RAPPORT D'ANALYSE DU SCHÉMA - RELATIONS AVEC PAPIERS_ARTICLES ET PAPIERS_IMPRIMEURS")
    print("=" * 80)
    print(f"\nDate de génération: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nTables de départ: {', '.join(start_tables)}")
    print("\n" + "=" * 80)
    
    # Trouver toutes les tables liées
    related_tables = find_all_related_tables(start_tables, fk_dict, reverse_graph)
    
    print(f"\n📊 RÉSUMÉ")
    print(f"   - Nombre total de tables liées: {len(related_tables)}")
    print(f"   - Tables de départ: {len(start_tables)}")
    print(f"   - Tables liées (directement ou indirectement): {len(related_tables) - len(start_tables)}")
    
    # Séparer les tables par type de relation
    direct_children = set()
    direct_parents = set()
    indirect_related = set()
    
    for table in related_tables:
        if table in start_tables:
            continue
        
        is_direct_child = False
        is_direct_parent = False
        
        # Vérifier si c'est un enfant direct
        for start_table in start_tables:
            if start_table in reverse_graph and table in reverse_graph[start_table]:
                is_direct_child = True
                direct_children.add(table)
                break
        
        # Vérifier si c'est un parent direct
        for start_table in start_tables:
            if start_table in fk_dict:
                for fk in fk_dict[start_table]:
                    if fk['referenced_table'] == table:
                        is_direct_parent = True
                        direct_parents.add(table)
                        break
                if is_direct_parent:
                    break
        
        if not is_direct_child and not is_direct_parent:
            indirect_related.add(table)
    
    print(f"\n   - Tables enfants directes (référencent les tables de départ): {len(direct_children)}")
    print(f"   - Tables parents directes (référencées par les tables de départ): {len(direct_parents)}")
    print(f"   - Tables liées indirectement: {len(indirect_related)}")
    
    # Détails par table de départ
    for start_table in start_tables:
        print(f"\n" + "=" * 80)
        print(f"📋 TABLE: {start_table}")
        print("=" * 80)
        
        # Informations sur la table
        table_info = get_table_info(cursor, start_table)
        if table_info:
            print(f"\n   Informations:")
            print(f"   - Nombre de lignes: {table_info['row_count']}")
            print(f"   - Nombre de colonnes: {len(table_info['columns'])}")
        
        # Tables enfants (qui référencent cette table)
        children = []
        if start_table in reverse_graph:
            children = list(reverse_graph[start_table])
        
        if children:
            print(f"\n   🔗 Tables ENFANTS (référencent {start_table}):")
            for child in sorted(children):
                print(f"      - {child}")
                # Détails de la FK
                if child in fk_dict:
                    for fk in fk_dict[child]:
                        if fk['referenced_table'] == start_table:
                            print(f"        FK: {fk['details']['fk_name']}")
                            print(f"        Colonnes: {fk['details']['parent_column']} -> {fk['details']['referenced_column']}")
                            if fk['details']['is_disabled']:
                                print(f"        ⚠️  FK désactivée")
                            if fk['details']['is_not_trusted']:
                                print(f"        ⚠️  FK non vérifiée")
        else:
            print(f"\n   🔗 Tables ENFANTS: Aucune")
        
        # Tables parents (référencées par cette table)
        parents = []
        if start_table in fk_dict:
            for fk in fk_dict[start_table]:
                if fk['referenced_table'] not in parents:
                    parents.append(fk['referenced_table'])
        
        if parents:
            print(f"\n   🔗 Tables PARENTS (référencées par {start_table}):")
            for parent in sorted(parents):
                print(f"      - {parent}")
                # Détails de la FK
                for fk in fk_dict[start_table]:
                    if fk['referenced_table'] == parent:
                        print(f"        FK: {fk['details']['fk_name']}")
                        print(f"        Colonnes: {fk['details']['parent_column']} -> {fk['details']['referenced_column']}")
                        if fk['details']['is_disabled']:
                            print(f"        ⚠️  FK désactivée")
                        if fk['details']['is_not_trusted']:
                            print(f"        ⚠️  FK non vérifiée")
        else:
            print(f"\n   🔗 Tables PARENTS: Aucune")
    
    # Liste complète des tables liées
    print(f"\n" + "=" * 80)
    print(f"📋 LISTE COMPLÈTE DES TABLES LIÉES")
    print("=" * 80)
    
    all_related_sorted = sorted(related_tables)
    for i, table in enumerate(all_related_sorted, 1):
        relation_type = []
        if table in start_tables:
            relation_type.append("TABLE DE DÉPART")
        if table in direct_children:
            relation_type.append("ENFANT DIRECT")
        if table in direct_parents:
            relation_type.append("PARENT DIRECT")
        if table in indirect_related:
            relation_type.append("LIÉE INDIRECTEMENT")
        
        print(f"\n{i}. {table}")
        print(f"   Type: {', '.join(relation_type)}")
        
        # Informations sur la table
        table_info = get_table_info(cursor, table)
        if table_info:
            print(f"   Lignes: {table_info['row_count']}")
            print(f"   Colonnes: {len(table_info['columns'])}")
    
    # Générer un fichier JSON pour export
    report_data = {
        'generation_date': datetime.now().isoformat(),
        'start_tables': list(start_tables),
        'summary': {
            'total_related_tables': len(related_tables),
            'direct_children_count': len(direct_children),
            'direct_parents_count': len(direct_parents),
            'indirect_related_count': len(indirect_related)
        },
        'tables': {}
    }
    
    for table in all_related_sorted:
        table_info = get_table_info(cursor, table)
        relation_type = []
        if table in start_tables:
            relation_type.append("start")
        if table in direct_children:
            relation_type.append("direct_child")
        if table in direct_parents:
            relation_type.append("direct_parent")
        if table in indirect_related:
            relation_type.append("indirect")
        
        # Trouver les relations FK
        fk_relations = []
        if table in fk_dict:
            for fk in fk_dict[table]:
                fk_relations.append({
                    'type': 'references',
                    'referenced_table': fk['referenced_table'],
                    'fk_name': fk['details']['fk_name'],
                    'parent_column': fk['details']['parent_column'],
                    'referenced_column': fk['details']['referenced_column']
                })
        
        if table in reverse_graph:
            for child_table in reverse_graph[table]:
                fk_relations.append({
                    'type': 'referenced_by',
                    'referencing_table': child_table
                })
        
        report_data['tables'][table] = {
            'relation_types': relation_type,
            'row_count': table_info['row_count'] if table_info else None,
            'column_count': len(table_info['columns']) if table_info else None,
            'columns': table_info['columns'] if table_info else [],
            'foreign_key_relations': fk_relations
        }
    
    # Sauvegarder le rapport JSON
    json_filename = f"projet21_rapport_schema_papiers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n" + "=" * 80)
    print(f"✅ Rapport JSON généré: {json_filename}")
    print("=" * 80)

def main():
    """Fonction principale"""
    try:
        print("Connexion à la base de données...")
        conn = get_connection(TARGET_CONFIG, readonly=True)
        cursor = conn.cursor()
        
        print("Récupération des clés étrangères...")
        fk_dict = get_all_foreign_keys(cursor)
        
        print("Construction du graphe de dépendances...")
        reverse_graph = build_reverse_fk_graph(fk_dict)
        
        # Tables de départ
        start_tables = ['PAPIERS_ARTICLES', 'PAPIERS_IMPRIMEURS']
        
        # Vérifier que les tables existent
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME IN (?, ?) AND TABLE_TYPE = 'BASE TABLE'
        """, start_tables[0], start_tables[1])
        
        existing_tables = [row.TABLE_NAME for row in cursor.fetchall()]
        missing_tables = [t for t in start_tables if t not in existing_tables]
        
        if missing_tables:
            print(f"\n⚠️  ATTENTION: Les tables suivantes n'existent pas: {', '.join(missing_tables)}")
            start_tables = [t for t in start_tables if t in existing_tables]
        
        if not start_tables:
            print("\n❌ Aucune table de départ trouvée. Arrêt.")
            return
        
        print(f"\nTables de départ trouvées: {', '.join(start_tables)}")
        
        # Générer le rapport
        generate_report(start_tables, fk_dict, reverse_graph, cursor)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
