"""
Projet 21 - Mise à jour base de données
Synchronisation Novaprint -> novaprint_restored
"""

from flask import Blueprint, render_template, jsonify, send_file
import pyodbc
import threading
from datetime import datetime
from flask import request
from io import BytesIO
import pandas as pd
from openpyxl.styles import PatternFill

projet21_bp = Blueprint('projet21', __name__, url_prefix='/projet21')

# Marqueur pour vérifier quelle version du code est chargée par Flask
PROJET21_CODE_VERSION = "projet21_routes.py::topo-sort-update-ultime-v3::2026-01-19"

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

sync_status = {'running': False, 'message': '', 'progress': 0, 'details': [], 'code_version': PROJET21_CODE_VERSION}

def get_connection(config, readonly=False):
    """
    Connexion SQL Server.

    Important: éviter le driver legacy "{SQL Server}" côté cible, car il déclenche
    des erreurs HYC00 sur certains types lors des INSERT/SQLBindParameter.
    On privilégie ODBC Driver 17/18 avec fallback contrôlé.
    """
    if config.get('trusted_connection'):
        driver_candidates = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"]
        last_err = None
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

def build_dependency_graph(source_cursor, target_cursor, tables):
    """
    Construit un graphe de dépendances FK : {table: [tables_dont_elle_depend]}
    Utilise la SOURCE pour détecter les FK (plus fiable que la cible qui peut être incomplète)
    Retourne aussi un set de toutes les tables référencées (pour détecter les tables externes)
    """
    graph = {table: [] for table in tables}
    all_referenced_tables = set()
    
    for table_name in tables:
        try:
            # Utiliser la SOURCE pour détecter les FK (plus fiable)
            fks = get_foreign_keys(source_cursor, table_name)
            for fk_info in fks:
                fk_name, parent_table, parent_col, ref_table, ref_col = fk_info
                # Ne considérer que les FK vers d'autres tables de notre liste
                if ref_table in tables and ref_table != table_name:
                    if ref_table not in graph[table_name]:
                        graph[table_name].append(ref_table)
                    all_referenced_tables.add(ref_table)
        except Exception:
            # Si erreur, considérer la table comme sans dépendances
            pass
    
    return graph, all_referenced_tables

def topological_sort(tables, dependency_graph):
    """
    Tri topologique pour déterminer l'ordre de synchronisation.
    Les tables sans dépendances sont traitées en premier.
    Gère les cycles en les plaçant à la fin.
    """
    # Copie du graphe pour ne pas le modifier
    graph = {table: list(deps) for table, deps in dependency_graph.items()}
    
    # Calculer le nombre de dépendances SORTANTES (dépendances de cette table)
    # Pour le tri topologique, on veut traiter d'abord les tables avec le moins de dépendances
    out_degree = {table: len(graph.get(table, [])) for table in tables}
    
    # Calculer aussi les dépendances ENTRANTES (combien de tables dépendent de cette table)
    in_degree = {table: 0 for table in tables}
    for table in tables:
        for dep in graph.get(table, []):
            if dep in in_degree:
                in_degree[dep] += 1
    
    # Tables sans dépendances SORTANTES (ne dépendent de rien) = prioritaires
    queue = [table for table in tables if out_degree[table] == 0]
    result = []
    processed = set()
    
    # Traiter d'abord les tables sans dépendances
    while queue:
        queue.sort()  # Ordre déterministe
        current = queue.pop(0)
        if current in processed:
            continue
        result.append(current)
        processed.add(current)
        
        # Réduire le degré des tables qui dépendent de current
        for table in tables:
            if current in graph.get(table, []):
                out_degree[table] -= 1
                if out_degree[table] == 0 and table not in processed:
                    queue.append(table)
    
    # Ajouter les tables restantes (cycles ou dépendances complexes)
    remaining = [table for table in tables if table not in processed]
    if remaining:
        # Trier par nombre de dépendances (moins de dépendances = prioritaire)
        remaining.sort(key=lambda t: (out_degree[t], t))
        result.extend(remaining)
    
    return result

def find_row_by_unique_index(target_cursor, table_name, unique_index_cols, values):
    """
    Trouve une ligne existante dans la cible via un index unique (hors PK).
    Retourne la ligne complète si trouvée, None sinon.
    Gère correctement les NULL avec IS NULL.
    """
    if not unique_index_cols or len(unique_index_cols) != len(values):
        return None
    
    # Gérer correctement les NULL: "=" ne matche pas NULL -> utiliser IS NULL
    where_parts = []
    params = []
    for col, val in zip(unique_index_cols, values):
        if val is None:
            where_parts.append(f"[{col}] IS NULL")
        else:
            # Pour les chaînes, normaliser les espaces et la casse si nécessaire
            where_parts.append(f"[{col}] = ?")
            params.append(val)
    
    if not where_parts:
        return None
    
    where_clause = " AND ".join(where_parts)
    try:
        target_cursor.execute(f"SELECT * FROM [{table_name}] WHERE {where_clause}", tuple(params))
        row = target_cursor.fetchone()
        if row:
            # Récupérer les noms de colonnes (une seule fois pour optimiser)
            try:
                # Utiliser la description de la requête précédente si disponible
                columns = [desc[0] for desc in target_cursor.description]
            except:
                # Fallback : requête vide pour obtenir les colonnes
                target_cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
                columns = [desc[0] for desc in target_cursor.description]
            return {columns[i]: row[i] for i in range(len(columns))}
    except Exception as e:
        # En cas d'erreur, retourner None (la ligne n'existe peut-être pas)
        pass
    return None

def compare_rows_for_update(source_row_dict, target_row_dict, exclude_cols=None):
    """
    Compare deux lignes et retourne les colonnes qui diffèrent (hors colonnes exclues).
    Retourne (has_diff, diff_cols, update_values) où update_values est un dict {col: source_value}
    """
    if exclude_cols is None:
        exclude_cols = set()
    
    diff_cols = []
    update_values = {}
    
    for col in source_row_dict:
        if col in exclude_cols:
            continue
        source_val = source_row_dict.get(col)
        target_val = target_row_dict.get(col)
        
        # Comparaison robuste (gérer None, types différents)
        if source_val != target_val:
            # Vérifier si c'est vraiment différent (pas juste type)
            if source_val is None and target_val is None:
                continue
            if source_val is None or target_val is None:
                diff_cols.append(col)
                update_values[col] = source_val
            else:
                # Comparaison de valeurs
                try:
                    # Pour les nombres, comparer numériquement
                    if isinstance(source_val, (int, float)) and isinstance(target_val, (int, float)):
                        if abs(float(source_val) - float(target_val)) > 1e-10:
                            diff_cols.append(col)
                            update_values[col] = source_val
                    elif str(source_val) != str(target_val):
                        diff_cols.append(col)
                        update_values[col] = source_val
                except Exception:
                    # En cas de doute, considérer comme différent
                    diff_cols.append(col)
                    update_values[col] = source_val
    
    return len(diff_cols) > 0, diff_cols, update_values

