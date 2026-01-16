"""
Script de vérification de la synchronisation
Compare les comptes d'enregistrements entre Novaprint (source) et novaprint_restored (cible)
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
    if config.get('trusted_connection'):
        conn_str = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={config['server']};"
            f"DATABASE={config['database']};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes"
        )
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

source_conn = get_connection(SOURCE_CONFIG, readonly=True)
target_conn = get_connection(TARGET_CONFIG)

source_cursor = source_conn.cursor()
target_cursor = target_conn.cursor()

# Récupérer toutes les tables source
source_cursor.execute("""
    SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_NAME
""")
source_tables = [row[0] for row in source_cursor.fetchall()]

# Récupérer toutes les tables cible
target_cursor.execute("""
    SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_NAME
""")
target_tables = [row[0] for row in target_cursor.fetchall()]

print("=" * 80)
print("VÉRIFICATION DE LA SYNCHRONISATION")
print("=" * 80)
print(f"\nTables source: {len(source_tables)}")
print(f"Tables cible: {len(target_tables)}")
print(f"Tables communes: {len(set(source_tables) & set(target_tables))}")
print(f"Tables uniquement dans cible: {len(set(target_tables) - set(source_tables))}")
print("\n" + "=" * 80)
print("COMPARAISON DES COMPTES D'ENREGISTREMENTS")
print("=" * 80)

differences = []
missing_tables = []
for table_name in source_tables:
    try:
        source_cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
        source_count = source_cursor.fetchone()[0]
        
        if table_name in target_tables:
            target_cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
            target_count = target_cursor.fetchone()[0]
            
            if source_count != target_count:
                diff = source_count - target_count
                differences.append((table_name, source_count, target_count, diff))
                print(f"[!] {table_name}: Source={source_count}, Cible={target_count}, Difference={diff}")
            else:
                print(f"[OK] {table_name}: {source_count} enregistrements (identique)")
        else:
            missing_tables.append(table_name)
            print(f"[X] {table_name}: Table absente dans la cible ({source_count} enregistrements source)")
    except Exception as e:
        print(f"[ERR] {table_name}: Erreur - {str(e)}")

print("\n" + "=" * 80)
print("RÉSUMÉ")
print("=" * 80)
print(f"Tables avec différences: {len(differences)}")
print(f"Tables manquantes dans la cible: {len(missing_tables)}")

if differences:
    print("\nTables avec différences:")
    for table, source, target, diff in sorted(differences, key=lambda x: abs(x[3]), reverse=True)[:20]:
        print(f"  {table}: {source} -> {target} (diff: {diff:+d})")

if missing_tables:
    print("\nTables manquantes:")
    for table in missing_tables[:10]:
        print(f"  {table}")

source_conn.close()
target_conn.close()
