"""
Script de diagnostic pour la connexion du matricule 321
"""
from db import get_db_cursor
import sys

# Test d'import bcrypt
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
    print("[OK] Module bcrypt disponible")
except ImportError:
    BCRYPT_AVAILABLE = False
    print("[ERREUR] Module bcrypt NON disponible")
    print("Installez-le avec: pip install bcrypt")
    sys.exit(1)

def check_password(password, hashed):
    """Vérifie un mot de passe contre un hash bcrypt"""
    if not BCRYPT_AVAILABLE:
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        print(f"Erreur lors de la verification: {e}")
        return False

try:
    with get_db_cursor() as cursor:
        print("=" * 80)
        print("DIAGNOSTIC CONNEXION MATRICULE 321")
        print("=" * 80)
        
        # 1. Vérifier que le matricule existe
        cursor.execute("""
            SELECT Matricule, Nom, Prenom, mdp
            FROM personel
            WHERE Matricule = 321
        """)
        
        employee = cursor.fetchone()
        if not employee:
            print("[ERREUR] Matricule 321 introuvable dans la table personel")
            sys.exit(1)
        
        print(f"\n1. Employe trouve:")
        print(f"   Matricule: {employee.Matricule}")
        print(f"   Nom: {employee.Nom}")
        print(f"   Prenom: {employee.Prenom}")
        
        # 2. Vérifier le mot de passe (colonne mdp en minuscule)
        mdp_hash = None
        if hasattr(employee, 'mdp'):
            mdp_hash = employee.mdp
        else:
            # Récupérer directement
            cursor.execute("SELECT mdp FROM personel WHERE Matricule = 321")
            row = cursor.fetchone()
            if row:
                mdp_hash = row[0]
        if not mdp_hash:
            print("\n[ERREUR] Aucun mot de passe (MDP) trouve dans la base")
            print("   La colonne MDP est NULL ou vide")
            sys.exit(1)
        
        print(f"\n2. Mot de passe trouve:")
        print(f"   Hash complet: {mdp_hash}")
        print(f"   Longueur: {len(mdp_hash)} caracteres")
        print(f"   Type: {type(mdp_hash)}")
        
        # 3. Vérifier le format bcrypt
        print(f"\n3. Verification du format:")
        if isinstance(mdp_hash, str):
            if mdp_hash.startswith('$2a$') or mdp_hash.startswith('$2b$') or mdp_hash.startswith('$2y$'):
                print("   [OK] Format bcrypt valide (commence par $2)")
            else:
                print(f"   [ATTENTION] Format non standard: commence par '{mdp_hash[:5]}'")
                print("   Les hashs bcrypt commencent normalement par $2a$, $2b$ ou $2y$")
        else:
            print(f"   [ATTENTION] Le hash n'est pas une string, c'est un {type(mdp_hash)}")
            mdp_hash = str(mdp_hash)
        
        # 4. Test de vérification
        print(f"\n4. Test de verification:")
        print("   Entrez le mot de passe que vous utilisez pour vous connecter:")
        test_password = input("   Mot de passe: ")
        
        if test_password:
            print(f"\n   Test avec le mot de passe saisi...")
            print(f"   Longueur du mot de passe: {len(test_password)} caracteres")
            
            # Nettoyer le hash (enlever les espaces éventuels)
            mdp_hash_clean = mdp_hash.strip()
            
            try:
                result = check_password(test_password, mdp_hash_clean)
                if result:
                    print("   [OK] Le mot de passe correspond!")
                else:
                    print("   [ERREUR] Le mot de passe ne correspond PAS")
                    print("\n   Diagnostics supplementaires:")
                    print(f"   - Hash utilise: {mdp_hash_clean[:30]}...")
                    print(f"   - Longueur hash: {len(mdp_hash_clean)}")
                    
                    # Essayer différentes variantes
                    print("\n   Tentatives avec variantes:")
                    # Essayer avec le hash tel quel
                    try:
                        r1 = bcrypt.checkpw(test_password.encode('utf-8'), mdp_hash_clean.encode('utf-8'))
                        print(f"   - Hash tel quel: {r1}")
                    except Exception as e:
                        print(f"   - Hash tel quel: ERREUR - {e}")
                    
                    # Essayer avec bytes directement si c'est déjà bytes
                    if isinstance(employee.MDP, bytes):
                        try:
                            r2 = bcrypt.checkpw(test_password.encode('utf-8'), employee.MDP)
                            print(f"   - Hash bytes direct: {r2}")
                        except Exception as e:
                            print(f"   - Hash bytes direct: ERREUR - {e}")
            except Exception as e:
                print(f"   [ERREUR] Exception lors de la verification: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("   Test ignore")
        
        # 5. Vérifier les droits
        print(f"\n5. Verification des droits:")
        cursor.execute("""
            SELECT COUNT(*) as nb_droits
            FROM WEB_DROITS_ACCES
            WHERE Matricule = 321 AND Autorise = 1
        """)
        result = cursor.fetchone()
        nb_droits = result.nb_droits if result else 0
        print(f"   Nombre de droits dans WEB_DROITS_ACCES: {nb_droits}")
        if nb_droits == 0:
            print("   [INFO] Aucun droit trouve, mais le matricule 321 sera traite comme super-utilisateur")
        
        print("\n" + "=" * 80)
        print("FIN DU DIAGNOSTIC")
        print("=" * 80)
            
except Exception as e:
    print(f"\n[ERREUR] {e}")
    import traceback
    traceback.print_exc()
