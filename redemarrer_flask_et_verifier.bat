@echo off
echo ================================================================================
echo REDEMARRAGE DE FLASK ET VERIFICATION DES BOUTONS D'EXPORT
echo ================================================================================
echo.

cd /d "%~dp0"

echo [1/4] Arret des processus Flask existants...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *flask*" 2>nul
timeout /t 2 /nobreak >nul

echo [2/4] Nettoyage du cache Python...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /r . %%f in (*.pyc) do @if exist "%%f" del /q "%%f" 2>nul

echo [3/4] Demarrage de Flask...
echo.
echo ATTENTION: Flask va demarrer dans une nouvelle fenetre.
echo Fermez cette fenetre pour arreter Flask.
echo.
pause

start "Flask Server" cmd /k "cd /d %~dp0 && python app.py"

echo [4/4] Attente du demarrage de Flask...
timeout /t 5 /nobreak >nul

echo.
echo ================================================================================
echo VERIFICATION
echo ================================================================================
echo.
echo Test des routes d'export...
curl.exe -s -o nul -w "Route export-excel: %%{http_code}\n" http://localhost:5000/projet11/statistiques/export-excel
curl.exe -s -o nul -w "Route export-pdf: %%{http_code}\n" http://localhost:5000/projet11/statistiques/export-pdf

echo.
echo Test de la page statistiques...
curl.exe -s http://localhost:5000/projet11/statistiques | findstr /C:"Export Excel" /C:"Export PDF" >nul
if %errorlevel% equ 0 (
    echo SUCCES: Les boutons Export Excel et Export PDF sont visibles!
) else (
    echo ATTENTION: Les boutons ne sont pas encore visibles.
    echo Attendez quelques secondes et actualisez la page dans votre navigateur.
)

echo.
echo ================================================================================
echo Flask est maintenant demarre.
echo Ouvrez http://localhost:5000/projet11/statistiques dans votre navigateur.
echo ================================================================================
echo.
pause
