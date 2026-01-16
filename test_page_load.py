#!/usr/bin/env python3
"""
Test du chargement de la page projet16
"""
import requests
import re

def test_page_visibility():
    """Vérifier ce qui est visible au chargement de la page"""
    print("=== Test de la visibilité au chargement ===")
    
    try:
        response = requests.get("http://localhost:5000/projet16/")
        if response.status_code == 200:
            content = response.text
            
            # Vérifier la présence des éléments
            checks = [
                ("Bouton Maintenance Préventive", r'Maintenance Préventive', True),
                ("Bouton Maintenance Corrective", r'Maintenance Corrective', True),
                ("Options correctives masquées", r'corrective-options.*display:\s*none', True),
                ("Section demandes masquée", r'demandes-section.*display:\s*none', True),
                ("Pas de loadDemandes() au démarrage", r'//\s*loadDemandes\(\)', True),
            ]
            
            print("Vérifications:")
            for name, pattern, should_exist in checks:
                match = re.search(pattern, content, re.DOTALL)
                status = "✅" if (match and should_exist) or (not match and not should_exist) else "❌"
                print(f"  {status} {name}")
            
            print("\n✅ Au chargement de la page, vous devriez voir:")
            print("  • Les 2 boutons principaux uniquement")
            print("  • Aucune option corrective")
            print("  • Aucune liste de demandes")
            
        else:
            print(f"❌ Erreur {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    print("🔍 Test du chargement initial de la page Projet 16")
    print("=" * 55)
    
    test_page_visibility()
    
    print("\n" + "=" * 55)
    print("📋 Instructions de test:")
    print("1. Ouvrez http://localhost:5000/projet16/")
    print("2. Vérifiez que seuls 2 boutons sont visibles")
    print("3. Cliquez sur 'Maintenance Corrective'")
    print("4. Les options et la liste devraient apparaître")

if __name__ == "__main__":
    main()





















