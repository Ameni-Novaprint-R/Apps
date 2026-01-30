@echo off
REM Vérifier si le script est exécuté en tant qu'administrateur
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ========================================
    echo ELEVATION DES DROITS REQUISE
    echo ========================================
    echo.
    echo Ce script doit etre execute en tant qu'administrateur.
    echo.
    echo Relancement avec droits administrateur...
    echo.
    pause
    
    REM Relancer le script avec les droits administrateur
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo ========================================
echo ARRET DE TOUTES LES INSTANCES FLASK
echo (Mode Administrateur)
echo ========================================
echo.

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
    )
    timeout /t 2 /nobreak >nul
) else (
    echo   Aucun processus Python trouve.
)

echo.
echo [3/3] Verification du port 5000...
netstat -ano | findstr :5000 >nul
if %errorlevel% equ 0 (
    echo   ATTENTION: Le port 5000 est toujours utilise!
    echo   Recherche du processus utilisant le port...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
        echo   PID utilisant le port: %%a
        taskkill /F /PID %%a >nul 2>&1
        if %errorlevel% equ 0 (
            echo   -> Processus %%a arrete
        )
    )
    timeout /t 2 /nobreak >nul
    netstat -ano | findstr :5000 >nul
    if %errorlevel% neq 0 (
        echo   Le port 5000 est maintenant libre.
    ) else (
        echo   Le port 5000 est toujours utilise.
    )
) else (
    echo   Le port 5000 est libre.
)

echo.
echo ========================================
echo Verification finale...
echo ========================================
tasklist /FI "IMAGENAME eq python.exe" /FO CSV | findstr python.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo   ATTENTION: Il reste des processus Python!
) else (
    echo   SUCCES: Aucun processus Python restant!
)

netstat -ano | findstr ":5000" >nul 2>&1
if %errorlevel% equ 0 (
    echo   ATTENTION: Le port 5000 est toujours utilise!
) else (
    echo   SUCCES: Le port 5000 est libre!
)

echo.
echo ========================================
echo Termine!
echo ========================================
echo.
pause
