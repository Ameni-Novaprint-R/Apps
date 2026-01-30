@echo off
title Redemarrer Flask
chcp 65001 >nul
echo ============================================================
echo REDEMARRAGE DE FLASK
echo ============================================================
echo.

cd /d c:\Apps

echo [1/3] Arret des processus Flask existants...
echo.

REM Trouver et arreter les processus Python qui utilisent le port 5000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    echo   Arret du processus PID %%a...
    taskkill /PID %%a /F >nul 2>&1
)

REM Arreter tous les processus python.exe (plus agressif)
REM Decommenter la ligne suivante si besoin :
REM taskkill /IM python.exe /F >nul 2>&1

timeout /t 2 /nobreak >nul

echo.
echo [2/3] Verification du port 5000...
netstat -ano | findstr ":5000" | findstr "LISTENING" >nul
if %errorlevel% == 0 (
    echo   [ATTENTION] Le port 5000 est encore utilise.
    echo   Fermez manuellement les processus Flask avant de continuer.
    pause
    exit /b 1
) else (
    echo   [OK] Le port 5000 est libre.
)

echo.
echo [3/3] Demarrage de Flask...
echo.
echo Flask va demarrer dans une nouvelle fenetre.
echo Cette fenetre se fermera automatiquement.
echo.
echo Appuyez sur une touche pour demarrer Flask...
pause >nul

REM Activer l'environnement virtuel si disponible
if exist "venv\Scripts\activate.bat" (
    echo   Utilisation de l'environnement virtuel...
    start "Flask Server" cmd /k "cd /d c:\Apps && call venv\Scripts\activate.bat && python app.py"
) else (
    echo   Pas d'environnement virtuel trouve, utilisation de Python systeme...
    start "Flask Server" cmd /k "cd /d c:\Apps && python app.py"
)

echo.
echo Flask a ete lance dans une nouvelle fenetre.
echo.
echo ============================================================
echo   APPUYEZ SUR UNE TOUCHE POUR FERMER CETTE FENETRE
echo ============================================================
pause >nul
