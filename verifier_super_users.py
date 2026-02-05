"""
Script pour vérifier que les matricules 321 et 179 sont bien configurés comme super-utilisateurs
"""
from logic.auth import SUPER_USER_MATRICULES, is_super_user
from db import get_db_cursor

def verifier():
    print("=" * 80)
    print("VERIFICATION DES SUPER-UTILISATEURS")
    print("=" * 80)
    print()
    
    print(f"Matricules configures comme super-utilisateurs: {SUPER_USER_MATRICULES}")
    print()
    
    # Vérifier que les matricules existent dans la table personel
    with get_db_cursor() as cursor:
        for matricule in SUPER_USER_MATRICULES:
            cursor.execute("""
                SELECT Matricule, Nom, Prenom, archive 
                FROM personel 
                WHERE Matricule = ?
            """, (matricule,))
            row = cursor.fetchone()
            if row:
                print(f"Matricule {matricule}: {row.Nom} {row.Prenom}")
                print(f"  - Archive: {row.archive} {'[OK]' if row.archive == 0 else '[ERREUR - doit etre 0]'}")
                
                # Vérifier les droits dans WEB_DROITS_ACCES
                cursor.execute("""
                    SELECT COUNT(*) as nb_droits
                    FROM WEB_DROITS_ACCES
                    WHERE Matricule = ? AND Autorise = 1
                """, (matricule,))
                result = cursor.fetchone()
                nb_droits = result.nb_droits if result else 0
                print(f"  - Droits dans WEB_DROITS_ACCES: {nb_droits}")
                print(f"  - Note: Les super-utilisateurs n'ont pas besoin de droits dans WEB_DROITS_ACCES")
                print(f"  - Acces: Tous les projets (sans passer par WEB_DROITS_ACCES)")
                print()
            else:
                print(f"Matricule {matricule}: [ERREUR] Non trouve dans la table personel")
                print()
    
    print("=" * 80)
    print("FONCTIONNALITE:")
    print("Les matricules dans SUPER_USER_MATRICULES ont acces a tous les projets")
    print("sans avoir besoin de lignes dans WEB_DROITS_ACCES.")
    print("La fonction is_super_user() retourne True pour ces matricules.")
    print("=" * 80)

if __name__ == "__main__":
    verifier()
