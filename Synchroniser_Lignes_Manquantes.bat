@echo off
echo ================================================================================
echo SYNCHRONISATION DES 13 LIGNES MANQUANTES - PAPIERS_IMPRIMEURS
echo ================================================================================
echo.

cd /d "%~dp0"

REM Activer l'environnement virtuel si il existe
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python synchroniser_lignes_papiers_imprimeurs_manquantes.py

echo.
echo ================================================================================
echo Appuyez sur une touche pour fermer...
pause >nul
