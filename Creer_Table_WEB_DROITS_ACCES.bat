@echo off
echo ================================================================================
echo CREATION DE LA TABLE WEB_DROITS_ACCES
echo ================================================================================
echo.

cd /d "%~dp0"

REM Activer l'environnement virtuel si il existe
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python creer_table_web_droits_acces.py

echo.
echo ================================================================================
echo Appuyez sur une touche pour fermer...
pause >nul
