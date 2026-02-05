"""
Migration pour désactiver les ID_Action 3 et 4 pour tous les ateliers (Atelier1 à Atelier10)
dans la table WEB_DROITS_ACCES en mettant Autorise = 0
"""
from db import get_db_cursor

def run():
    print("=" * 80)
    print("MIGRATION: Desactivation des ID_Action 3 et 4 pour les ateliers")
    print("=" * 80)
    print()
    
    with get_db_cursor() as cursor:
        try:
            # Récupérer tous les ateliers
            cursor.execute("""
                SELECT DISTINCT NomAtelier 
                FROM WEB_DROITS_ACCES 
                WHERE NomAtelier IS NOT NULL 
                ORDER BY NomAtelier
            """)
            ateliers = [row.NomAtelier for row in cursor.fetchall()]
            print(f"Ateliers trouves: {ateliers}")
            print()
            
            # Mettre à jour Autorise = 0 pour ID_Action 3 et 4 pour tous les ateliers
            updated_count = 0
            for atelier in ateliers:
                # ID_Action 3
                cursor.execute("""
                    UPDATE WEB_DROITS_ACCES
                    SET Autorise = 0
                    WHERE NomAtelier = ?
                    AND ID_Action = 3
                """, (atelier,))
                count_3 = cursor.rowcount
                
                # ID_Action 4
                cursor.execute("""
                    UPDATE WEB_DROITS_ACCES
                    SET Autorise = 0
                    WHERE NomAtelier = ?
                    AND ID_Action = 4
                """, (atelier,))
                count_4 = cursor.rowcount
                
                if count_3 > 0 or count_4 > 0:
                    print(f"  [OK] {atelier}: ID_Action 3 ({count_3} ligne(s)), ID_Action 4 ({count_4} ligne(s))")
                    updated_count += count_3 + count_4
            
            cursor.connection.commit()
            
            print()
            print(f"Total de lignes mises a jour: {updated_count}")
            print()
            
            # Vérification
            print("=" * 80)
            print("VERIFICATION APRES MIGRATION:")
            print("=" * 80)
            cursor.execute("""
                SELECT NomAtelier, ID_Action, Autorise 
                FROM WEB_DROITS_ACCES 
                WHERE NomAtelier IS NOT NULL 
                AND ID_Action IN (3, 4)
                ORDER BY NomAtelier, ID_Action
            """)
            resultats = cursor.fetchall()
            for row in resultats:
                status = "AUTORISE" if row.Autorise == 1 else "REFUSE"
                print(f"{row.NomAtelier} - ID_Action {row.ID_Action}: {status} (Autorise = {row.Autorise})")
            
            print()
            print("=" * 80)
            print("MIGRATION TERMINEE AVEC SUCCES!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\nERREUR lors de la migration : {e}")
            import traceback
            traceback.print_exc()
            cursor.connection.rollback()

if __name__ == "__main__":
    run()
