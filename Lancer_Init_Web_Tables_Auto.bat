@echo off
chcp 65001 >nul
title Lancement automatique Init Web Tables
echo ============================================================
echo Lancement automatique de l'initialisation des tables WEB
echo ============================================================
echo.

cd /d c:\Apps

REM Verifier si l'app Flask tourne deja
netstat -an | findstr ":5000" >nul
if %errorlevel% == 0 (
    echo [INFO] L'app Flask semble deja en cours d'execution sur le port 5000.
    echo.
) else (
    echo [INFO] Demarrage de l'app Flask en arriere-plan...
    start /B python app.py
    timeout /t 3 /nobreak >nul
    echo [OK] App Flask demarree.
    echo.
)

REM Ouvrir le navigateur sur la route
echo Ouverture du navigateur sur http://localhost:5000/admin/init-web-tables
start http://localhost:5000/admin/init-web-tables

echo.
echo [OK] Le navigateur a ete ouvert.
echo.
echo L'initialisation des tables va s'executer automatiquement.
echo Fermez cette fenetre apres avoir verifie le resultat dans le navigateur.
echo.
pause
