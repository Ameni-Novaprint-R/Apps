"""
Script standalone pour exécuter la synchronisation automatique Projet 21
À utiliser avec le Planificateur de tâches Windows (Task Scheduler)
"""

import sys
import os
from pathlib import Path

# Déterminer le répertoire racine du projet
# Le script est dans routes/, donc remonter d'un niveau
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent

# Changer le répertoire de travail vers la racine du projet
# pour que les chemins relatifs fonctionnent correctement
os.chdir(project_root)

# Ajouter le répertoire racine au path pour les imports
sys.path.insert(0, str(project_root))

# Logs de diagnostic
print(f"📁 Script: {__file__}")
print(f"📁 Répertoire du script: {script_dir}")
print(f"📁 Racine du projet: {project_root}")
print(f"📁 Répertoire de travail: {os.getcwd()}")

if __name__ == "__main__":
    try:
        print(f"🔄 Démarrage de la synchronisation automatique - {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Importer et exécuter la fonction de synchronisation
        from routes.projet21_auto_sync import run_auto_sync_and_verify, RESULTS_FILE, RESULTS_DIR
        
        print(f"📁 Dossier de résultats attendu: {RESULTS_DIR}")
        print(f"📄 Fichier de résultats attendu: {RESULTS_FILE}")
        
        run_auto_sync_and_verify()
        
        # Vérifier que le fichier a bien été créé
        if RESULTS_FILE and RESULTS_FILE.exists():
            print(f"✅ Fichier de résultats créé avec succès: {RESULTS_FILE}")
            import json
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
                print(f"   Timestamp: {result_data.get('timestamp')}")
        else:
            print(f"⚠️ ATTENTION: Le fichier de résultats n'a pas été créé: {RESULTS_FILE}")
        
        print(f"✅ Synchronisation automatique terminée - {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        sys.exit(0)
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
