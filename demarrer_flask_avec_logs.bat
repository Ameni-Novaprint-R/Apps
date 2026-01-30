@echo off
cd /d c:\Apps
echo ================================================================================
echo DEMARRAGE DE FLASK AVEC LOGS
echo ================================================================================
echo.

REM Arrêter Flask existant
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    echo Arret du processus PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul

REM Démarrer Flask avec redirection des erreurs
echo Demarrage de Flask...
echo Les erreurs seront affichees ci-dessous:
echo.

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    python app.py 2>&1
) else (
    python app.py 2>&1
)

pause
