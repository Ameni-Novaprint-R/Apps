#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Vérifier pourquoi les lignes avec ID_IMPRIMEUR = 0 ne sont pas synchronisées
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
    print("VERIFICATION LIGNES ID_IMPRIMEUR = 0 MANQUANTES")
    print("=" * 80)
    print()
    
    source_conn = get_connection(SOURCE_CONFIG, readonly=True)
    source_cursor = source_conn.cursor()
    target_conn = get_connection(TARGET_CONFIG, readonly=True)
    target_cursor = target_conn.cursor()
    
    try:
        # 1. Vérifier les lignes avec ID_IMPRIMEUR = 0 dans la source
        print("[1] Lignes avec ID_IMPRIMEUR = 0 dans la SOURCE...")
        source_cursor.execute("""
            SELECT COUNT(*) FROM PAPIERS_IMPRIMEURS WHERE ID_IMPRIMEUR = 0
        """)
        source_count_zero = source_cursor.fetchone()[0]
        print(f"  Nombre de lignes: {source_count_zero}")
        
        source_cursor.execute("""
            SELECT ID, ID_PAPIER, ID_IMPRIMEUR 
            FROM PAPIERS_IMPRIMEURS 
            WHERE ID_IMPRIMEUR = 0
            ORDER BY ID
        """)
        source_rows_zero = source_cursor.fetchall()
        source_ids_zero = {row[0] for row in source_rows_zero}
        print(f"  IDs: {sorted(list(source_ids_zero))[:20]}...")
        print()
        
        # 2. Vérifier les lignes avec ID_IMPRIMEUR = 0 dans la cible
        print("[2] Lignes avec ID_IMPRIMEUR = 0 dans la CIBLE...")
        target_cursor.execute("""
            SELECT COUNT(*) FROM PAPIERS_IMPRIMEURS WHERE ID_IMPRIMEUR = 0
        """)
        target_count_zero = target_cursor.fetchone()[0]
        print(f"  Nombre de lignes: {target_count_zero}")
        
        target_cursor.execute("""
            SELECT ID, ID_PAPIER, ID_IMPRIMEUR 
            FROM PAPIERS_IMPRIMEURS 
            WHERE ID_IMPRIMEUR = 0
            ORDER BY ID
        """)
        target_rows_zero = target_cursor.fetchall()
        target_ids_zero = {row[0] for row in target_rows_zero}
        print(f"  IDs: {sorted(list(target_ids_zero))[:20]}...")
        print()
        
        # 3. Identifier les lignes manquantes
        print("[3] Lignes manquantes dans la CIBLE...")
        missing_ids = source_ids_zero - target_ids_zero
        print(f"  Nombre de lignes manquantes: {len(missing_ids)}")
        if missing_ids:
            print(f"  IDs manquants: {sorted(list(missing_ids))}")
        print()
        
        # 4. Vérifier si ID_SOCIETE = 0 existe dans IMPRIMEURS (cible)
        print("[4] Verification ID_SOCIETE = 0 dans IMPRIMEURS (cible)...")
        target_cursor.execute("SELECT COUNT(*) FROM IMPRIMEURS WHERE ID_SOCIETE = 0")
        imprimeur_zero_exists = target_cursor.fetchone()[0] > 0
        print(f"  ID_SOCIETE = 0 existe: {imprimeur_zero_exists}")
        print()
        
        # 5. Simuler la logique de vérification FK
        print("[5] Simulation de la logique de verification FK...")
        # Construire le cache FK comme dans le code
        target_cursor.execute("SELECT DISTINCT [ID_SOCIETE] FROM [IMPRIMEURS] WHERE [ID_SOCIETE] IS NOT NULL")
        fk_cache = {row[0] for row in target_cursor.fetchall()}
        print(f"  Cache FK (ID_SOCIETE): {sorted(list(fk_cache))[:20]}...")
        print(f"  0 dans le cache: {0 in fk_cache}")
        print()
        
        # Tester chaque ligne manquante
        print("[6] Test de chaque ligne manquante...")
        for missing_id in sorted(list(missing_ids))[:5]:  # Tester les 5 premières
            source_cursor.execute("""
                SELECT ID, ID_PAPIER, ID_IMPRIMEUR 
                FROM PAPIERS_IMPRIMEURS 
                WHERE ID = ?
            """, missing_id)
            row = source_cursor.fetchone()
            if row:
                fk_value = row[2]  # ID_IMPRIMEUR
                print(f"  ID {missing_id}: ID_IMPRIMEUR = {fk_value}")
                print(f"    fk_value is not None: {fk_value is not None}")
                print(f"    fk_value in fk_cache: {fk_value in fk_cache}")
                if fk_value == 0:
                    target_cursor.execute("SELECT COUNT(*) FROM IMPRIMEURS WHERE ID_SOCIETE = 0")
                    count = target_cursor.fetchone()[0]
                    print(f"    COUNT(*) FROM IMPRIMEURS WHERE ID_SOCIETE = 0: {count}")
        print()
        
        print("=" * 80)
        print("CONCLUSION")
        print("=" * 80)
        if len(missing_ids) > 0:
            if imprimeur_zero_exists and 0 in fk_cache:
                print("❌ PROBLEME IDENTIFIE:")
                print("  - ID_SOCIETE = 0 existe dans IMPRIMEURS")
                print("  - 0 est dans le cache FK")
                print("  - Mais les lignes avec ID_IMPRIMEUR = 0 ne sont pas synchronisees")
                print()
                print("  CAUSE PROBABLE:")
                print("  - Les lignes ont ete ignorees lors d'une synchronisation precedente")
                print("  - Lorsque ID_SOCIETE = 0 n'existait pas encore dans IMPRIMEURS")
                print("  - Maintenant qu'il existe, les lignes ne sont pas reessayees")
                print()
                print("  SOLUTION:")
                print("  - Resynchroniser PAPIERS_IMPRIMEURS pour reessayer les lignes ignorees")
                print("  - Ou utiliser le script synchroniser_lignes_papiers_imprimeurs_manquantes.py")
            else:
                print("⚠️ ID_SOCIETE = 0 n'existe pas dans IMPRIMEURS ou n'est pas dans le cache")
                print("  Il faut d'abord synchroniser IMPRIMEURS avec ID_SOCIETE = 0")
        else:
            print("✓ Toutes les lignes avec ID_IMPRIMEUR = 0 sont synchronisees")
        
    finally:
        source_conn.close()
        target_conn.close()

if __name__ == "__main__":
    main()
