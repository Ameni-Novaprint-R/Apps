#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour verifier et creer la table WEB_S_DOS_ENCOURS sur le serveur reseau 192.168.10.225
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from db import get_db_cursor, get_connection_string

def verifier_et_creer_table():
    """Verifie et cree la table WEB_S_DOS_ENCOURS sur le serveur reseau"""
    
    print("=" * 80)
    print("Verification de la table WEB_S_DOS_ENCOURS sur le serveur reseau")
    print("=" * 80)
    print()
    print(f"Configuration de connexion: {get_connection_string()}")
    print()
    
    try:
        with get_db_cursor() as cursor:
            # Verifier la connexion en testant une requete simple
            cursor.execute("SELECT @@SERVERNAME AS ServerName, DB_NAME() AS DatabaseName")
            row = cursor.fetchone()
            print(f"[INFO] Serveur connecte: {row.ServerName}")
            print(f"[INFO] Base de donnees: {row.DatabaseName}")
            print()
            
            # Verifier si la table existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if table_exists:
                print("[INFO] La table WEB_S_DOS_ENCOURS existe deja sur le serveur reseau.")
                
                # Compter les lignes
                cursor.execute("SELECT COUNT(*) FROM WEB_S_DOS_ENCOURS")
                count = cursor.fetchone()[0]
                print(f"[INFO] Nombre de lignes dans la table: {count}")
                
                # Afficher la structure
                cursor.execute("""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        CHARACTER_MAXIMUM_LENGTH,
                        IS_NULLABLE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS'
                    ORDER BY ORDINAL_POSITION
                """)
                print("\nStructure de la table:")
                print("-" * 80)
                for row in cursor.fetchall():
                    max_len = f"({row.CHARACTER_MAXIMUM_LENGTH})" if row.CHARACTER_MAXIMUM_LENGTH else ""
                    nullable = "NULL" if row.IS_NULLABLE == "YES" else "NOT NULL"
                    print(f"  {row.COLUMN_NAME:<25} {row.DATA_TYPE}{max_len:<15} {nullable}")
                
            else:
                print("[ATTENTION] La table WEB_S_DOS_ENCOURS n'existe pas sur le serveur reseau.")
                print("Creation de la table...")
                
                # Creer la table
                cursor.execute("""
                    CREATE TABLE WEB_S_DOS_ENCOURS (
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
                cursor.connection.commit()
                print("[OK] Table creee avec succes")
                
                # Creer l'index
                try:
                    cursor.execute("""
                        CREATE INDEX IX_WEB_S_DOS_ENCOURS_Numero 
                        ON WEB_S_DOS_ENCOURS(Numero_COMMANDES)
                    """)
                    cursor.connection.commit()
                    print("[OK] Index cree")
                except Exception as e:
                    print(f"[ATTENTION] Erreur lors de la creation de l'index: {e}")
            
            print()
            print("=" * 80)
            print("[OK] Verification terminee avec succes !")
            print("=" * 80)
            
    except Exception as e:
        print(f"[ERREUR] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = verifier_et_creer_table()
    sys.exit(0 if success else 1)




