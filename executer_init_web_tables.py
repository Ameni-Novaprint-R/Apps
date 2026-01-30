#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour executer l'initialisation des tables WEB via la route Flask API.
Permet d'executer les scripts SQL depuis Cursor sans desactiver le sandbox.

Utilise une requete HTTP vers la route /admin/init-web-tables.json (API JSON).
L'app Flask doit etre en cours d'execution (python app.py).
"""

import urllib.request
import urllib.error
import json
import sys

def executer_init_web_tables():
    """Appelle la route /admin/init-web-tables.json et affiche le resultat."""
    
    url = "http://localhost:5000/admin/init-web-tables.json"
    
    print("=" * 70)
    print("Execution des scripts SQL via la route web (API JSON)")
    print("=" * 70)
    print()
    print(f"Connexion a: {url}")
    print("(L'app Flask doit etre en cours d'execution: python app.py)")
    print()
    
    try:
        # Faire la requete HTTP
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            print("Resultat:")
            print(f"  WEB_PROJETS: {'[OK]' if data.get('ok1') else '[ECHEC]'}")
            print(f"  WEB_SECTIONS: {'[OK]' if data.get('ok2') else '[ECHEC]'}")
            print()
            
            if data.get('success'):
                print("[OK] Succes - WEB_PROJETS et WEB_SECTIONS ont ete creees ou mises a jour.")
            else:
                print("[ERREUR] Echec - voir les details ci-dessous.")
            
            if data.get('error'):
                print(f"Erreur: {data.get('error')}")
            
            print()
            print("Sortie des scripts:")
            print("-" * 70)
            logs = data.get('logs', '')
            if logs:
                print(logs)
            else:
                print("(aucune sortie)")
            print("-" * 70)
            print()
            print("=" * 70)
            return data.get('success', False)
            
    except urllib.error.URLError as e:
        print(f"[ERREUR] Impossible de se connecter a l'app Flask: {e}")
        print()
        print("SOLUTION:")
        print("  1. Ouvrir PowerShell")
        print("  2. cd c:\\Apps")
        print("  3. python app.py")
        print("  4. Laisser cette fenetre ouverte, puis relancer ce script")
        print()
        return False
    except json.JSONDecodeError as e:
        print(f"[ERREUR] Reponse invalide (pas du JSON): {e}")
        return False
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = executer_init_web_tables()
    sys.exit(0 if success else 1)
