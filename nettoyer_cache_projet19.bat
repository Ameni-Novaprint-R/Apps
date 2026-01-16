@echo off
REM ========================================
REM Script pour supprimer les fichiers __pycache__ du projet 19
REM A executer depuis le repertoire racine du projet (C:\Apps)
REM ========================================

echo ========================================
echo NETTOYAGE DU CACHE PYTHON - PROJET 19
echo ========================================
echo.

REM Aller dans le repertoire du projet
cd /d "%~dp0"
echo Repertoire de travail: %CD%
echo.

REM Supprimer SPECIFIQUEMENT les fichiers .pyc du projet19 dans routes\__pycache__
echo Suppression des fichiers .pyc du projet19 dans routes\__pycache__...
if exist "routes\__pycache__" (
    del /q "routes\__pycache__\*projet19*" 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Fichiers projet19 supprimes dans routes\__pycache__
    ) else (
        echo [INFO] Aucun fichier projet19 trouve dans routes\__pycache__
    )
) else (
    echo [INFO] routes\__pycache__ n'existe pas
)
echo.

REM Supprimer db.cpython-*.pyc dans __pycache__ (utilise par projet19)
echo Suppression de db.cpython-*.pyc dans __pycache__...
if exist "__pycache__" (
    del /q "__pycache__\db.cpython-*.pyc" 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Fichier db.cpython-*.pyc supprime
    ) else (
        echo [INFO] Aucun fichier db.cpython-*.pyc trouve
    )
) else (
    echo [INFO] __pycache__ n'existe pas
)
echo.

REM Supprimer app.cpython-*.pyc dans __pycache__ (au cas ou)
echo Suppression de app.cpython-*.pyc dans __pycache__...
if exist "__pycache__" (
    del /q "__pycache__\app.cpython-*.pyc" 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Fichier app.cpython-*.pyc supprime
    ) else (
        echo [INFO] Aucun fichier app.cpython-*.pyc trouve
    )
) else (
    echo [INFO] __pycache__ n'existe pas
)
echo.

REM OPTION: Supprimer tout le dossier routes\__pycache__ (recompte pour forcer le rechargement)
echo Option: Supprimer tout routes\__pycache__ pour forcer le rechargement...
choice /C O /N /M "Supprimer tout routes\__pycache__? (O)ui/(N)on: "
if %ERRORLEVEL% EQU 1 (
    if exist "routes\__pycache__" (
        rmdir /s /q "routes\__pycache__"
        echo [OK] routes\__pycache__ supprime completement
    )
) else (
    echo [INFO] Conservation de routes\__pycache__
)
echo.

REM OPTION: Supprimer tout le dossier __pycache__ a la racine (recompte pour forcer le rechargement)
echo Option: Supprimer tout __pycache__ a la racine pour forcer le rechargement...
choice /C O /N /M "Supprimer tout __pycache__? (O)ui/(N)on: "
if %ERRORLEVEL% EQU 1 (
    if exist "__pycache__" (
        rmdir /s /q "__pycache__"
        echo [OK] __pycache__ supprime completement
    )
) else (
    echo [INFO] Conservation de __pycache__
)
echo.

echo ========================================
echo NETTOYAGE TERMINE
echo ========================================
echo.
echo IMPORTANT: Maintenant vous devez:
echo 1. Arreter le serveur Flask (Ctrl+C ou Gestionnaire des taches)
echo 2. Redemarrer avec: python app.py
echo.
pause
