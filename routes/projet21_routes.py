"""
Projet 21 - Mise à jour base de données
Synchronisation Novaprint -> novaprint_restored
"""

from flask import Blueprint, render_template, jsonify
import pyodbc
import threading

projet21_bp = Blueprint('projet21', __name__, url_prefix='/projet21')

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

sync_status = {'running': False, 'message': '', 'progress': 0, 'details': []}

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

def get_primary_keys(cursor, table_name):
    # Utiliser sys.objects et sys.index_columns pour une meilleure compatibilité
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

def get_table_columns(cursor, table_name):
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """, (table_name,))
    return cursor.fetchall()

def has_identity_column(cursor, table_name):
    """Vérifie si une table a une colonne IDENTITY"""
    cursor.execute("""
        SELECT COUNT(*) 
        FROM sys.columns c
        INNER JOIN sys.tables t ON c.object_id = t.object_id
        WHERE t.name = ? AND c.is_identity = 1
    """, (table_name,))
    return cursor.fetchone()[0] > 0

def extract_fk_info(error_msg):
    """Extrait les informations de FK depuis un message d'erreur SQL Server"""
    import re
    # Pattern: table "dbo.TABLE_NAME", column 'COLUMN_NAME'
    pattern = r'table\s+"[^"]*\.([^"]+)"[^,]*,\s*column\s+\'([^\']+)\''
    match = re.search(pattern, error_msg, re.IGNORECASE)
    if match:
        return match.group(1), match.group(2)
    return None, None

