@echo off
echo ================================================================================
echo INSERTION DES SECTIONS DU PROJET 11 DANS WEB_SECTIONS
echo ================================================================================
echo.

cd /d "%~dp0"

REM Activer l'environnement virtuel si il existe
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python creer_table_web_sections.py

echo.
echo ================================================================================
echo Appuyez sur une touche pour fermer...
pause >nul
