#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour verifier et creer la table WEB_S_DOS_ENCOURS sur le serveur reseau 192.168.10.225
Version avec support de l'authentification SQL Server
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pyodbc
import os

SERVER_IP = "192.168.10.225"
DATABASE = "novaprint_restored"
TABLE_NAME = "WEB_S_DOS_ENCOURS"

print("=" * 80)
print("VERIFICATION ET CREATION DE WEB_S_DOS_ENCOURS")
print("=" * 80)
print()
print(f"Serveur: {SERVER_IP}")
print(f"Base de donnees: {DATABASE}")
print(f"Table: {TABLE_NAME}")
print()

# Essayer differentes methodes de connexion
connection_methods = [
    {
        "name": "Authentification Windows avec IP",
        "conn_str": f"DRIVER={{SQL Server}};SERVER={SERVER_IP};DATABASE={DATABASE};Trusted_Connection=yes;TrustServerCertificate=yes"
    },
    {
        "name": "Authentification Windows avec nom serveur (SRV-KBA1)",
        "conn_str": f"DRIVER={{SQL Server}};SERVER=SRV-KBA1;DATABASE={DATABASE};Trusted_Connection=yes;TrustServerCertificate=yes"
    }
]

# Si des credentials SQL Server sont disponibles dans les variables d'environnement
sql_user = os.environ.get('SQL_SERVER_USER')
sql_pwd = os.environ.get('SQL_SERVER_PWD')

if sql_user and sql_pwd:
    connection_methods.append({
        "name": "Authentification SQL Server",
        "conn_str": f"DRIVER={{SQL Server}};SERVER={SERVER_IP};DATABASE={DATABASE};UID={sql_user};PWD={sql_pwd};TrustServerCertificate=yes"
    })

conn = None
method_used = None

for method in connection_methods:
    print(f"Essai: {method['name']}...")
    try:
        conn = pyodbc.connect(method['conn_str'], timeout=10)
        method_used = method['name']
        print(f"[OK] Connexion reussie avec: {method['name']}")
        break
    except Exception as e:
        print(f"[ERREUR] {str(e)[:100]}")
        continue

if not conn:
    print()
    print("=" * 80)
    print("[ERREUR] Impossible de se connecter au serveur reseau")
    print("=" * 80)
    print()
    print("SOLUTIONS:")
    print("1. Configurer l'authentification SQL Server sur le serveur 192.168.10.225")
    print("2. Definir les variables d'environnement SQL_SERVER_USER et SQL_SERVER_PWD")
    print("3. Ou executer le script SQL directement sur le serveur:")
    print("   verifier_creer_web_s_dos_encours_sql.sql")
    sys.exit(1)

