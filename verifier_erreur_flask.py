#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour vérifier les erreurs Flask en temps réel
"""
import sys
import time
import requests
from datetime import datetime

def test_endpoint():
    """Teste l'endpoint et affiche tous les détails"""
    url = "http://192.168.10.225:5000/projet18/export-pdf-multilang-style2"
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Test de l'endpoint: {url}")
    print("-" * 80)
    
    try:
        response = requests.get(url, timeout=20)
        print(f"✓ SUCCÈS - Status: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"  Content-Length: {len(response.content)} bytes")
        if len(response.content) > 0:
            print(f"  Premiers 100 bytes: {response.content[:100]}")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"✗ ERREUR HTTP - Status: {e.response.status_code}")
        print(f"  Headers: {dict(e.response.headers)}")
        print(f"  Content-Length: {len(e.response.content)} bytes")
        if len(e.response.content) > 0:
            print(f"  Contenu: {e.response.content[:500].decode('utf-8', errors='ignore')}")
        return False
    except Exception as e:
        print(f"✗ ERREUR: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("VÉRIFICATION DES ERREURS FLASK")
    print("=" * 80)
    print()
    
    # Test initial
    test_endpoint()
    
    print()
    print("=" * 80)
    print("INSTRUCTIONS:")
    print("1. Ouvrez la fenêtre de console où Flask s'exécute")
    print("2. Relancez ce script avec: python verifier_erreur_flask.py")
    print("3. Observez les erreurs dans la console Flask pendant le test")
    print("=" * 80)




