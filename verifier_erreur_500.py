"""
Script pour verifier l'erreur 500 sur la route principale
Avec Watchdog, les logs Flask s'affichent dans la console où run_flask_with_watchdog.py tourne
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests
import json

def test_route_principale():
    """Teste la route principale et affiche les details de l'erreur"""
    print("=" * 80)
    print("VERIFICATION DE L'ERREUR 500 SUR LA ROUTE PRINCIPALE")
    print("=" * 80)
    print()
    
    url = "http://127.0.0.1:5000/"
    
    print(f"1. Test de la route: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   Taille de la reponse: {len(response.content)} bytes")
        
        if response.status_code == 500:
            print()
            print("   [ERREUR 500 DETECTEE]")
            print()
            
            # Essayer de parser la reponse JSON
            try:
                error_data = response.json()
                print("   Contenu de l'erreur (JSON):")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print("   Contenu de l'erreur (texte):")
                print(response.text[:1000])  # Limiter a 1000 caracteres
        else:
            print(f"   [SUCCES] La route fonctionne correctement")
            
    except requests.exceptions.ConnectionError:
        print("   [ERREUR] Impossible de se connecter au serveur Flask")
        print("   Verifiez que Flask tourne sur http://127.0.0.1:5000")
    except Exception as e:
        print(f"   [ERREUR] {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("INSTRUCTIONS POUR VERIFIER LES LOGS AVEC WATCHDOG:")
    print("=" * 80)
    print()
    print("1. OUVREZ LA CONSOLE où vous avez lance run_flask_with_watchdog.py")
    print("   (ou run-flask-watchdog.bat / run-flask-watchdog.ps1)")
    print()
    print("2. DANS CETTE CONSOLE, vous devriez voir:")
    print("   - Les messages de demarrage de Flask")
    print("   - Les requetes HTTP avec leur statut")
    print("   - Les erreurs Python completes avec traceback")
    print()
    print("3. VERIFIEZ LE FICHIER DE LOG:")
    print("   C:\\Apps\\.cursor\\flask_errors.log")
    print("   (Ce fichier contient toutes les erreurs capturees)")
    print()
    print("4. POUR VOIR L'ERREUR EN TEMPS REEL:")
    print("   a) Gardez la console Watchdog ouverte")
    print("   b) Accedez a http://127.0.0.1:5000/ dans votre navigateur")
    print("   c) Regardez immediatement la console pour voir l'erreur")
    print()
    print("=" * 80)

if __name__ == "__main__":
    test_route_principale()
