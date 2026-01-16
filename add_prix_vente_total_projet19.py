"""
Script pour ajouter la colonne PrixVenteTotal à la table WEB_S_DOS_ENCOURS
Projet 19 - Gestion des Dossiers en Cours
Calcul : PrixVenteUnitaire * QteComm_COMMANDES
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from db import get_db_cursor

def add_prix_vente_total_column():
    """Ajoute la colonne PrixVenteTotal si elle n'existe pas"""
    try:
        with get_db_cursor() as cursor:
            print("=" * 80)
            print("AJOUT DE LA COLONNE PrixVenteTotal À WEB_S_DOS_ENCOURS")
            print("=" * 80)
            print()
            
            # Vérifier si la colonne existe déjà
            cursor.execute("""
                SELECT COUNT(*) as col_exists
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
                AND COLUMN_NAME = 'PrixVenteTotal'
            """)
            col_exists = cursor.fetchone().col_exists > 0
            
            if col_exists:
                print("✅ La colonne PrixVenteTotal existe déjà dans WEB_S_DOS_ENCOURS")
                print()
                
                # Afficher les informations de la colonne
                cursor.execute("""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        NUMERIC_PRECISION,
                        NUMERIC_SCALE,
                        IS_NULLABLE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
                    AND COLUMN_NAME = 'PrixVenteTotal'
                """)
                col_info = cursor.fetchone()
                if col_info:
                    precision = f"({col_info.NUMERIC_PRECISION},{col_info.NUMERIC_SCALE})" if col_info.NUMERIC_PRECISION else ""
                    nullable = "NULL" if col_info.IS_NULLABLE == "YES" else "NOT NULL"
                    print(f"   Type: {col_info.DATA_TYPE}{precision}")
                    print(f"   Nullable: {nullable}")
                    print()
            else:
                print("⚠️  La colonne PrixVenteTotal n'existe pas encore")
                print("   Ajout de la colonne...")
                print()
                
                try:
                    cursor.execute("""
                        ALTER TABLE WEB_S_DOS_ENCOURS
                        ADD PrixVenteTotal DECIMAL(18,3) NULL
                    """)
                    cursor.connection.commit()
                    print("✅ Colonne PrixVenteTotal ajoutée avec succès!")
                    print()
                except Exception as e:
                    print(f"❌ Erreur lors de l'ajout de la colonne: {e}")
                    print()
                    raise
            
            print("=" * 80)
            print("OPÉRATION TERMINÉE")
            print("=" * 80)
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    add_prix_vente_total_column()
