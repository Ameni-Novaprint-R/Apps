"""
Projet 21 - Mise à jour base de données
Synchronisation Novaprint -> novaprint_restored
"""

from flask import Flask, render_template, jsonify
import pyodbc
import threading

app = Flask(__name__)

# Configuration des bases de données
SOURCE_CONFIG = {
    'server': 'SageSRV\\Graphisoft',
    'database': 'Novaprint',
    'username': 'sa',
    'password': 'Graphis0ft'
}

TARGET_CONFIG = {
    'server': 'SRV-KBA1',
    'database': 'novaprint_restored',
    'username': 'sa',
    'password': 'Graphis0ft'  # À ajuster si différent
}

sync_status = {'running': False, 'message': '', 'progress': 0, 'details': []}

def get_connection(config, readonly=False):
    """Crée une connexion SQL Server"""
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
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
        WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsPrimaryKey') = 1
        AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """, (table_name,))
    return [row.COLUMN_NAME for row in cursor.fetchall()]

def get_table_columns(cursor, table_name):
    """Récupère les colonnes d'une table"""
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """, (table_name,))
    return cursor.fetchall()

def get_table_definition(cursor, table_name):
    """Génère le script de création d'une table"""
    columns = get_table_columns(cursor, table_name)
    pk_columns = get_primary_keys(cursor, table_name)
    
    col_defs = []
    for col in columns:
        col_name, data_type, max_len, nullable, default = col
        col_def = f"[{col_name}] {data_type}"
        if max_len and data_type in ('varchar', 'nvarchar', 'char', 'nchar'):
            col_def += f"({max_len if max_len != -1 else 'MAX'})"
        if nullable == 'NO':
            col_def += " NOT NULL"
        col_defs.append(col_def)
    
    create_sql = f"CREATE TABLE [{table_name}] (\n  " + ",\n  ".join(col_defs)
    if pk_columns:
        create_sql += f",\n  PRIMARY KEY ([" + "], [".join(pk_columns) + "])"
    create_sql += "\n)"
    return create_sql

def sync_databases():
    """Synchronise les données de SOURCE vers CIBLE"""
    global sync_status
    sync_status = {'running': True, 'message': 'Démarrage...', 'progress': 0, 'details': []}
    
    try:
        # Connexion SOURCE en lecture seule
        source_conn = get_connection(SOURCE_CONFIG, readonly=True)
        source_cursor = source_conn.cursor()
        
        # Connexion CIBLE
        target_conn = get_connection(TARGET_CONFIG)
        target_cursor = target_conn.cursor()
        
        # Récupérer les tables sources
        source_cursor.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        source_tables = [row.TABLE_NAME for row in source_cursor.fetchall()]
        
        # Récupérer les tables cibles
        target_cursor.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        target_tables = [row.TABLE_NAME for row in target_cursor.fetchall()]
        
        total_tables = len(source_tables)
        
        for i, table_name in enumerate(source_tables):
            sync_status['message'] = f"Traitement: {table_name}"
            sync_status['progress'] = int((i / total_tables) * 100)
            
            try:
                if table_name not in target_tables:
                    # Créer la table dans la cible
                    create_sql = get_table_definition(source_cursor, table_name)
                    target_cursor.execute(create_sql)
                    target_conn.commit()
                    sync_status['details'].append(f"✓ Table créée: {table_name}")
                
                # Synchroniser les données
                pk_columns = get_primary_keys(source_cursor, table_name)
                
                if not pk_columns:
                    # Sans clé primaire, utiliser toutes les colonnes pour comparaison
                    cols = get_table_columns(source_cursor, table_name)
                    pk_columns = [c.COLUMN_NAME for c in cols]
                
                # Récupérer colonnes
                source_cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
                columns = [desc[0] for desc in source_cursor.description]
                
                # Construire la requête d'insertion des enregistrements manquants
                pk_conditions = " AND ".join([f"t.[{pk}] = s.[{pk}]" for pk in pk_columns])
                col_list = ", ".join([f"[{c}]" for c in columns])
                
                insert_sql = f"""
                    INSERT INTO [{table_name}] ({col_list})
                    SELECT {col_list} FROM [{table_name}] s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM [{table_name}] t WHERE {pk_conditions}
                    )
                """
                
                # Lire données source
                source_cursor.execute(f"SELECT {col_list} FROM [{table_name}]")
                source_rows = source_cursor.fetchall()
                
                inserted = 0
                for row in source_rows:
                    # Vérifier si existe déjà
                    where_clause = " AND ".join([f"[{pk}] = ?" for pk in pk_columns])
                    pk_values = [row[columns.index(pk)] for pk in pk_columns]
                    
                    target_cursor.execute(f"SELECT 1 FROM [{table_name}] WHERE {where_clause}", pk_values)
                    if not target_cursor.fetchone():
                        placeholders = ", ".join(["?" for _ in columns])
                        target_cursor.execute(f"INSERT INTO [{table_name}] ({col_list}) VALUES ({placeholders})", list(row))
                        inserted += 1
                
                if inserted > 0:
                    target_conn.commit()
                    sync_status['details'].append(f"✓ {table_name}: {inserted} enregistrements ajoutés")
                else:
                    sync_status['details'].append(f"○ {table_name}: à jour")
                    
            except Exception as e:
                target_conn.rollback()
                sync_status['details'].append(f"✗ {table_name}: {str(e)}")
        
        source_conn.close()
        target_conn.close()
        
        sync_status['message'] = 'Synchronisation terminée'
        sync_status['progress'] = 100
        
    except Exception as e:
        sync_status['message'] = f'Erreur: {str(e)}'
        sync_status['details'].append(f"Erreur globale: {str(e)}")
    
    sync_status['running'] = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sync', methods=['POST'])
def start_sync():
    global sync_status
    if sync_status['running']:
        return jsonify({'error': 'Synchronisation déjà en cours'}), 400
    
    thread = threading.Thread(target=sync_databases)
    thread.start()
    return jsonify({'status': 'started'})

@app.route('/status')
def get_status():
    return jsonify(sync_status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5021, debug=True)
