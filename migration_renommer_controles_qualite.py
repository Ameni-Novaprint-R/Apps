"""
Migration pour renommer la table CONTROLES_QUALITE en WEB_CONTROLES_QUALITE
"""
from db import get_db_cursor

def run():
    print("=" * 80)
    print("MIGRATION: Renommage de CONTROLES_QUALITE en WEB_CONTROLES_QUALITE")
    print("=" * 80)
    print()
    
    with get_db_cursor() as cursor:
        try:
            # Vérifier si l'ancienne table existe
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'CONTROLES_QUALITE'
            """)
            old_exists = cursor.fetchone().count > 0
            
            # Vérifier si la nouvelle table existe déjà
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_CONTROLES_QUALITE'
            """)
            new_exists = cursor.fetchone().count > 0
            
            if not old_exists and new_exists:
                print("  [INFO] La table WEB_CONTROLES_QUALITE existe deja.")
                print("  [INFO] Migration deja effectuee ou table deja renommee.")
                return
            
            if not old_exists:
                print("  [ERREUR] La table CONTROLES_QUALITE n'existe pas.")
                print("  [INFO] Verifiez le nom de la table dans la base de donnees.")
                return
            
            if new_exists:
                print("  [ERREUR] La table WEB_CONTROLES_QUALITE existe deja.")
                print("  [INFO] Impossible de renommer, la table cible existe deja.")
                return
            
            # Renommer la table
            print("Renommage de la table CONTROLES_QUALITE en WEB_CONTROLES_QUALITE...")
            cursor.execute("""
                EXEC sp_rename 'dbo.CONTROLES_QUALITE', 'WEB_CONTROLES_QUALITE'
            """)
            cursor.connection.commit()
            print("  [OK] Table renommee avec succes")
            
            # Vérification
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'WEB_CONTROLES_QUALITE'
            """)
            verify = cursor.fetchone().count > 0
            
            if verify:
                print("  [OK] Verification: La table WEB_CONTROLES_QUALITE existe maintenant")
            else:
                print("  [ATTENTION] Verification echouee - la table n'a pas ete trouvee")
            
            print()
            print("=" * 80)
            print("MIGRATION TERMINEE AVEC SUCCES!")
            print("=" * 80)
            print()
            print("IMPORTANT: Les references dans le code Python ont ete mises a jour.")
            print("Assurez-vous que la base de donnees est synchronisee.")
            
        except Exception as e:
            print(f"\nERREUR lors de la migration : {e}")
            import traceback
            traceback.print_exc()
            cursor.connection.rollback()
            print("\n[ATTENTION] La migration a echoue. La table n'a pas ete renommee.")

if __name__ == "__main__":
    run()
