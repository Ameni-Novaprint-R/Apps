@echo off
echo ================================================================================
echo FORCER LE RECHARGEMENT DE FLASK
echo ================================================================================
echo.
echo Ce script va forcer Flask a recharger les templates et routes en :
echo 1. Modifiant legerement les fichiers pour declencher le rechargement
echo 2. Vidant le cache Python
echo.
pause

cd /d "%~dp0"

echo [1/3] Modification des fichiers pour forcer le rechargement...
echo. >> routes\projet11_routes.py
echo. >> templates\projet11_stats.html

echo [2/3] Nettoyage du cache Python...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /r . %%f in (*.pyc) do @if exist "%%f" del /q "%%f" 2>nul

echo [3/3] Termine!
echo.
echo Redemarrez Flask maintenant pour que les changements soient pris en compte.
echo.
pause
