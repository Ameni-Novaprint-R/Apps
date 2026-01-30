#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour analyser les lignes manquantes dans PAPIERS_IMPRIMEURS
après synchronisation.
"""

from db import get_db_cursor
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
    print("ANALYSE DES LIGNES MANQUANTES - PAPIERS_IMPRIMEURS")
    print("=" * 80)
    print()
    
    source_conn = get_connection(SOURCE_CONFIG, readonly=True)
    source_cursor = source_conn.cursor()
    target_conn = get_connection(TARGET_CONFIG, readonly=True)
    target_cursor = target_conn.cursor()
    
    try:
        # 1. Compter les lignes dans source et cible
        print("[1] Comptage des lignes...")
        source_cursor.execute("SELECT COUNT(*) FROM PAPIERS_IMPRIMEURS")
        source_count = source_cursor.fetchone()[0]
        
        target_cursor.execute("SELECT COUNT(*) FROM PAPIERS_IMPRIMEURS")
        target_count = target_cursor.fetchone()[0]
        
        print(f"  Source (Novaprint): {source_count} lignes")
        print(f"  Cible (novaprint_restored): {target_count} lignes")
        print(f"  Manquantes: {source_count - target_count} lignes")
        print()
        
        # 2. Identifier les lignes manquantes
        print("[2] Identification des lignes manquantes...")
        source_cursor.execute("""
            SELECT 
                ID,
                ID_PAPIER,
                ID_IMPRIMEUR
            FROM PAPIERS_IMPRIMEURS
            ORDER BY ID
        """)
        source_rows = source_cursor.fetchall()
        
        target_cursor.execute("""
            SELECT ID, ID_PAPIER, ID_IMPRIMEUR
            FROM PAPIERS_IMPRIMEURS
        """)
        target_ids = {row[0] for row in target_cursor.fetchall()}
        
        missing_rows = []
        for row in source_rows:
            source_id = row[0]
            if source_id not in target_ids:
                missing_rows.append({
                    'ID': source_id,
                    'ID_PAPIER': row[1],
                    'ID_IMPRIMEUR': row[2]
                })
        
        print(f"  {len(missing_rows)} lignes manquantes identifiees")
        print()
        
        # 3. Analyser pourquoi ces lignes sont manquantes
        print("[3] Analyse des causes...")
        
        # Vérifier les FK vers PAPIERS
        print("  Verification des FK vers PAPIERS...")
        target_cursor.execute("SELECT DISTINCT ID FROM PAPIERS")
        papier_ids = {row[0] for row in target_cursor.fetchall()}
        
        # Vérifier les FK vers IMPRIMEURS
        print("  Verification des FK vers IMPRIMEURS...")
        target_cursor.execute("SELECT DISTINCT ID_SOCIETE FROM IMPRIMEURS")
        imprimeur_ids = {row[0] for row in target_cursor.fetchall()}
        
        analysis = {
            'total_missing': len(missing_rows),
            'missing_by_id': [],
            'fk_papier_missing': [],
            'fk_imprimeur_missing': [],
            'both_fk_missing': [],
            'fk_ok_but_missing': []
        }
        
        for row in missing_rows:
            id_papier = row['ID_PAPIER']
            id_imprimeur = row['ID_IMPRIMEUR']
            
            papier_exists = id_papier is None or id_papier in papier_ids
            imprimeur_exists = id_imprimeur is None or id_imprimeur in imprimeur_ids
            
            analysis['missing_by_id'].append({
                'ID': row['ID'],
                'ID_PAPIER': id_papier,
                'ID_IMPRIMEUR': id_imprimeur,
                'FK_PAPIER_OK': papier_exists,
                'FK_IMPRIMEUR_OK': imprimeur_exists
            })
            
            if not papier_exists and not imprimeur_exists:
                analysis['both_fk_missing'].append(row)
            elif not papier_exists:
                analysis['fk_papier_missing'].append(row)
            elif not imprimeur_exists:
                analysis['fk_imprimeur_missing'].append(row)
            else:
                analysis['fk_ok_but_missing'].append(row)
        
        # Afficher les résultats
        print()
        print("=" * 80)
        print("RESULTATS DE L'ANALYSE")
        print("=" * 80)
        print()
        print(f"Total lignes manquantes: {analysis['total_missing']}")
        print()
        print(f"Lignes avec FK PAPIER manquante: {len(analysis['fk_papier_missing'])}")
        print(f"Lignes avec FK IMPRIMEUR manquante: {len(analysis['fk_imprimeur_missing'])}")
        print(f"Lignes avec les deux FK manquantes: {len(analysis['both_fk_missing'])}")
        print(f"Lignes avec FK OK mais toujours manquantes: {len(analysis['fk_ok_but_missing'])}")
        print()
        
        # Afficher le détail des lignes manquantes
        if analysis['missing_by_id']:
            print("DETAIL DES LIGNES MANQUANTES:")
            print("-" * 80)
            for item in analysis['missing_by_id']:
                print(f"ID: {item['ID']}, ID_PAPIER: {item['ID_PAPIER']}, ID_IMPRIMEUR: {item['ID_IMPRIMEUR']}")
                print(f"  FK_PAPIER_OK: {item['FK_PAPIER_OK']}, FK_IMPRIMEUR_OK: {item['FK_IMPRIMEUR_OK']}")
                print()
        
        # Vérifier si les FK existent dans la source
        print("=" * 80)
        print("VERIFICATION DES FK DANS LA SOURCE")
        print("=" * 80)
        print()
        
        for item in analysis['missing_by_id']:
            id_papier = item['ID_PAPIER']
            id_imprimeur = item['ID_IMPRIMEUR']
            
            if id_papier:
                source_cursor.execute("SELECT COUNT(*) FROM PAPIERS WHERE ID = ?", (id_papier,))
                papier_in_source = source_cursor.fetchone()[0] > 0
                print(f"ID {item['ID']}: PAPIER {id_papier} existe dans source: {papier_in_source}")
            
            if id_imprimeur:
                source_cursor.execute("SELECT COUNT(*) FROM IMPRIMEURS WHERE ID_SOCIETE = ?", (id_imprimeur,))
                imprimeur_in_source = source_cursor.fetchone()[0] > 0
                print(f"ID {item['ID']}: IMPRIMEUR {id_imprimeur} existe dans source: {imprimeur_in_source}")
        
        # Sauvegarder le rapport JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"analyse_lignes_manquantes_papiers_imprimeurs_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
        
        print()
        print(f"Rapport sauvegarde dans: {report_file}")
        
    finally:
        source_conn.close()
        target_conn.close()

if __name__ == "__main__":
    main()
