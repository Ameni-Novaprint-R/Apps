"""
Script pour ajouter la colonne CoutTotal
à la table WEB_S_DOS_ENCOURS pour le projet 19
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from db import get_db_cursor

def add_cout_total_column():
    """Ajoute la colonne CoutTotal si elle n'existe pas"""
    try:
        with get_db_cursor() as cursor:
            print("=" * 80)
            print("AJOUT DE LA COLONNE CoutTotal À WEB_S_DOS_ENCOURS")
            print("=" * 80)
            print()
            
            # Vérifier si la colonne CoutTotal existe déjà
            cursor.execute("""
                SELECT COUNT(*) as col_exists
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
                AND COLUMN_NAME = 'CoutTotal'
            """)
            cout_total_exists = cursor.fetchone().col_exists > 0
            
            if not cout_total_exists:
                cursor.execute("""
                    ALTER TABLE WEB_S_DOS_ENCOURS
                    ADD CoutTotal DECIMAL(18,3) NULL
                """)
                cursor.connection.commit()
                print("Colonne CoutTotal ajoutée avec succès")
            else:
                print("La colonne CoutTotal existe déjà")
            
            # Vérifier la structure finale
            print()
            print("Structure de la colonne ajoutée:")
            cursor.execute("""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS'
                    AND COLUMN_NAME = 'CoutTotal'
            """)
            row = cursor.fetchone()
            if row:
                print(f"  - {row.COLUMN_NAME}: {row.DATA_TYPE}" + 
                      (f"({row.NUMERIC_PRECISION},{row.NUMERIC_SCALE})" if row.NUMERIC_PRECISION else "") +
                      f" - Nullable: {row.IS_NULLABLE}")
            
            print()
            print("=" * 80)
            print("La colonne a été ajoutée avec succès")
            print("=" * 80)
            
    except Exception as e:
        print(f"Erreur lors de l'ajout de la colonne: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    add_cout_total_column()
