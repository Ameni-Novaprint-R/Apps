"""
Script pour installer bcrypt (nécessaire pour le Projet 22)
"""

import subprocess
import sys

def install_bcrypt():
    """Installe le module bcrypt"""
    try:
        print("Installation de bcrypt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "bcrypt"])
        print("[OK] bcrypt installe avec succes!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Erreur lors de l'installation de bcrypt: {e}")
        return False
    except Exception as e:
        print(f"[ERREUR] Erreur: {e}")
        return False

if __name__ == "__main__":
    install_bcrypt()
