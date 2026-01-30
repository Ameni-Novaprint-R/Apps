"""
Script de vérification de la synchronisation
Compare les comptes de toutes les tables entre source et cible
"""

import pyodbc

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
    """
    Connexion SQL Server pour la vérification.

    Important: éviter le driver legacy "{SQL Server}" côté cible, car il déclenche
    des erreurs HYC00 sur certains types.
    """
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
    """Récupère les colonnes de clé primaire d'une table"""
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
        # Fallback: chercher colonne ID
        cursor.execute("""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = ? AND COLUMN_NAME = 'ID'
        """, (table_name,))
        row = cursor.fetchone()
        if row:
            return [row[0]]
    return result

def compare_table_records(source_cursor, target_cursor, table_name):
    """Compare les enregistrements réels par clé primaire"""
    try:
        # Récupérer les clés primaires
        pk_columns = get_primary_keys(source_cursor, table_name)
        
        if not pk_columns:
            # Pas de PK, utiliser toutes les colonnes
            source_cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
            columns = [desc[0] for desc in source_cursor.description]
            pk_columns = columns
        
        # Récupérer les PKs de la source
        pk_list = ", ".join([f"[{pk}]" for pk in pk_columns])
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
        
        # Enregistrements manquants dans la cible
        missing = source_pks - target_pks
        # Enregistrements supplémentaires dans la cible (OK)
        extra = target_pks - source_pks
        
        return {
            'source_count': len(source_pks),
            'target_count': len(target_pks),
            'missing_count': len(missing),
            'extra_count': len(extra),
            'missing_pks': list(missing)[:10] if missing else []  # Limiter à 10 exemples
        }
    except Exception as e:
        return {'error': str(e)}

