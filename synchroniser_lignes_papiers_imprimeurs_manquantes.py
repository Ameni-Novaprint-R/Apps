#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour synchroniser les 13 lignes manquantes de PAPIERS_IMPRIMEURS
qui ont ID_IMPRIMEUR = 0
"""

import json
from datetime import datetime

def get_connection(config, readonly=False):
    """
    Connexion SQL Server.
    Utilise la même logique que projet21_routes.py
    """
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
    print("SYNCHRONISATION DES LIGNES MANQUANTES - PAPIERS_IMPRIMEURS")
    print("=" * 80)
    print()
    
    source_conn = get_connection(SOURCE_CONFIG, readonly=True)
    source_cursor = source_conn.cursor()
    target_conn = get_connection(TARGET_CONFIG, readonly=False)
    target_cursor = target_conn.cursor()
    
    try:
        # 1. Identifier les lignes manquantes avec ID_IMPRIMEUR = 0
        print("[1] Identification des lignes manquantes avec ID_IMPRIMEUR = 0...")
        source_cursor.execute("""
            SELECT 
                ID,
                ID_PAPIER,
                ID_IMPRIMEUR
            FROM PAPIERS_IMPRIMEURS
            WHERE ID_IMPRIMEUR = 0
            ORDER BY ID
        """)
        source_rows = source_cursor.fetchall()
        
        target_cursor.execute("SELECT ID FROM PAPIERS_IMPRIMEURS")
        target_ids = {row[0] for row in target_cursor.fetchall()}
        
        missing_rows = []
        for row in source_rows:
            source_id = row[0]
            if source_id not in target_ids:
                missing_rows.append({
                    'ID': row[0],
                    'ID_PAPIER': row[1],
                    'ID_IMPRIMEUR': row[2]
                })
        
        print(f"  {len(missing_rows)} lignes manquantes identifiees")
        if missing_rows:
            print("  IDs manquants:", [r['ID'] for r in missing_rows])
        print()
        
        if not missing_rows:
            print("Aucune ligne manquante a synchroniser.")
            return
        
        # 2. Vérifier si ID_SOCIETE = 0 existe dans IMPRIMEURS de la cible
        print("[2] Verification de ID_SOCIETE = 0 dans IMPRIMEURS (cible)...")
        target_cursor.execute("SELECT COUNT(*) FROM IMPRIMEURS WHERE ID_SOCIETE = 0")
        imprimeur_zero_exists = target_cursor.fetchone()[0] > 0
        
        if not imprimeur_zero_exists:
            print("  ⚠️ ID_SOCIETE = 0 n'existe PAS dans IMPRIMEURS de la cible")
            print("  Les lignes avec ID_IMPRIMEUR = 0 seront inserees avec ID_IMPRIMEUR = 0")
            print("  (meme si la FK ne peut pas etre validee)")
        else:
            print("  ✓ ID_SOCIETE = 0 existe dans IMPRIMEURS de la cible")
        print()
        
        # 3. Récupérer toutes les colonnes de PAPIERS_IMPRIMEURS
        print("[3] Recuperation des colonnes de PAPIERS_IMPRIMEURS...")
        source_cursor.execute("SELECT * FROM PAPIERS_IMPRIMEURS WHERE 1=0")
        columns = [desc[0] for desc in source_cursor.description]
        print(f"  {len(columns)} colonnes trouvees: {', '.join(columns[:5])}...")
        print()
        
        # 4. Récupérer les données complètes des lignes manquantes
        print("[4] Recuperation des donnees completes des lignes manquantes...")
        missing_ids = [r['ID'] for r in missing_rows]
        placeholders = ','.join(['?' for _ in missing_ids])
        
        source_cursor.execute(f"""
            SELECT * FROM PAPIERS_IMPRIMEURS 
            WHERE ID IN ({placeholders})
        """, missing_ids)
        
        rows_to_insert = source_cursor.fetchall()
        print(f"  {len(rows_to_insert)} lignes recuperees")
        print()
        
        # 5. Vérifier si IDENTITY_INSERT est nécessaire
        print("[5] Verification de la colonne IDENTITY...")
        target_cursor.execute("""
            SELECT COLUMNPROPERTY(OBJECT_ID('dbo.PAPIERS_IMPRIMEURS'), 'ID', 'IsIdentity')
        """)
        is_identity = target_cursor.fetchone()[0] == 1
        
        if is_identity:
            print("  Colonne ID est IDENTITY, activation de IDENTITY_INSERT...")
            target_cursor.execute("SET IDENTITY_INSERT dbo.PAPIERS_IMPRIMEURS ON")
        else:
            print("  Colonne ID n'est pas IDENTITY")
        print()
        
        # 6. Insérer les lignes manquantes
        print("[6] Insertion des lignes manquantes...")
        col_list = ", ".join([f"[{c}]" for c in columns])
        placeholders = ", ".join(["?" for _ in columns])
        
        inserted = 0
        errors = []
        
        for row in rows_to_insert:
            try:
                target_cursor.execute(
                    f"INSERT INTO PAPIERS_IMPRIMEURS ({col_list}) VALUES ({placeholders})",
                    row
                )
                inserted += 1
                print(f"  ✓ ID {row[0]} insere")
            except Exception as e:
                error_msg = f"ID {row[0]}: {str(e)}"
                errors.append(error_msg)
                print(f"  ✗ {error_msg}")
        
        if inserted > 0:
            target_conn.commit()
            print()
            print(f"  {inserted} lignes inserees avec succes")
        
        if errors:
            print()
            print(f"  {len(errors)} erreurs:")
            for err in errors:
                print(f"    - {err}")
        
        if is_identity:
            target_cursor.execute("SET IDENTITY_INSERT dbo.PAPIERS_IMPRIMEURS OFF")
            print()
            print("  IDENTITY_INSERT desactive")
        
        print()
        print("=" * 80)
        print("SYNCHRONISATION TERMINEE")
        print("=" * 80)
        print()
        print(f"Lignes inserees: {inserted}/{len(rows_to_insert)}")
        if errors:
            print(f"Erreurs: {len(errors)}")
        
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
        target_conn.rollback()
    finally:
        if is_identity:
            try:
                target_cursor.execute("SET IDENTITY_INSERT dbo.PAPIERS_IMPRIMEURS OFF")
            except:
                pass
        source_conn.close()
        target_conn.close()

if __name__ == "__main__":
    main()
