#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour créer la table WEB_S_DOS_ENCOURS dans la base de données NOVAPRINT_restored
et copier les données initiales depuis COMMANDES et SOCIETES
"""
import pyodbc
from datetime import datetime
from db import get_db_cursor, get_connection_string

def create_table_web_s_dos_encours():
    """Crée la table WEB_S_DOS_ENCOURS et copie les données initiales"""
    
    print("=" * 80)
    print("Création de la table WEB_S_DOS_ENCOURS")
    print("=" * 80)
    print()
    
    try:
        with get_db_cursor() as cursor:
            # Vérifier si la table existe déjà
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if table_exists:
                print("[ATTENTION] La table WEB_S_DOS_ENCOURS existe deja.")
                response = input("Voulez-vous la supprimer et la recréer ? (o/n): ")
                if response.lower() != 'o':
                    print("Opération annulée.")
                    return
                
                print("Suppression de l'ancienne table...")
                cursor.execute("DROP TABLE WEB_S_DOS_ENCOURS")
                cursor.connection.commit()
                print("[OK] Table supprimee")
            
            # Créer la table
            print("Création de la table WEB_S_DOS_ENCOURS...")
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
            
            # Créer un index sur Numero_COMMANDES pour améliorer les performances
            print("Création de l'index sur Numero_COMMANDES...")
            try:
                cursor.execute("""
                    CREATE INDEX IX_WEB_S_DOS_ENCOURS_Numero 
                    ON WEB_S_DOS_ENCOURS(Numero_COMMANDES)
                """)
                cursor.connection.commit()
                print("[OK] Index cree")
            except Exception as e:
                print(f"[ATTENTION] Erreur lors de la creation de l'index (peut-etre deja existant): {e}")
            
            # Copier les données initiales
            print("Copie des données depuis COMMANDES et SOCIETES...")
            cursor.execute("""
                INSERT INTO WEB_S_DOS_ENCOURS (
                    Numero_COMMANDES,
                    RaiSocTri_SOCIETES,
                    Reference_COMMANDES,
                    QteComm_COMMANDES,
                    Coef_COMMANDES
                )
                SELECT 
                    C.Numero AS Numero_COMMANDES,
                    S.RaiSocTri AS RaiSocTri_SOCIETES,
                    C.Reference AS Reference_COMMANDES,
                    C.QteComm AS QteComm_COMMANDES,
                    C.Coef AS Coef_COMMANDES
                FROM 
                    COMMANDES C
                    LEFT JOIN SOCIETES S ON C.ID_SOCIETE = S.ID
            """)
            rows_inserted = cursor.rowcount
            cursor.connection.commit()
            print(f"[OK] {rows_inserted} lignes inserees")
            
            # Vérifier le nombre de lignes
            cursor.execute("SELECT COUNT(*) FROM WEB_S_DOS_ENCOURS")
            total_rows = cursor.fetchone()[0]
            print(f"[OK] Total de lignes dans la table: {total_rows}")
            
            # Afficher un échantillon des données
            print("\nÉchantillon des données (5 premières lignes):")
            cursor.execute("""
                SELECT TOP 5 
                    ID,
                    Numero_COMMANDES,
                    RaiSocTri_SOCIETES,
                    Reference_COMMANDES,
                    QteComm_COMMANDES,
                    Coef_COMMANDES
                FROM WEB_S_DOS_ENCOURS
                ORDER BY ID
            """)
            print("-" * 80)
            print(f"{'ID':<5} {'Numero':<15} {'Client':<30} {'Reference':<20} {'Qte':<8} {'Coef':<8}")
            print("-" * 80)
            for row in cursor.fetchall():
                print(f"{row.ID:<5} {str(row.Numero_COMMANDES or ''):<15} {str(row.RaiSocTri_SOCIETES or '')[:30]:<30} {str(row.Reference_COMMANDES or '')[:20]:<20} {str(row.QteComm_COMMANDES or ''):<8} {str(row.Coef_COMMANDES or ''):<8}")
            
            print()
            print("=" * 80)
            print("[OK] Table WEB_S_DOS_ENCOURS creee avec succes !")
            print("=" * 80)
            
    except pyodbc.Error as e:
        print(f"[ERREUR] Erreur SQL: {e}")
        raise
    except Exception as e:
        print(f"[ERREUR] Erreur: {e}")
        raise

if __name__ == "__main__":
    try:
        create_table_web_s_dos_encours()
    except Exception as e:
        print(f"\n[ERREUR] Erreur lors de la creation de la table: {e}")
        import traceback
        traceback.print_exc()