def verify_sync():
    source_conn = get_connection(SOURCE_CONFIG, readonly=True)
    source_cursor = source_conn.cursor()
    target_conn = get_connection(TARGET_CONFIG)
    target_cursor = target_conn.cursor()
    
    # Récupérer toutes les tables source
    source_cursor.execute("""
        SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """)
    source_tables = [row.TABLE_NAME for row in source_cursor.fetchall()]
    
    # Récupérer toutes les tables cible
    target_cursor.execute("""
        SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """)
    target_tables = [row.TABLE_NAME for row in target_cursor.fetchall()]
    
    results = {
        'synchronisees': [],
        'ecarts_critiques': [],  # Enregistrements manquants dans la cible
        'ecarts_normaux': [],    # Plus de données dans la cible (OK)
        'manquantes_cible': [],
        'manquantes_source': []
    }
    
    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append("VÉRIFICATION DE LA SYNCHRONISATION")
    output_lines.append("=" * 80)
    output_lines.append(f"\nTables source: {len(source_tables)}")
    output_lines.append(f"Tables cible: {len(target_tables)}")
    output_lines.append("\n" + "=" * 80)
    
    # Vérifier les tables communes - comparaison par clé primaire
    for table_name in source_tables:
        try:
            if table_name in target_tables:
                # Comparaison réelle par clé primaire
                comparison = compare_table_records(source_cursor, target_cursor, table_name)
                
                if 'error' in comparison:
                    output_lines.append(f"Erreur sur {table_name}: {comparison['error']}")
                    continue
                
                source_count = comparison['source_count']
                target_count = comparison['target_count']
                missing_count = comparison['missing_count']
                extra_count = comparison['extra_count']
                
                if missing_count == 0:
                    # Tous les enregistrements source sont présents
                    if extra_count > 0:
                        # Des données supplémentaires dans la cible (OK)
                        results['ecarts_normaux'].append((table_name, source_count, target_count, extra_count))
                    else:
                        # Parfaitement synchronisé
                        results['synchronisees'].append((table_name, source_count))
                else:
                    # Enregistrements manquants = CRITIQUE
                    results['ecarts_critiques'].append((
                        table_name, 
                        source_count, 
                        target_count, 
                        missing_count,
                        comparison.get('missing_pks', [])
                    ))
            else:
                # Table manquante dans la cible
                source_cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
                source_count = source_cursor.fetchone()[0]
                results['manquantes_cible'].append((table_name, source_count))
        except Exception as e:
            output_lines.append(f"Erreur sur {table_name}: {e}")
    
    # Tables présentes uniquement dans la cible
    for table_name in target_tables:
        if table_name not in source_tables:
            target_cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
            target_count = target_cursor.fetchone()[0]
            results['manquantes_source'].append((table_name, target_count))
    
    # Afficher les résultats
    output_lines.append(f"\n✓ TABLES SYNCHRONISÉES ({len(results['synchronisees'])}):")
    for table, count in sorted(results['synchronisees']):
        output_lines.append(f"  {table}: {count} enregistrements")
    
    if results['ecarts_critiques']:
        output_lines.append(f"\n🔴 ÉCARTS CRITIQUES - ENREGISTREMENTS MANQUANTS ({len(results['ecarts_critiques'])}):")
        output_lines.append("  ⚠️ Ces tables ont des enregistrements de la source ABSENTS de la cible")
        for item in sorted(results['ecarts_critiques'], key=lambda x: x[3], reverse=True):
            if len(item) == 5:
                table, source, target, missing_count, missing_pks = item
                output_lines.append(f"  {table}: Source={source}, Cible={target}, MANQUE={missing_count} enregistrements")
                if missing_pks:
                    output_lines.append(f"    Exemples de clés manquantes: {missing_pks[:5]}")
            else:
                table, source, target, missing_count = item
                output_lines.append(f"  {table}: Source={source}, Cible={target}, MANQUE={missing_count} enregistrements")
    
    if results['ecarts_normaux']:
        output_lines.append(f"\n🟢 DONNÉES SUPPLÉMENTAIRES DANS LA CIBLE ({len(results['ecarts_normaux'])}):")
        output_lines.append("  ✓ Ces tables ont des enregistrements supplémentaires dans la cible (données ajoutées localement)")
        for item in sorted(results['ecarts_normaux']):
            if len(item) == 4:
                table, source, target, extra = item
                output_lines.append(f"  {table}: Source={source}, Cible={target}, Supplément={extra} enregistrements")
            else:
                table, source, target = item
                output_lines.append(f"  {table}: Source={source}, Cible={target}")
    
    if results['manquantes_cible']:
        output_lines.append(f"\n✗ TABLES MANQUANTES DANS LA CIBLE ({len(results['manquantes_cible'])}):")
        for table, count in sorted(results['manquantes_cible']):
            output_lines.append(f"  {table}: {count} enregistrements dans la source")
    
    if results['manquantes_source']:
        output_lines.append(f"\nℹ TABLES SPÉCIFIQUES À LA CIBLE (conservées) ({len(results['manquantes_source'])}):")
        for table, count in sorted(results['manquantes_source']):
            output_lines.append(f"  {table}: {count} enregistrements")
    
    output_lines.append("\n" + "=" * 80)
    output_lines.append(f"RÉSUMÉ:")
    output_lines.append(f"  ✓ Tables parfaitement synchronisées: {len(results['synchronisees'])}")
    output_lines.append(f"  🔴 Tables avec enregistrements manquants (CRITIQUE): {len(results['ecarts_critiques'])}")
    output_lines.append(f"  🟢 Tables avec données supplémentaires (OK): {len(results['ecarts_normaux'])}")
    output_lines.append(f"  ✗ Tables manquantes dans cible: {len(results['manquantes_cible'])}")
    output_lines.append(f"  ℹ Tables spécifiques à la cible (conservées): {len(results['manquantes_source'])}")
    
    total_manquants = 0
    for item in results['ecarts_critiques']:
        if len(item) >= 4:
            total_manquants += item[3]  # missing_count
    
    if total_manquants > 0:
        output_lines.append(f"\n⚠️ TOTAL D'ENREGISTREMENTS MANQUANTS: {total_manquants:,}")
        output_lines.append("  → Relancer la synchronisation pour corriger ces écarts")
    elif len(results['ecarts_critiques']) == 0 and len(results['manquantes_cible']) == 0:
        output_lines.append(f"\n✅ TOUTES LES TABLES SONT SYNCHRONISÉES !")
        output_lines.append("  Tous les enregistrements de la source sont présents dans la cible.")
    
    output_lines.append("=" * 80)
    
    results['output'] = '\n'.join(output_lines)
    
    source_conn.close()
    target_conn.close()
    
    return results

if __name__ == '__main__':
    verify_sync()
