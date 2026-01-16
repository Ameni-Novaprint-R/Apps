"""
Script pour vérifier que les colonnes QteComm_COMMANDES et PrixVenteTotal
existent bien dans la table WEB_S_DOS_ENCOURS
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from db import get_db_cursor

def verifier_colonnes():
    """Vérifie si les colonnes existent"""
    try:
        with get_db_cursor() as cursor:
            print("=" * 80)
            print("VERIFICATION DES COLONNES QteComm_COMMANDES ET PrixVenteTotal")
            print("=" * 80)
            print()
            
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
            
            colonnes = cursor.fetchall()
            
            if not colonnes:
                print("Aucune colonne trouvee !")
                print()
                print("Les colonnes QteComm_COMMANDES et PrixVenteTotal n'existent pas encore.")
                print("Vous devez executer le script add_quantite_prix_total_projet19.py")
                return False
            
            print("Colonnes trouvees:")
            for row in colonnes:
                type_info = row.DATA_TYPE
                if row.NUMERIC_PRECISION:
                    type_info += f"({row.NUMERIC_PRECISION},{row.NUMERIC_SCALE})"
                print(f"  - {row.COLUMN_NAME}: {type_info} - Nullable: {row.IS_NULLABLE}")
            
            print()
            
            # Vérifier spécifiquement les deux colonnes
            colonnes_noms = [row.COLUMN_NAME for row in colonnes]
            
            quantite_ok = 'QteComm_COMMANDES' in colonnes_noms
            prix_total_ok = 'PrixVenteTotal' in colonnes_noms
            
            if quantite_ok and prix_total_ok:
                print("SUCCES: Les deux colonnes QteComm_COMMANDES et PrixVenteTotal existent !")
                print("=" * 80)
                return True
            else:
                print("ATTENTION:")
                if not quantite_ok:
                    print("  - La colonne QteComm_COMMANDES n'existe pas")
                if not prix_total_ok:
                    print("  - La colonne PrixVenteTotal n'existe pas")
                print()
                print("Vous devez executer le script add_quantite_prix_total_projet19.py")
                print("=" * 80)
                return False
                
    except Exception as e:
        print(f"Erreur lors de la verification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verifier_colonnes()
