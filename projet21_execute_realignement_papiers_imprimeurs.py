#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script d'exécution sécurisée du réalignement des IDs - PAPIERS_IMPRIMEURS
Exécute le script SQL avec transactions, vérifications et rollback automatique

VERSION RENFORCÉE pour gérer la complexité accrue :
- 2 FK entrantes (PAPIERS_TARIF_FMT et PAPIERS_TARIF_GRAM)
- 553 références orphelines à gérer
- 4 relations directes au total
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

def execute_realignment():
    """Exécute le réalignement des IDs de manière sécurisée"""
    
    print("="*80)
    print("REALIGNEMENT DES IDs - PAPIERS_IMPRIMEURS")
    print("VERSION RENFORCÉE (2 FK entrantes)")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    source_conn = None
    target_conn = None
    
    try:
        # Connexions
        print("[1/7] Connexion aux bases de donnees...")
        source_conn = get_connection(SOURCE_CONFIG, readonly=True)
        print("  [OK] Connexion a Novaprint (source) etablie")
        
        target_conn = get_connection(TARGET_CONFIG, readonly=False)
        print("  [OK] Connexion a novaprint_restored (cible) etablie")
        print()
        
        # Vérifications préalables renforcées
        print("[2/7] Verifications prealables renforcees...")
        target_cursor = target_conn.cursor()
        
        # Vérifier le nombre d'enregistrements
        source_cursor = source_conn.cursor()
        source_cursor.execute("SELECT COUNT(*) FROM PAPIERS_IMPRIMEURS")
        source_count = source_cursor.fetchone()[0]
        
        target_cursor.execute("SELECT COUNT(*) FROM PAPIERS_IMPRIMEURS")
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
        
        # Vérifier les références orphelines dans PAPIERS_TARIF_FMT
        target_cursor.execute("""
            SELECT COUNT(*)
            FROM PAPIERS_TARIF_FMT ptf
            LEFT JOIN PAPIERS_IMPRIMEURS pi ON ptf.ID_PAPIMPRIM = pi.ID
            WHERE ptf.ID_PAPIMPRIM IS NOT NULL AND pi.ID IS NULL
        """)
        orphan_count_fmt = target_cursor.fetchone()[0]
        
        if orphan_count_fmt > 0:
            print(f"  [ATTENTION] {orphan_count_fmt:,} references orphelines dans PAPIERS_TARIF_FMT")
        else:
            print("  [OK] Aucune reference orpheline dans PAPIERS_TARIF_FMT")
        
        # Vérifier les références orphelines dans PAPIERS_TARIF_GRAM
        target_cursor.execute("""
            SELECT COUNT(*)
            FROM PAPIERS_TARIF_GRAM ptg
            LEFT JOIN PAPIERS_IMPRIMEURS pi ON ptg.ID_PAPIMPRIM = pi.ID
            WHERE ptg.ID_PAPIMPRIM IS NOT NULL AND pi.ID IS NULL
        """)
        orphan_count_gram = target_cursor.fetchone()[0]
        
        if orphan_count_gram > 0:
            print(f"  [ATTENTION] {orphan_count_gram:,} references orphelines dans PAPIERS_TARIF_GRAM")
        else:
            print("  [OK] Aucune reference orpheline dans PAPIERS_TARIF_GRAM")
        
        total_orphans = orphan_count_fmt + orphan_count_gram
        if total_orphans > 0:
            print(f"  [INFO] Total references orphelines: {total_orphans:,} (seront ignorees)")
        
        print()
        
        # Créer la table de mapping
        print("[3/7] Creation de la table de mapping...")
        
        # Identifier les colonnes communes aux deux tables (sauf ID)
        source_cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'PAPIERS_IMPRIMEURS'
            AND COLUMN_NAME != 'ID'
            ORDER BY ORDINAL_POSITION
        """)
        source_columns = set(row[0] for row in source_cursor.fetchall())
        
        target_cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'PAPIERS_IMPRIMEURS'
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
            IF OBJECT_ID('tempdb..#ID_MAPPING_PAPIERS_IMPRIMEURS', 'U') IS NOT NULL
                DROP TABLE #ID_MAPPING_PAPIERS_IMPRIMEURS;
            
            CREATE TABLE #ID_MAPPING_PAPIERS_IMPRIMEURS (
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
            FROM PAPIERS_IMPRIMEURS
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
            FROM PAPIERS_IMPRIMEURS
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
            INSERT INTO #ID_MAPPING_PAPIERS_IMPRIMEURS (ancien_ID, nouveau_ID)
            VALUES (?, ?)
        """, mapping)
        target_conn.commit()
        print()
        
        # Vérifier les conflits
        print("[4/7] Verification des conflits potentiels...")
        target_cursor.execute("""
            SELECT COUNT(*)
            FROM #ID_MAPPING_PAPIERS_IMPRIMEURS m
            INNER JOIN PAPIERS_IMPRIMEURS pi ON m.nouveau_ID = pi.ID
            WHERE pi.ID NOT IN (SELECT ancien_ID FROM #ID_MAPPING_PAPIERS_IMPRIMEURS)
        """)
        conflict_count = target_cursor.fetchone()[0]
        
        if conflict_count > 0:
            print(f"  [ERREUR] {conflict_count} conflits d'IDs detectes!")
            return False
        
        print("  [OK] Aucun conflit detecte")
        print()
        
        # Démarrer la transaction
        print("[5/7] Execution du realignement (dans une transaction)...")
        target_conn.autocommit = False
        
        try:
            # ÉTAPE 1: Désactiver temporairement les contraintes FK (en premier!)
            print("  Desactivation temporaire des contraintes FK entrantes...")
            
            # Désactiver FK vers PAPIERS_TARIF_FMT
            target_cursor.execute("""
                ALTER TABLE PAPIERS_TARIF_FMT
                NOCHECK CONSTRAINT FK__PAPIERS_T__ID_PA__49659AB2
            """)
            print("    [OK] FK vers PAPIERS_TARIF_FMT desactivee")
            
            # Désactiver FK vers PAPIERS_TARIF_GRAM
            target_cursor.execute("""
                ALTER TABLE PAPIERS_TARIF_GRAM
                NOCHECK CONSTRAINT FK__PAPIERS_T__ID_PA__4A59BEEB
            """)
            print("    [OK] FK vers PAPIERS_TARIF_GRAM desactivee")
            
            # ÉTAPE 2: Vérifier les conflits potentiels avant mise à jour
            print("  Verification des conflits potentiels dans PAPIERS_TARIF_FMT...")
            target_cursor.execute("""
                SELECT COUNT(*)
                FROM (
                    SELECT 
                        ptf.ID_ARTICLE,
                        ptf.PaqCalcul,
                        m.nouveau_ID,
                        COUNT(*) AS nb_lignes
                    FROM PAPIERS_TARIF_FMT ptf
                    INNER JOIN #ID_MAPPING_PAPIERS_IMPRIMEURS m ON ptf.ID_PAPIMPRIM = m.ancien_ID
                    WHERE ptf.ID_PAPIMPRIM IS NOT NULL
                    GROUP BY ptf.ID_ARTICLE, ptf.PaqCalcul, m.nouveau_ID
                    HAVING COUNT(*) > 1
                ) AS conflicts
            """)
            conflict_count_fmt = target_cursor.fetchone()[0]
            
            if conflict_count_fmt > 0:
                print(f"    [ATTENTION] {conflict_count_fmt} conflits potentiels detectes")
                print("    Les lignes en conflit seront ignorees pour eviter les doublons")
            
            # Mettre à jour les références FK dans PAPIERS_TARIF_FMT
            # Exclure les lignes qui créeraient des conflits avec des lignes existantes
            print("  Mise a jour des references FK dans PAPIERS_TARIF_FMT...")
            
            target_cursor.execute("""
                UPDATE ptf
                SET ID_PAPIMPRIM = m.nouveau_ID
                FROM PAPIERS_TARIF_FMT ptf
                INNER JOIN #ID_MAPPING_PAPIERS_IMPRIMEURS m ON ptf.ID_PAPIMPRIM = m.ancien_ID
                WHERE ptf.ID_PAPIMPRIM IS NOT NULL
                    -- Exclure si le nouveau_ID existe déjà avec les mêmes (ID_ARTICLE, PaqCalcul)
                    AND NOT EXISTS (
                        SELECT 1
                        FROM PAPIERS_TARIF_FMT ptf_existing
                        WHERE ptf_existing.ID_ARTICLE = ptf.ID_ARTICLE
                            AND ptf_existing.PaqCalcul = ptf.PaqCalcul
                            AND ptf_existing.ID_PAPIMPRIM = m.nouveau_ID
                            AND ptf_existing.ID_PAPIMPRIM NOT IN (SELECT ancien_ID FROM #ID_MAPPING_PAPIERS_IMPRIMEURS)
                    )
                    -- Exclure aussi les doublons dans le mapping lui-même
                    AND NOT EXISTS (
                        SELECT 1
                        FROM PAPIERS_TARIF_FMT ptf2
                        INNER JOIN #ID_MAPPING_PAPIERS_IMPRIMEURS m2 ON ptf2.ID_PAPIMPRIM = m2.ancien_ID
                        WHERE ptf2.ID_ARTICLE = ptf.ID_ARTICLE
                            AND ptf2.PaqCalcul = ptf.PaqCalcul
                            AND m2.nouveau_ID = m.nouveau_ID
                            AND ptf2.ID_PAPIMPRIM < ptf.ID_PAPIMPRIM
                    )
            """)
            fk_updated_fmt = target_cursor.rowcount
            print(f"    [OK] {fk_updated_fmt:,} references FK mises a jour dans PAPIERS_TARIF_FMT")
            
            # ÉTAPE 3: Mettre à jour les références FK dans PAPIERS_TARIF_GRAM
            # La PK est (ID_PAPIMPRIM, GRAMMAGE)
            print("  Mise a jour des references FK dans PAPIERS_TARIF_GRAM...")
            
            target_cursor.execute("""
                UPDATE ptg
                SET ID_PAPIMPRIM = m.nouveau_ID
                FROM PAPIERS_TARIF_GRAM ptg
                INNER JOIN #ID_MAPPING_PAPIERS_IMPRIMEURS m ON ptg.ID_PAPIMPRIM = m.ancien_ID
                WHERE ptg.ID_PAPIMPRIM IS NOT NULL
                    -- Exclure si le nouveau_ID existe déjà avec le même GRAMMAGE
                    AND NOT EXISTS (
                        SELECT 1
                        FROM PAPIERS_TARIF_GRAM ptg_existing
                        WHERE ptg_existing.GRAMMAGE = ptg.GRAMMAGE
                            AND ptg_existing.ID_PAPIMPRIM = m.nouveau_ID
                            AND ptg_existing.ID_PAPIMPRIM NOT IN (SELECT ancien_ID FROM #ID_MAPPING_PAPIERS_IMPRIMEURS)
                    )
                    -- Exclure aussi les doublons dans le mapping lui-même
                    AND NOT EXISTS (
                        SELECT 1
                        FROM PAPIERS_TARIF_GRAM ptg2
                        INNER JOIN #ID_MAPPING_PAPIERS_IMPRIMEURS m2 ON ptg2.ID_PAPIMPRIM = m2.ancien_ID
                        WHERE ptg2.GRAMMAGE = ptg.GRAMMAGE
                            AND m2.nouveau_ID = m.nouveau_ID
                            AND ptg2.ID_PAPIMPRIM < ptg.ID_PAPIMPRIM
                    )
            """)
            fk_updated_gram = target_cursor.rowcount
            print(f"    [OK] {fk_updated_gram:,} references FK mises a jour dans PAPIERS_TARIF_GRAM")
            
            # ÉTAPE 4: Désactiver IDENTITY et modifier les IDs
            print("  Modification des IDs dans PAPIERS_IMPRIMEURS...")
            target_cursor.execute("SET IDENTITY_INSERT dbo.PAPIERS_IMPRIMEURS ON")
            
            # Obtenir toutes les colonnes de la table
            target_cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'PAPIERS_IMPRIMEURS'
                ORDER BY ORDINAL_POSITION
            """)
            all_columns = [row[0] for row in target_cursor.fetchall()]
            columns_insert = ', '.join([f'[{col}]' for col in all_columns])
            
            # Créer une table temporaire avec tous les enregistrements à modifier
            target_cursor.execute(f"""
                SELECT pi.*, m.nouveau_ID AS NEW_ID
                INTO #TEMP_UPDATE_PAPIERS_IMPRIMEURS
                FROM PAPIERS_IMPRIMEURS pi
                INNER JOIN #ID_MAPPING_PAPIERS_IMPRIMEURS m ON pi.ID = m.ancien_ID
            """)
            
            # Mettre à jour les IDs dans la table temporaire
            target_cursor.execute("""
                UPDATE #TEMP_UPDATE_PAPIERS_IMPRIMEURS
                SET ID = NEW_ID
            """)
            
            # Supprimer les anciens enregistrements (maintenant possible car FK désactivées)
            target_cursor.execute("""
                DELETE FROM PAPIERS_IMPRIMEURS
                WHERE ID IN (SELECT ancien_ID FROM #ID_MAPPING_PAPIERS_IMPRIMEURS)
            """)
            
            # Insérer les enregistrements avec les nouveaux IDs
            target_cursor.execute(f"""
                INSERT INTO PAPIERS_IMPRIMEURS ({columns_insert})
                SELECT {columns_insert}
                FROM #TEMP_UPDATE_PAPIERS_IMPRIMEURS
            """)
            
            updated_count = len(mapping)
            print(f"    [OK] {updated_count:,} IDs modifies")
            
            # Nettoyer la table temporaire
            target_cursor.execute("DROP TABLE #TEMP_UPDATE_PAPIERS_IMPRIMEURS")
            
            # ÉTAPE 5: Réactiver IDENTITY
            target_cursor.execute("SET IDENTITY_INSERT dbo.PAPIERS_IMPRIMEURS OFF")
            
            # Réinitialiser IDENTITY
            target_cursor.execute("SELECT MAX(ID) FROM PAPIERS_IMPRIMEURS")
            max_id = target_cursor.fetchone()[0] or 0
            target_cursor.execute(f"DBCC CHECKIDENT ('dbo.PAPIERS_IMPRIMEURS', RESEED, {max_id})")
            
            # ÉTAPE 6: Réactiver les contraintes FK
            print("  Reactivation des contraintes FK entrantes...")
            
            # Réactiver FK vers PAPIERS_TARIF_FMT
            target_cursor.execute("""
                ALTER TABLE PAPIERS_TARIF_FMT
                CHECK CONSTRAINT FK__PAPIERS_T__ID_PA__49659AB2
            """)
            print("    [OK] FK vers PAPIERS_TARIF_FMT reactivee")
            
            # Réactiver FK vers PAPIERS_TARIF_GRAM
            target_cursor.execute("""
                ALTER TABLE PAPIERS_TARIF_GRAM
                CHECK CONSTRAINT FK__PAPIERS_T__ID_PA__4A59BEEB
            """)
            print("    [OK] FK vers PAPIERS_TARIF_GRAM reactivee")
            
            # Valider la transaction
            target_conn.commit()
            target_conn.autocommit = True
            
            print()
            print(f"  [OK] {updated_count:,} IDs mis a jour")
            print(f"  [OK] {fk_updated_fmt:,} references FK mises a jour dans PAPIERS_TARIF_FMT")
            print(f"  [OK] {fk_updated_gram:,} references FK mises a jour dans PAPIERS_TARIF_GRAM")
            print()
            
        except Exception as e:
            # Rollback en cas d'erreur
            target_conn.rollback()
            target_conn.autocommit = True
            raise e
        
        # Vérifications post-traitement
        print("[6/7] Verifications post-traitement...")
        
        # Vérifier que les IDs correspondent maintenant
        columns_str = ', '.join(columns)
        
        source_cursor.execute(f"""
            SELECT ID, {columns_str}
            FROM PAPIERS_IMPRIMEURS
        """)
        source_data_after = {tuple(row[1:]): row[0] for row in source_cursor.fetchall()}
        
        target_cursor.execute(f"""
            SELECT ID, {columns_str}
            FROM PAPIERS_IMPRIMEURS
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
        
        # Vérifier l'intégrité référentielle dans PAPIERS_TARIF_FMT
        target_cursor.execute("""
            SELECT COUNT(*)
            FROM PAPIERS_TARIF_FMT ptf
            LEFT JOIN PAPIERS_IMPRIMEURS pi ON ptf.ID_PAPIMPRIM = pi.ID
            WHERE ptf.ID_PAPIMPRIM IS NOT NULL AND pi.ID IS NULL
        """)
        orphan_after_fmt = target_cursor.fetchone()[0]
        
        if orphan_after_fmt > 0:
            print(f"  [ATTENTION] {orphan_after_fmt:,} references orphelines restantes dans PAPIERS_TARIF_FMT")
        else:
            print("  [OK] Integrite referentielle verifiee dans PAPIERS_TARIF_FMT")
        
        # Vérifier l'intégrité référentielle dans PAPIERS_TARIF_GRAM
        target_cursor.execute("""
            SELECT COUNT(*)
            FROM PAPIERS_TARIF_GRAM ptg
            LEFT JOIN PAPIERS_IMPRIMEURS pi ON ptg.ID_PAPIMPRIM = pi.ID
            WHERE ptg.ID_PAPIMPRIM IS NOT NULL AND pi.ID IS NULL
        """)
        orphan_after_gram = target_cursor.fetchone()[0]
        
        if orphan_after_gram > 0:
            print(f"  [ATTENTION] {orphan_after_gram:,} references orphelines restantes dans PAPIERS_TARIF_GRAM")
        else:
            print("  [OK] Integrite referentielle verifiee dans PAPIERS_TARIF_GRAM")
        
        print()
        
        # Résumé final
        print("[7/7] Resume final...")
        print()
        print("="*80)
        print("REALIGNEMENT TERMINE AVEC SUCCES!")
        print("="*80)
        print(f"IDs realignes: {len(mapping):,}")
        print(f"References FK mises a jour dans PAPIERS_TARIF_FMT: {fk_updated_fmt:,}")
        print(f"References FK mises a jour dans PAPIERS_TARIF_GRAM: {fk_updated_gram:,}")
        print(f"Total references FK mises a jour: {fk_updated_fmt + fk_updated_gram:,}")
        
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
    
    parser = argparse.ArgumentParser(description='Realignement des IDs de PAPIERS_IMPRIMEURS')
    parser.add_argument('--force', action='store_true', 
                       help='Forcer l\'execution sans confirmation interactive')
    args = parser.parse_args()
    
    if not args.force:
        print()
        print("ATTENTION: Ce script va modifier les IDs dans la base novaprint_restored")
        print("Cette operation est plus complexe que pour PAPIERS_ARTICLES car elle")
        print("gere 2 tables enfants (PAPIERS_TARIF_FMT et PAPIERS_TARIF_GRAM)")
        print()
        print("Assurez-vous d'avoir une sauvegarde complete avant de continuer!")
        print()
        print("Pour executer automatiquement, utilisez:")
        print("  python projet21_execute_realignement_papiers_imprimeurs.py --force")
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