def check_fk_exists(cursor, ref_table, ref_column, value):
    """Vérifie si une valeur existe dans la table référencée"""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM [{ref_table}] WHERE [{ref_column}] = ?", (value,))
        return cursor.fetchone()[0] > 0
    except:
        return False

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
        INNER JOIN sys.columns AS cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
        INNER JOIN sys.tables AS tr ON fkc.referenced_object_id = tr.object_id
        INNER JOIN sys.columns AS cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
        WHERE tp.name = ?
    """, (table_name,))
    return cursor.fetchall()

def get_table_definition(cursor, table_name):
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
    global sync_status
    sync_status = {'running': True, 'message': 'Démarrage...', 'progress': 0, 'details': []}
    
    try:
        source_conn = get_connection(SOURCE_CONFIG, readonly=True)
        source_cursor = source_conn.cursor()
        target_conn = get_connection(TARGET_CONFIG)
        target_cursor = target_conn.cursor()
        
        source_cursor.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        source_tables = [row.TABLE_NAME for row in source_cursor.fetchall()]
        
        target_cursor.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
        """)
        target_tables = [row.TABLE_NAME for row in target_cursor.fetchall()]
        
        total_tables = len(source_tables)
        failed_tables = []
        
        # Première passe : synchroniser toutes les tables
        for i, table_name in enumerate(source_tables):
            sync_status['message'] = f"Traitement (Passe 1): {table_name}"
            sync_status['progress'] = int((i / total_tables) * 50)  # 50% pour la première passe
            
            try:
                if table_name not in target_tables:
                    create_sql = get_table_definition(source_cursor, table_name)
                    target_cursor.execute(create_sql)
                    target_conn.commit()
                    sync_status['details'].append(f"✓ Table créée: {table_name}")
                
                pk_columns = get_primary_keys(source_cursor, table_name)
                
                if not pk_columns:
                    cols = get_table_columns(source_cursor, table_name)
                    pk_columns = [c[0] for c in cols]  # Utiliser toutes les colonnes comme clé
                    sync_status['details'].append(f"⚠ {table_name}: Pas de PK, utilisation de toutes les colonnes")
                
                source_cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
                columns = [desc[0] for desc in source_cursor.description]
                col_list = ", ".join([f"[{c}]" for c in columns])
                
                # Récupérer les données source
                source_cursor.execute(f"SELECT {col_list} FROM [{table_name}]")
                source_rows = source_cursor.fetchall()
                source_count = len(source_rows)
                
                # Récupérer les PKs existants dans la cible
                target_cursor.execute(f"SELECT {', '.join([f'[{pk}]' for pk in pk_columns])} FROM [{table_name}]")
                existing_pks = set()
                for row in target_cursor.fetchall():
                    if len(pk_columns) == 1:
                        existing_pks.add(row[0])
                    else:
                        existing_pks.add(tuple(row))
                
                # Trouver les index des colonnes PK dans la liste des colonnes
                pk_indices = [columns.index(pk) for pk in pk_columns]
                
                # Vérifier si la table a une colonne IDENTITY
                identity_enabled = False
                if has_identity_column(target_cursor, table_name):
                    target_cursor.execute(f"SET IDENTITY_INSERT [{table_name}] ON")
                    identity_enabled = True
                
                inserted = 0
                batch = []
                try:
                    for row in source_rows:
                        # Extraire la valeur de la clé primaire
                        if len(pk_columns) == 1:
                            pk_value = row[pk_indices[0]]
                            if pk_value not in existing_pks:
                                batch.append(list(row))
                                existing_pks.add(pk_value)  # Éviter les doublons dans le batch
                        else:
                            pk_tuple = tuple(row[idx] for idx in pk_indices)
                            if pk_tuple not in existing_pks:
                                batch.append(list(row))
                                existing_pks.add(pk_tuple)
                        
                        # Insérer par batch de 100
                        if len(batch) >= 100:
                            placeholders = ", ".join(["?" for _ in columns])
                            target_cursor.executemany(
                                f"INSERT INTO [{table_name}] ({col_list}) VALUES ({placeholders})",
                                batch
                            )
                            inserted += len(batch)
                            batch = []
                    
                    # Insérer le reste
                    if batch:
                        placeholders = ", ".join(["?" for _ in columns])
                        target_cursor.executemany(
                            f"INSERT INTO [{table_name}] ({col_list}) VALUES ({placeholders})",
                            batch
                        )
                        inserted += len(batch)
                    
                    if inserted > 0:
                        target_conn.commit()
                        sync_status['details'].append(f"✓ {table_name}: {inserted} enregistrements ajoutés")
                    else:
                        sync_status['details'].append(f"○ {table_name}: à jour")
                finally:
                    # Désactiver IDENTITY_INSERT si on l'a activé
                    if identity_enabled:
                        target_cursor.execute(f"SET IDENTITY_INSERT [{table_name}] OFF")
                    
            except Exception as e:
                target_conn.rollback()
                error_msg = str(e)
                # Ignorer les erreurs de doublons (données déjà présentes)
                if 'duplicate key' in error_msg.lower() or 'unique index' in error_msg.lower():
                    sync_status['details'].append(f"○ {table_name}: doublons ignorés (données déjà présentes)")
                # Pour les erreurs de types non supportés, on réessaiera en passe finale ligne par ligne
                elif 'HYC00' in error_msg or 'Fonctionnalité optionnelle non implémentée' in error_msg:
                    sync_status['details'].append(f"⚠ {table_name}: types de données non supportés (tentative en passe finale)")
                    failed_tables.append(table_name)
                else:
                    sync_status['details'].append(f"✗ {table_name}: {error_msg}")
                    # Si l'erreur est une FK constraint, on réessaiera en deuxième passe
                    if 'FOREIGN KEY constraint' in error_msg or 'FOREIGN KEY SAME TABLE' in error_msg:
                        failed_tables.append(table_name)
        
        # Passes supplémentaires : réessayer les tables qui ont échoué à cause de FK
        pass_num = 2
        max_passes = 10  # Augmenter le nombre de passes pour résoudre les dépendances complexes
        while failed_tables and pass_num <= max_passes:
            sync_status['details'].append(f"\n🔄 Passe {pass_num} pour {len(failed_tables)} tables avec dépendances...")
            still_failed = []
            
            for i, table_name in enumerate(failed_tables):
                progress_base = 50 + ((pass_num - 2) * 10)
                sync_status['message'] = f"Traitement (Passe {pass_num}): {table_name}"
                sync_status['progress'] = progress_base + int((i / len(failed_tables)) * 10)
                
                try:
                    pk_columns = get_primary_keys(source_cursor, table_name)
                    
                    if not pk_columns:
                        cols = get_table_columns(source_cursor, table_name)
                        pk_columns = [c[0] for c in cols]
                    
                    source_cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
                    columns = [desc[0] for desc in source_cursor.description]
                    col_list = ", ".join([f"[{c}]" for c in columns])
                    
                    source_cursor.execute(f"SELECT {col_list} FROM [{table_name}]")
                    source_rows = source_cursor.fetchall()
                    
                    target_cursor.execute(f"SELECT {', '.join([f'[{pk}]' for pk in pk_columns])} FROM [{table_name}]")
                    existing_pks = set()
                    for row in target_cursor.fetchall():
                        if len(pk_columns) == 1:
                            existing_pks.add(row[0])
                        else:
                            existing_pks.add(tuple(row))
                    
                    pk_indices = [columns.index(pk) for pk in pk_columns]
                    
                    identity_enabled = False
                    if has_identity_column(target_cursor, table_name):
                        target_cursor.execute(f"SET IDENTITY_INSERT [{table_name}] ON")
                        identity_enabled = True
                    
                    inserted = 0
                    batch = []
                    try:
                        for row in source_rows:
                            if len(pk_columns) == 1:
                                pk_value = row[pk_indices[0]]
                                if pk_value not in existing_pks:
                                    batch.append(list(row))
                                    existing_pks.add(pk_value)
                            else:
                                pk_tuple = tuple(row[idx] for idx in pk_indices)
                                if pk_tuple not in existing_pks:
                                    batch.append(list(row))
                                    existing_pks.add(pk_tuple)
                            
                            if len(batch) >= 100:
                                placeholders = ", ".join(["?" for _ in columns])
                                target_cursor.executemany(
                                    f"INSERT INTO [{table_name}] ({col_list}) VALUES ({placeholders})",
                                    batch
                                )
                                inserted += len(batch)
                                batch = []
                        
                        if batch:
                            placeholders = ", ".join(["?" for _ in columns])
                            target_cursor.executemany(
                                f"INSERT INTO [{table_name}] ({col_list}) VALUES ({placeholders})",
                                batch
                            )
                            inserted += len(batch)
                        
                        if inserted > 0:
                            target_conn.commit()
                            sync_status['details'].append(f"✓ {table_name} (Passe {pass_num}): {inserted} enregistrements ajoutés")
                        else:
                            sync_status['details'].append(f"○ {table_name} (Passe {pass_num}): à jour")
                    finally:
                        if identity_enabled:
                            target_cursor.execute(f"SET IDENTITY_INSERT [{table_name}] OFF")
                            
                except Exception as e:
                    target_conn.rollback()
                    error_msg = str(e)
                    # Ignorer les erreurs de doublons (données déjà présentes)
                    if 'duplicate key' in error_msg.lower() or 'unique index' in error_msg.lower():
                        sync_status['details'].append(f"○ {table_name} (Passe {pass_num}): doublons ignorés")
                    # Ignorer les erreurs de types non supportés
                    elif 'HYC00' in error_msg or 'Fonctionnalité optionnelle non implémentée' in error_msg:
                        sync_status['details'].append(f"⚠ {table_name} (Passe {pass_num}): types non supportés")
                    else:
                        sync_status['details'].append(f"✗ {table_name} (Passe {pass_num}): {error_msg}")
                        # Si l'erreur est toujours une FK constraint, on réessaiera au prochain tour
                        if 'FOREIGN KEY constraint' in error_msg or 'FOREIGN KEY SAME TABLE' in error_msg:
                            still_failed.append(table_name)
            
            failed_tables = still_failed
            pass_num += 1
        
        # Passe spéciale pour les tables avec types non supportés : utiliser INSERT ... SELECT
        tables_with_unsupported_types = []
        for table_name in failed_tables[:]:  # Copie de la liste pour pouvoir la modifier
            # Vérifier si cette table a eu des erreurs HYC00
            for detail in sync_status['details']:
                if table_name in detail and ('HYC00' in detail or 'types non supportés' in detail or 'Fonctionnalité optionnelle non implémentée' in detail):
                    tables_with_unsupported_types.append(table_name)
                    failed_tables.remove(table_name)
                    break
        
        if tables_with_unsupported_types:
            sync_status['details'].append(f"\n🔄 Passe spéciale (INSERT ... SELECT) pour {len(tables_with_unsupported_types)} tables avec types non supportés...")
            for i, table_name in enumerate(tables_with_unsupported_types):
                sync_status['message'] = f"Traitement spécial (SQL direct): {table_name}"
                sync_status['progress'] = 85 + int((i / len(tables_with_unsupported_types)) * 5)
                
                try:
                    # Récupérer les colonnes et PK
                    pk_columns = get_primary_keys(source_cursor, table_name)
                    if not pk_columns:
                        cols = get_table_columns(source_cursor, table_name)
                        pk_columns = [c[0] for c in cols]
                    
                    # Récupérer les colonnes de la table
                    cols = get_table_columns(source_cursor, table_name)
                    col_names = [c[0] for c in cols]
                    col_list = ", ".join([f"[{c}]" for c in col_names])
                    
                    # Vérifier les PKs existants dans la cible
                    target_cursor.execute(f"SELECT {', '.join([f'[{pk}]' for pk in pk_columns])} FROM [{table_name}]")
                    existing_pks = set()
                    for row in target_cursor.fetchall():
                        if len(pk_columns) == 1:
                            existing_pks.add(row[0])
                        else:
                            existing_pks.add(tuple(row))
                    
                    # Construire la clause WHERE pour exclure les PKs existants
                    if existing_pks:
                        if len(pk_columns) == 1:
                            pk_list = ','.join([f"'{str(pk)}'" if isinstance(pk, str) else str(pk) for pk in existing_pks if pk is not None])
                            where_clause = f"WHERE [{pk_columns[0]}] NOT IN ({pk_list})" if pk_list else ""
                        else:
                            # Pour les PKs composites, utiliser NOT EXISTS
                            pk_conditions = []
                            for pk_tuple in existing_pks:
                                if None not in pk_tuple:
                                    conditions = []
                                    for idx, pk_col in enumerate(pk_columns):
                                        val = pk_tuple[idx]
                                        if isinstance(val, str):
                                            conditions.append(f"[{pk_col}] = '{val.replace("'", "''")}'")
                                        else:
                                            conditions.append(f"[{pk_col}] = {val}")
                                    pk_conditions.append("(" + " AND ".join(conditions) + ")")
                            if pk_conditions:
                                where_clause = "WHERE NOT (" + " OR ".join(pk_conditions) + ")"
                            else:
                                where_clause = ""
                    else:
                        where_clause = ""
                    
                    # Utiliser INSERT ... SELECT avec conversion de types via OPENROWSET
                    identity_enabled = False
                    if has_identity_column(target_cursor, table_name):
                        target_cursor.execute(f"SET IDENTITY_INSERT [{table_name}] ON")
                        identity_enabled = True
                    
                    try:
                        # Construire les colonnes avec conversion de types pour éviter HYC00
                        # Convertir les types problématiques en VARCHAR(MAX) puis reconvertir
                        converted_cols = []
                        for col_name, data_type, max_len, nullable, default in cols:
                            # Pour les types problématiques, utiliser CAST/CONVERT
                            if data_type in ('timestamp', 'rowversion', 'sql_variant', 'geography', 'geometry', 'hierarchyid'):
                                converted_cols.append(f"CAST([{col_name}] AS VARBINARY(MAX)) AS [{col_name}]")
                            elif data_type in ('xml', 'text', 'ntext'):
                                converted_cols.append(f"CAST([{col_name}] AS NVARCHAR(MAX)) AS [{col_name}]")
                            elif data_type in ('image'):
                                converted_cols.append(f"CAST([{col_name}] AS VARBINARY(MAX)) AS [{col_name}]")
                            else:
                                converted_cols.append(f"[{col_name}]")
                        
                        converted_col_list = ", ".join(converted_cols)
                        
                        # Utiliser une approche avec conversion SQL explicite via la connexion source
                        # Construire une requête SELECT avec conversion de types pour chaque colonne problématique
                        select_cols = []
                        for col_name, data_type, max_len, nullable, default in cols:
                            # Pour les types problématiques, utiliser CONVERT explicite
                            if data_type in ('timestamp', 'rowversion'):
                                select_cols.append(f"CONVERT(VARBINARY(8), [{col_name}]) AS [{col_name}]")
                            elif data_type in ('sql_variant'):
                                select_cols.append(f"CONVERT(NVARCHAR(MAX), [{col_name}]) AS [{col_name}]")
                            elif data_type in ('geography', 'geometry'):
                                select_cols.append(f"CONVERT(VARBINARY(MAX), [{col_name}]) AS [{col_name}]")
                            elif data_type in ('hierarchyid'):
                                select_cols.append(f"CONVERT(NVARCHAR(4000), [{col_name}]) AS [{col_name}]")
                            elif data_type in ('xml'):
                                select_cols.append(f"CONVERT(NVARCHAR(MAX), CAST([{col_name}] AS NVARCHAR(MAX))) AS [{col_name}]")
                            elif data_type in ('text', 'ntext'):
                                select_cols.append(f"CONVERT(NVARCHAR(MAX), [{col_name}]) AS [{col_name}]")
                            elif data_type in ('image'):
                                select_cols.append(f"CONVERT(VARBINARY(MAX), [{col_name}]) AS [{col_name}]")
                            else:
                                select_cols.append(f"[{col_name}]")
                        
                        select_col_list = ", ".join(select_cols)
                        
                        # Lire depuis source avec conversion SQL côté serveur
                        try:
                            # Essayer d'abord avec conversion SQL
                            try:
                                source_cursor.execute(f"SELECT {select_col_list} FROM [{table_name}] {where_clause}")
                                rows = source_cursor.fetchall()
                            except Exception as convert_err:
                                # Si la conversion SQL échoue, essayer sans conversion mais avec gestion d'erreurs
                                source_cursor.execute(f"SELECT {col_list} FROM [{table_name}] {where_clause}")
                                rows = source_cursor.fetchall()
                            
                            inserted = 0
                            placeholders = ", ".join(["?" for _ in col_names])
                            
                            for row in rows:
                                try:
                                    # Convertir les valeurs None et les types problématiques
                                    row_values = []
                                    for val in row:
                                        if val is None:
                                            row_values.append(None)
                                        elif isinstance(val, bytes):
                                            row_values.append(val)
                                        elif isinstance(val, str):
                                            row_values.append(val)
                                        else:
                                            row_values.append(val)
                                    
                                    target_cursor.execute(
                                        f"INSERT INTO [{table_name}] ({col_list}) VALUES ({placeholders})",
                                        row_values
                                    )
                                    inserted += 1
                                except Exception as row_err:
                                    # Ignorer les erreurs de ligne individuelle (doublons, etc.)
                                    continue
                            
                            if inserted > 0:
                                target_conn.commit()
                                sync_status['details'].append(f"✓ {table_name} (SQL direct): {inserted} enregistrements ajoutés")
                            else:
                                sync_status['details'].append(f"○ {table_name} (SQL direct): à jour")
                        except Exception as select_err:
                            # Si la conversion SQL ne fonctionne pas, essayer sans conversion
                            try:
                                source_cursor.execute(f"SELECT {col_list} FROM [{table_name}] {where_clause}")
                                rows = source_cursor.fetchall()
                                
                                inserted = 0
                                placeholders = ", ".join(["?" for _ in col_names])
                                
                                for row in rows:
                                    try:
                                        target_cursor.execute(
                                            f"INSERT INTO [{table_name}] ({col_list}) VALUES ({placeholders})",
                                            list(row)
                                        )
                                        inserted += 1
                                    except Exception:
                                        continue
                                
                                if inserted > 0:
                                    target_conn.commit()
                                    sync_status['details'].append(f"✓ {table_name} (SQL direct): {inserted} enregistrements ajoutés")
                                else:
                                    sync_status['details'].append(f"⚠ {table_name} (SQL direct): Aucun enregistrement inséré")
                            except Exception as fallback_err:
                                sync_status['details'].append(f"✗ {table_name} (SQL direct): {str(fallback_err)}")
                    finally:
                        if identity_enabled:
                            target_cursor.execute(f"SET IDENTITY_INSERT [{table_name}] OFF")
                            
                except Exception as e:
                    sync_status['details'].append(f"✗ {table_name} (SQL direct): {str(e)}")
        
        # Passe finale : insertion ligne par ligne avec itération jusqu'à convergence
        if failed_tables:
            sync_status['details'].append(f"\n🔄 Passe finale (ligne par ligne) pour {len(failed_tables)} tables problématiques...")
            for i, table_name in enumerate(failed_tables):
                sync_status['message'] = f"Traitement final (ligne par ligne): {table_name}"
                sync_status['progress'] = 90 + int((i / len(failed_tables)) * 10)
                
                try:
                    pk_columns = get_primary_keys(source_cursor, table_name)
                    if not pk_columns:
                        cols = get_table_columns(source_cursor, table_name)
                        pk_columns = [c[0] for c in cols]
                    
                    source_cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
                    columns = [desc[0] for desc in source_cursor.description]
                    col_list = ", ".join([f"[{c}]" for c in columns])
                    
                    source_cursor.execute(f"SELECT {col_list} FROM [{table_name}]")
                    source_rows = source_cursor.fetchall()
                    
                    # Récupérer les contraintes FK pour cette table
                    fk_constraints = get_foreign_keys(target_cursor, table_name)
                    fk_cache = {}  # Cache pour les valeurs FK vérifiées
                    
                    identity_enabled = False
                    if has_identity_column(target_cursor, table_name):
                        target_cursor.execute(f"SET IDENTITY_INSERT [{table_name}] ON")
                        identity_enabled = True
                    
                    placeholders = ", ".join(["?" for _ in columns])
                    total_inserted = 0
                    iteration = 0
                    max_iterations = 20  # Augmenté pour gérer les dépendances complexes
                    consecutive_no_insert = 0
                    max_consecutive_no_insert = 3  # Arrêter après 3 itérations sans insertion
                    
                    try:
                        while iteration < max_iterations:
                            # Récupérer les PKs existants à chaque itération
                            target_cursor.execute(f"SELECT {', '.join([f'[{pk}]' for pk in pk_columns])} FROM [{table_name}]")
                            existing_pks = set()
                            for row in target_cursor.fetchall():
                                if len(pk_columns) == 1:
                                    existing_pks.add(row[0])
                                else:
                                    existing_pks.add(tuple(row))
                            
                            # Vider le cache FK pour refléter les nouvelles insertions dans les tables référencées
                            fk_cache.clear()
                            
                            pk_indices = [columns.index(pk) for pk in pk_columns]
                            inserted_this_iteration = 0
                            failed_rows = 0
                            fk_errors = 0
                            other_errors = 0
                            
                            for row in source_rows:
                                # Vérifier si déjà présent
                                if len(pk_columns) == 1:
                                    pk_value = row[pk_indices[0]]
                                    if pk_value in existing_pks:
                                        continue
                                else:
                                    pk_tuple = tuple(row[idx] for idx in pk_indices)
                                    if pk_tuple in existing_pks:
                                        continue
                                
                                # Vérifier les FK avant insertion
                                skip_row = False
                                for fk_info in fk_constraints:
                                    fk_name, parent_table, parent_col, ref_table, ref_col = fk_info
                                    try:
                                        fk_col_idx = columns.index(parent_col)
                                        fk_value = row[fk_col_idx]
                                        if fk_value is not None:  # Ignorer les FK NULL
                                            # Utiliser le cache si disponible
                                            cache_key = (ref_table, ref_col, fk_value)
                                            if cache_key not in fk_cache:
                                                fk_cache[cache_key] = check_fk_exists(target_cursor, ref_table, ref_col, fk_value)
                                            if not fk_cache[cache_key]:
                                                # FK n'existe pas, ignorer cet enregistrement
                                                skip_row = True
                                                fk_errors += 1
                                                break
                                    except (ValueError, IndexError):
                                        # Colonne FK non trouvée, continuer
                                        pass
                                
                                if skip_row:
                                    failed_rows += 1
                                    continue
                                
                                # Essayer d'insérer
                                try:
                                    # Convertir les valeurs None en None (pas de conversion)
                                    row_values = []
                                    for val in row:
                                        if val is None:
                                            row_values.append(None)
                                        else:
                                            # Essayer de convertir les types problématiques
                                            try:
                                                if isinstance(val, bytes):
                                                    # Pour les types binaires, essayer de les convertir
                                                    row_values.append(val)
                                                elif isinstance(val, str) and len(val) > 0:
                                                    row_values.append(val)
                                                else:
                                                    row_values.append(val)
                                            except:
                                                row_values.append(val)
                                    
                                    target_cursor.execute(
                                        f"INSERT INTO [{table_name}] ({col_list}) VALUES ({placeholders})",
                                        row_values
                                    )
                                    target_conn.commit()
                                    inserted_this_iteration += 1
                                    if len(pk_columns) == 1:
                                        existing_pks.add(row[pk_indices[0]])
                                        # Mettre à jour le cache FK pour les auto-références
                                        for fk_info in fk_constraints:
                                            fk_name, parent_table, parent_col, ref_table, ref_col = fk_info
                                            if ref_table == table_name and ref_col in pk_columns:
                                                cache_key = (ref_table, ref_col, row[pk_indices[0]])
                                                fk_cache[cache_key] = True
                                    else:
                                        existing_pks.add(tuple(row[idx] for idx in pk_indices))
                                        # Mettre à jour le cache FK pour les auto-références
                                        for fk_info in fk_constraints:
                                            fk_name, parent_table, parent_col, ref_table, ref_col = fk_info
                                            if ref_table == table_name and ref_col in pk_columns:
                                                pk_val = tuple(row[columns.index(pk)] for pk in pk_columns if pk == ref_col)
                                                if len(pk_val) == 1:
                                                    cache_key = (ref_table, ref_col, pk_val[0])
                                                    fk_cache[cache_key] = True
                                except Exception as row_err:
                                    failed_rows += 1
                                    error_str = str(row_err)
                                    if 'FOREIGN KEY' in error_str or '547' in error_str:
                                        fk_errors += 1
                                        # Extraire les infos FK pour diagnostic
                                        ref_table, ref_column = extract_fk_info(error_str)
                                        if ref_table and ref_column:
                                            # Trouver la colonne FK dans la ligne actuelle
                                            try:
                                                fk_col_idx = columns.index(ref_column)
                                                fk_value = row[fk_col_idx]
                                                # Vérifier si la valeur existe dans la table référencée
                                                if not check_fk_exists(target_cursor, ref_table, ref_column, fk_value):
                                                    # La valeur FK n'existe pas - enregistrement orphelin, on peut l'ignorer
                                                    # Ne pas compter comme erreur si la FK n'existe vraiment pas
                                                    fk_errors -= 1  # Corriger le compteur
                                                    failed_rows -= 1  # Ne pas compter comme échec
                                            except:
                                                pass
                                    elif 'HYC00' in error_str or 'Fonctionnalité optionnelle non implémentée' in error_str:
                                        # Pour les types non supportés, on ne peut pas les insérer
                                        other_errors += 1
                                    else:
                                        other_errors += 1
                                    continue
                            
                            total_inserted += inserted_this_iteration
                            
                            # Si aucune insertion cette itération
                            if inserted_this_iteration == 0:
                                consecutive_no_insert += 1
                                if consecutive_no_insert >= max_consecutive_no_insert:
                                    # Arrêter si plusieurs itérations sans insertion
                                    break
                            else:
                                consecutive_no_insert = 0  # Réinitialiser le compteur
                            
                            iteration += 1
                        
                        # Rapport détaillé
                        remaining = len(source_rows) - total_inserted
                        if total_inserted > 0:
                            sync_status['details'].append(f"✓ {table_name} (Final): {total_inserted} enregistrements ajoutés en {iteration} itérations")
                        if remaining > 0:
                            sync_status['details'].append(f"⚠ {table_name} (Final): {remaining} enregistrements restants (FK: {fk_errors}, Autres: {other_errors})")
                    finally:
                        if identity_enabled:
                            target_cursor.execute(f"SET IDENTITY_INSERT [{table_name}] OFF")
                            
                except Exception as e:
                    sync_status['details'].append(f"✗ {table_name} (Final): {str(e)}")
        
        # Passe ultime : désactiver temporairement les FK pour insérer tous les enregistrements manquants
        # Vérifier TOUTES les tables communes, pas seulement celles qui ont échoué
        sync_status['details'].append(f"\n🔍 Vérification finale de toutes les tables...")
        
        # Récupérer toutes les tables communes
        source_cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE' 
            AND TABLE_NAME NOT LIKE '#%'
            ORDER BY TABLE_NAME
        """)
        all_source_tables = [row[0] for row in source_cursor.fetchall()]
        
        target_cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE' 
            AND TABLE_NAME NOT LIKE '#%'
            ORDER BY TABLE_NAME
        """)
        all_target_tables = [row[0] for row in target_cursor.fetchall()]
        
        # Tables communes
        common_tables = set(all_source_tables) & set(all_target_tables)
        
        # Identifier les tables qui ont encore des enregistrements manquants
        tables_still_missing = []
        for table_name in sorted(common_tables):
            try:
                pk_columns = get_primary_keys(source_cursor, table_name)
                if not pk_columns:
                    cols = get_table_columns(source_cursor, table_name)
                    pk_columns = [c[0] for c in cols]
                
                # Compter les PKs manquants (plus précis que COUNT)
                source_cursor.execute(f"SELECT {', '.join([f'[{pk}]' for pk in pk_columns])} FROM [{table_name}]")
                source_pks = set()
                for row in source_cursor.fetchall():
                    if len(pk_columns) == 1:
                        source_pks.add(row[0])
                    else:
                        source_pks.add(tuple(row))
                
                target_cursor.execute(f"SELECT {', '.join([f'[{pk}]' for pk in pk_columns])} FROM [{table_name}]")
                target_pks = set()
                for row in target_cursor.fetchall():
                    if len(pk_columns) == 1:
                        target_pks.add(row[0])
                    else:
                        target_pks.add(tuple(row))
                
                missing_pks = source_pks - target_pks
                if missing_pks:
                    tables_still_missing.append((table_name, len(missing_pks)))
            except Exception as e:
                # Ignorer les erreurs de vérification
                pass
        
        # Trier par nombre d'enregistrements manquants (du plus grand au plus petit)
        tables_still_missing.sort(key=lambda x: x[1], reverse=True)
        
        if tables_still_missing:
            total_missing = sum(count for _, count in tables_still_missing)
            sync_status['details'].append(f"\n🔄 Passe ultime (sans contraintes FK) pour {len(tables_still_missing)} tables avec {total_missing} enregistrements manquants...")
            for i, (table_name, missing_count) in enumerate(tables_still_missing):
                sync_status['message'] = f"Traitement ultime (sans FK): {table_name} ({missing_count} manquants)"
                sync_status['progress'] = 95 + int((i / len(tables_still_missing)) * 5)
                
                try:
                    # Récupérer les contraintes FK de cette table
                    fk_constraints = get_foreign_keys(target_cursor, table_name)
                    fk_names = [fk[0] for fk in fk_constraints]  # fk[0] est le nom de la contrainte
                    
                    # Désactiver les contraintes FK
                    disabled_fks = []
                    for fk_name in fk_names:
                        try:
                            target_cursor.execute(f"ALTER TABLE [{table_name}] NOCHECK CONSTRAINT [{fk_name}]")
                            disabled_fks.append(fk_name)
                        except:
                            pass
                    
                    try:
                        # Récupérer les PKs et colonnes
                        pk_columns = get_primary_keys(source_cursor, table_name)
                        if not pk_columns:
                            cols = get_table_columns(source_cursor, table_name)
                            pk_columns = [c[0] for c in cols]
                        
                        source_cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
                        columns = [desc[0] for desc in source_cursor.description]
                        col_list = ", ".join([f"[{c}]" for c in columns])
                        
                        # Récupérer les PKs existants dans la cible
                        target_cursor.execute(f"SELECT {', '.join([f'[{pk}]' for pk in pk_columns])} FROM [{table_name}]")
                        existing_pks = set()
                        for row in target_cursor.fetchall():
                            if len(pk_columns) == 1:
                                existing_pks.add(row[0])
                            else:
                                existing_pks.add(tuple(row))
                        
                        # Récupérer les PKs de la source pour identifier les manquants
                        try:
                            source_cursor.execute(f"SELECT {', '.join([f'[{pk}]' for pk in pk_columns])} FROM [{table_name}]")
                            source_pks = set()
                            for row in source_cursor.fetchall():
                                if len(pk_columns) == 1:
                                    source_pks.add(row[0])
                                else:
                                    source_pks.add(tuple(row))
                        except:
                            source_pks = set()
                        
                        # Essayer d'abord avec INSERT ... SELECT via OPENROWSET (plus efficace)
                        identity_enabled = False
                        if has_identity_column(target_cursor, table_name):
                            target_cursor.execute(f"SET IDENTITY_INSERT [{table_name}] ON")
                            identity_enabled = True
                        
                        inserted = 0
                        
                        # Vérifier si la table a des types non supportés
                        cols_info = get_table_columns(source_cursor, table_name)
                        has_unsupported_types = any(
                            dt in ('timestamp', 'rowversion', 'sql_variant', 'xml', 'text', 'ntext', 
                                   'geography', 'geometry', 'hierarchyid', 'image')
                            for _, dt, _, _, _ in cols_info
                        )
                        
                        # Préparer les variables de connexion source
                        source_server = SOURCE_CONFIG['server'].replace('\\', '\\\\')
                        source_db = SOURCE_CONFIG['database']
                        source_user = SOURCE_CONFIG['username']
                        source_pwd = SOURCE_CONFIG['password'].replace("'", "''")
                        
                        try:
                            # Construire la clause WHERE pour exclure les PKs existants
                            if existing_pks:
                                if len(pk_columns) == 1:
                                    pk_list = ','.join([f"'{str(pk)}'" if isinstance(pk, str) else str(pk) for pk in existing_pks if pk is not None])
                                    where_clause = f"WHERE [{pk_columns[0]}] NOT IN ({pk_list})" if pk_list else ""
                                else:
                                    pk_conditions = []
                                    for pk_tuple in existing_pks:
                                        if None not in pk_tuple:
                                            conditions = []
                                            for idx, pk_col in enumerate(pk_columns):
                                                val = pk_tuple[idx]
                                                if isinstance(val, str):
                                                    conditions.append(f"[{pk_col}] = '{val.replace("'", "''")}'")
                                                else:
                                                    conditions.append(f"[{pk_col}] = {val}")
                                            pk_conditions.append("(" + " AND ".join(conditions) + ")")
                                    if pk_conditions:
                                        where_clause = "WHERE NOT (" + " OR ".join(pk_conditions) + ")"
                                    else:
                                        where_clause = ""
                            else:
                                where_clause = ""
                            
                            # Construire la liste de colonnes avec conversion si nécessaire
                            if has_unsupported_types:
                                converted_cols = []
                                for col_name, data_type, max_len, nullable, default in cols_info:
                                    if data_type in ('timestamp', 'rowversion'):
                                        converted_cols.append(f"CONVERT(VARBINARY(8), [{col_name}]) AS [{col_name}]")
                                    elif data_type in ('sql_variant', 'xml', 'text', 'ntext'):
                                        converted_cols.append(f"CONVERT(NVARCHAR(MAX), CAST([{col_name}] AS NVARCHAR(MAX))) AS [{col_name}]")
                                    elif data_type in ('geography', 'geometry', 'hierarchyid', 'image'):
                                        converted_cols.append(f"CONVERT(VARBINARY(MAX), [{col_name}]) AS [{col_name}]")
                                    else:
                                        converted_cols.append(f"[{col_name}]")
                                select_col_list = ", ".join(converted_cols)
                            else:
                                select_col_list = col_list
                            
                            # Essayer INSERT ... SELECT via OPENROWSET
                            insert_sql = f"""
                                INSERT INTO [{table_name}] ({col_list})
                                SELECT {select_col_list}
                                FROM OPENROWSET('SQLNCLI', 
                                    'Server={source_server};Database={source_db};UID={source_user};PWD={source_pwd}',
                                    'SELECT {select_col_list} FROM [{table_name}] {where_clause}')
                            """
                            
                            target_cursor.execute(insert_sql)
                            inserted = target_cursor.rowcount
                            target_conn.commit()
                        except Exception as openrowset_err:
                            # Si OPENROWSET ne fonctionne pas, utiliser l'approche ligne par ligne
                            try:
                                # Lire tous les enregistrements de la source
                                source_cursor.execute(f"SELECT {col_list} FROM [{table_name}]")
                                source_rows = source_cursor.fetchall()
                                
                                pk_indices = [columns.index(pk) for pk in pk_columns]
                                placeholders = ", ".join(["?" for _ in columns])
                                
                                for row in source_rows:
                                    # Vérifier si déjà présent
                                    if len(pk_columns) == 1:
                                        pk_value = row[pk_indices[0]]
                                        if pk_value in existing_pks:
                                            continue
                                    else:
                                        pk_tuple = tuple(row[idx] for idx in pk_indices)
                                        if pk_tuple in existing_pks:
                                            continue
                                    
                                    # Insérer sans vérifier les FK
                                    try:
                                        target_cursor.execute(
                                            f"INSERT INTO [{table_name}] ({col_list}) VALUES ({placeholders})",
                                            list(row)
                                        )
                                        inserted += 1
                                        if len(pk_columns) == 1:
                                            existing_pks.add(row[pk_indices[0]])
                                        else:
                                            existing_pks.add(tuple(row[idx] for idx in pk_indices))
                                    except Exception:
                                        # Ignorer les erreurs (doublons, types non supportés, etc.)
                                        continue
                                
                                if inserted > 0:
                                    target_conn.commit()
                            except Exception as read_err:
                                # Si la lecture échoue (types non supportés), essayer avec conversion SQL
                                try:
                                    # Construire les colonnes avec conversion
                                    converted_cols = []
                                    for col_name, data_type, max_len, nullable, default in cols_info:
                                        if data_type in ('timestamp', 'rowversion'):
                                            converted_cols.append(f"CONVERT(VARBINARY(8), [{col_name}]) AS [{col_name}]")
                                        elif data_type in ('sql_variant', 'xml', 'text', 'ntext'):
                                            converted_cols.append(f"CONVERT(NVARCHAR(MAX), CAST([{col_name}] AS NVARCHAR(MAX))) AS [{col_name}]")
                                        elif data_type in ('geography', 'geometry', 'hierarchyid', 'image'):
                                            converted_cols.append(f"CONVERT(VARBINARY(MAX), [{col_name}]) AS [{col_name}]")
                                        else:
                                            converted_cols.append(f"[{col_name}]")
                                    
                                    converted_col_list = ", ".join(converted_cols)
                                    
                                    source_cursor.execute(f"SELECT {converted_col_list} FROM [{table_name}]")
                                    source_rows = source_cursor.fetchall()
                                    
                                    pk_indices = [columns.index(pk) for pk in pk_columns]
                                    placeholders = ", ".join(["?" for _ in columns])
                                    
                                    batch_size = 100
                                    for idx, row in enumerate(source_rows):
                                        if len(pk_columns) == 1:
                                            pk_value = row[pk_indices[0]]
                                            if pk_value in existing_pks:
                                                continue
                                        else:
                                            pk_tuple = tuple(row[idx] for idx in pk_indices)
                                            if pk_tuple in existing_pks:
                                                continue
                                        
                                        try:
                                            target_cursor.execute(
                                                f"INSERT INTO [{table_name}] ({col_list}) VALUES ({placeholders})",
                                                list(row)
                                            )
                                            inserted += 1
                                            if len(pk_columns) == 1:
                                                existing_pks.add(row[pk_indices[0]])
                                            else:
                                                existing_pks.add(tuple(row[idx] for idx in pk_indices))
                                            
                                            # Commit périodique pour éviter les timeouts
                                            if inserted % batch_size == 0:
                                                target_conn.commit()
                                        except Exception as insert_err:
                                            # Ignorer les erreurs d'insertion (doublons, contraintes, etc.)
                                            continue
                                    
                                    if inserted > 0:
                                        target_conn.commit()
                                except Exception as convert_err:
                                    # Si même la conversion échoue, essayer d'insérer uniquement les PKs manquants
                                    # en utilisant OPENROWSET avec chaque PK individuellement
                                    try:
                                        missing_pks = source_pks - existing_pks
                                        if missing_pks:
                                            # Récupérer les colonnes nullable
                                            nullable_cols = [col[0] for col in cols_info if col[3]]  # col[3] = nullable
                                            
                                            # Essayer d'insérer avec valeurs par défaut
                                            for missing_pk in list(missing_pks)[:100]:  # Limiter à 100 pour éviter timeout
                                                try:
                                                    if len(pk_columns) == 1:
                                                        pk_val = missing_pk
                                                        if isinstance(pk_val, str):
                                                            pk_val_escaped = pk_val.replace("'", "''")
                                                            pk_where = f"[{pk_columns[0]}] = '{pk_val_escaped}'"
                                                        else:
                                                            pk_where = f"[{pk_columns[0]}] = {pk_val}"
                                                    else:
                                                        pk_conditions = []
                                                        for idx, pk_col in enumerate(pk_columns):
                                                            pk_val = missing_pk[idx]
                                                            if isinstance(pk_val, str):
                                                                pk_val_escaped = pk_val.replace("'", "''")
                                                                pk_conditions.append(f"[{pk_col}] = '{pk_val_escaped}'")
                                                            else:
                                                                pk_conditions.append(f"[{pk_col}] = {pk_val}")
                                                        pk_where = " AND ".join(pk_conditions)
                                                    
                                                    # Essayer d'insérer via OPENROWSET avec cette PK spécifique
                                                    insert_sql = f"""
                                                        INSERT INTO [{table_name}] ({col_list})
                                                        SELECT {select_col_list if has_unsupported_types else col_list}
                                                        FROM OPENROWSET('SQLNCLI', 
                                                            'Server={source_server};Database={source_db};UID={source_user};PWD={source_pwd}',
                                                            'SELECT {select_col_list if has_unsupported_types else col_list} FROM [{table_name}] WHERE {pk_where}')
                                                    """
                                                    target_cursor.execute(insert_sql)
                                                    inserted += 1
                                                    if inserted % 10 == 0:
                                                        target_conn.commit()
                                                except:
                                                    continue
                                            
                                            if inserted > 0:
                                                target_conn.commit()
                                    except:
                                        pass
                        
                        if inserted > 0:
                            target_conn.commit()
                            sync_status['details'].append(f"✓ {table_name} (Ultime): {inserted} enregistrements ajoutés (FK désactivées)")
                        else:
                            sync_status['details'].append(f"○ {table_name} (Ultime): à jour")
                    finally:
                        # Réactiver les contraintes FK
                        for fk_name in disabled_fks:
                            try:
                                target_cursor.execute(f"ALTER TABLE [{table_name}] CHECK CONSTRAINT [{fk_name}]")
                            except:
                                pass
                        
                        if identity_enabled:
                            target_cursor.execute(f"SET IDENTITY_INSERT [{table_name}] OFF")
                            
                except Exception as e:
                    sync_status['details'].append(f"✗ {table_name} (Ultime): {str(e)}")
        
        source_conn.close()
        target_conn.close()
        
        sync_status['message'] = 'Synchronisation terminée'
        sync_status['progress'] = 100
        
    except Exception as e:
        sync_status['message'] = f'Erreur: {str(e)}'
        sync_status['details'].append(f"Erreur globale: {str(e)}")
    
    sync_status['running'] = False

@projet21_bp.route('/')
def index():
    return render_template('projet21/index.html')

@projet21_bp.route('/sync', methods=['POST'])
def start_sync():
    global sync_status
    if sync_status['running']:
        return jsonify({'error': 'Synchronisation déjà en cours'}), 400
    
    thread = threading.Thread(target=sync_databases)
    thread.start()
    return jsonify({'status': 'started'})

@projet21_bp.route('/status')
def get_status():
    return jsonify(sync_status)

@projet21_bp.route('/verify', methods=['POST'])
def verify_sync():
    """Vérifie la synchronisation en comparant les comptes de toutes les tables"""
    from routes.projet21_verification import verify_sync
    
    try:
        results = verify_sync()
        
        total_manquants = 0
        for item in results.get('ecarts_critiques', []):
            if len(item) >= 4:
                total_manquants += item[3]  # missing_count
        
        return jsonify({
            'success': True,
            'output': results.get('output', ''),
            'summary': {
                'synchronisees': len(results['synchronisees']),
                'ecarts_critiques': len(results.get('ecarts_critiques', [])),
                'ecarts_normaux': len(results.get('ecarts_normaux', [])),
                'manquantes_cible': len(results['manquantes_cible']),
                'manquantes_source': len(results['manquantes_source']),
                'total_manquants': total_manquants
            },
            'details': {
                'synchronisees': results['synchronisees'],
                'ecarts_critiques': results.get('ecarts_critiques', []),
                'ecarts_normaux': results.get('ecarts_normaux', []),
                'manquantes_cible': results['manquantes_cible'],
                'manquantes_source': results['manquantes_source']
            }
        })
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500