def sync_databases():
    global sync_status
    sync_status = {'running': True, 'message': 'Démarrage...', 'progress': 0, 'details': [], 'code_version': PROJET21_CODE_VERSION}
    sync_status['details'].append(
        f"🧩 Version code Projet21: {PROJET21_CODE_VERSION} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
    )
    
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
        
        # Construire le graphe de dépendances et trier topologiquement
        sync_status['details'].append("🔍 Analyse des dépendances FK...")
        dependency_graph, referenced_tables = build_dependency_graph(source_cursor, target_cursor, source_tables)
        sorted_tables = topological_sort(source_tables, dependency_graph)
        
        # Log des dépendances pour diagnostic
        deps_count = sum(len(deps) for deps in dependency_graph.values())
        sync_status['details'].append(f"✓ Ordre de synchronisation déterminé ({len(sorted_tables)} tables, {deps_count} dépendances FK)")
        
        # Afficher quelques exemples d'ordre pour vérification
        if len(sorted_tables) > 0:
            sample_size = min(10, len(sorted_tables))
            sample_order = sorted_tables[:sample_size]
            sync_status['details'].append(f"  Exemples d'ordre: {', '.join(sample_order)}...")
        
        total_tables = len(sorted_tables)
        failed_tables = []
        
        # Première passe : synchroniser toutes les tables dans l'ordre topologique
        for i, table_name in enumerate(sorted_tables):
            sync_status['message'] = f"Traitement (Passe 1): {table_name}"
            sync_status['progress'] = int((i / total_tables) * 50)  # 50% pour la première passe
            
            try:
                if table_name not in target_tables:
                    try:
                        create_sql = get_table_definition(source_cursor, table_name)
                        target_cursor.execute(create_sql)
                        target_conn.commit()
                        sync_status['details'].append(f"✓ Table créée: {table_name}")
                    except Exception as create_err:
                        err_str = str(create_err)
                        if 'F_COMPTET' in err_str or 'regNOVA' in err_str:
                            sync_status['details'].append(f"✗ {table_name}: Impossible de créer la table (dépendance vers regNOVA.dbo.F_COMPTET: {err_str[:150]})")
                            continue
                        else:
                            raise
                
                pk_columns = get_primary_keys(source_cursor, table_name)
                
                if not pk_columns:
                    cols = get_table_columns(source_cursor, table_name)
                    pk_columns = [c[0] for c in cols]  # Utiliser toutes les colonnes comme clé
                    sync_status['details'].append(f"⚠ {table_name}: Pas de PK, utilisation de toutes les colonnes")
                
                # Récupérer les colonnes de la table source
                try:
                    source_cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
                    columns = [desc[0] for desc in source_cursor.description]
                    col_list = ", ".join([f"[{c}]" for c in columns])
                except Exception as col_err:
                    err_str = str(col_err)
                    if 'F_COMPTET' in err_str or 'regNOVA' in err_str:
                        # Table FACTURES a une dépendance vers une table externe inexistante (regNOVA.dbo.F_COMPTET)
                        sync_status['details'].append(f"✗ {table_name}: Table ignorée (dépendance vers regNOVA.dbo.F_COMPTET inexistante)")
                        continue
                    else:
                        raise
                
                # Récupérer les données source
                try:
                    source_cursor.execute(f"SELECT {col_list} FROM [{table_name}]")
                    source_rows = source_cursor.fetchall()
                    source_count = len(source_rows)
                except Exception as select_err:
                    err_str = str(select_err)
                    if 'F_COMPTET' in err_str or 'regNOVA' in err_str:
                        sync_status['details'].append(f"✗ {table_name}: Impossible de lire les données (dépendance vers regNOVA.dbo.F_COMPTET: {err_str[:150]})")
                        continue
                    else:
                        raise
                
                # Récupérer les PKs existants dans la cible
                target_cursor.execute(f"SELECT {', '.join([f'[{pk}]' for pk in pk_columns])} FROM [{table_name}]")
                existing_pks = set()
                for row in target_cursor.fetchall():
                    if len(pk_columns) == 1:
                        existing_pks.add(row[0])
                    else:
                        existing_pks.add(tuple(row))
                
                # OPTIMISATION : Charger toutes les lignes existantes en mémoire (pour UPDATE rapide)
                existing_rows_by_pk = {}
                if existing_pks:
                    target_cursor.execute(f"SELECT * FROM [{table_name}]")
                    for row in target_cursor.fetchall():
                        row_dict = {columns[i]: row[i] for i in range(len(columns))}
                        if len(pk_columns) == 1:
                            existing_rows_by_pk[row_dict[pk_columns[0]]] = row_dict
                        else:
                            pk_tuple = tuple(row_dict[pk] for pk in pk_columns)
                            existing_rows_by_pk[pk_tuple] = row_dict
                
                # Trouver les index des colonnes PK dans la liste des colonnes
                pk_indices = [columns.index(pk) for pk in pk_columns]
                
                # Vérifier si la table a une colonne IDENTITY
                identity_enabled = False
                if has_identity_column(target_cursor, table_name):
                    target_cursor.execute(f"SET IDENTITY_INSERT [{table_name}] ON")
                    identity_enabled = True
                
                inserted = 0
                updated = 0
                batch = []
                update_batch = []  # Batch pour les UPDATEs
                
                # Récupérer les index uniques (hors PK) pour détecter les conflits
                unique_indexes = _get_unique_indexes(target_cursor, table_name)
                
                # OPTIMISATION : Précharger toutes les combinaisons d'index unique existantes
                existing_unique_indexes = {}
                for idx_name, idx_cols in unique_indexes:
                    if idx_cols:
                        idx_col_list = ", ".join([f"[{c}]" for c in idx_cols])
                        target_cursor.execute(f"SELECT {idx_col_list} FROM [{table_name}] WHERE {' AND '.join([f'[{c}] IS NOT NULL' for c in idx_cols])}")
                        existing_unique_indexes[idx_name] = set()
                        for row in target_cursor.fetchall():
                            if len(idx_cols) == 1:
                                existing_unique_indexes[idx_name].add(row[0])
                            else:
                                existing_unique_indexes[idx_name].add(tuple(row))
                
                # Récupérer les contraintes FK pour vérifier avant insertion
                fk_constraints = get_foreign_keys(target_cursor, table_name)
                
                # OPTIMISATION : Précharger toutes les valeurs FK des tables référencées
                fk_values_cache = {}
                for fk_info in fk_constraints:
                    fk_name, parent_table, parent_col, ref_table, ref_col = fk_info
                    if ref_table not in fk_values_cache:
                        try:
                            # Charger toutes les valeurs FK (y compris 0)
                            # Utiliser IS NOT NULL pour exclure uniquement les NULL réels
                            target_cursor.execute(f"SELECT DISTINCT [{ref_col}] FROM [{ref_table}] WHERE [{ref_col}] IS NOT NULL")
                            fk_values_cache[ref_table] = {row[0] for row in target_cursor.fetchall()}
                            
                            # CORRECTION : Vérifier explicitement si 0 existe dans la table référencée
                            # et l'ajouter au cache si nécessaire (car 0 IS NOT NULL est vrai mais peut être exclu)
                            try:
                                target_cursor.execute(f"SELECT COUNT(*) FROM [{ref_table}] WHERE [{ref_col}] = 0")
                                if target_cursor.fetchone()[0] > 0:
                                    fk_values_cache[ref_table].add(0)
                            except:
                                pass  # Si la vérification échoue, continuer avec le cache existant
                        except Exception:
                            fk_values_cache[ref_table] = set()
                
                # Colonnes à exclure de la comparaison/UPDATE (ID et colonnes système)
                exclude_cols = set(pk_columns)  # Exclure la PK (ID)
                
                try:
                    for row in source_rows:
                        row_dict = {columns[i]: row[i] for i in range(len(columns))}
                        
                        # Extraire la valeur de la clé primaire
                        if len(pk_columns) == 1:
                            pk_value = row[pk_indices[0]]
                            pk_exists = pk_value in existing_pks
                        else:
                            pk_tuple = tuple(row[idx] for idx in pk_indices)
                            pk_exists = pk_tuple in existing_pks
                        
                        # Si PK existe déjà, vérifier si UPDATE nécessaire
                        if pk_exists:
                            # OPTIMISATION : Utiliser le cache en mémoire au lieu de requête SQL
                            pk_key = pk_value if len(pk_columns) == 1 else pk_tuple
                            target_row_dict = existing_rows_by_pk.get(pk_key)
                            
                            if target_row_dict:
                                has_diff, diff_cols, update_values = compare_rows_for_update(row_dict, target_row_dict, exclude_cols)
                                
                                if has_diff:
                                    # Ajouter au batch UPDATE au lieu d'exécuter immédiatement
                                    if len(pk_columns) == 1:
                                        where_pk = f"[{pk_columns[0]}] = ?"
                                        update_batch.append((diff_cols, update_values, pk_value, None))
                                    else:
                                        where_parts = [f"[{pk}] = ?" for pk in pk_columns]
                                        where_pk = " AND ".join(where_parts)
                                        update_batch.append((diff_cols, update_values, None, pk_tuple))
                            continue  # PK existe, pas besoin d'INSERT
                        
                        # Vérifier les conflits d'index unique AVANT insertion (OPTIMISÉ avec cache)
                        unique_conflict = False
                        for idx_name, idx_cols in unique_indexes:
                            idx_values = []
                            has_all_cols = True
                            has_null = False
                            for col in idx_cols:
                                if col not in row_dict:
                                    has_all_cols = False
                                    break
                                val = row_dict.get(col)
                                if val is None:
                                    has_null = True
                                idx_values.append(val)
                            
                            if not has_all_cols or has_null:
                                continue  # Index unique avec NULL autorise plusieurs NULL
                            
                            # OPTIMISATION : Vérifier dans le cache préchargé au lieu de requête SQL
                            idx_key = idx_values[0] if len(idx_cols) == 1 else tuple(idx_values)
                            if idx_key in existing_unique_indexes.get(idx_name, set()):
                                # Conflit détecté, récupérer la ligne existante (une seule requête)
                                existing_row = find_row_by_unique_index(target_cursor, table_name, idx_cols, idx_values)
                                if existing_row:
                                    unique_conflict = True
                                    
                                    # Comparer les colonnes (hors PK et colonnes de l'index unique)
                                    exclude_for_update = exclude_cols | set(idx_cols)
                                    has_diff, diff_cols, update_values = compare_rows_for_update(row_dict, existing_row, exclude_for_update)
                                    
                                    if has_diff:
                                        # Ajouter au batch UPDATE
                                        update_batch.append((diff_cols, update_values, None, None, idx_cols, idx_values))
                                    break
                        
                        if unique_conflict:
                            continue  # Déjà traité par UPDATE
                        
                        # Vérifier les FK avant insertion (OPTIMISÉ avec cache préchargé)
                        skip_row = False
                        for fk_info in fk_constraints:
                            fk_name, parent_table, parent_col, ref_table, ref_col = fk_info
                            try:
                                fk_col_idx = columns.index(parent_col)
                                fk_value = row[fk_col_idx]
                                if fk_value is not None:  # Ignorer les FK NULL
                                    # OPTIMISATION : Utiliser le cache préchargé au lieu de requête SQL
                                    if ref_table in fk_values_cache:
                                        if fk_value not in fk_values_cache[ref_table]:
                                            # CORRECTION : Pour la valeur 0, vérifier directement dans la table
                                            # car 0 peut être valide même s'il n'est pas dans le cache
                                            if fk_value == 0:
                                                try:
                                                    target_cursor.execute(f"SELECT COUNT(*) FROM [{ref_table}] WHERE [{ref_col}] = 0")
                                                    if target_cursor.fetchone()[0] > 0:
                                                        # 0 existe dans la table, l'ajouter au cache et continuer
                                                        fk_values_cache[ref_table].add(0)
                                                        continue  # FK valide, passer à la suivante
                                                except:
                                                    pass  # Si la vérification échoue, traiter comme FK manquante
                                            
                                            # FK n'existe pas encore, ignorer cette ligne (sera réessayée en passe suivante)
                                            skip_row = True
                                            break
                            except (ValueError, IndexError):
                                # Colonne FK non trouvée, continuer
                                pass
                        
                        if skip_row:
                            continue  # FK manquante, sera réessayée en passe suivante
                        
                        # Pas de conflit et FK OK : ajouter au batch pour INSERT
                        if len(pk_columns) == 1:
                            batch.append(list(row))
                            existing_pks.add(pk_value)
                        else:
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
                    
                    # OPTIMISATION : Exécuter les UPDATEs en batch
                    if update_batch:
                        for update_item in update_batch:
                            # Format: (diff_cols, update_values, pk_value, pk_tuple) ou (diff_cols, update_values, None, None, idx_cols, idx_values)
                            if len(update_item) == 4:
                                diff_cols, update_values, pk_value, pk_tuple = update_item
                                idx_cols, idx_values = None, None
                            else:
                                diff_cols, update_values, _, _, idx_cols, idx_values = update_item
                                pk_value, pk_tuple = None, None
                            
                            if pk_value is not None or pk_tuple is not None:
                                # UPDATE par PK
                                if pk_value is not None:
                                    where_pk = f"[{pk_columns[0]}] = ?"
                                    set_clauses = [f"[{col}] = ?" for col in diff_cols]
                                    set_values = [update_values[col] for col in diff_cols]
                                    update_sql = f"UPDATE [{table_name}] SET {', '.join(set_clauses)} WHERE {where_pk}"
                                    target_cursor.execute(update_sql, tuple(set_values) + (pk_value,))
                                else:
                                    where_parts = [f"[{pk}] = ?" for pk in pk_columns]
                                    where_pk = " AND ".join(where_parts)
                                    set_clauses = [f"[{col}] = ?" for col in diff_cols]
                                    set_values = [update_values[col] for col in diff_cols]
                                    update_sql = f"UPDATE [{table_name}] SET {', '.join(set_clauses)} WHERE {where_pk}"
                                    target_cursor.execute(update_sql, tuple(set_values) + pk_tuple)
                            elif idx_cols and idx_values:
                                # UPDATE par index unique
                                where_unique = " AND ".join([f"[{col}] = ?" for col in idx_cols])
                                set_clauses = [f"[{col}] = ?" for col in diff_cols]
                                set_values = [update_values[col] for col in diff_cols]
                                update_sql = f"UPDATE [{table_name}] SET {', '.join(set_clauses)} WHERE {where_unique}"
                                target_cursor.execute(update_sql, tuple(set_values) + tuple(idx_values))
                            updated += 1
                    
                    if inserted > 0 or updated > 0:
                        target_conn.commit()
                        msg_parts = []
                        if inserted > 0:
                            msg_parts.append(f"{inserted} ajoutés")
                        if updated > 0:
                            msg_parts.append(f"{updated} mis à jour")
                        sync_status['details'].append(f"✓ {table_name}: {', '.join(msg_parts)}")
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
                        source_pks = set()
                        missing_pks_list = []
                        try:
                            source_cursor.execute(f"SELECT {', '.join([f'[{pk}]' for pk in pk_columns])} FROM [{table_name}]")
                            for row in source_cursor.fetchall():
                                if len(pk_columns) == 1:
                                    pk_val = row[0]
                                    source_pks.add(pk_val)
                                    if pk_val not in existing_pks:
                                        missing_pks_list.append(pk_val)
                                else:
                                    pk_tuple = tuple(row)
                                    source_pks.add(pk_tuple)
                                    if pk_tuple not in existing_pks:
                                        missing_pks_list.append(pk_tuple)
                        except Exception as pk_err:
                            # Si la lecture des PKs échoue, réessayer avec une approche différente
                            sync_status['details'].append(f"  ⚠ Lecture PKs source échouée, utilisation d'une approche alternative...")
                            # On utilisera OPENROWSET directement avec WHERE basé sur les PKs manquantes identifiées précédemment
                            pass
                        
                        # Essayer d'abord avec INSERT ... SELECT via OPENROWSET (plus efficace)
                        identity_enabled = False
                        if has_identity_column(target_cursor, table_name):
                            target_cursor.execute(f"SET IDENTITY_INSERT [{table_name}] ON")
                            identity_enabled = True
                        
                        inserted = 0
                        updated_ultime = 0  # Compteur pour les UPDATEs dans la passe ultime
                        # Diagnostics: conserver quelques erreurs représentatives
                        ultime_diag = {
                            "openrowset": None,
                            "read": None,
                            "convert": None,
                            "insert_samples": [],
                            "openrowset_pk_samples": [],
                        }
                        
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
                            ultime_diag["openrowset"] = str(openrowset_err)
                            # Si OPENROWSET ne fonctionne pas, utiliser l'approche ligne par ligne
                            try:
                                # Index uniques disponibles pour résoudre les conflits (INSERT -> UPDATE)
                                unique_indexes = _get_unique_indexes(target_cursor, table_name)
                                exclude_cols = set(pk_columns)
                                updated_ultime = 0
                                
                                # Si on a la liste des PKs manquantes, construire une clause WHERE
                                if missing_pks_list and len(missing_pks_list) > 0:
                                    # Construire WHERE pour filtrer uniquement les PKs manquantes
                                    if len(pk_columns) == 1:
                                        pk_values = [pk for pk in missing_pks_list if pk is not None]
                                        if pk_values:
                                            # Limiter à 1000 pour éviter les requêtes trop longues
                                            for batch in [pk_values[i:i+1000] for i in range(0, len(pk_values), 1000)]:
                                                pk_strs = []
                                                for pk_val in batch:
                                                    if isinstance(pk_val, str):
                                                        pk_strs.append(f"'{pk_val.replace("'", "''")}'")
                                                    else:
                                                        pk_strs.append(str(pk_val))
                                                where_clause = f"WHERE [{pk_columns[0]}] IN ({','.join(pk_strs)})"
                                                source_cursor.execute(f"SELECT {col_list} FROM [{table_name}] {where_clause}")
                                                source_rows = source_cursor.fetchall()
                                                
                                                pk_indices = [columns.index(pk) for pk in pk_columns]
                                                placeholders = ", ".join(["?" for _ in columns])
                                                
                                                for row in source_rows:
                                                    row_dict = {columns[i]: row[i] for i in range(len(columns))}
                                                    
                                                    try:
                                                        target_cursor.execute(
                                                            f"INSERT INTO [{table_name}] ({col_list}) VALUES ({placeholders})",
                                                            list(row)
                                                        )
                                                        inserted += 1
                                                        if inserted % 100 == 0:
                                                            target_conn.commit()
                                                    except Exception as ins_err:
                                                        err_str = str(ins_err)
                                                        
                                                        # Si erreur de conflit d'index unique, essayer UPDATE (Option A)
                                                        if 'duplicate key' in err_str.lower() or 'unique index' in err_str.lower() or '2601' in err_str:
                                                            updated_via_unique = False
                                                            
                                                            for idx_name, idx_cols in unique_indexes:
                                                                if not idx_cols:
                                                                    continue
                                                                
                                                                # Construire les valeurs de l'index (NULL inclus)
                                                                idx_values = []
                                                                has_all = True
                                                                for col in idx_cols:
                                                                    if col not in row_dict:
                                                                        has_all = False
                                                                        break
                                                                    idx_values.append(row_dict.get(col))
                                                                if not has_all:
                                                                    continue
                                                                
                                                                # Utiliser find_row_by_unique_index pour gérer les NULL correctement
                                                                existing_row = find_row_by_unique_index(
                                                                    target_cursor, table_name, idx_cols, idx_values
                                                                )
                                                                if not existing_row:
                                                                    # Fallback : essayer de trouver la ligne avec une requête directe
                                                                    # (parfois find_row_by_unique_index échoue à cause de problèmes de types)
                                                                    try:
                                                                        where_parts_fallback = []
                                                                        where_params_fallback = []
                                                                        for col, val in zip(idx_cols, idx_values):
                                                                            if val is None:
                                                                                where_parts_fallback.append(f"[{col}] IS NULL")
                                                                            else:
                                                                                where_parts_fallback.append(f"[{col}] = ?")
                                                                                where_params_fallback.append(val)
                                                                        where_clause_fallback = " AND ".join(where_parts_fallback)
                                                                        target_cursor.execute(f"SELECT * FROM [{table_name}] WHERE {where_clause_fallback}", tuple(where_params_fallback))
                                                                        row_fallback = target_cursor.fetchone()
                                                                        if row_fallback:
                                                                            # Récupérer les noms de colonnes
                                                                            target_cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
                                                                            cols_fallback = [desc[0] for desc in target_cursor.description]
                                                                            existing_row = {cols_fallback[i]: row_fallback[i] for i in range(len(cols_fallback))}
                                                                    except Exception:
                                                                        pass
                                                                
                                                                if not existing_row:
                                                                    # Essayer une dernière fois avec une comparaison plus souple (types différents)
                                                                    # Parfois les types ne correspondent pas exactement (INT vs BIGINT, etc.)
                                                                    try:
                                                                        # Construire WHERE avec CONVERT pour normaliser les types
                                                                        where_parts_convert = []
                                                                        where_params_convert = []
                                                                        for col, val in zip(idx_cols, idx_values):
                                                                            if val is None:
                                                                                where_parts_convert.append(f"[{col}] IS NULL")
                                                                            else:
                                                                                # Essayer avec conversion de type pour les nombres
                                                                                if isinstance(val, (int, float)):
                                                                                    where_parts_convert.append(f"CAST([{col}] AS FLOAT) = ?")
                                                                                    where_params_convert.append(float(val))
                                                                                elif isinstance(val, str):
                                                                                    where_parts_convert.append(f"LTRIM(RTRIM([{col}])) = ?")
                                                                                    where_params_convert.append(val.strip())
                                                                                else:
                                                                                    where_parts_convert.append(f"[{col}] = ?")
                                                                                    where_params_convert.append(val)
                                                                        where_clause_convert = " AND ".join(where_parts_convert)
                                                                        target_cursor.execute(f"SELECT * FROM [{table_name}] WHERE {where_clause_convert}", tuple(where_params_convert))
                                                                        row_convert = target_cursor.fetchone()
                                                                        if row_convert:
                                                                            target_cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
                                                                            cols_convert = [desc[0] for desc in target_cursor.description]
                                                                            existing_row = {cols_convert[i]: row_convert[i] for i in range(len(cols_convert))}
                                                                    except Exception:
                                                                        pass
                                                                
                                                                if not existing_row:
                                                                    continue
                                                                
                                                                # Conflit détecté : UPDATE uniquement si différence
                                                                exclude_for_update = exclude_cols | set(idx_cols)
                                                                has_diff, diff_cols, update_values = compare_rows_for_update(
                                                                    row_dict, existing_row, exclude_for_update
                                                                )
                                                                if not has_diff:
                                                                    updated_via_unique = True
                                                                    break
                                                                
                                                                # WHERE unique avec gestion des NULL
                                                                where_parts = []
                                                                where_params = []
                                                                for col, val in zip(idx_cols, idx_values):
                                                                    if val is None:
                                                                        where_parts.append(f"[{col}] IS NULL")
                                                                    else:
                                                                        where_parts.append(f"[{col}] = ?")
                                                                        where_params.append(val)
                                                                where_unique = " AND ".join(where_parts)
                                                                
                                                                set_clauses = [f"[{col}] = ?" for col in diff_cols]
                                                                set_values = [update_values[col] for col in diff_cols]
                                                                update_sql = f"UPDATE [{table_name}] SET {', '.join(set_clauses)} WHERE {where_unique}"
                                                                target_cursor.execute(update_sql, tuple(set_values) + tuple(where_params))
                                                                
                                                                updated_ultime += 1
                                                                if updated_ultime % 100 == 0:
                                                                    target_conn.commit()
                                                                updated_via_unique = True
                                                                break
                                                            
                                                            if not updated_via_unique:
                                                                # Logging de diagnostic : pourquoi l'UPDATE n'a pas fonctionné
                                                                if len(ultime_diag["insert_samples"]) < 3:
                                                                    # Ajouter plus de détails sur pourquoi l'UPDATE a échoué
                                                                    diag_msg = f"Duplicate key mais UPDATE impossible: {str(ins_err)[:100]}"
                                                                    if unique_indexes:
                                                                        diag_msg += f" (index uniques testés: {len(unique_indexes)})"
                                                                    ultime_diag["insert_samples"].append(diag_msg)
                                                        else:
                                                            if len(ultime_diag["insert_samples"]) < 3:
                                                                ultime_diag["insert_samples"].append(str(ins_err))
                                                        continue
                                                
                                                if inserted > 0 or updated_ultime > 0:
                                                    target_conn.commit()
                                    else:
                                        # PK composite - lire tous et filtrer
                                        source_cursor.execute(f"SELECT {col_list} FROM [{table_name}]")
                                        source_rows = source_cursor.fetchall()
                                        
                                        pk_indices = [columns.index(pk) for pk in pk_columns]
                                        placeholders = ", ".join(["?" for _ in columns])
                                        
                                        for row in source_rows:
                                            pk_tuple = tuple(row[idx] for idx in pk_indices)
                                            if pk_tuple not in existing_pks:
                                                row_dict = {columns[i]: row[i] for i in range(len(columns))}
                                                
                                                try:
                                                    target_cursor.execute(
                                                        f"INSERT INTO [{table_name}] ({col_list}) VALUES ({placeholders})",
                                                        list(row)
                                                    )
                                                    inserted += 1
                                                    existing_pks.add(pk_tuple)
                                                    if inserted % 100 == 0:
                                                        target_conn.commit()
                                                except Exception as ins_err:
                                                    err_str = str(ins_err)
                                                    
                                                    # Si erreur de conflit d'index unique, essayer UPDATE (Option A)
                                                    if 'duplicate key' in err_str.lower() or 'unique index' in err_str.lower() or '2601' in err_str:
                                                        updated_via_unique = False
                                                        
                                                        for idx_name, idx_cols in unique_indexes:
                                                            if not idx_cols:
                                                                continue
                                                            
                                                            # Construire les valeurs de l'index (NULL inclus)
                                                            idx_values = []
                                                            has_all = True
                                                            for col in idx_cols:
                                                                if col not in row_dict:
                                                                    has_all = False
                                                                    break
                                                                idx_values.append(row_dict.get(col))
                                                            if not has_all:
                                                                continue
                                                            
                                                            # Utiliser find_row_by_unique_index pour gérer les NULL correctement
                                                            existing_row = find_row_by_unique_index(
                                                                target_cursor, table_name, idx_cols, idx_values
                                                            )
                                                            if not existing_row:
                                                                # Fallback : essayer de trouver la ligne avec une requête directe
                                                                try:
                                                                    where_parts_fallback = []
                                                                    where_params_fallback = []
                                                                    for col, val in zip(idx_cols, idx_values):
                                                                        if val is None:
                                                                            where_parts_fallback.append(f"[{col}] IS NULL")
                                                                        else:
                                                                            where_parts_fallback.append(f"[{col}] = ?")
                                                                            where_params_fallback.append(val)
                                                                    where_clause_fallback = " AND ".join(where_parts_fallback)
                                                                    target_cursor.execute(f"SELECT * FROM [{table_name}] WHERE {where_clause_fallback}", tuple(where_params_fallback))
                                                                    row_fallback = target_cursor.fetchone()
                                                                    if row_fallback:
                                                                        target_cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
                                                                        cols_fallback = [desc[0] for desc in target_cursor.description]
                                                                        existing_row = {cols_fallback[i]: row_fallback[i] for i in range(len(cols_fallback))}
                                                                except Exception:
                                                                    pass
                                                            
                                                            if not existing_row:
                                                                continue
                                                            
                                                            # Conflit détecté : UPDATE uniquement si différence
                                                            exclude_for_update = exclude_cols | set(idx_cols)
                                                            has_diff, diff_cols, update_values = compare_rows_for_update(
                                                                row_dict, existing_row, exclude_for_update
                                                            )
                                                            if not has_diff:
                                                                updated_via_unique = True
                                                                break
                                                            
                                                            # WHERE unique avec gestion des NULL
                                                            where_parts = []
                                                            where_params = []
                                                            for col, val in zip(idx_cols, idx_values):
                                                                if val is None:
                                                                    where_parts.append(f"[{col}] IS NULL")
                                                                else:
                                                                    where_parts.append(f"[{col}] = ?")
                                                                    where_params.append(val)
                                                            where_unique = " AND ".join(where_parts)
                                                            
                                                            set_clauses = [f"[{col}] = ?" for col in diff_cols]
                                                            set_values = [update_values[col] for col in diff_cols]
                                                            update_sql = f"UPDATE [{table_name}] SET {', '.join(set_clauses)} WHERE {where_unique}"
                                                            target_cursor.execute(update_sql, tuple(set_values) + tuple(where_params))
                                                            
                                                            updated_ultime += 1
                                                            if updated_ultime % 100 == 0:
                                                                target_conn.commit()
                                                            updated_via_unique = True
                                                            break
                                                        
                                                        if not updated_via_unique:
                                                            if len(ultime_diag["insert_samples"]) < 3:
                                                                ultime_diag["insert_samples"].append(str(ins_err))
                                                    else:
                                                        if len(ultime_diag["insert_samples"]) < 3:
                                                            ultime_diag["insert_samples"].append(str(ins_err))
                                                    continue
                                        
                                        if inserted > 0 or updated_ultime > 0:
                                            target_conn.commit()
                                else:
                                    # Lire tous les enregistrements de la source
                                    source_cursor.execute(f"SELECT {col_list} FROM [{table_name}]")
                                    source_rows = source_cursor.fetchall()
                                    
                                    pk_indices = [columns.index(pk) for pk in pk_columns]
                                    placeholders = ", ".join(["?" for _ in columns])
                                    
                                    # Index uniques disponibles pour résoudre les conflits (INSERT -> UPDATE)
                                    unique_indexes_ultime = _get_unique_indexes(target_cursor, table_name)
                                    exclude_cols_ultime = set(pk_columns)
                                    
                                    updated_ultime_2 = 0
                                    
                                    for row in source_rows:
                                        row_dict = {columns[i]: row[i] for i in range(len(columns))}
                                        
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
                                            if inserted % 100 == 0:
                                                target_conn.commit()
                                        except Exception as ins_err:
                                            err_str = str(ins_err)
                                            
                                            # Si erreur de conflit d'index unique, essayer UPDATE (Option A)
                                            if 'duplicate key' in err_str.lower() or 'unique index' in err_str.lower() or '2601' in err_str:
                                                updated_via_unique = False

                                                for idx_name, idx_cols in unique_indexes_ultime:
                                                    if not idx_cols:
                                                        continue

                                                    # Construire les valeurs de l'index (NULL inclus)
                                                    idx_values = []
                                                    has_all = True
                                                    for col in idx_cols:
                                                        if col not in row_dict:
                                                            has_all = False
                                                            break
                                                        idx_values.append(row_dict.get(col))
                                                    if not has_all:
                                                        continue

                                                    existing_row = find_row_by_unique_index(
                                                        target_cursor, table_name, idx_cols, idx_values
                                                    )
                                                    if not existing_row:
                                                        continue

                                                    # Conflit détecté : UPDATE uniquement si différence
                                                    exclude_for_update = exclude_cols_ultime | set(idx_cols)
                                                    has_diff, diff_cols, update_values = compare_rows_for_update(
                                                        row_dict, existing_row, exclude_for_update
                                                    )
                                                    if not has_diff:
                                                        updated_via_unique = True
                                                        break

                                                    # WHERE unique avec gestion des NULL
                                                    where_parts = []
                                                    where_params = []
                                                    for col, val in zip(idx_cols, idx_values):
                                                        if val is None:
                                                            where_parts.append(f"[{col}] IS NULL")
                                                        else:
                                                            where_parts.append(f"[{col}] = ?")
                                                            where_params.append(val)
                                                    where_unique = " AND ".join(where_parts)

                                                    set_clauses = [f"[{col}] = ?" for col in diff_cols]
                                                    set_values = [update_values[col] for col in diff_cols]
                                                    update_sql = f"UPDATE [{table_name}] SET {', '.join(set_clauses)} WHERE {where_unique}"
                                                    target_cursor.execute(update_sql, tuple(set_values) + tuple(where_params))

                                                    updated_ultime_2 += 1
                                                    if updated_ultime_2 % 100 == 0:
                                                        target_conn.commit()
                                                    updated_via_unique = True
                                                    break
                                                
                                                if not updated_via_unique:
                                                    if len(ultime_diag["insert_samples"]) < 3:
                                                        ultime_diag["insert_samples"].append(str(ins_err))
                                            else:
                                                if len(ultime_diag["insert_samples"]) < 3:
                                                    ultime_diag["insert_samples"].append(str(ins_err))
                                            # Ignorer les erreurs (doublons, types non supportés, etc.)
                                            continue
                                    
                                    if inserted > 0 or updated_ultime_2 > 0:
                                        target_conn.commit()
                                    updated_ultime += updated_ultime_2
                            except Exception as read_err:
                                ultime_diag["read"] = str(read_err)
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
                                    
                                    # Si on a la liste des PKs manquantes, filtrer directement
                                    if missing_pks_list and len(missing_pks_list) > 0 and len(pk_columns) == 1:
                                        pk_values = [pk for pk in missing_pks_list if pk is not None]
                                        # Traiter par lots de 1000
                                        for batch in [pk_values[i:i+1000] for i in range(0, len(pk_values), 1000)]:
                                            pk_strs = []
                                            for pk_val in batch:
                                                if isinstance(pk_val, str):
                                                    pk_strs.append(f"'{pk_val.replace("'", "''")}'")
                                                else:
                                                    pk_strs.append(str(pk_val))
                                            where_clause = f"WHERE [{pk_columns[0]}] IN ({','.join(pk_strs)})"
                                            source_cursor.execute(f"SELECT {converted_col_list} FROM [{table_name}] {where_clause}")
                                            source_rows = source_cursor.fetchall()
                                            
                                            pk_indices = [columns.index(pk) for pk in pk_columns]
                                            placeholders = ", ".join(["?" for _ in columns])
                                            
                                            for row in source_rows:
                                                try:
                                                    target_cursor.execute(
                                                        f"INSERT INTO [{table_name}] ({col_list}) VALUES ({placeholders})",
                                                        list(row)
                                                    )
                                                    inserted += 1
                                                    if inserted % 100 == 0:
                                                        target_conn.commit()
                                                except Exception as ins_err:
                                                    if len(ultime_diag["insert_samples"]) < 3:
                                                        ultime_diag["insert_samples"].append(str(ins_err))
                                                    continue
                                        
                                        if inserted > 0:
                                            target_conn.commit()
                                    else:
                                        # Lire tous et filtrer
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
                                                if len(ultime_diag["insert_samples"]) < 3:
                                                    ultime_diag["insert_samples"].append(str(insert_err))
                                                # Ignorer les erreurs d'insertion (doublons, contraintes, etc.)
                                                continue
                                        
                                        if inserted > 0:
                                            target_conn.commit()
                                except Exception as convert_err:
                                    ultime_diag["convert"] = str(convert_err)
                                    # Si même la conversion échoue, utiliser OPENROWSET avec INSERT ... SELECT direct
                                    # en construisant une clause WHERE pour chaque PK manquante
                                    try:
                                        # Utiliser missing_pks_list si disponible, sinon recalculer
                                        if missing_pks_list:
                                            missing_pks = set(missing_pks_list)
                                        else:
                                            missing_pks = source_pks - existing_pks
                                        
                                        if missing_pks:
                                            sync_status['details'].append(f"  Tentative avec OPENROWSET pour {len(missing_pks)} PKs manquantes...")
                                            
                                            # Construire une clause WHERE pour tous les PKs manquants
                                            if len(pk_columns) == 1:
                                                pk_values = [pk for pk in missing_pks if pk is not None]
                                                if pk_values:
                                                    # Construire la liste des valeurs
                                                    pk_strs = []
                                                    for pk_val in pk_values:
                                                        if isinstance(pk_val, str):
                                                            pk_strs.append(f"'{pk_val.replace("'", "''")}'")
                                                        else:
                                                            pk_strs.append(str(pk_val))
                                                    
                                                    if pk_strs:
                                                        # Diviser en lots de 1000 pour éviter les requêtes trop longues
                                                        batch_size = 1000
                                                        for batch_start in range(0, len(pk_strs), batch_size):
                                                            batch = pk_strs[batch_start:batch_start + batch_size]
                                                            pk_list = ",".join(batch)
                                                            where_clause = f"WHERE [{pk_columns[0]}] IN ({pk_list})"
                                                            
                                                            try:
                                                                insert_sql = f"""
                                                                    INSERT INTO [{table_name}] ({col_list})
                                                                    SELECT {select_col_list if has_unsupported_types else col_list}
                                                                    FROM OPENROWSET('SQLNCLI', 
                                                                        'Server={source_server};Database={source_db};UID={source_user};PWD={source_pwd}',
                                                                        'SELECT {select_col_list if has_unsupported_types else col_list} FROM [{table_name}] {where_clause}')
                                                                """
                                                                target_cursor.execute(insert_sql)
                                                                batch_inserted = target_cursor.rowcount
                                                                inserted += batch_inserted
                                                                target_conn.commit()
                                                            except Exception as batch_err:
                                                                if ultime_diag["openrowset_pk_samples"] is None:
                                                                    ultime_diag["openrowset_pk_samples"] = []
                                                                # Si le batch échoue, essayer PK par PK
                                                                for pk_str in batch:
                                                                    try:
                                                                        where_clause = f"WHERE [{pk_columns[0]}] = {pk_str}"
                                                                        insert_sql = f"""
                                                                            INSERT INTO [{table_name}] ({col_list})
                                                                            SELECT {select_col_list if has_unsupported_types else col_list}
                                                                            FROM OPENROWSET('SQLNCLI', 
                                                                                'Server={source_server};Database={source_db};UID={source_user};PWD={source_pwd}',
                                                                                'SELECT {select_col_list if has_unsupported_types else col_list} FROM [{table_name}] {where_clause}')
                                                                        """
                                                                        target_cursor.execute(insert_sql)
                                                                        inserted += 1
                                                                        if inserted % 50 == 0:
                                                                            target_conn.commit()
                                                                    except Exception as pk_err:
                                                                        if len(ultime_diag["openrowset_pk_samples"]) < 3:
                                                                            ultime_diag["openrowset_pk_samples"].append(str(pk_err))
                                                                        continue
                                                                if inserted > 0:
                                                                    target_conn.commit()
                                            else:
                                                # PK composite - traiter une par une
                                                for missing_pk in list(missing_pks)[:500]:  # Limiter à 500
                                                    try:
                                                        pk_conditions = []
                                                        for idx, pk_col in enumerate(pk_columns):
                                                            pk_val = missing_pk[idx]
                                                            if isinstance(pk_val, str):
                                                                pk_val_escaped = pk_val.replace("'", "''")
                                                                pk_conditions.append(f"[{pk_col}] = '{pk_val_escaped}'")
                                                            else:
                                                                pk_conditions.append(f"[{pk_col}] = {pk_val}")
                                                        pk_where = " AND ".join(pk_conditions)
                                                        
                                                        insert_sql = f"""
                                                            INSERT INTO [{table_name}] ({col_list})
                                                            SELECT {select_col_list if has_unsupported_types else col_list}
                                                            FROM OPENROWSET('SQLNCLI', 
                                                                'Server={source_server};Database={source_db};UID={source_user};PWD={source_pwd}',
                                                                'SELECT {select_col_list if has_unsupported_types else col_list} FROM [{table_name}] WHERE {pk_where}')
                                                        """
                                                        target_cursor.execute(insert_sql)
                                                        inserted += 1
                                                        if inserted % 50 == 0:
                                                            target_conn.commit()
                                                    except Exception as pk_err:
                                                        if len(ultime_diag["openrowset_pk_samples"]) < 3:
                                                            ultime_diag["openrowset_pk_samples"].append(str(pk_err))
                                                        continue
                                                
                                                if inserted > 0:
                                                    target_conn.commit()
                                    except Exception as final_err:
                                        sync_status['details'].append(f"  ⚠ Impossible d'insérer via OPENROWSET: {str(final_err)[:100]}")
                                        pass
                        
                        if inserted > 0 or updated_ultime > 0:
                            target_conn.commit()
                            msg_parts = []
                            if inserted > 0:
                                msg_parts.append(f"{inserted} ajoutés")
                            if updated_ultime > 0:
                                msg_parts.append(f"{updated_ultime} mis à jour")
                            sync_status['details'].append(f"✓ {table_name} (Ultime): {', '.join(msg_parts)} (FK désactivées)")
                        else:
                            # Vérifier s'il y avait vraiment des enregistrements manquants
                            if missing_count > 0:
                                sync_status['details'].append(f"⚠ {table_name} (Ultime): {missing_count} enregistrements manquants non insérés.")
                                # Ajouter un diagnostic concis (ce qui bloque réellement)
                                if ultime_diag.get("openrowset"):
                                    sync_status['details'].append(f"   - Détail OPENROWSET: {ultime_diag['openrowset'][:180]}")
                                if ultime_diag.get("read"):
                                    sync_status['details'].append(f"   - Détail lecture source: {ultime_diag['read'][:180]}")
                                if ultime_diag.get("convert"):
                                    sync_status['details'].append(f"   - Détail conversion: {ultime_diag['convert'][:180]}")
                                if ultime_diag.get("insert_samples"):
                                    for j, msg in enumerate(ultime_diag["insert_samples"][:3], start=1):
                                        sync_status['details'].append(f"   - Exemple erreur INSERT {j}: {msg[:180]}")
                                if ultime_diag.get("openrowset_pk_samples"):
                                    for j, msg in enumerate(ultime_diag["openrowset_pk_samples"][:3], start=1):
                                        sync_status['details'].append(f"   - Exemple erreur OPENROWSET/PK {j}: {msg[:180]}")
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
    # Toujours exposer la version de code réellement chargée,
    # même si sync_status a été réinitialisé ailleurs.
    payload = dict(sync_status) if isinstance(sync_status, dict) else {'running': False, 'message': '', 'progress': 0, 'details': []}
    payload['code_version'] = PROJET21_CODE_VERSION
    return jsonify(payload)

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


def _normalize_pyodbc_value(v):
    # Valeurs JSON-safe
    if isinstance(v, (datetime,)):
        return v.isoformat(sep=" ", timespec="seconds")
    return v


def _fetch_missing_pks_for_table(source_cursor, target_cursor, table_name):
    """
    Retourne (pk_columns, missing_pks_sorted).
    missing_pks_sorted: liste (peut être valeurs simples ou tuples).
    """
    pk_columns = get_primary_keys(source_cursor, table_name)
    if not pk_columns:
        # Pas de PK -> pas supporté pour "lignes manquantes" en mode efficace
        return [], []

    pk_list = ", ".join([f"[{pk}]" for pk in pk_columns])

    source_cursor.execute(f"SELECT {pk_list} FROM [{table_name}]")
    source_pks = set()
    for row in source_cursor.fetchall():
        if len(pk_columns) == 1:
            source_pks.add(row[0])
        else:
            source_pks.add(tuple(row))

    target_cursor.execute(f"SELECT {pk_list} FROM [{table_name}]")
    target_pks = set()
    for row in target_cursor.fetchall():
        if len(pk_columns) == 1:
            target_pks.add(row[0])
        else:
            target_pks.add(tuple(row))

    missing = list(source_pks - target_pks)
    try:
        missing.sort()
    except Exception:
        # types mixtes => tri non garanti
        pass
    return pk_columns, missing


def _select_rows_by_pks(cursor, table_name, pk_columns, pks):
    """
    Récupère les lignes complètes depuis la base (source) pour une liste de PK.
    """
    if not pks:
        return [], []

    if len(pk_columns) == 1:
        pk = pk_columns[0]
        placeholders = ", ".join(["?"] * len(pks))
        sql = f"SELECT * FROM [{table_name}] WHERE [{pk}] IN ({placeholders}) ORDER BY [{pk}]"
        cursor.execute(sql, tuple(pks))
    else:
        # composite PK: (A=? AND B=?) OR (A=? AND B=?)
        clauses = []
        params = []
        for pk_tuple in pks:
            sub = []
            for i, pk in enumerate(pk_columns):
                sub.append(f"[{pk}] = ?")
                params.append(pk_tuple[i])
            clauses.append("(" + " AND ".join(sub) + ")")
        sql = f"SELECT * FROM [{table_name}] WHERE " + " OR ".join(clauses)
        cursor.execute(sql, tuple(params))

    columns = [desc[0] for desc in cursor.description]
    rows = []
    for r in cursor.fetchall():
        rows.append({columns[i]: _normalize_pyodbc_value(r[i]) for i in range(len(columns))})
    return columns, rows


def _get_unique_indexes(target_cursor, table_name):
    """
    Retourne une liste d'index uniques (hors PK) sous forme de listes de colonnes.
    """
    target_cursor.execute("""
        SELECT i.name, c.name, ic.key_ordinal
        FROM sys.indexes i
        INNER JOIN sys.index_columns ic
            ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        INNER JOIN sys.columns c
            ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        INNER JOIN sys.tables t
            ON i.object_id = t.object_id
        WHERE t.name = ?
          AND i.is_unique = 1
          AND i.is_primary_key = 0
          AND ic.key_ordinal > 0
        ORDER BY i.name, ic.key_ordinal
    """, (table_name,))
    rows = target_cursor.fetchall()
    by_index = {}
    for idx_name, col_name, key_ordinal in rows:
        by_index.setdefault(idx_name, []).append((key_ordinal, col_name))
    indexes = []
    for idx_name, cols in by_index.items():
        cols_sorted = [c for _, c in sorted(cols, key=lambda x: x[0])]
        if cols_sorted:
            indexes.append((idx_name, cols_sorted))
    return indexes


def _get_column_types(source_cursor, table_name):
    cols = get_table_columns(source_cursor, table_name)
    # cols: (COLUMN_NAME, DATA_TYPE, ...)
    return {c[0]: (c[1] or '').lower() for c in cols}


def _diagnose_missing_row(table_name, row_dict, source_types, target_cursor):
    """
    Heuristique "cause de non synchronisation" (non destructive) :
    - conflit de clé unique (existe déjà dans cible sous un autre ID)
    - FK manquante (référence absente en cible)
    - types potentiellement problématiques
    """
    # 1) Conflit de clé unique (index unique hors PK)
    try:
        unique_indexes = _get_unique_indexes(target_cursor, table_name)
        for idx_name, cols in unique_indexes:
            values = []
            has_all = True
            has_null = False
            for c in cols:
                if c not in row_dict:
                    has_all = False
                    break
                v = row_dict.get(c)
                if v is None:
                    has_null = True
                values.append(v)
            if not has_all:
                continue
            # si une des colonnes est NULL, SQL Server autorise souvent plusieurs NULL selon index,
            # donc ce test est moins fiable
            if has_null:
                continue
            where = " AND ".join([f"[{c}] = ?" for c in cols])
            sql = f"SELECT TOP 1 1 FROM [{table_name}] WHERE {where}"
            target_cursor.execute(sql, tuple(values))
            if target_cursor.fetchone():
                return f"Conflit clé unique ({idx_name}) : la ligne existe déjà dans la cible (mêmes {cols})"
    except Exception:
        pass

    # 2) FK manquante
    try:
        fks = get_foreign_keys(target_cursor, table_name)
        missing_fks = []
        for fk_name, parent_table, parent_col, ref_table, ref_col in fks:
            if parent_col not in row_dict:
                continue
            v = row_dict.get(parent_col)
            if v is None:
                continue
            if not check_fk_exists(target_cursor, ref_table, ref_col, v):
                missing_fks.append(f"{parent_col} -> {ref_table}.{ref_col}={v}")
        if missing_fks:
            # limiter l'affichage
            shown = ", ".join(missing_fks[:3])
            more = f" (+{len(missing_fks)-3})" if len(missing_fks) > 3 else ""
            return f"Clé étrangère manquante en cible: {shown}{more}"
    except Exception:
        pass

    # 3) Types potentiellement non supportés / délicats
    try:
        problematic = {"sql_variant", "hierarchyid", "geography", "geometry", "image", "text", "ntext"}
        prob_cols = []
        for col, typ in source_types.items():
            if typ in problematic and col in row_dict:
                prob_cols.append(f"{col}({typ})")
        if prob_cols:
            return "Type(s) délicat(s): " + ", ".join(prob_cols[:6]) + ("..." if len(prob_cols) > 6 else "")
    except Exception:
        pass

    return "Cause inconnue (nécessite diagnostic SQL plus poussé)"


@projet21_bp.route('/missing-rows', methods=['GET'])
def missing_rows():
    """
    Renvoie les lignes manquantes (dans la cible) pour une table donnée,
    avec toutes les colonnes + valeurs depuis la SOURCE.

    Query:
      - table: nom de table (obligatoire)
      - limit: nb lignes (défaut 50, max 200)
      - offset: pagination (défaut 0)
    """
    table_name = (request.args.get('table') or '').strip()
    if not table_name:
        return jsonify({'success': False, 'error': "Paramètre 'table' obligatoire"}), 400

    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
    except Exception:
        return jsonify({'success': False, 'error': "Paramètres 'limit' et 'offset' doivent être des entiers"}), 400

    if limit < 1:
        limit = 1
    if limit > 200:
        limit = 200
    if offset < 0:
        offset = 0

    source_conn = None
    target_conn = None
    try:
        source_conn = get_connection(SOURCE_CONFIG, readonly=True)
        target_conn = get_connection(TARGET_CONFIG)
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()

        pk_columns, missing_pks = _fetch_missing_pks_for_table(source_cursor, target_cursor, table_name)
        if not pk_columns:
            return jsonify({
                'success': False,
                'error': f"Impossible d'afficher les lignes manquantes: table '{table_name}' sans clé primaire détectée."
            }), 400

        total_missing = len(missing_pks)
        page_pks = missing_pks[offset: offset + limit]

        columns, rows = _select_rows_by_pks(source_cursor, table_name, pk_columns, page_pks)
        source_types = _get_column_types(source_cursor, table_name)

        # Ajouter la cause à chaque ligne
        for r in rows:
            r["__cause"] = _diagnose_missing_row(table_name, r, source_types, target_cursor)

        return jsonify({
            'success': True,
            'table': table_name,
            'pk_columns': pk_columns,
            'total_missing': total_missing,
            'offset': offset,
            'limit': limit,
            'columns': columns,
            'rows': rows,
        })
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500
    finally:
        try:
            if source_conn:
                source_conn.close()
        except Exception:
            pass
        try:
            if target_conn:
                target_conn.close()
        except Exception:
            pass


def _select_row_by_pk(cursor, table_name, pk_columns, pk_value):
    """Retourne une ligne (dict) depuis la base cible pour une PK donnée, ou None."""
    if not pk_columns:
        return None
    if len(pk_columns) == 1:
        sql = f"SELECT * FROM [{table_name}] WHERE [{pk_columns[0]}] = ?"
        cursor.execute(sql, (pk_value,))
    else:
        # composite PK
        where = " AND ".join([f"[{c}] = ?" for c in pk_columns])
        sql = f"SELECT * FROM [{table_name}] WHERE {where}"
        cursor.execute(sql, tuple(pk_value))
    row = cursor.fetchone()
    if not row:
        return None
    columns = [desc[0] for desc in cursor.description]
    return {columns[i]: _normalize_pyodbc_value(row[i]) for i in range(len(columns))}


@projet21_bp.route('/compare-rows', methods=['GET'])
def compare_rows():
    """
    Génère un tableau de comparaison SOURCE vs CIBLE pour des PK "manquantes" (PK-based),
    en affichant sur une seule ligne les valeurs des 2 bases.

    - Si la PK n'existe pas en cible, on tente de trouver la ligne cible via un index unique (Option A).

    Query:
      - table: nom de table (obligatoire)
      - limit: nb lignes (défaut 10, max 50)
      - offset: pagination (défaut 0)
    """
    table_name = (request.args.get('table') or '').strip()
    if not table_name:
        return jsonify({'success': False, 'error': "Paramètre 'table' obligatoire"}), 400

    try:
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
    except Exception:
        return jsonify({'success': False, 'error': "Paramètres 'limit' et 'offset' doivent être des entiers"}), 400

    if limit < 1:
        limit = 1
    if limit > 50:
        limit = 50
    if offset < 0:
        offset = 0

    source_conn = None
    target_conn = None
    try:
        source_conn = get_connection(SOURCE_CONFIG, readonly=True)
        target_conn = get_connection(TARGET_CONFIG)
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()

        pk_columns, missing_pks = _fetch_missing_pks_for_table(source_cursor, target_cursor, table_name)
        if not pk_columns:
            return jsonify({
                'success': False,
                'error': f"Impossible de comparer: table '{table_name}' sans clé primaire détectée."
            }), 400

        total_missing = len(missing_pks)
        page_pks = missing_pks[offset: offset + limit]

        # Charger les lignes source (celles dont la PK est manquante côté cible)
        source_cols, source_rows = _select_rows_by_pks(source_cursor, table_name, pk_columns, page_pks)

        # Colonnes cible (pour affichage stable)
        target_cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
        target_cols = [desc[0] for desc in target_cursor.description]

        unique_indexes = _get_unique_indexes(target_cursor, table_name)

        out_rows = []
        for src in source_rows:
            pk_val = src.get(pk_columns[0]) if len(pk_columns) == 1 else tuple(src.get(c) for c in pk_columns)

            # 1) Essayer match exact par PK
            tgt = _select_row_by_pk(target_cursor, table_name, pk_columns, pk_val)
            matched_by = {'type': 'pk', 'columns': pk_columns} if tgt else None

            # 2) Sinon, essayer match par index unique (Option A)
            if not tgt:
                for idx_name, idx_cols in unique_indexes:
                    # ne tester que si toutes les colonnes existent dans la source
                    vals = []
                    ok = True
                    for c in idx_cols:
                        if c not in src:
                            ok = False
                            break
                        vals.append(src.get(c))
                    if not ok:
                        continue

                    tgt_candidate = find_row_by_unique_index(target_cursor, table_name, idx_cols, vals)
                    if tgt_candidate:
                        tgt = tgt_candidate
                        matched_by = {'type': 'unique', 'index': idx_name, 'columns': idx_cols}
                        break

            # Construire une ligne "plate" : SRC_* et CIBLE_*
            flat = {
                '__table': table_name,
                '__pk': pk_val,
                '__matched_by': matched_by,
            }
            for c in source_cols:
                flat[f"SRC.{c}"] = src.get(c)
            for c in target_cols:
                flat[f"CIBLE.{c}"] = (tgt.get(c) if tgt else None)

            out_rows.append(flat)

        # Colonnes du tableau (une seule ligne = toutes les colonnes)
        columns = ['__table', '__pk', '__matched_by'] + [f"SRC.{c}" for c in source_cols] + [f"CIBLE.{c}" for c in target_cols]

        return jsonify({
            'success': True,
            'table': table_name,
            'pk_columns': pk_columns,
            'total_missing': total_missing,
            'offset': offset,
            'limit': limit,
            'columns': columns,
            'rows': out_rows,
        })
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500
    finally:
        try:
            if source_conn:
                source_conn.close()
        except Exception:
            pass
        try:
            if target_conn:
                target_conn.close()
        except Exception:
            pass


@projet21_bp.route('/compare-rows.xlsx', methods=['GET'])
def compare_rows_xlsx():
    """
    Export Excel (.xlsx) du tableau de comparaison SOURCE vs CIBLE.
    Exporte TOUTES les lignes "manquantes PK" (PK-based) pour la table sélectionnée.

    Query:
      - table (obligatoire)
    """
    table_name = (request.args.get('table') or '').strip()
    if not table_name:
        return jsonify({'success': False, 'error': "Paramètre 'table' obligatoire"}), 400

    source_conn = None
    target_conn = None
    try:
        source_conn = get_connection(SOURCE_CONFIG, readonly=True)
        target_conn = get_connection(TARGET_CONFIG)
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()

        pk_columns, missing_pks = _fetch_missing_pks_for_table(source_cursor, target_cursor, table_name)
        if not pk_columns:
            return jsonify({
                'success': False,
                'error': f"Impossible d'exporter: table '{table_name}' sans clé primaire détectée."
            }), 400

        # Export complet
        source_cols, source_rows = _select_rows_by_pks(source_cursor, table_name, pk_columns, list(missing_pks))

        target_cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
        target_cols = [desc[0] for desc in target_cursor.description]

        unique_indexes = _get_unique_indexes(target_cursor, table_name)

        out_rows = []
        for src in source_rows:
            pk_val = src.get(pk_columns[0]) if len(pk_columns) == 1 else tuple(src.get(c) for c in pk_columns)
            tgt = _select_row_by_pk(target_cursor, table_name, pk_columns, pk_val)
            matched_by = {'type': 'pk', 'columns': pk_columns} if tgt else None

            if not tgt:
                for idx_name, idx_cols in unique_indexes:
                    vals = []
                    ok = True
                    for c in idx_cols:
                        if c not in src:
                            ok = False
                            break
                        vals.append(src.get(c))
                    if not ok:
                        continue
                    tgt_candidate = find_row_by_unique_index(target_cursor, table_name, idx_cols, vals)
                    if tgt_candidate:
                        tgt = tgt_candidate
                        matched_by = {'type': 'unique', 'index': idx_name, 'columns': idx_cols}
                        break

            flat = {'__table': table_name, '__pk': pk_val, '__matched_by': matched_by}
            for c in source_cols:
                flat[f"SRC.{c}"] = src.get(c)
            for c in target_cols:
                flat[f"CIBLE.{c}"] = (tgt.get(c) if tgt else None)
            out_rows.append(flat)

        columns = ['__table', '__pk', '__matched_by'] + [f"SRC.{c}" for c in source_cols] + [f"CIBLE.{c}" for c in target_cols]

        df = pd.DataFrame(out_rows, columns=columns)
        bio = BytesIO()
        with pd.ExcelWriter(bio, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Comparaison')

            # Mise en forme: colorer en rouge les valeurs différentes SRC vs CIBLE
            try:
                ws = writer.sheets.get('Comparaison')
                if ws is not None:
                    header_to_col = {}
                    for col_idx in range(1, ws.max_column + 1):
                        v = ws.cell(row=1, column=col_idx).value
                        if isinstance(v, str) and v:
                            header_to_col[v] = col_idx

                    red_fill = PatternFill(start_color="FFFFC7CE", end_color="FFFFC7CE", fill_type="solid")

                    # Comparer seulement les paires SRC.<col> et CIBLE.<col> basées sur les colonnes source
                    comparable_cols = [c for c in source_cols if f"SRC.{c}" in header_to_col and f"CIBLE.{c}" in header_to_col]

                    def _eq(a, b):
                        # Considérer None, "" et espaces comme équivalents
                        def _norm(x):
                            if x is None:
                                return ""
                            if isinstance(x, str):
                                return x.strip()
                            return x
                        na = _norm(a)
                        nb = _norm(b)
                        # Comparaison robuste par string si types différents
                        if type(na) != type(nb):
                            return str(na) == str(nb)
                        return na == nb

                    for row_idx in range(2, ws.max_row + 1):
                        for c in comparable_cols:
                            src_col_idx = header_to_col[f"SRC.{c}"]
                            tgt_col_idx = header_to_col[f"CIBLE.{c}"]
                            src_val = ws.cell(row=row_idx, column=src_col_idx).value
                            tgt_val = ws.cell(row=row_idx, column=tgt_col_idx).value
                            if not _eq(src_val, tgt_val):
                                ws.cell(row=row_idx, column=src_col_idx).fill = red_fill
                                ws.cell(row=row_idx, column=tgt_col_idx).fill = red_fill
            except Exception:
                # Ne pas bloquer l'export si la mise en forme échoue
                pass
        bio.seek(0)

        filename = f"comparaison_{table_name}_TOTAL_{len(missing_pks)}.xlsx"
        return send_file(
            bio,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500
    finally:
        try:
            if source_conn:
                source_conn.close()
        except Exception:
            pass
        try:
            if target_conn:
                target_conn.close()
        except Exception:
            pass


@projet21_bp.route('/analyse-schema-papiers')
def analyse_schema_papiers():
    """
    Analyse le schéma de la base de données et génère un rapport détaillé
    listant toutes les tables ayant une relation directe ou indirecte
    avec PAPIERS_ARTICLES et PAPIERS_IMPRIMEURS
    """
    try:
        from collections import defaultdict, deque
        
        conn = get_connection(TARGET_CONFIG, readonly=True)
        cursor = conn.cursor()
        
        # Récupérer toutes les clés étrangères
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
        reverse_graph = defaultdict(set)
        
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
            
            # Construire le graphe inversé
            reverse_graph[referenced_table].add(parent_table)
        
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
            return jsonify({
                'success': False,
                'error': f"Tables non trouvées: {', '.join(missing_tables)}"
            }), 404
        
        # Trouver toutes les tables liées (BFS)
        related_tables = set()
        visited = set()
        queue = deque()
        
        for table in start_tables:
            if table not in visited:
                visited.add(table)
                queue.append((table, 0))
                related_tables.add(table)
        
        # Parcourir les enfants et parents directs
        for table in start_tables:
            if table in reverse_graph:
                for child_table in reverse_graph[table]:
                    if child_table not in visited:
                        visited.add(child_table)
                        queue.append((child_table, 1))
                        related_tables.add(child_table)
            
            if table in fk_dict:
                for fk in fk_dict[table]:
                    parent_table = fk['referenced_table']
                    if parent_table not in visited:
                        visited.add(parent_table)
                        queue.append((parent_table, 1))
                        related_tables.add(parent_table)
        
        # BFS pour relations indirectes
        while queue:
            current_table, level = queue.popleft()
            
            if current_table in reverse_graph:
                for child_table in reverse_graph[current_table]:
                    if child_table not in visited:
                        visited.add(child_table)
                        queue.append((child_table, level + 1))
                        related_tables.add(child_table)
            
            if current_table in fk_dict:
                for fk in fk_dict[current_table]:
                    parent_table = fk['referenced_table']
                    if parent_table not in visited:
                        visited.add(parent_table)
                        queue.append((parent_table, level + 1))
                        related_tables.add(parent_table)
        
        # Construire le rapport détaillé
        report = {
            'generation_date': datetime.now().isoformat(),
            'start_tables': start_tables,
            'summary': {
                'total_related_tables': len(related_tables),
                'start_tables_count': len(start_tables),
                'related_tables_count': len(related_tables) - len(start_tables)
            },
            'tables': {}
        }
        
        # Séparer par type de relation
        direct_children = set()
        direct_parents = set()
        
        for table in related_tables:
            if table in start_tables:
                continue
            
            for start_table in start_tables:
                if start_table in reverse_graph and table in reverse_graph[start_table]:
                    direct_children.add(table)
                if start_table in fk_dict:
                    for fk in fk_dict[start_table]:
                        if fk['referenced_table'] == table:
                            direct_parents.add(table)
        
        report['summary']['direct_children_count'] = len(direct_children)
        report['summary']['direct_parents_count'] = len(direct_parents)
        report['summary']['indirect_related_count'] = len(related_tables) - len(start_tables) - len(direct_children) - len(direct_parents)
        
        # Détails par table
        for table in sorted(related_tables):
            relation_types = []
            if table in start_tables:
                relation_types.append('start')
            if table in direct_children:
                relation_types.append('direct_child')
            if table in direct_parents:
                relation_types.append('direct_parent')
            if table not in start_tables and table not in direct_children and table not in direct_parents:
                relation_types.append('indirect')
            
            # Relations FK
            fk_relations = []
            if table in fk_dict:
                for fk in fk_dict[table]:
                    fk_relations.append({
                        'type': 'references',
                        'referenced_table': fk['referenced_table'],
                        'fk_name': fk['details']['fk_name'],
                        'parent_column': fk['details']['parent_column'],
                        'referenced_column': fk['details']['referenced_column'],
                        'is_disabled': bool(fk['details']['is_disabled']),
                        'is_not_trusted': bool(fk['details']['is_not_trusted'])
                    })
            
            if table in reverse_graph:
                for child_table in reverse_graph[table]:
                    fk_relations.append({
                        'type': 'referenced_by',
                        'referencing_table': child_table
                    })
            
            # Compter les lignes (peut être lent)
            try:
                cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                row_count = cursor.fetchone()[0]
            except:
                row_count = None
            
            # Colonnes
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """, (table,))
            
            columns = []
            for col_row in cursor.fetchall():
                columns.append({
                    'name': col_row.COLUMN_NAME,
                    'type': col_row.DATA_TYPE,
                    'nullable': col_row.IS_NULLABLE == 'YES'
                })
            
            report['tables'][table] = {
                'relation_types': relation_types,
                'row_count': row_count,
                'column_count': len(columns),
                'columns': columns,
                'foreign_key_relations': fk_relations
            }
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
