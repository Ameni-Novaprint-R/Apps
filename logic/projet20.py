"""
Logique pour le Projet 20 - Analyse et affichage des données de dossier
Analyse la base de données pour identifier les relations et afficher toutes les données liées à un numéro de dossier
"""
from db import get_db_cursor
import re

def search_numeros_dossier(search_term):
    """
    Recherche les numéros de dossier dans COMMANDES (autocomplete)
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT Numero
            FROM COMMANDES
            WHERE Numero LIKE ?
            AND Numero IS NOT NULL
            ORDER BY Numero
        """, (f'%{search_term}%',))
        return [row.Numero for row in cursor.fetchall()]

def sanitize_table_name(table_name):
    """
    Nettoie le nom de table pour éviter les injections SQL
    Ne permet que les caractères alphanumériques et underscore
    """
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', table_name):
        raise ValueError(f"Nom de table invalide: {table_name}")
    return table_name

def sanitize_column_name(column_name):
    """
    Nettoie le nom de colonne pour éviter les injections SQL
    """
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', column_name):
        raise ValueError(f"Nom de colonne invalide: {column_name}")
    return column_name

def get_all_tables():
    """
    Récupère toutes les tables de la base de données (sauf les tables système)
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            AND TABLE_NAME NOT LIKE 'sys%'
            AND TABLE_NAME NOT LIKE 'MS%'
            AND TABLE_NAME NOT LIKE 'dt%'
            ORDER BY TABLE_NAME
        """)
        return [row.TABLE_NAME for row in cursor.fetchall()]

