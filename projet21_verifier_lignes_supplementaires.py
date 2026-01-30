#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Vérification des lignes supplémentaires dans PAPIERS_ARTICLES"""

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
    if config.get('trusted_connection'):
        driver_candidates = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"]
        for drv in driver_candidates:
            try:
                conn_str = f"DRIVER={{{drv}}};SERVER={config['server']};DATABASE={config['database']};Trusted_Connection=yes;TrustServerCertificate=yes"
                return pyodbc.connect(conn_str)
            except:
                continue
    else:
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config['server']};DATABASE={config['database']};UID={config['username']};PWD={config['password']}"
        return pyodbc.connect(conn_str)

source_conn = get_connection(SOURCE_CONFIG, readonly=True)
target_conn = get_connection(TARGET_CONFIG, readonly=True)

source_cursor = source_conn.cursor()
target_cursor = target_conn.cursor()

# Lire les données source
source_cursor.execute("""
    SELECT ID_PAPIER, ID_CERTIFICATION, Grammage, Epaisseur, FormLaize, FormLong
    FROM PAPIERS_ARTICLES
""")
source_keys = {tuple(row) for row in source_cursor.fetchall()}

# Lire les données cible
target_cursor.execute("""
    SELECT ID, ID_PAPIER, ID_CERTIFICATION, Grammage, Epaisseur, FormLaize, FormLong
    FROM PAPIERS_ARTICLES
""")
target_data = [(row[0], tuple(row[1:])) for row in target_cursor.fetchall()]

# Identifier les lignes supplémentaires
supplementaires = []
for target_id, target_key in target_data:
    if target_key not in source_keys:
        supplementaires.append(target_id)

print(f"Lignes supplementaires: {len(supplementaires)}")

# Vérifier si elles sont référencées
if supplementaires:
    placeholders = ','.join('?' * len(supplementaires))
    target_cursor.execute(f"""
        SELECT ID_ARTICLE, COUNT(*) AS Refs
        FROM PAPIERS_TARIF_FMT
        WHERE ID_ARTICLE IN ({placeholders})
        GROUP BY ID_ARTICLE
    """, supplementaires)
    
    refs_data = {row[0]: row[1] for row in target_cursor.fetchall()}
    
    avec_refs = sum(1 for sid in supplementaires if refs_data.get(sid, 0) > 0)
    sans_refs = len(supplementaires) - avec_refs
    
    print(f"Lignes avec references: {avec_refs}")
    print(f"Lignes sans references: {sans_refs}")
    
    if avec_refs > 0:
        print("\n[ATTENTION] Certaines lignes supplementaires sont referencees!")
        for sid in supplementaires:
            if refs_data.get(sid, 0) > 0:
                print(f"  ID {sid}: {refs_data[sid]} references")
    else:
        print("\n[OK] Aucune ligne supplementaire n'est referencee - SÛR")
else:
    print("[OK] Aucune ligne supplementaire")

source_conn.close()
target_conn.close()
