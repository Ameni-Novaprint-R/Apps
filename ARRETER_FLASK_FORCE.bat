@echo off
echo ========================================
echo ARRET FORCE DE TOUTES LES INSTANCES FLASK
echo ========================================
echo.
echo Ce script va utiliser taskkill pour arreter tous les processus Python.
echo.
pause

cd /d "%~dp0"

echo [1/3] Recherche des processus Python...
tasklist /FI "IMAGENAME eq python.exe" /FO CSV | findstr python.exe >nul
if %errorlevel% equ 0 (
    echo   Processus Python trouves!
    echo.
    echo [2/3] Arret de tous les processus Python...
    taskkill /F /IM python.exe /T
    if %errorlevel% equ 0 (
        echo   SUCCES: Tous les processus Python ont ete arretes!
    ) else (
        echo   ERREUR: Impossible d'arreter certains processus.
        echo   Essayez d'executer ce script en tant qu'administrateur.
    )
) else (
    echo   Aucun processus Python trouve.
)

echo.
echo [3/3] Verification du port 5000...
netstat -ano | findstr :5000 >nul
if %errorlevel% equ 0 (
    echo   ATTENTION: Le port 5000 est toujours utilise!
    echo   Utilisez: netstat -ano | findstr :5000
    echo   pour voir quel processus utilise le port.
) else (
    echo   Le port 5000 est libre.
)

echo.
echo ========================================
echo Termine!
echo ========================================
echo.
pause
