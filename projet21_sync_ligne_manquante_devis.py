#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script pour synchroniser la ligne manquante de la table DEVIS
ID manquant: 287636
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

def sync_missing_devis():
    """Synchronise la ligne manquante de DEVIS (ID=287636)"""
    
    print("="*80)
    print("SYNCHRONISATION DE LA LIGNE MANQUANTE - DEVIS")
    print("="*80)
    print(f"ID manquant: 287636")
    print()
    
    source_conn = None
    target_conn = None
    
    try:
        # Connexions
        print("[1/4] Connexion aux bases de donnees...")
        source_conn = get_connection(SOURCE_CONFIG, readonly=True)
        target_conn = get_connection(TARGET_CONFIG, readonly=False)
        print("  [OK] Connexions etablies")
        print()
        
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()
        
        # Vérifier que la ligne existe bien en source
        print("[2/4] Verification de l'existence en source...")
        source_cursor.execute("SELECT COUNT(*) FROM DEVIS WHERE ID = 287636")
        source_exists = source_cursor.fetchone()[0]
        
        if source_exists == 0:
            print("  [ERREUR] La ligne ID=287636 n'existe pas en source")
            return False
        
        print("  [OK] Ligne trouvee en source")
        
        # Vérifier qu'elle n'existe pas en cible
        target_cursor.execute("SELECT COUNT(*) FROM DEVIS WHERE ID = 287636")
        target_exists = target_cursor.fetchone()[0]
        
        if target_exists > 0:
            print("  [INFO] La ligne existe deja en cible")
            return True
        
        print("  [OK] Ligne confirmee manquante en cible")
        print()
        
        # Obtenir toutes les colonnes de la table
        print("[3/4] Lecture de la ligne depuis la source...")
        source_cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'DEVIS'
            ORDER BY ORDINAL_POSITION
        """)
        columns = [row[0] for row in source_cursor.fetchall()]
        col_list = ', '.join([f'[{col}]' for col in columns])
        
        # Lire la ligne depuis la source
        source_cursor.execute(f"SELECT {col_list} FROM DEVIS WHERE ID = 287636")
        source_row = source_cursor.fetchone()
        
        if not source_row:
            print("  [ERREUR] Impossible de lire la ligne depuis la source")
            return False
        
        print(f"  [OK] Ligne lue ({len(columns)} colonnes)")
        print()
        
        # Insérer la ligne dans la cible
        print("[4/4] Insertion de la ligne dans la cible...")
        target_conn.autocommit = False
        
        try:
            # Vérifier si ID est IDENTITY
            target_cursor.execute("""
                SELECT COLUMNPROPERTY(OBJECT_ID('DEVIS'), 'ID', 'IsIdentity')
            """)
            is_identity = target_cursor.fetchone()[0]
            
            if is_identity:
                print("  Activation de IDENTITY_INSERT...")
                target_cursor.execute("SET IDENTITY_INSERT dbo.DEVIS ON")
            
            placeholders = ', '.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO DEVIS ({col_list}) VALUES ({placeholders})"
            
            target_cursor.execute(insert_sql, list(source_row))
            
            if is_identity:
                target_cursor.execute("SET IDENTITY_INSERT dbo.DEVIS OFF")
            
            target_conn.commit()
            target_conn.autocommit = True
            
            print("  [OK] Ligne inseree avec succes")
            print()
            
            # Vérification finale
            target_cursor.execute("SELECT COUNT(*) FROM DEVIS WHERE ID = 287636")
            final_check = target_cursor.fetchone()[0]
            
            if final_check > 0:
                print("="*80)
                print("SYNCHRONISATION REUSSIE!")
                print("="*80)
                print(f"Ligne ID=287636 synchronisee avec succes")
                return True
            else:
                print("  [ERREUR] La ligne n'a pas ete inseree correctement")
                return False
                
        except Exception as e:
            target_conn.rollback()
            target_conn.autocommit = True
            print(f"  [ERREUR] Erreur lors de l'insertion: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print()
        print("="*80)
        print("[ERREUR] La synchronisation a echoue!")
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
    success = sync_missing_devis()
    exit(0 if success else 1)
