"""
Script Python pour ajouter la colonne CtRel (Coût Total Réel) à WEB_S_DOS_ENCOURS
Formule: CtRel = (CoutTotal / QteComm_COMMANDES) * Quantité_application
"""
import sys
sys.path.insert(0, 'C:\\Apps')

from db import get_db_cursor

def add_ctrel_column():
    """Ajoute la colonne CtRel à WEB_S_DOS_ENCOURS si elle n'existe pas"""
    with get_db_cursor() as cursor:
        # Vérifier si la colonne existe déjà
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'WEB_S_DOS_ENCOURS' 
            AND COLUMN_NAME = 'CtRel'
        """)
        
        if cursor.fetchone():
            print("[OK] La colonne CtRel existe deja dans WEB_S_DOS_ENCOURS")
            return True
        
        # Ajouter la colonne
        try:
            cursor.execute("""
                ALTER TABLE WEB_S_DOS_ENCOURS
                ADD CtRel DECIMAL(18, 3) NULL
            """)
            cursor.connection.commit()
            print("[OK] Colonne CtRel ajoutee avec succes a WEB_S_DOS_ENCOURS")
            return True
        except Exception as e:
            print(f"[ERREUR] Erreur lors de l'ajout de la colonne CtRel: {e}")
            cursor.connection.rollback()
            return False

if __name__ == "__main__":
    print("="*80)
    print("Ajout de la colonne CtRel à WEB_S_DOS_ENCOURS")
    print("="*80)
    add_ctrel_column()
    print("="*80)
