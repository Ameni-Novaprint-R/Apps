#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script d'exécution sécurisée du réalignement des IDs - PAPIERS_ARTICLES
Exécute le script SQL avec transactions, vérifications et rollback automatique
"""

import pyodbc
import sys
from datetime import datetime

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

def read_sql_file(filename):
    """Lit le contenu d'un fichier SQL"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[ERREUR] Impossible de lire le fichier {filename}: {e}")
        return None

def execute_realignment():
    """Exécute le réalignement des IDs de manière sécurisée"""
    
    print("="*80)
    print("REALIGNEMENT DES IDs - PAPIERS_ARTICLES")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    source_conn = None
    target_conn = None
    
    try:
        # Connexions
        print("[1/6] Connexion aux bases de donnees...")
        source_conn = get_connection(SOURCE_CONFIG, readonly=True)
        print("  [OK] Connexion a Novaprint (source) etablie")
        
        target_conn = get_connection(TARGET_CONFIG, readonly=False)
        print("  [OK] Connexion a novaprint_restored (cible) etablie")
        print()
        
        # Vérifications préalables
        print("[2/6] Verifications prealables...")
        target_cursor = target_conn.cursor()
        
        # Vérifier le nombre d'enregistrements
        source_cursor = source_conn.cursor()
        source_cursor.execute("SELECT COUNT(*) FROM PAPIERS_ARTICLES")
        source_count = source_cursor.fetchone()[0]
        
        target_cursor.execute("SELECT COUNT(*) FROM PAPIERS_ARTICLES")
        target_count = target_cursor.fetchone()[0]
        
        print(f"  Enregistrements source: {source_count:,}")
        print(f"  Enregistrements cible: {target_count:,}")
        
        if source_count != target_count:
            diff = target_count - source_count
            if diff > 0:
                print(f"  [ATTENTION] {diff:,} enregistrements supplementaires en cible")
                print(f"  Ces enregistrements ne seront pas realignes (ils n'existent pas en source)")
            else:
                print(f"  [ATTENTION] {abs(diff):,} enregistrements manquants en cible")
        else:
            print("  [OK] Nombre d'enregistrements identique")
        
        # Vérifier les références orphelines
        target_cursor.execute("""
            SELECT COUNT(*)
            FROM PAPIERS_TARIF_FMT ptf
            LEFT JOIN PAPIERS_ARTICLES pa ON ptf.ID_ARTICLE = pa.ID
            WHERE ptf.ID_ARTICLE IS NOT NULL AND pa.ID IS NULL
        """)
        orphan_count = target_cursor.fetchone()[0]
        
        if orphan_count > 0:
            print(f"  [ATTENTION] {orphan_count:,} references orphelines detectees")
        else:
            print("  [OK] Aucune reference orpheline")
        print()
        
        # Créer la table de mapping
        print("[3/6] Creation de la table de mapping...")
        
        # Identifier les colonnes communes aux deux tables (sauf ID)
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
        
        # Utiliser uniquement les colonnes communes
        columns = sorted(list(source_columns & target_columns))
        
        if not columns:
            print("  [ERREUR] Aucune colonne commune trouvee entre source et cible")
            return False
        
        print(f"  Colonnes de correspondance ({len(columns)}): {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
        
        # Créer la table de mapping
        target_cursor.execute("""
            IF OBJECT_ID('tempdb..#ID_MAPPING_PAPIERS_ARTICLES', 'U') IS NOT NULL
                DROP TABLE #ID_MAPPING_PAPIERS_ARTICLES;
            
            CREATE TABLE #ID_MAPPING_PAPIERS_ARTICLES (
                ancien_ID INT NOT NULL,
                nouveau_ID INT NOT NULL,
                PRIMARY KEY (ancien_ID)
            );
        """)
        
        # Construire la requête dynamique pour lire toutes les colonnes
        columns_str = ', '.join(columns)
        
        print("  Lecture des donnees source et cible...")
        
        # Lire les données source
        source_cursor.execute(f"""
            SELECT ID, {columns_str}
            FROM PAPIERS_ARTICLES
        """)
        source_rows = source_cursor.fetchall()
        source_data = {}
        for row in source_rows:
            # Utiliser toutes les colonnes (sauf ID) comme clé de correspondance
            key = tuple(row[1:])  # Toutes les colonnes sauf ID
            source_data[key] = row[0]  # ID source
        
        print(f"  [OK] {len(source_data):,} enregistrements lus depuis la source")
        
        # Lire les données cible
        target_cursor.execute(f"""
            SELECT ID, {columns_str}
            FROM PAPIERS_ARTICLES
        """)
        target_rows = target_cursor.fetchall()
        
        # Créer le mapping
        mapping = []
        for row in target_rows:
            target_id = row[0]
            key = tuple(row[1:])  # Toutes les colonnes sauf ID
            
            if key in source_data:
                source_id = source_data[key]
                if target_id != source_id:
                    mapping.append((target_id, source_id))
        
        if not mapping:
            print("  [INFO] Aucun ID a realigner - tous les IDs correspondent deja")
            target_conn.commit()
            return True
        
        print(f"  [OK] {len(mapping):,} correspondances trouvees")
        
        # Insérer le mapping dans la table temporaire
        target_cursor.executemany("""
            INSERT INTO #ID_MAPPING_PAPIERS_ARTICLES (ancien_ID, nouveau_ID)
            VALUES (?, ?)
        """, mapping)
        target_conn.commit()
        print()
        
        # Vérifier les conflits
        print("[4/6] Verification des conflits potentiels...")
        target_cursor.execute("""
            SELECT COUNT(*)
            FROM #ID_MAPPING_PAPIERS_ARTICLES m
            INNER JOIN PAPIERS_ARTICLES pa ON m.nouveau_ID = pa.ID
            WHERE pa.ID NOT IN (SELECT ancien_ID FROM #ID_MAPPING_PAPIERS_ARTICLES)
        """)
        conflict_count = target_cursor.fetchone()[0]
        
        if conflict_count > 0:
            print(f"  [ERREUR] {conflict_count} conflits d'IDs detectes!")
            return False
        
        print("  [OK] Aucun conflit detecte")
        print()
        
        # Démarrer la transaction
        print("[5/6] Execution du realignement (dans une transaction)...")
        target_conn.autocommit = False
        
        try:
            # ÉTAPE 1: Désactiver temporairement la contrainte FK (en premier!)
            print("  Desactivation temporaire de la contrainte FK...")
            target_cursor.execute("""
                ALTER TABLE PAPIERS_TARIF_FMT
                NOCHECK CONSTRAINT FK__PAPIERS_T__ID_AR__48717679
            """)
            
            # ÉTAPE 2: Mettre à jour les références FK
            print("  Mise a jour des references FK...")
            target_cursor.execute("""
                UPDATE PAPIERS_TARIF_FMT
                SET ID_ARTICLE = m.nouveau_ID
                FROM PAPIERS_TARIF_FMT ptf
                INNER JOIN #ID_MAPPING_PAPIERS_ARTICLES m ON ptf.ID_ARTICLE = m.ancien_ID
                WHERE ptf.ID_ARTICLE IS NOT NULL
            """)
            fk_updated = target_cursor.rowcount
            print(f"  [OK] {fk_updated:,} references FK mises a jour")
            
            # ÉTAPE 3: Désactiver IDENTITY et modifier les IDs
            print("  Modification des IDs dans PAPIERS_ARTICLES...")
            target_cursor.execute("SET IDENTITY_INSERT dbo.PAPIERS_ARTICLES ON")
            
            # Obtenir toutes les colonnes de la table
            target_cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'PAPIERS_ARTICLES'
                ORDER BY ORDINAL_POSITION
            """)
            all_columns = [row[0] for row in target_cursor.fetchall()]
            columns_insert = ', '.join([f'[{col}]' for col in all_columns])
            
            # Créer une table temporaire avec tous les enregistrements à modifier
            target_cursor.execute(f"""
                SELECT pa.*, m.nouveau_ID AS NEW_ID
                INTO #TEMP_UPDATE_PAPIERS_ARTICLES
                FROM PAPIERS_ARTICLES pa
                INNER JOIN #ID_MAPPING_PAPIERS_ARTICLES m ON pa.ID = m.ancien_ID
            """)
            
            # Mettre à jour les IDs dans la table temporaire
            target_cursor.execute("""
                UPDATE #TEMP_UPDATE_PAPIERS_ARTICLES
                SET ID = NEW_ID
            """)
            
            # Supprimer les anciens enregistrements (maintenant possible car FK désactivée)
            target_cursor.execute("""
                DELETE FROM PAPIERS_ARTICLES
                WHERE ID IN (SELECT ancien_ID FROM #ID_MAPPING_PAPIERS_ARTICLES)
            """)
            
            # Insérer les enregistrements avec les nouveaux IDs
            target_cursor.execute(f"""
                INSERT INTO PAPIERS_ARTICLES ({columns_insert})
                SELECT {columns_insert}
                FROM #TEMP_UPDATE_PAPIERS_ARTICLES
            """)
            
            updated_count = len(mapping)
            print(f"  [OK] {updated_count:,} IDs modifies")
            
            # Nettoyer la table temporaire
            target_cursor.execute("DROP TABLE #TEMP_UPDATE_PAPIERS_ARTICLES")
            
            # ÉTAPE 4: Réactiver IDENTITY
            target_cursor.execute("SET IDENTITY_INSERT dbo.PAPIERS_ARTICLES OFF")
            
            # ÉTAPE 5: Réactiver la contrainte FK
            print("  Reactivation de la contrainte FK...")
            target_cursor.execute("""
                ALTER TABLE PAPIERS_TARIF_FMT
                CHECK CONSTRAINT FK__PAPIERS_T__ID_AR__48717679
            """)
            
            
            # Réactiver IDENTITY
            target_cursor.execute("SET IDENTITY_INSERT dbo.PAPIERS_ARTICLES OFF")
            
            # Réinitialiser IDENTITY
            target_cursor.execute("SELECT MAX(ID) FROM PAPIERS_ARTICLES")
            max_id = target_cursor.fetchone()[0] or 0
            target_cursor.execute(f"DBCC CHECKIDENT ('dbo.PAPIERS_ARTICLES', RESEED, {max_id})")
            
            # Valider la transaction
            target_conn.commit()
            target_conn.autocommit = True
            
            print(f"  [OK] {updated_count:,} IDs mis a jour")
            print(f"  [OK] {fk_updated:,} references FK mises a jour")
            print()
            
        except Exception as e:
            # Rollback en cas d'erreur
            target_conn.rollback()
            target_conn.autocommit = True
            raise e
        
        # Vérifications post-traitement
        print("[6/6] Verifications post-traitement...")
        
        # Vérifier que les IDs correspondent maintenant
        columns_str = ', '.join(columns)
        
        source_cursor.execute(f"""
            SELECT ID, {columns_str}
            FROM PAPIERS_ARTICLES
        """)
        source_data_after = {tuple(row[1:]): row[0] for row in source_cursor.fetchall()}
        
        target_cursor.execute(f"""
            SELECT ID, {columns_str}
            FROM PAPIERS_ARTICLES
        """)
        target_data_after = [(row[0], tuple(row[1:])) for row in target_cursor.fetchall()]
        
        mismatches = 0
        for target_id, target_key in target_data_after:
            if target_key in source_data_after:
                if target_id != source_data_after[target_key]:
                    mismatches += 1
        
        if mismatches > 0:
            print(f"  [ATTENTION] {mismatches} IDs ne correspondent toujours pas")
        else:
            print("  [OK] Tous les IDs correspondent maintenant")
        
        # Vérifier l'intégrité référentielle
        target_cursor.execute("""
            SELECT COUNT(*)
            FROM PAPIERS_TARIF_FMT ptf
            LEFT JOIN PAPIERS_ARTICLES pa ON ptf.ID_ARTICLE = pa.ID
            WHERE ptf.ID_ARTICLE IS NOT NULL AND pa.ID IS NULL
        """)
        orphan_after = target_cursor.fetchone()[0]
        
        if orphan_after > 0:
            print(f"  [ATTENTION] {orphan_after:,} references orphelines restantes")
        else:
            print("  [OK] Integrite referentielle verifiee")
        
        print()
        print("="*80)
        print("REALIGNEMENT TERMINE AVEC SUCCES!")
        print("="*80)
        print(f"IDs realignes: {len(mapping):,}")
        print(f"References FK mises a jour: {fk_updated:,}")
        
        return True
        
    except Exception as e:
        print()
        print("="*80)
        print("[ERREUR] Le realignement a echoue!")
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
    import argparse
    
    parser = argparse.ArgumentParser(description='Realignement des IDs de PAPIERS_ARTICLES')
    parser.add_argument('--force', action='store_true', 
                       help='Forcer l\'execution sans confirmation interactive')
    args = parser.parse_args()
    
    if not args.force:
        print()
        print("ATTENTION: Ce script va modifier les IDs dans la base novaprint_restored")
        print("Assurez-vous d'avoir une sauvegarde complete avant de continuer!")
        print()
        print("Pour executer automatiquement, utilisez: python projet21_execute_realignement_papiers_articles.py --force")
        print()
        
        try:
            response = input("Voulez-vous continuer? (oui/non): ")
            if response.lower() not in ['oui', 'o', 'yes', 'y']:
                print("Operation annulee.")
                sys.exit(0)
        except EOFError:
            print("Mode interactif non disponible. Utilisez --force pour executer automatiquement.")
            sys.exit(1)
    
    success = execute_realignment()
    sys.exit(0 if success else 1)
