#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script Python pour démarrer Flask automatiquement.
Peut être exécuté directement ou via une tâche planifiée Windows.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_flask_running():
    """Vérifie si Flask est déjà en cours d'exécution"""
    try:
        response = requests.get("http://localhost:5000", timeout=2)
        return True, response.status_code
    except:
        return False, None

def start_flask():
    """Démarre Flask dans un processus séparé"""
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # Vérifier si Flask est déjà en cours
    is_running, status = check_flask_running()
    if is_running:
        print(f"[INFO] Flask semble déjà être en cours d'exécution (Status: {status})")
        response = input("Voulez-vous redémarrer Flask? (o/N): ")
        if response.lower() != 'o':
            print("[INFO] Démarrage annulé.")
            return False
    
    # Vérifier l'environnement virtuel
    venv_path = script_dir / "venv"
    if not venv_path.exists():
        print(f"[ERREUR] L'environnement virtuel 'venv' n'existe pas dans {script_dir}")
        print("         Créez-le avec: python -m venv venv")
        return False
    
    # Déterminer le script Python à utiliser
    python_exe = venv_path / "Scripts" / "python.exe"
    if not python_exe.exists():
        python_exe = sys.executable  # Fallback sur Python système
    
    # Choisir le script Flask
    watchdog_script = script_dir / "run_flask_with_watchdog.py"
    flask_script = watchdog_script if watchdog_script.exists() else script_dir / "app.py"
    
    print(f"[INFO] Démarrage de Flask avec: {flask_script.name}")
    print(f"[INFO] Python: {python_exe}")
    
    # Démarrer Flask dans un nouveau processus
    try:
        if sys.platform == "win32":
            # Windows: démarrer dans une nouvelle fenêtre console
            subprocess.Popen(
                [str(python_exe), str(flask_script)],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=str(script_dir)
            )
        else:
            # Linux/Mac: démarrer en arrière-plan
            subprocess.Popen(
                [str(python_exe), str(flask_script)],
                cwd=str(script_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        print("[SUCCES] Flask a été démarré dans un nouveau processus.")
        
        # Attendre et vérifier
        print("[INFO] Attente du démarrage de Flask (5 secondes)...")
        time.sleep(5)
        
        is_running, status = check_flask_running()
        if is_running:
            print(f"[SUCCES] Flask répond correctement! (Status: {status})")
            print(f"\n{'='*70}")
            print("Flask est maintenant accessible sur: http://localhost:5000")
            print(f"{'='*70}")
            return True
        else:
            print("[ATTENTION] Flask ne répond pas encore. Vérifiez le processus pour d'éventuelles erreurs.")
            return False
            
    except Exception as e:
        print(f"[ERREUR] Impossible de démarrer Flask: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("DEMARRAGE AUTOMATIQUE DE FLASK")
    print("=" * 70)
    print()
    
    success = start_flask()
    
    if not success:
        print("\n[ERREUR] Le démarrage de Flask a échoué.")
        sys.exit(1)
    
    print("\n[INFO] Flask est en cours d'exécution.")
    print("       Appuyez sur Ctrl+C pour arrêter ce script (Flask continuera de tourner).")
    
    try:
        # Garder le script actif pour permettre de voir les messages
        while True:
            time.sleep(10)
            is_running, status = check_flask_running()
            if not is_running:
                print("[ATTENTION] Flask ne répond plus!")
    except KeyboardInterrupt:
        print("\n[INFO] Script arrêté. Flask continue de tourner dans son propre processus.")
