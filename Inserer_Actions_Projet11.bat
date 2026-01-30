@echo off
echo ================================================================================
echo INSERTION DES ACTIONS DU PROJET 11 DANS WEB_DROITS_ACCES
echo ================================================================================
echo.

cd /d "%~dp0"

REM Activer l'environnement virtuel si il existe
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python inserer_actions_projet11.py

echo.
echo ================================================================================
echo Appuyez sur une touche pour fermer...
pause >nul
