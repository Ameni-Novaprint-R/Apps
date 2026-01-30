#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour démarrer Flask en arrière-plan de manière silencieuse.
Utilisé par Cursor pour démarrer Flask automatiquement.
"""

import os
import sys
import subprocess
import time
import urllib.request
import urllib.error
from pathlib import Path

def check_flask_running():
    """Vérifie si Flask est déjà en cours d'exécution"""
    try:
        response = urllib.request.urlopen("http://localhost:5000", timeout=2)
        return True, response.getcode()
    except:
        return False, None

def start_flask_background():
    """Démarre Flask en arrière-plan"""
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # Vérifier si Flask est déjà en cours
    is_running, status = check_flask_running()
    if is_running:
        print(f"[INFO] Flask est déjà en cours d'exécution (Status: {status})")
        return True
    
    # Vérifier l'environnement virtuel
    venv_path = script_dir / "venv"
    if not venv_path.exists():
        print(f"[ERREUR] Environnement virtuel 'venv' introuvable")
        return False
    
    # Déterminer le script Python à utiliser
    python_exe = venv_path / "Scripts" / "python.exe"
    if not python_exe.exists():
        python_exe = sys.executable
    
    # Choisir le script Flask
    watchdog_script = script_dir / "run_flask_with_watchdog.py"
    flask_script = watchdog_script if watchdog_script.exists() else script_dir / "app.py"
    
    print(f"[INFO] Démarrage de Flask en arrière-plan...")
    
    # Démarrer Flask en arrière-plan
    try:
        if sys.platform == "win32":
            # Windows: démarrer sans fenêtre visible
            subprocess.Popen(
                [str(python_exe), str(flask_script)],
                creationflags=subprocess.CREATE_NO_WINDOW,
                cwd=str(script_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            # Linux/Mac: démarrer en arrière-plan
            subprocess.Popen(
                [str(python_exe), str(flask_script)],
                cwd=str(script_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        # Attendre que Flask démarre
        print("[INFO] Attente du démarrage de Flask...")
        for i in range(10):  # Attendre jusqu'à 10 secondes
            time.sleep(1)
            is_running, status = check_flask_running()
            if is_running:
                print(f"[SUCCES] Flask démarré avec succès! (Status: {status})")
                return True
        
        print("[ATTENTION] Flask ne répond pas encore après 10 secondes.")
        return False
            
    except Exception as e:
        print(f"[ERREUR] Impossible de démarrer Flask: {e}")
        return False

if __name__ == "__main__":
    success = start_flask_background()
    sys.exit(0 if success else 1)
