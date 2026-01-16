@echo off
REM ========================================
REM Script pour supprimer TOUS les fichiers __pycache__ 
REM du projet 19 (version complete - sans confirmation)
REM A executer depuis le repertoire racine du projet (C:\Apps)
REM ========================================

echo ========================================
echo NETTOYAGE COMPLET DU CACHE - PROJET 19
echo ========================================
echo.

REM Aller dans le repertoire du projet
cd /d "%~dp0"
echo Repertoire de travail: %CD%
echo.

REM Supprimer routes\__pycache__ (contient projet19_routes.pyc)
echo Suppression de routes\__pycache__...
if exist "routes\__pycache__" (
    rmdir /s /q "routes\__pycache__"
    echo [OK] routes\__pycache__ supprime
) else (
    echo [INFO] routes\__pycache__ n'existe pas
)
echo.

REM Supprimer __pycache__ a la racine (contient db.pyc et app.pyc)
echo Suppression de __pycache__ a la racine...
if exist "__pycache__" (
    rmdir /s /q "__pycache__"
    echo [OK] __pycache__ supprime
) else (
    echo [INFO] __pycache__ n'existe pas
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
