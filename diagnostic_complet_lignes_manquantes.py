#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnostic complet : Pourquoi les 13 lignes ne sont pas synchronisées
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
    print("DIAGNOSTIC COMPLET - LIGNES MANQUANTES")
    print("=" * 80)
    print()
    
    source_conn = get_connection(SOURCE_CONFIG, readonly=True)
    source_cursor = source_conn.cursor()
    target_conn = get_connection(TARGET_CONFIG, readonly=True)
    target_cursor = target_conn.cursor()
    
    try:
        # 1. Identifier les 13 lignes manquantes
        print("[1] Identification des lignes manquantes...")
        source_cursor.execute("SELECT ID FROM PAPIERS_IMPRIMEURS WHERE ID_IMPRIMEUR = 0")
        source_ids = {row[0] for row in source_cursor.fetchall()}
        
        target_cursor.execute("SELECT ID FROM PAPIERS_IMPRIMEURS")
        target_ids = {row[0] for row in target_cursor.fetchall()}
        
        missing_ids = source_ids - target_ids
        print(f"  Lignes avec ID_IMPRIMEUR = 0 dans source: {len(source_ids)}")
        print(f"  Lignes totales dans cible: {len(target_ids)}")
        print(f"  Lignes manquantes: {len(missing_ids)}")
        if missing_ids:
            print(f"  IDs manquants: {sorted(list(missing_ids))}")
        print()
        
        if not missing_ids:
            print("✓ Aucune ligne manquante !")
            return
        
        # 2. Vérifier si ces IDs existent dans la cible avec d'autres valeurs
        print("[2] Verification si les IDs existent dans la cible avec d'autres valeurs...")
        for missing_id in sorted(list(missing_ids))[:5]:
            target_cursor.execute("SELECT ID, ID_PAPIER, ID_IMPRIMEUR FROM PAPIERS_IMPRIMEURS WHERE ID = ?", missing_id)
            row = target_cursor.fetchone()
            if row:
                print(f"  ID {missing_id}: EXISTE dans cible avec ID_IMPRIMEUR = {row[2]}")
            else:
                print(f"  ID {missing_id}: N'EXISTE PAS dans cible")
        print()
        
        # 3. Récupérer les données complètes des lignes manquantes
        print("[3] Donnees completes des lignes manquantes (source)...")
        missing_ids_list = sorted(list(missing_ids))
        placeholders = ','.join(['?' for _ in missing_ids_list])
        source_cursor.execute(f"""
            SELECT ID, ID_PAPIER, ID_IMPRIMEUR 
            FROM PAPIERS_IMPRIMEURS 
            WHERE ID IN ({placeholders})
            ORDER BY ID
        """, missing_ids_list)
        
        missing_rows = source_cursor.fetchall()
        print(f"  {len(missing_rows)} lignes recuperees")
        for row in missing_rows[:5]:
            print(f"    ID={row[0]}, ID_PAPIER={row[1]}, ID_IMPRIMEUR={row[2]}")
        print()
        
        # 4. Vérifier les FK
        print("[4] Verification des FK...")
        target_cursor.execute("SELECT COUNT(*) FROM IMPRIMEURS WHERE ID_SOCIETE = 0")
        imprimeur_zero_exists = target_cursor.fetchone()[0] > 0
        print(f"  ID_SOCIETE = 0 existe dans IMPRIMEURS: {imprimeur_zero_exists}")
        
        # Vérifier ID_PAPIER pour chaque ligne manquante
        papier_ids = set()
        for row in missing_rows:
            if row[1]:  # ID_PAPIER
                papier_ids.add(row[1])
        
        if papier_ids:
            placeholders_papier = ','.join(['?' for _ in papier_ids])
            target_cursor.execute(f"""
                SELECT DISTINCT ID FROM PAPIERS WHERE ID IN ({placeholders_papier})
            """, list(papier_ids))
            existing_papier_ids = {row[0] for row in target_cursor.fetchall()}
            missing_papier_ids = papier_ids - existing_papier_ids
            print(f"  ID_PAPIER manquants dans PAPIERS: {len(missing_papier_ids)}")
            if missing_papier_ids:
                print(f"    IDs: {sorted(list(missing_papier_ids))[:10]}")
        print()
        
        # 5. Simuler la logique de vérification FK exacte du code
        print("[5] Simulation de la logique de verification FK (code actuel)...")
        target_cursor.execute("SELECT DISTINCT [ID_SOCIETE] FROM [IMPRIMEURS] WHERE [ID_SOCIETE] IS NOT NULL")
        fk_cache = {row[0] for row in target_cursor.fetchall()}
        print(f"  Cache FK initial: {sorted(list(fk_cache))[:10]}...")
        print(f"  0 dans le cache initial: {0 in fk_cache}")
        
        # Simuler la vérification pour chaque ligne manquante
        for row in missing_rows[:5]:
            fk_value = row[2]  # ID_IMPRIMEUR
            print(f"\n  Ligne ID={row[0]}, ID_IMPRIMEUR={fk_value}:")
            print(f"    fk_value is not None: {fk_value is not None}")
            if fk_value is not None:
                print(f"    fk_value in fk_cache: {fk_value in fk_cache}")
                if fk_value not in fk_cache:
                    print(f"    → fk_value PAS dans cache")
                    if fk_value == 0:
                        print(f"    → fk_value == 0, verification directe...")
                        target_cursor.execute("SELECT COUNT(*) FROM IMPRIMEURS WHERE ID_SOCIETE = 0")
                        count = target_cursor.fetchone()[0]
                        print(f"    → COUNT(*) FROM IMPRIMEURS WHERE ID_SOCIETE = 0 = {count}")
                        if count > 0:
                            print(f"    → ✓ 0 existe, devrait etre ajoute au cache et ligne inseree")
                        else:
                            print(f"    → ✗ 0 n'existe pas, ligne devrait etre ignoree")
                    else:
                        print(f"    → ✗ FK manquante, ligne devrait etre ignoree")
                else:
                    print(f"    → ✓ fk_value dans cache, ligne devrait etre inseree")
        print()
        
        print("=" * 80)
        print("CONCLUSION")
        print("=" * 80)
        if imprimeur_zero_exists and 0 in fk_cache:
            print("✓ Les conditions sont remplies pour synchroniser les lignes")
            print("  - ID_SOCIETE = 0 existe dans IMPRIMEURS")
            print("  - 0 est dans le cache FK")
            print()
            print("  SOLUTION:")
            print("  1. Utiliser le script synchroniser_lignes_papiers_imprimeurs_manquantes.py")
            print("  2. Ou resynchroniser PAPIERS_IMPRIMEURS via l'interface web")
        else:
            print("⚠️ Conditions non remplies")
            if not imprimeur_zero_exists:
                print("  - ID_SOCIETE = 0 n'existe pas dans IMPRIMEURS")
            if 0 not in fk_cache:
                print("  - 0 n'est pas dans le cache FK")
        
    finally:
        source_conn.close()
        target_conn.close()

if __name__ == "__main__":
    main()
