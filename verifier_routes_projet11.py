#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour vérifier que les routes d'export sont bien enregistrées dans Flask.
"""

import requests

try:
    # Tester la route d'export Excel
    r = requests.get('http://localhost:5000/projet11/statistiques/export-excel', timeout=5)
    print(f"Route export-excel: {r.status_code}")
    if r.status_code == 200:
        print("  ✓ Route fonctionnelle")
    elif r.status_code == 404:
        print("  ✗ Route non trouvée - Flask n'a pas rechargé les routes")
    elif r.status_code == 500:
        print(f"  ✗ Erreur serveur: {r.text[:200]}")
except Exception as e:
    print(f"Route export-excel: Erreur - {e}")

try:
    # Tester la route d'export PDF
    r = requests.get('http://localhost:5000/projet11/statistiques/export-pdf', timeout=5)
    print(f"Route export-pdf: {r.status_code}")
    if r.status_code == 200:
        print("  ✓ Route fonctionnelle")
    elif r.status_code == 404:
        print("  ✗ Route non trouvée - Flask n'a pas rechargé les routes")
    elif r.status_code == 500:
        print(f"  ✗ Erreur serveur: {r.text[:200]}")
except Exception as e:
    print(f"Route export-pdf: Erreur - {e}")
