"""
Script pour lancer Flask avec rechargement automatique via Watchdog
Surveille les modifications de fichiers Python et redémarre Flask automatiquement
"""
import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
APP_DIR = Path(__file__).parent.absolute()
FLASK_SCRIPT = APP_DIR / "app.py"
WATCHED_EXTENSIONS = {'.py', '.html', '.js', '.css', '.sql'}
EXCLUDED_DIRS = {'__pycache__', '.git', 'venv', '.venv', 'node_modules', '.cursor'}
EXCLUDED_FILES = {'run_flask_with_watchdog.py'}  # Éviter de se surveiller soi-même

class FlaskReloadHandler(FileSystemEventHandler):
    """Gestionnaire d'événements pour surveiller les modifications de fichiers"""
    
    def __init__(self, flask_process):
        self.flask_process = flask_process
        self.last_reload = 0
        self.reload_delay = 1.0  # Délai minimum entre deux rechargements (secondes)
        self.pending_reload = False
        
    def should_reload(self, file_path):
        """Détermine si un fichier modifié doit déclencher un rechargement"""
        file_path = Path(file_path)
        
        # Ignorer les fichiers exclus
        if file_path.name in EXCLUDED_FILES:
            return False
        
        # Ignorer les répertoires exclus
        for part in file_path.parts:
            if part in EXCLUDED_DIRS:
                return False
        
        # Vérifier l'extension
        if file_path.suffix.lower() not in WATCHED_EXTENSIONS:
            return False
        
        return True
    
    def on_modified(self, event):
        """Appelé lorsqu'un fichier est modifié"""
        if event.is_directory:
            return
        
        if not self.should_reload(event.src_path):
            return
        
        # Éviter les rechargements trop fréquents (délai anti-rebond)
        current_time = time.time()
        if current_time - self.last_reload < self.reload_delay:
            self.pending_reload = True
            return
        
        self.reload_flask(event.src_path)
    
    def reload_flask(self, changed_file=None):
        """Redémarre Flask"""
        current_time = time.time()
        self.last_reload = current_time
        
        if changed_file:
            print(f"\n{'='*80}")
            print(f"[WATCHDOG] Fichier modifié: {changed_file}")
            print(f"[WATCHDOG] Redémarrage de Flask...")
            print(f"{'='*80}\n")
        else:
            print(f"\n{'='*80}")
            print(f"[WATCHDOG] Redémarrage de Flask...")
            print(f"{'='*80}\n")
        
        # Arrêter Flask proprement
        if self.flask_process and self.flask_process.poll() is None:
            try:
                # Envoyer SIGTERM sur Windows (équivalent à Ctrl+C)
                if sys.platform == 'win32':
                    self.flask_process.terminate()
                else:
                    self.flask_process.send_signal(signal.SIGTERM)
                
                # Attendre jusqu'à 5 secondes pour l'arrêt propre
                try:
                    self.flask_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Forcer l'arrêt si nécessaire
                    self.flask_process.kill()
                    self.flask_process.wait()
            except Exception as e:
                print(f"[WATCHDOG] Erreur lors de l'arrêt de Flask: {e}")
                if self.flask_process.poll() is None:
                    self.flask_process.kill()
        
        # Nettoyer le cache Python avant de redémarrer
        self.clean_pycache()
        
        # Redémarrer Flask
        self.start_flask()
    
    def clean_pycache(self):
        """Nettoie les fichiers __pycache__ pour éviter les problèmes de cache"""
        print("[WATCHDOG] Nettoyage du cache Python...")
        cleaned_count = 0
        
        for root, dirs, files in os.walk(APP_DIR):
            # Ne pas parcourir les répertoires exclus
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            
            if '__pycache__' in root:
                # Supprimer tous les fichiers .pyc dans ce répertoire
                for file in files:
                    if file.endswith('.pyc'):
                        try:
                            file_path = os.path.join(root, file)
                            os.remove(file_path)
                            cleaned_count += 1
                        except Exception as e:
                            pass
        
        if cleaned_count > 0:
            print(f"[WATCHDOG] {cleaned_count} fichier(s) .pyc supprimé(s)")
    
    def start_flask(self):
        """Démarre Flask"""
        print("[WATCHDOG] Démarrage de Flask...")
        try:
            # Lancer Flask avec rechargement désactivé (watchdog gère le rechargement)
            env = os.environ.copy()
            env['FLASK_USE_WATCHDOG'] = 'true'
            self.flask_process = subprocess.Popen(
                [sys.executable, str(FLASK_SCRIPT)],
                cwd=str(APP_DIR),
                env=env,
                stdout=sys.stdout,
                stderr=sys.stderr,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            print(f"[WATCHDOG] Flask démarré (PID: {self.flask_process.pid})")
        except Exception as e:
            print(f"[WATCHDOG] ERREUR lors du démarrage de Flask: {e}")
            sys.exit(1)

def main():
    """Fonction principale"""
    print("="*80)
    print("FLASK AVEC WATCHDOG - Rechargement automatique")
    print("="*80)
    print(f"Répertoire surveillé: {APP_DIR}")
    print(f"Extensions surveillées: {', '.join(WATCHED_EXTENSIONS)}")
    print(f"Répertoires exclus: {', '.join(EXCLUDED_DIRS)}")
    print("="*80)
    print("\nAppuyez sur Ctrl+C pour arrêter\n")
    
    # Créer le gestionnaire d'événements
    flask_process = None
    handler = FlaskReloadHandler(flask_process)
    
    # Démarrer Flask initialement
    handler.start_flask()
    flask_process = handler.flask_process
    
    # Créer l'observateur de fichiers
    observer = Observer()
    
    # Surveiller le répertoire de l'application (récursif)
    observer.schedule(handler, str(APP_DIR), recursive=True)
    
    # Démarrer l'observateur
    observer.start()
    print(f"[WATCHDOG] Surveillance des fichiers activée\n")
    
    try:
        # Boucle principale
        while True:
            time.sleep(1)
            
            # Vérifier si Flask est toujours en cours d'exécution
            if flask_process.poll() is not None:
                print("\n[WATCHDOG] Flask s'est arrêté. Redémarrage...")
                handler.start_flask()
                flask_process = handler.flask_process
            
            # Gérer les rechargements en attente (anti-rebond)
            if handler.pending_reload:
                handler.pending_reload = False
                handler.reload_flask()
    except KeyboardInterrupt:
        print("\n\n[WATCHDOG] Arrêt demandé...")
    finally:
        # Arrêter l'observateur
        observer.stop()
        observer.join()
        
        # Arrêter Flask
        if flask_process and flask_process.poll() is None:
            print("[WATCHDOG] Arrêt de Flask...")
            try:
                flask_process.terminate()
                flask_process.wait(timeout=5)
            except:
                flask_process.kill()
        
        print("[WATCHDOG] Arrêté proprement")

if __name__ == "__main__":
    main()
