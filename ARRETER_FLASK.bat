@echo off
echo ========================================
echo ARRET DE TOUTES LES INSTANCES FLASK
echo ========================================
echo.
echo Ce script va arreter toutes les instances Flask en cours d'execution.
echo.
pause

cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File ".\arreter_toutes_instances_flask.ps1"

echo.
echo ========================================
echo Appuyez sur une touche pour fermer...
pause >nul
