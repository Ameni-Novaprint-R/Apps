#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de diagnostic pour Flask
Vérifie les imports et la connexion à la base de données
"""
import sys
import traceback

print("=" * 70)
print("DIAGNOSTIC FLASK")
print("=" * 70)
print()

# Test 1: Imports de base
print("[1/5] Test des imports Python de base...")
try:
    import flask
    print(f"  [OK] Flask version: {flask.__version__}")
except Exception as e:
    print(f"  [ERREUR] Erreur import Flask: {e}")
    sys.exit(1)

# Test 2: Import app.py
print("\n[2/5] Test de l'import de app.py...")
try:
    import app
    print("  ✓ app.py importé avec succès")
except Exception as e:
    print(f"  ✗ Erreur import app.py: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Import db.py
print("\n[3/5] Test de l'import de db.py...")
try:
    from db import get_db_connection, DB_CONFIG
    print(f"  [OK] db.py importe avec succes")
    print(f"  [OK] Configuration DB: SERVER={DB_CONFIG.get('SERVER')}, DATABASE={DB_CONFIG.get('DATABASE')}")
except Exception as e:
    print(f"  [ERREUR] Erreur import db.py: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 4: Connexion à la base de données
print("\n[4/5] Test de connexion à la base de données...")
try:
    conn = get_db_connection()
    print("  [OK] Connexion a la base de donnees reussie!")
    conn.close()
except Exception as e:
    print(f"  [ERREUR] Erreur de connexion a la base de donnees: {e}")
    print("  [ATTENTION] Flask peut demarrer mais certaines fonctionnalites ne fonctionneront pas")
    traceback.print_exc()

# Test 5: Création de l'application Flask
print("\n[5/5] Test de création de l'application Flask...")
try:
    app_instance = app.app
    print("  [OK] Application Flask creee avec succes")
    print(f"  [OK] Nombre de routes enregistrees: {len(app_instance.url_map._rules)}")
except Exception as e:
    print(f"  [ERREUR] Erreur creation application Flask: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("DIAGNOSTIC TERMINE - Flask devrait pouvoir démarrer")
print("=" * 70)
print("\nPour démarrer Flask, exécutez: python app.py")
print()
