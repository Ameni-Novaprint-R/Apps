@echo off
REM Script batch pour démarrer Flask automatiquement
REM Peut être exécuté manuellement ou via une tâche planifiée Windows

cd /d "%~dp0"

echo ================================================================================
echo DEMARRAGE AUTOMATIQUE DE FLASK
echo ================================================================================
echo.

REM Vérifier si Flask est déjà en cours d'exécution
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *flask*" 2>nul | find /I "python.exe" >nul
if %errorlevel% equ 0 (
    echo [INFO] Flask semble deja etre en cours d'execution.
    echo.
    set /p restart="Voulez-vous arreter les processus existants et redemarrer Flask? (O/N): "
    if /I "%restart%"=="O" (
        echo [INFO] Arret des processus Flask existants...
        taskkill /F /IM python.exe /FI "WINDOWTITLE eq *flask*" 2>nul
        timeout /t 2 /nobreak >nul
    ) else (
        echo [INFO] Demarrage annule.
        exit /b 0
    )
)

REM Vérifier si l'environnement virtuel existe
if not exist "venv\Scripts\activate.bat" (
    echo [ERREUR] L'environnement virtuel 'venv' n'existe pas.
    echo          Creez-le avec: python -m venv venv
    pause
    exit /b 1
)

REM Démarrer Flask
echo [INFO] Demarrage de Flask avec watchdog...
echo.

if exist "run_flask_with_watchdog.py" (
    start "Flask Server" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && python run_flask_with_watchdog.py"
    echo [SUCCES] Flask a ete demarre dans une nouvelle fenetre.
) else (
    start "Flask Server" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && python app.py"
    echo [SUCCES] Flask a ete demarre dans une nouvelle fenetre (mode simple).
)

echo.
echo [INFO] Attente du demarrage de Flask (5 secondes)...
timeout /t 5 /nobreak >nul

REM Vérifier que Flask répond
echo [INFO] Verification que Flask repond...
curl.exe -s -o nul -w "Status: %%{http_code}\n" http://localhost:5000 >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCES] Flask repond correctement!
    echo.
    echo ================================================================================
    echo Flask est maintenant accessible sur: http://localhost:5000
    echo ================================================================================
) else (
    echo [ATTENTION] Flask ne repond pas encore. Attendez quelques secondes supplementaires.
    echo            Verifiez la fenetre Flask pour d'eventuelles erreurs.
)

echo.
pause
