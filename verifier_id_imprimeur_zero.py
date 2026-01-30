#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Vérifier si ID_SOCIETE = 0 existe dans IMPRIMEURS
"""

from db import get_db_cursor

def get_connection(config, readonly=False):
    import pyodbc
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

def main():
    print("=" * 80)
    print("VERIFICATION ID_IMPRIMEUR = 0")
    print("=" * 80)
    print()
    
    source_conn = get_connection(SOURCE_CONFIG, readonly=True)
    source_cursor = source_conn.cursor()
    target_conn = get_connection(TARGET_CONFIG, readonly=True)
    target_cursor = target_conn.cursor()
    
    try:
        # Vérifier dans la source
        print("[SOURCE] Vérification de ID_SOCIETE = 0 dans IMPRIMEURS...")
        source_cursor.execute("SELECT COUNT(*) FROM IMPRIMEURS WHERE ID_SOCIETE = 0")
        source_count = source_cursor.fetchone()[0]
        print(f"  Nombre de lignes avec ID_SOCIETE = 0: {source_count}")
        
        if source_count > 0:
            source_cursor.execute("SELECT TOP 1 * FROM IMPRIMEURS WHERE ID_SOCIETE = 0")
            row = source_cursor.fetchone()
            if row:
                columns = [desc[0] for desc in source_cursor.description]
                print(f"  Exemple de ligne:")
                for i, col in enumerate(columns[:5]):  # Afficher les 5 premières colonnes
                    print(f"    {col}: {row[i]}")
        print()
        
        # Vérifier dans la cible
        print("[CIBLE] Vérification de ID_SOCIETE = 0 dans IMPRIMEURS...")
        target_cursor.execute("SELECT COUNT(*) FROM IMPRIMEURS WHERE ID_SOCIETE = 0")
        target_count = target_cursor.fetchone()[0]
        print(f"  Nombre de lignes avec ID_SOCIETE = 0: {target_count}")
        
        if target_count > 0:
            target_cursor.execute("SELECT TOP 1 * FROM IMPRIMEURS WHERE ID_SOCIETE = 0")
            row = target_cursor.fetchone()
            if row:
                columns = [desc[0] for desc in target_cursor.description]
                print(f"  Exemple de ligne:")
                for i, col in enumerate(columns[:5]):  # Afficher les 5 premières colonnes
                    print(f"    {col}: {row[i]}")
        print()
        
        # Conclusion
        print("=" * 80)
        print("CONCLUSION")
        print("=" * 80)
        if source_count > 0 and target_count == 0:
            print("❌ PROBLÈME IDENTIFIÉ:")
            print("  - ID_SOCIETE = 0 existe dans la SOURCE mais PAS dans la CIBLE")
            print("  - C'est pourquoi les 13 lignes avec ID_IMPRIMEUR = 0 ne sont pas synchronisées")
            print()
            print("SOLUTION:")
            print("  1. Synchroniser d'abord la table IMPRIMEURS pour inclure ID_SOCIETE = 0")
            print("  2. Puis resynchroniser PAPIERS_IMPRIMEURS")
        elif source_count == 0 and target_count == 0:
            print("⚠️ ID_SOCIETE = 0 n'existe ni dans la source ni dans la cible")
            print("  Les lignes avec ID_IMPRIMEUR = 0 sont des données orphelines")
        else:
            print("✓ ID_SOCIETE = 0 existe dans les deux bases")
            print("  Le problème vient d'ailleurs dans la synchronisation")
        
    finally:
        source_conn.close()
        target_conn.close()

if __name__ == "__main__":
    main()
