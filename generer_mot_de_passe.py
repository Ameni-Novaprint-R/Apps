"""
Script pour générer et tester des mots de passe bcrypt
"""
import sys
try:
    import bcrypt
except ImportError:
    print("ERREUR: Le module bcrypt n'est pas installe.")
    print("Installez-le avec: pip install bcrypt")
    sys.exit(1)

from db import get_db_cursor
from logic.auth import hash_password, check_password

def generer_mot_de_passe(matricule, password):
    """
    Génère un hash bcrypt pour un mot de passe et l'enregistre dans la base
    """
    try:
        with get_db_cursor() as cursor:
            # Vérifier que l'employé existe
            cursor.execute("""
                SELECT Matricule, Nom, Prenom
                FROM personel
                WHERE Matricule = ?
            """, (matricule,))
            
            employee = cursor.fetchone()
            if not employee:
                print(f"ERREUR: Matricule {matricule} introuvable dans la table personel")
                return False
            
            # Générer le hash
            password_hash = hash_password(password)
            
            # Mettre à jour dans la base (utiliser la colonne mdp en minuscule)
            cursor.execute("""
                UPDATE personel
                SET mdp = ?
                WHERE Matricule = ?
            """, (password_hash, matricule))
            
            cursor.connection.commit()
            
            print(f"[OK] Mot de passe genere pour:")
            print(f"  Matricule: {matricule}")
            print(f"  Nom: {employee.Nom} {employee.Prenom}")
            print(f"  Hash: {password_hash[:20]}...")
            
            # Tester le mot de passe
            if check_password(password, password_hash):
                print(f"  [OK] Verification: Le mot de passe fonctionne correctement")
            else:
                print(f"  [ERREUR] Verification: Le mot de passe ne fonctionne pas!")
                return False
            
            return True
            
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generer_mot_de_passe.py <matricule> <mot_de_passe>")
        print("\nExemple:")
        print("  python generer_mot_de_passe.py 321 admin123")
        sys.exit(1)
    
    matricule = int(sys.argv[1])
    password = sys.argv[2]
    
    print("=" * 80)
    print("GENERATION DE MOT DE PASSE")
    print("=" * 80)
    print()
    
    success = generer_mot_de_passe(matricule, password)
    
    if success:
        print("\n[OK] Operation terminee avec succes!")
    else:
        print("\n[ERREUR] Operation echouee!")
        sys.exit(1)