try:
    cursor = conn.cursor()
    
    # Verifier le serveur connecte
    print()
    print("=" * 80)
    print("ETAPE 1: Verification du serveur connecte")
    print("=" * 80)
    cursor.execute("SELECT @@SERVERNAME AS ServerName, DB_NAME() AS DatabaseName, HOST_NAME() AS HostName")
    row = cursor.fetchone()
    server_name = str(row.ServerName)
    database_name = str(row.DatabaseName)
    host_name = str(row.HostName)
    
    print(f"[INFO] Serveur SQL: {server_name}")
    print(f"[INFO] Base de donnees: {database_name}")
    print(f"[INFO] Machine hote: {host_name}")
    print()
    
    # Verifier qu'on est sur le serveur reseau
    is_network = False
    if "192.168.10.225" in server_name or "SRV-KBA1" in server_name.upper():
        is_network = True
        print("[OK] Connexion au serveur RESEAU confirmee!")
    elif "LAPTOP" in host_name.upper() or "LOCAL" in host_name.upper():
        print("[ERREUR CRITIQUE] Connexion a une base LOCALE detectee!")
        print("  La table WEB_S_DOS_ENCOURS ne doit PAS etre sur la base locale!")
        conn.close()
        sys.exit(1)
    else:
        print(f"[ATTENTION] Serveur: {server_name}")
        print("  Verifiez manuellement si c'est le serveur reseau 192.168.10.225")
        is_network = True
    
    # Verifier si la table existe
    print()
    print("=" * 80)
    print("ETAPE 2: Verification de l'existence de la table WEB_S_DOS_ENCOURS")
    print("=" * 80)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = ?
    """, (TABLE_NAME,))
    table_exists = cursor.fetchone()[0] > 0
    
    if table_exists:
        print(f"[OK] La table {TABLE_NAME} existe sur le serveur reseau")
        
        cursor.execute(f"SELECT COUNT(*) FROM [{TABLE_NAME}]")
        count = cursor.fetchone()[0]
        print(f"[INFO] Nombre de lignes: {count}")
        
        # Afficher la structure
        print()
        print("Structure de la table:")
        print("-" * 80)
        cursor.execute("""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """, (TABLE_NAME,))
        
        for col in cursor.fetchall():
            max_len = f"({col.CHARACTER_MAXIMUM_LENGTH})" if col.CHARACTER_MAXIMUM_LENGTH else ""
            nullable = "NULL" if col.IS_NULLABLE == "YES" else "NOT NULL"
            print(f"  {col.COLUMN_NAME:<30} {col.DATA_TYPE}{max_len:<15} {nullable}")
        
        print()
        print("=" * 80)
        print("[SUCCES] La table WEB_S_DOS_ENCOURS existe sur le serveur reseau!")
        print("=" * 80)
        
    else:
        print(f"[INFO] La table {TABLE_NAME} n'existe pas sur le serveur reseau")
        print()
        
        # Creer la table
        print("=" * 80)
        print("ETAPE 3: Creation de la table WEB_S_DOS_ENCOURS")
        print("=" * 80)
        print()
        print("Creation de la table...")
        
        cursor.execute(f"""
            CREATE TABLE {TABLE_NAME} (
                ID INT IDENTITY(1,1) PRIMARY KEY,
                Numero_COMMANDES NVARCHAR(255) NULL,
                RaiSocTri_SOCIETES NVARCHAR(255) NULL,
                Reference_COMMANDES NVARCHAR(255) NULL,
                QteComm_COMMANDES INT NULL,
                Coef_COMMANDES DECIMAL(18,2) NULL,
                DateCreation DATETIME DEFAULT GETDATE(),
                DateModification DATETIME DEFAULT GETDATE()
            )
        """)
        conn.commit()
        print("[OK] Table creee avec succes")
        
        # Creer l'index
        print("Creation de l'index...")
        try:
            cursor.execute(f"""
                CREATE INDEX IX_WEB_S_DOS_ENCOURS_Numero 
                ON {TABLE_NAME}(Numero_COMMANDES)
            """)
            conn.commit()
            print("[OK] Index cree avec succes")
        except Exception as e:
            print(f"[ATTENTION] Erreur lors de la creation de l'index: {e}")
        
        # Verifier
        cursor.execute(f"SELECT COUNT(*) FROM [{TABLE_NAME}]")
        count = cursor.fetchone()[0]
        print(f"[OK] Table creee avec succes ({count} lignes)")
        
        print()
        print("=" * 80)
        print("[SUCCES] Table WEB_S_DOS_ENCOURS creee sur le serveur reseau!")
        print("=" * 80)
    
    conn.close()
    
    print()
    print("=" * 80)
    print("[SUCCES] Verification terminee avec succes!")
    print(f"  Methode de connexion utilisee: {method_used}")
    print("  Table WEB_S_DOS_ENCOURS: Sur le serveur reseau 192.168.10.225")
    print("=" * 80)
    
except Exception as e:
    print(f"[ERREUR] {e}")
    import traceback
    traceback.print_exc()
    if conn:
        conn.close()
    sys.exit(1)

