#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnostic : Pourquoi le cache FK ne contient pas ID_SOCIETE = 0
"""

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

TARGET_CONFIG = {
    'server': '192.168.10.225',
    'database': 'novaprint_restored',
    'trusted_connection': True
}

def main():
    print("=" * 80)
    print("DIAGNOSTIC CACHE FK - ID_SOCIETE = 0")
    print("=" * 80)
    print()
    
    target_conn = get_connection(TARGET_CONFIG, readonly=True)
    target_cursor = target_conn.cursor()
    
    try:
        # Simuler exactement ce que fait le code de synchronisation
        print("[1] Test de la requete utilisee dans le cache FK...")
        print("    Requete: SELECT DISTINCT [ID_SOCIETE] FROM [IMPRIMEURS] WHERE [ID_SOCIETE] IS NOT NULL")
        print()
        
        target_cursor.execute("SELECT DISTINCT [ID_SOCIETE] FROM [IMPRIMEURS] WHERE [ID_SOCIETE] IS NOT NULL")
        fk_values = {row[0] for row in target_cursor.fetchall()}
        
        print(f"  Valeurs trouvees dans le cache: {sorted(list(fk_values))[:20]}...")
        print(f"  Nombre total de valeurs: {len(fk_values)}")
        print()
        
        # Vérifier si 0 est dans le cache
        zero_in_cache = 0 in fk_values
        print(f"  ✓ 0 est dans le cache: {zero_in_cache}")
        print()
        
        # Vérifier directement dans la table
        print("[2] Verification directe dans IMPRIMEURS...")
        target_cursor.execute("SELECT COUNT(*) FROM IMPRIMEURS WHERE ID_SOCIETE = 0")
        count_zero = target_cursor.fetchone()[0]
        print(f"  Nombre de lignes avec ID_SOCIETE = 0: {count_zero}")
        
        if count_zero > 0:
            target_cursor.execute("SELECT TOP 1 ID_SOCIETE FROM IMPRIMEURS WHERE ID_SOCIETE = 0")
            row = target_cursor.fetchone()
            if row:
                print(f"  Valeur recuperee: {row[0]} (type: {type(row[0])})")
                print(f"  Comparaison 0 == row[0]: {0 == row[0]}")
                print(f"  Comparaison 0 in {{row[0]}}: {0 in {row[0]}}")
        print()
        
        # Test avec différentes requêtes
        print("[3] Tests avec differentes requetes...")
        
        # Test 1: Sans WHERE
        target_cursor.execute("SELECT DISTINCT ID_SOCIETE FROM IMPRIMEURS")
        all_values = {row[0] for row in target_cursor.fetchall()}
        print(f"  Sans WHERE: {len(all_values)} valeurs, 0 present: {0 in all_values}")
        
        # Test 2: Avec WHERE IS NOT NULL
        target_cursor.execute("SELECT DISTINCT ID_SOCIETE FROM IMPRIMEURS WHERE ID_SOCIETE IS NOT NULL")
        not_null_values = {row[0] for row in target_cursor.fetchall()}
        print(f"  Avec WHERE IS NOT NULL: {len(not_null_values)} valeurs, 0 present: {0 in not_null_values}")
        
        # Test 3: Vérifier le type de données
        target_cursor.execute("SELECT TOP 1 ID_SOCIETE FROM IMPRIMEURS WHERE ID_SOCIETE = 0")
        row = target_cursor.fetchone()
        if row:
            print(f"  Type de ID_SOCIETE = 0: {type(row[0])}")
            print(f"  Valeur: {repr(row[0])}")
        
        print()
        print("=" * 80)
        print("CONCLUSION")
        print("=" * 80)
        if zero_in_cache:
            print("✓ 0 EST dans le cache FK")
            print("  Le probleme vient d'ailleurs dans la logique de synchronisation")
        else:
            print("❌ 0 N'EST PAS dans le cache FK")
            if count_zero > 0:
                print("  Mais ID_SOCIETE = 0 existe dans IMPRIMEURS !")
                print("  C'est un bug dans la requete ou le cache")
            else:
                print("  Et ID_SOCIETE = 0 n'existe pas dans IMPRIMEURS")
                print("  Il faut d'abord synchroniser IMPRIMEURS avec ID_SOCIETE = 0")
        
    finally:
        target_conn.close()

if __name__ == "__main__":
    main()
