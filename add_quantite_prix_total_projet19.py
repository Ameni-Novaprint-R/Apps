"""
Script pour ajouter les colonnes QteComm_COMMANDES et PrixVenteTotal
à la table WEB_S_DOS_ENCOURS pour le projet 19
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from db import get_db_cursor

def add_quantite_prix_total_columns():
    """Ajoute les colonnes QteComm_COMMANDES et PrixVenteTotal si elles n'existent pas"""
    try:
        with get_db_cursor() as cursor:
            print("=" * 80)
            print("AJOUT DES COLONNES QteComm_COMMANDES ET PrixVenteTotal À WEB_S_DOS_ENCOURS")
            print("=" * 80)
            print()
            
            # Vérifier si la colonne QteComm_COMMANDES existe déjà
            cursor.execute("""
                SELECT COUNT(*) as col_exists
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
                AND COLUMN_NAME = 'QteComm_COMMANDES'
            """)
            quantite_exists = cursor.fetchone().col_exists > 0
            
            if not quantite_exists:
                cursor.execute("""
                    ALTER TABLE WEB_S_DOS_ENCOURS
                    ADD QteComm_COMMANDES INT NULL
                """)
                cursor.connection.commit()
                print("Colonne QteComm_COMMANDES ajoutée avec succès")
            else:
                print("La colonne QteComm_COMMANDES existe déjà")
            
            # Vérifier si la colonne PrixVenteTotal existe déjà
            cursor.execute("""
                SELECT COUNT(*) as col_exists
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
                AND COLUMN_NAME = 'PrixVenteTotal'
            """)
            prix_total_exists = cursor.fetchone().col_exists > 0
            
            if not prix_total_exists:
                cursor.execute("""
                    ALTER TABLE WEB_S_DOS_ENCOURS
                    ADD PrixVenteTotal DECIMAL(18,3) NULL
                """)
                cursor.connection.commit()
                print("Colonne PrixVenteTotal ajoutée avec succès")
            else:
                print("La colonne PrixVenteTotal existe déjà")
            
            # Vérifier la structure finale
            print()
            print("Structure des colonnes ajoutées:")
            cursor.execute("""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS'
                    AND COLUMN_NAME IN ('QteComm_COMMANDES', 'PrixVenteTotal', 'PrixVenteUnitaire')
                ORDER BY COLUMN_NAME
            """)
            for row in cursor.fetchall():
                print(f"  - {row.COLUMN_NAME}: {row.DATA_TYPE}" + 
                      (f"({row.NUMERIC_PRECISION},{row.NUMERIC_SCALE})" if row.NUMERIC_PRECISION else "") +
                      f" - Nullable: {row.IS_NULLABLE}")
            
            print()
            print("=" * 80)
            print("Les colonnes ont été ajoutées avec succès")
            print("=" * 80)
            
    except Exception as e:
        print(f"Erreur lors de l'ajout des colonnes: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    add_quantite_prix_total_columns()
