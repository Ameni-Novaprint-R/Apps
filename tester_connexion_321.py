"""
Script pour tester la connexion du matricule 321
"""
from db import get_db_cursor
from logic.auth import check_password, hash_password

try:
    with get_db_cursor() as cursor:
        # Vérifier le matricule 321
        cursor.execute("""
            SELECT Matricule, Nom, Prenom, MDP
            FROM personel
            WHERE Matricule = 321
        """)
        
        employee = cursor.fetchone()
        if not employee:
            print("ERREUR: Matricule 321 introuvable dans la table personel")
        else:
            print("=" * 80)
            print("VERIFICATION MATRICULE 321")
            print("=" * 80)
            print(f"Matricule: {employee.Matricule}")
            print(f"Nom: {employee.Nom}")
            print(f"Prenom: {employee.Prenom}")
            
            mdp_hash = employee.MDP if hasattr(employee, 'MDP') else None
            if mdp_hash:
                print(f"\nMot de passe (hash): {mdp_hash[:30]}...")
                print(f"Longueur du hash: {len(mdp_hash)} caracteres")
                
                # Vérifier que c'est bien un hash bcrypt (commence par $2a$, $2b$ ou $2y$)
                if mdp_hash.startswith('$2'):
                    print("  [OK] Format bcrypt valide")
                else:
                    print("  [ATTENTION] Le format ne semble pas etre bcrypt standard")
                
                # Test avec un mot de passe (vous pouvez modifier pour tester)
                print("\n" + "=" * 80)
                print("TEST DE VERIFICATION")
                print("=" * 80)
                print("Pour tester, entrez un mot de passe (ou appuyez sur Entree pour ignorer):")
                test_password = input("Mot de passe a tester: ")
                
                if test_password:
                    if check_password(test_password, mdp_hash):
                        print("  [OK] Le mot de passe correspond!")
                    else:
                        print("  [ERREUR] Le mot de passe ne correspond pas")
                else:
                    print("  Test ignore")
            else:
                print("\n[ATTENTION] Aucun mot de passe defini pour ce matricule")
                print("Vous pouvez en generer un avec: python generer_mot_de_passe.py 321 votre_mot_de_passe")
            
            print("\n" + "=" * 80)
            
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()
