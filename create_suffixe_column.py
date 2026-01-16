"""
Script pour créer la colonne Suffixe dans WEB_GMAO si elle n'existe pas
"""
from db import get_db_cursor

def create_suffixe_column_if_not_exists():
    """Crée la colonne Suffixe dans WEB_GMAO si elle n'existe pas"""
    try:
        with get_db_cursor() as cursor:
            # Vérifier si la colonne existe
            cursor.execute("""
                SELECT COUNT(*) as col_exists
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'WEB_GMAO' AND COLUMN_NAME = 'Suffixe'
            """)
            result = cursor.fetchone()
            col_exists = result.col_exists > 0 if result else False
            
            if col_exists:
                print("✅ La colonne Suffixe existe déjà dans WEB_GMAO")
                return True
            else:
                print("📝 Création de la colonne Suffixe...")
                # Créer la colonne
                cursor.execute("""
                    ALTER TABLE WEB_GMAO
                    ADD Suffixe INT NOT NULL DEFAULT 0
                """)
                cursor.connection.commit()
                print("✅ Colonne Suffixe créée avec succès!")
                
                # Mettre à jour les enregistrements existants
                cursor.execute("""
                    UPDATE WEB_GMAO
                    SET Suffixe = 0
                    WHERE Suffixe IS NULL
                """)
                cursor.connection.commit()
                print("✅ Tous les enregistrements existants ont Suffixe = 0")
                return True
                
    except Exception as e:
        print(f"❌ Erreur lors de la création de la colonne Suffixe: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Création de la colonne Suffixe dans WEB_GMAO")
    print("=" * 60)
    create_suffixe_column_if_not_exists()
    print("=" * 60)


















