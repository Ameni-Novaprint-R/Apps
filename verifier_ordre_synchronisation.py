#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Vérifier l'ordre de synchronisation des tables IMPRIMEURS et PAPIERS_IMPRIMEURS
"""

def get_connection(config, readonly=False):
    import pyodbc
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

def get_foreign_keys(cursor, table_name):
    """Récupère les contraintes FK d'une table"""
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
        INNER JOIN sys.columns AS cp ON fkc.parent_object_id = cp.object_id 
            AND fkc.parent_column_id = cp.column_id
        INNER JOIN sys.tables AS tr ON fkc.referenced_object_id = tr.object_id
        INNER JOIN sys.columns AS cr ON fkc.referenced_object_id = cr.object_id 
            AND fkc.referenced_column_id = cr.column_id
        WHERE tp.name = ?
        ORDER BY fk.name, fkc.constraint_column_id
    """, table_name)
    
    return cursor.fetchall()

def build_dependency_graph(source_cursor, target_cursor, tables):
    """Construit le graphe de dépendances FK"""
    dependency_graph = {table: [] for table in tables}
    referenced_tables = set()
    
    for table in tables:
        try:
            fks = get_foreign_keys(target_cursor, table)
            for fk_row in fks:
                ref_table = fk_row.Referenced_Table
                if ref_table in tables:
                    dependency_graph[table].append(ref_table)
                    referenced_tables.add(ref_table)
        except Exception:
            pass
    
    return dependency_graph, referenced_tables

def topological_sort(tables, dependency_graph):
    """Tri topologique pour déterminer l'ordre de synchronisation"""
    graph = {table: list(deps) for table, deps in dependency_graph.items()}
    out_degree = {table: len(graph.get(table, [])) for table in tables}
    in_degree = {table: 0 for table in tables}
    for table in tables:
        for dep in graph.get(table, []):
            if dep in in_degree:
                in_degree[dep] += 1
    
    queue = [table for table in tables if out_degree[table] == 0]
    result = []
    processed = set()
    
    while queue:
        queue.sort()
        current = queue.pop(0)
        if current in processed:
            continue
        result.append(current)
        processed.add(current)
        
        for table in tables:
            if current in graph.get(table, []):
                out_degree[table] -= 1
                if out_degree[table] == 0 and table not in processed:
                    queue.append(table)
    
    remaining = [table for table in tables if table not in processed]
    if remaining:
        remaining.sort(key=lambda t: (out_degree[t], t))
        result.extend(remaining)
    
    return result

def main():
    print("=" * 80)
    print("VERIFICATION ORDRE DE SYNCHRONISATION")
    print("=" * 80)
    print()
    
    source_conn = get_connection(SOURCE_CONFIG, readonly=True)
    source_cursor = source_conn.cursor()
    target_conn = get_connection(TARGET_CONFIG, readonly=True)
    target_cursor = target_conn.cursor()
    
    try:
        # Récupérer toutes les tables
        source_cursor.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        source_tables = [row.TABLE_NAME for row in source_cursor.fetchall()]
        
        print(f"Nombre total de tables: {len(source_tables)}")
        print()
        
        # Construire le graphe de dépendances
        print("[1] Construction du graphe de dependances...")
        dependency_graph, referenced_tables = build_dependency_graph(source_cursor, target_cursor, source_tables)
        
        # Vérifier les dépendances de PAPIERS_IMPRIMEURS
        print("[2] Verification des dependances de PAPIERS_IMPRIMEURS...")
        if 'PAPIERS_IMPRIMEURS' in dependency_graph:
            deps = dependency_graph['PAPIERS_IMPRIMEURS']
            print(f"  Tables dont PAPIERS_IMPRIMEURS depend: {deps}")
            if 'IMPRIMEURS' in deps:
                print("  ✓ PAPIERS_IMPRIMEURS depend de IMPRIMEURS")
            else:
                print("  ✗ PAPIERS_IMPRIMEURS NE depend PAS de IMPRIMEURS")
        print()
        
        # Vérifier les dépendances de IMPRIMEURS
        print("[3] Verification des dependances de IMPRIMEURS...")
        if 'IMPRIMEURS' in dependency_graph:
            deps = dependency_graph['IMPRIMEURS']
            print(f"  Tables dont IMPRIMEURS depend: {deps}")
            if len(deps) == 0:
                print("  ✓ IMPRIMEURS n'a pas de dependances (sera synchronise en premier)")
        print()
        
        # Vérifier les FK de PAPIERS_IMPRIMEURS
        print("[4] Verification des FK de PAPIERS_IMPRIMEURS...")
        fks = get_foreign_keys(target_cursor, 'PAPIERS_IMPRIMEURS')
        print(f"  Nombre de FK: {len(fks)}")
        for fk in fks:
            print(f"    - {fk.Parent_Column} -> {fk.Referenced_Table}.{fk.Referenced_Column}")
        print()
        
        # Trier topologiquement
        print("[5] Tri topologique...")
        sorted_tables = topological_sort(source_tables, dependency_graph)
        
        # Trouver les positions de IMPRIMEURS et PAPIERS_IMPRIMEURS
        if 'IMPRIMEURS' in sorted_tables:
            idx_imprimeurs = sorted_tables.index('IMPRIMEURS')
            print(f"  Position de IMPRIMEURS: {idx_imprimeurs + 1}/{len(sorted_tables)}")
        else:
            print("  ✗ IMPRIMEURS non trouve dans la liste triee")
        
        if 'PAPIERS_IMPRIMEURS' in sorted_tables:
            idx_papiers_imprimeurs = sorted_tables.index('PAPIERS_IMPRIMEURS')
            print(f"  Position de PAPIERS_IMPRIMEURS: {idx_papiers_imprimeurs + 1}/{len(sorted_tables)}")
        else:
            print("  ✗ PAPIERS_IMPRIMEURS non trouve dans la liste triee")
        
        if 'IMPRIMEURS' in sorted_tables and 'PAPIERS_IMPRIMEURS' in sorted_tables:
            if idx_imprimeurs < idx_papiers_imprimeurs:
                print("  ✓ IMPRIMEURS est synchronise AVANT PAPIERS_IMPRIMEURS")
            else:
                print("  ✗ IMPRIMEURS est synchronise APRES PAPIERS_IMPRIMEURS")
                print("  ⚠️ C'est le probleme !")
        
        print()
        print("=" * 80)
        print("CONCLUSION")
        print("=" * 80)
        if 'IMPRIMEURS' in sorted_tables and 'PAPIERS_IMPRIMEURS' in sorted_tables:
            if idx_imprimeurs < idx_papiers_imprimeurs:
                print("✓ L'ordre de synchronisation est correct")
                print("  Le probleme vient d'ailleurs dans la logique de verification FK")
            else:
                print("❌ L'ordre de synchronisation est incorrect")
                print("  IMPRIMEURS doit etre synchronise avant PAPIERS_IMPRIMEURS")
        
    finally:
        source_conn.close()
        target_conn.close()

if __name__ == "__main__":
    main()
