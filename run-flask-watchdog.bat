@echo off
REM Script Batch pour lancer Flask avec Watchdog
REM Rechargement automatique lors des modifications de fichiers

cd /d C:\Apps

REM Activer l'environnement virtuel
call ".\venv\Scripts\activate.bat"

echo ========================================
echo FLASK AVEC WATCHDOG
echo Rechargement automatique active
echo ========================================
echo.

REM Vérifier que watchdog est installé
python -c "import watchdog" 2>nul
if errorlevel 1 (
    echo Watchdog n'est pas installe. Installation en cours...
    pip install watchdog
)

REM Lancer Flask avec watchdog
echo Demarrage de Flask avec Watchdog...
echo Appuyez sur Ctrl+C pour arreter
echo.

python run_flask_with_watchdog.py

echo.
echo Flask arrete.
