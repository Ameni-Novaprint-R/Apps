@echo off
cd /d c:\Apps
echo ================================================================================
echo DEMARRAGE DIRECT DE FLASK
echo ================================================================================
echo.

REM Arrêter les processus Flask existants
echo [1/3] Arret des processus Flask existants...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    echo   Arret du processus PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul

REM Vérifier le port
echo [2/3] Verification du port 5000...
netstat -ano | findstr ":5000" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo   [ATTENTION] Le port 5000 est encore utilise.
    pause
    exit /b 1
) else (
    echo   [OK] Le port 5000 est libre.
)

REM Démarrer Flask
echo [3/3] Demarrage de Flask...
echo.
if exist venv\Scripts\activate.bat (
    echo Flask va demarrer dans une nouvelle fenetre avec l'environnement virtuel...
    start "Flask Server" cmd /k "cd /d c:\Apps && call venv\Scripts\activate.bat && python app.py"
) else (
    echo Flask va demarrer dans une nouvelle fenetre...
    start "Flask Server" cmd /k "cd /d c:\Apps && python app.py"
)

echo.
echo Flask a ete lance dans une nouvelle fenetre.
echo Attendez 10-15 secondes que Flask demarre completement.
echo.
echo Flask sera accessible via:
echo   - http://localhost:5000
echo   - http://192.168.10.225:5000
echo.
echo Appuyez sur une touche pour fermer cette fenetre...
pause >nul
