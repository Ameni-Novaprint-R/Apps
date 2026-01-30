#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour résoudre le conflit DEVIS
Mise à jour de l'ID 287615 vers 287636 pour correspondre à la source
"""

import pyodbc

TARGET_CONFIG = {
    'server': '192.168.10.225',
    'database': 'novaprint_restored',
    'trusted_connection': True
}

def get_connection(config):
    """Connexion SQL Server"""
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
    return conn

def resoudre_conflit():
    """Résout le conflit en mettant à jour l'ID de 287615 vers 287636"""
    
    print("="*80)
    print("RESOLUTION DU CONFLIT DEVIS")
    print("="*80)
    print("ID cible: 287615 -> ID source: 287636")
    print()
    
    conn = None
    try:
        conn = get_connection(TARGET_CONFIG)
        cursor = conn.cursor()
        
        # Étape 1: Vérifier les références FK vers ID=287615
        print("[1/5] Verification des references FK vers ID=287615...")
        
        # Trouver toutes les tables qui référencent DEVIS
        cursor.execute("""
            SELECT 
                OBJECT_NAME(fk.parent_object_id) AS table_name,
                fk.name AS fk_name,
                COL_NAME(fc.parent_object_id, fc.parent_column_id) AS column_name
            FROM sys.foreign_keys fk
            INNER JOIN sys.foreign_key_columns fc ON fk.object_id = fc.constraint_object_id
            WHERE OBJECT_NAME(fk.referenced_object_id) = 'DEVIS'
            AND COL_NAME(fc.referenced_object_id, fc.referenced_column_id) = 'ID'
        """)
        
        fk_tables = cursor.fetchall()
        print(f"  Tables qui referencent DEVIS: {len(fk_tables)}")
        
        total_refs = 0
        for table_name, fk_name, column_name in fk_tables:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM [{table_name}] 
                WHERE [{column_name}] = 287615
            """)
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"    {table_name}.{column_name}: {count} references")
                total_refs += count
        
        if total_refs > 0:
            print(f"  [ATTENTION] {total_refs} references FK a mettre a jour")
        else:
            print("  [OK] Aucune reference FK trouvee")
        
        print()
        
        # Étape 2: Vérifier que l'ID 287636 n'existe pas déjà
        print("[2/5] Verification de l'ID 287636...")
        cursor.execute("SELECT COUNT(*) FROM DEVIS WHERE ID = 287636")
        exists_287636 = cursor.fetchone()[0]
        
        if exists_287636 > 0:
            print("  [ERREUR] L'ID 287636 existe deja en cible")
            return False
        
        print("  [OK] L'ID 287636 est disponible")
        print()
        
        # Étape 3: Démarrer la transaction
        print("[3/5] Mise a jour de l'ID (dans une transaction)...")
        conn.autocommit = False
        
        try:
            # Désactiver toutes les contraintes FK vers DEVIS
            print("  Desactivation des contraintes FK vers DEVIS...")
            for table_name, fk_name, column_name in fk_tables:
                try:
                    cursor.execute(f"""
                        ALTER TABLE [{table_name}]
                        NOCHECK CONSTRAINT [{fk_name}]
                    """)
                except Exception as e:
                    print(f"    [ATTENTION] Impossible de desactiver {fk_name}: {e}")
            
            # Désactiver aussi les FK qui référencent les tables enfants (pour éviter les cascades)
            print("  Desactivation des contraintes FK en cascade...")
            cascade_tables = ['DEV_VERSIONS', 'DEV_AFF', 'DEV_COUTS', 'DEV_ELEM', 'DEV_LIVRAISONS']
            all_disabled_fks = []
            
            for table_name in cascade_tables:
                try:
                    cursor.execute(f"""
                        SELECT name, OBJECT_NAME(parent_object_id) as parent_table
                        FROM sys.foreign_keys
                        WHERE OBJECT_NAME(parent_object_id) = '{table_name}'
                    """)
                    fks = cursor.fetchall()
                    for fk_name, parent_table in fks:
                        try:
                            cursor.execute(f"""
                                ALTER TABLE [{parent_table}]
                                NOCHECK CONSTRAINT [{fk_name}]
                            """)
                            all_disabled_fks.append((parent_table, fk_name))
                        except Exception as e:
                            print(f"    [ATTENTION] Impossible de desactiver {parent_table}.{fk_name}: {e}")
                except Exception as e:
                    print(f"    [ATTENTION] Erreur pour {table_name}: {e}")
            
            # Désactiver aussi les FK vers DEV_VERSIONS (comme DEV_LIV_VERSIONS)
            try:
                cursor.execute("""
                    SELECT OBJECT_NAME(parent_object_id) as parent_table, name as fk_name
                    FROM sys.foreign_keys
                    WHERE OBJECT_NAME(referenced_object_id) IN ('DEV_VERSIONS', 'DEV_AFF', 'DEV_COUTS', 'DEV_ELEM', 'DEV_LIVRAISONS')
                """)
                cascade_fks = cursor.fetchall()
                for parent_table, fk_name in cascade_fks:
                    try:
                        cursor.execute(f"""
                            ALTER TABLE [{parent_table}]
                            NOCHECK CONSTRAINT [{fk_name}]
                        """)
                        all_disabled_fks.append((parent_table, fk_name))
                    except:
                        pass
            except:
                pass
            
            print(f"    {len(all_disabled_fks)} contraintes FK en cascade desactivees")
            
            # Désactiver IDENTITY_INSERT
            cursor.execute("SET IDENTITY_INSERT dbo.DEVIS ON")
            
            # Mettre à jour ou supprimer les références FK
            if total_refs > 0:
                print("  Traitement des references FK...")
                for table_name, fk_name, column_name in fk_tables:
                    # Vérifier si une ligne avec ID_DEVIS=287636 existe déjà
                    cursor.execute(f"""
                        SELECT COUNT(*) 
                        FROM [{table_name}] 
                        WHERE [{column_name}] = 287636
                    """)
                    exists_287636 = cursor.fetchone()[0]
                    
                    if exists_287636 > 0:
                        # Si 287636 existe déjà, supprimer la ligne avec 287615
                        print(f"    {table_name}: Suppression de la ligne avec {column_name}=287615 (287636 existe deja)")
                        cursor.execute(f"""
                            DELETE FROM [{table_name}]
                            WHERE [{column_name}] = 287615
                        """)
                        deleted = cursor.rowcount
                        if deleted > 0:
                            print(f"      {deleted} ligne(s) supprimee(s)")
                    else:
                        # Sinon, mettre à jour vers 287636
                        cursor.execute(f"""
                            UPDATE [{table_name}]
                            SET [{column_name}] = 287636
                            WHERE [{column_name}] = 287615
                        """)
                        updated = cursor.rowcount
                        if updated > 0:
                            print(f"    {table_name}: {updated} references mises a jour vers 287636")
            
            # Mettre à jour l'ID dans DEVIS
            print("  Mise a jour de l'ID dans DEVIS...")
            
            # Obtenir toutes les colonnes
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'DEVIS'
                ORDER BY ORDINAL_POSITION
            """)
            columns = [row[0] for row in cursor.fetchall()]
            col_list = ', '.join([f'[{col}]' for col in columns])
            
            # Créer une table temporaire avec la ligne (sans IDENTITY)
            cursor.execute(f"""
                SELECT * INTO #TEMP_DEVIS_UPDATE
                FROM DEVIS
                WHERE ID = 287615
            """)
            
            # Supprimer l'ancienne ligne
            cursor.execute("DELETE FROM DEVIS WHERE ID = 287615")
            
            # Insérer avec le nouvel ID (IDENTITY_INSERT est déjà activé)
            # Construire la liste de colonnes avec ID=287636 explicitement
            non_id_cols = [col for col in columns if col != 'ID']
            col_list_insert = ', '.join([f'[{col}]' for col in columns])
            col_list_select = ', '.join([f'[{col}]' if col != 'ID' else '287636 AS [ID]' for col in columns])
            
            cursor.execute(f"""
                INSERT INTO DEVIS ({col_list_insert})
                SELECT {col_list_select}
                FROM #TEMP_DEVIS_UPDATE
            """)
            
            # Nettoyer
            cursor.execute("DROP TABLE #TEMP_DEVIS_UPDATE")
            
            # Réactiver IDENTITY_INSERT
            cursor.execute("SET IDENTITY_INSERT dbo.DEVIS OFF")
            
            # Réactiver les contraintes FK (dans l'ordre inverse)
            print("  Reactivation des contraintes FK...")
            # Réactiver d'abord les FK en cascade (ordre inverse)
            for parent_table, fk_name in reversed(all_disabled_fks):
                try:
                    cursor.execute(f"""
                        ALTER TABLE [{parent_table}]
                        CHECK CONSTRAINT [{fk_name}]
                    """)
                except:
                    pass
            
            # Puis réactiver les FK vers DEVIS
            for table_name, fk_name, column_name in fk_tables:
                try:
                    cursor.execute(f"""
                        ALTER TABLE [{table_name}]
                        CHECK CONSTRAINT [{fk_name}]
                    """)
                except Exception as e:
                    print(f"    [ATTENTION] Impossible de reactiver {fk_name}: {e}")
            
            # Valider
            conn.commit()
            conn.autocommit = True
            
            print("  [OK] ID mis a jour avec succes")
            print()
            
        except Exception as e:
            conn.rollback()
            conn.autocommit = True
            raise e
        
        # Étape 4: Vérification
        print("[4/5] Verification...")
        cursor.execute("SELECT COUNT(*) FROM DEVIS WHERE ID = 287636")
        check_287636 = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM DEVIS WHERE ID = 287615")
        check_287615 = cursor.fetchone()[0]
        
        if check_287636 == 1 and check_287615 == 0:
            print("  [OK] ID 287636 existe maintenant")
            print("  [OK] ID 287615 n'existe plus")
        else:
            print(f"  [ERREUR] Etat inattendu: 287636={check_287636}, 287615={check_287615}")
            return False
        
        print()
        
        # Étape 5: Vérifier les références FK
        print("[5/5] Verification des references FK...")
        total_refs_after = 0
        for table_name, fk_name, column_name in fk_tables:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM [{table_name}] 
                WHERE [{column_name}] = 287636
            """)
            count = cursor.fetchone()[0]
            if count > 0:
                total_refs_after += count
        
        if total_refs == total_refs_after:
            print(f"  [OK] Toutes les references FK sont correctes ({total_refs_after})")
        else:
            print(f"  [ATTENTION] Nombre de references different: avant={total_refs}, apres={total_refs_after}")
        
        print()
        print("="*80)
        print("CONFLIT RESOLU AVEC SUCCES!")
        print("="*80)
        print("ID 287615 mis a jour vers 287636")
        print(f"References FK mises a jour: {total_refs}")
        
        return True
        
    except Exception as e:
        print()
        print("="*80)
        print("[ERREUR] La resolution a echoue!")
        print("="*80)
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    success = resoudre_conflit()
    exit(0 if success else 1)