def get_table_columns(table_name):
    """
    Récupère toutes les colonnes d'une table
    """
    table_name = sanitize_table_name(table_name)
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """, table_name)
        return [(row.COLUMN_NAME, row.DATA_TYPE) for row in cursor.fetchall()]

def try_get_table_data(cursor, table_name, commande_id, numero_dossier):
    """
    Essaie de récupérer les données d'une table en testant toutes les méthodes possibles
    Retourne les lignes si trouvées, None sinon
    """
    table_name_clean = sanitize_table_name(table_name)
    
    # Récupérer les colonnes de la table
    try:
        columns_info = get_table_columns(table_name_clean)
        if not columns_info:
            return None
        column_names = [col[0] for col in columns_info]
    except:
        return None
    
    # Méthode 1: Table COMMANDES elle-même
    if table_name_clean == 'COMMANDES':
        try:
            cursor.execute(f"SELECT * FROM [{table_name_clean}] WHERE Numero = ?", numero_dossier)
            rows = cursor.fetchall()
            if rows:
                return rows
        except:
            pass
        return None
    
    # Méthode 2: Clé étrangère directe vers COMMANDES.ID
    try:
        cursor.execute(f"""
            SELECT COL_NAME(fc.parent_object_id, fc.parent_column_id) AS ColumnName
            FROM sys.foreign_keys AS fk
            INNER JOIN sys.foreign_key_columns AS fc
                ON fk.object_id = fc.constraint_object_id
            WHERE OBJECT_NAME(fk.parent_object_id) = '{table_name_clean}'
            AND OBJECT_NAME(fk.referenced_object_id) = 'COMMANDES'
        """)
        fk_result = cursor.fetchone()
        if fk_result:
            col_name = sanitize_column_name(fk_result.ColumnName)
            cursor.execute(f"SELECT * FROM [{table_name_clean}] WHERE [{col_name}] = ?", commande_id)
            rows = cursor.fetchall()
            if rows:
                return rows
    except Exception as e:
        pass
    
    # Méthode 3: GP_FICHES_TRAVAIL (ID_COMMANDE)
    if table_name_clean == 'GP_FICHES_TRAVAIL':
        try:
            cursor.execute(f"SELECT * FROM [{table_name_clean}] WHERE ID_COMMANDE = ?", commande_id)
            rows = cursor.fetchall()
            if rows:
                return rows
        except:
            pass
    
    # Méthode 4: Tables liées à GP_FICHES_TRAVAIL (GP_TRAITEMENTS, GP_FICHES_OPERATIONS, etc.)
    # Vérifier si la table a une clé étrangère vers GP_FICHES_TRAVAIL
    try:
        cursor.execute(f"""
            SELECT COL_NAME(fc.parent_object_id, fc.parent_column_id) AS ColumnName
            FROM sys.foreign_keys AS fk
            INNER JOIN sys.foreign_key_columns AS fc
                ON fk.object_id = fc.constraint_object_id
            WHERE OBJECT_NAME(fk.parent_object_id) = '{table_name_clean}'
            AND OBJECT_NAME(fk.referenced_object_id) = 'GP_FICHES_TRAVAIL'
        """)
        fk_result = cursor.fetchone()
        if fk_result:
            col_name = sanitize_column_name(fk_result.ColumnName)
            cursor.execute(f"""
                SELECT T.* FROM [{table_name_clean}] T
                INNER JOIN GP_FICHES_TRAVAIL FT ON T.[{col_name}] = FT.ID
                WHERE FT.ID_COMMANDE = ?
            """, commande_id)
            rows = cursor.fetchall()
            if rows:
                return rows
    except Exception as e:
        pass
    
    # Méthode 5: GP_TRAITEMENTS (peut avoir ID_FICHE_TRAVAIL ou être référencé différemment)
    if table_name_clean == 'GP_TRAITEMENTS':
        # Essayer avec ID_FICHE_TRAVAIL
        if 'ID_FICHE_TRAVAIL' in column_names:
            try:
                col_name = sanitize_column_name('ID_FICHE_TRAVAIL')
                cursor.execute(f"""
                    SELECT T.* FROM [{table_name_clean}] T
                    INNER JOIN GP_FICHES_TRAVAIL FT ON T.[{col_name}] = FT.ID
                    WHERE FT.ID_COMMANDE = ?
                """, commande_id)
                rows = cursor.fetchall()
                if rows:
                    return rows
            except:
                pass
    
    # Méthode 6: GP_POSTES via GP_FICHES_TRAVAIL.ID_POSTE
    if table_name_clean == 'GP_POSTES':
        try:
            cursor.execute(f"""
                SELECT DISTINCT P.* FROM [{table_name_clean}] P
                INNER JOIN GP_FICHES_TRAVAIL FT ON P.ID = FT.ID_POSTE
                WHERE FT.ID_COMMANDE = ?
            """, commande_id)
            rows = cursor.fetchall()
            if rows:
                return rows
        except:
            pass
    
    # Méthode 7: GP_SERVICES via GP_POSTES.ID_SERVICE et GP_FICHES_TRAVAIL
    if table_name_clean == 'GP_SERVICES':
        try:
            cursor.execute(f"""
                SELECT DISTINCT S.* FROM [{table_name_clean}] S
                INNER JOIN GP_POSTES P ON S.ID = P.ID_SERVICE
                INNER JOIN GP_FICHES_TRAVAIL FT ON P.ID = FT.ID_POSTE
                WHERE FT.ID_COMMANDE = ?
            """, commande_id)
            rows = cursor.fetchall()
            if rows:
                return rows
        except:
            pass
    
    # Méthode 8: GP_FICHES_OPERATIONS via GP_FICHES_TRAVAIL
    if table_name_clean == 'GP_FICHES_OPERATIONS':
        # Chercher une colonne qui pourrait lier à GP_FICHES_TRAVAIL
        for col_name in column_names:
            if 'FICHE' in col_name.upper() or 'ID_FICHE' in col_name.upper():
                try:
                    col_clean = sanitize_column_name(col_name)
                    cursor.execute(f"""
                        SELECT T.* FROM [{table_name_clean}] T
                        INNER JOIN GP_FICHES_TRAVAIL FT ON T.[{col_clean}] = FT.ID
                        WHERE FT.ID_COMMANDE = ?
                    """, commande_id)
                    rows = cursor.fetchall()
                    if rows:
                        return rows
                except:
                    continue
    
    # Méthode 9: Recherche par colonnes avec noms similaires (ID_COMMANDE, Numero_COMMANDES, etc.)
    for col_name in column_names:
        col_upper = col_name.upper()
        # Chercher des colonnes qui pourraient contenir l'ID de la commande
        if 'ID_COMMANDE' in col_upper or 'COMMANDE_ID' in col_upper:
            try:
                col_clean = sanitize_column_name(col_name)
                cursor.execute(f"SELECT * FROM [{table_name_clean}] WHERE [{col_clean}] = ?", commande_id)
                test_rows = cursor.fetchall()
                if test_rows:
                    return test_rows
            except:
                continue
        
        # Chercher des colonnes qui pourraient contenir le numéro de dossier
        if 'NUMERO' in col_upper or 'NUM_DOSSIER' in col_upper or 'NUMDOSSIER' in col_upper:
            try:
                col_clean = sanitize_column_name(col_name)
                # Essayer avec le numéro directement
                try:
                    cursor.execute(f"SELECT * FROM [{table_name_clean}] WHERE [{col_clean}] = ?", numero_dossier)
                    test_rows = cursor.fetchall()
                    if test_rows:
                        return test_rows
                except:
                    pass
                # Essayer avec CAST
                try:
                    cursor.execute(f"SELECT * FROM [{table_name_clean}] WHERE CAST([{col_clean}] AS NVARCHAR) = ?", numero_dossier)
                    test_rows = cursor.fetchall()
                    if test_rows:
                        return test_rows
                except:
                    pass
            except:
                continue
    
    return None

def get_dossier_data(numero_dossier):
    """
    Récupère toutes les données liées à un numéro de dossier
    Analyse TOUTES les tables de la base de données
    Retourne un dictionnaire avec table -> colonne -> valeurs
    """
    result = {}
    
    with get_db_cursor() as cursor:
        # D'abord, obtenir l'ID de la commande
        cursor.execute("SELECT ID FROM COMMANDES WHERE Numero = ?", numero_dossier)
        id_row = cursor.fetchone()
        if not id_row:
            return result  # Pas de commande trouvée
        commande_id = id_row[0]
        
        # Récupérer TOUTES les tables de la base de données
        all_tables = get_all_tables()
        
        # Pour chaque table, essayer de récupérer les données
        for table_name in all_tables:
            try:
                table_name_clean = sanitize_table_name(table_name)
                
                # Essayer de récupérer les données
                rows = try_get_table_data(cursor, table_name_clean, commande_id, numero_dossier)
                
                if rows:
                    # Récupérer les noms des colonnes
                    column_names = [col[0] for col in cursor.description]
                    
                    # Traiter les lignes trouvées
                    # Pour chaque colonne, collecter toutes les valeurs de tous les enregistrements
                    table_data = {}
                    for col_idx, col_name in enumerate(column_names):
                        values = []
                        for row in rows:
                            value = row[col_idx]
                            # Filtrer les valeurs 0 et les chaînes vides/null
                            if value is None:
                                continue
                            if isinstance(value, (int, float)) and value == 0:
                                continue
                            if isinstance(value, str) and value.strip() == '':
                                continue
                            values.append(str(value))
                        
                        if values:
                            table_data[col_name] = values
                    
                    if table_data:
                        result[table_name_clean] = table_data
                        
            except Exception as e:
                # Erreur sur cette table, on continue
                # Ne pas afficher toutes les erreurs pour ne pas polluer les logs
                continue
        
        return result
