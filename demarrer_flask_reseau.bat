@echo off
cd /d c:\Apps
echo ================================================================================
echo DEMARRAGE DE FLASK POUR ACCES RESEAU
echo ================================================================================
echo.
echo Flask va demarrer et ecouter sur 0.0.0.0:5000
echo Cela permettra l'acces depuis http://192.168.10.225:5000
echo.
if exist venv\Scripts\activate.bat (
    start "Flask Server (Reseau)" cmd /k "cd /d c:\Apps && call venv\Scripts\activate.bat && python app.py"
) else (
    start "Flask Server (Reseau)" cmd /k "cd /d c:\Apps && python app.py"
)
echo.
echo Flask a ete lance dans une nouvelle fenetre.
echo Attendez quelques secondes que Flask demarre completement.
echo.
echo Vous pouvez maintenant acceder a Flask via:
echo   - http://localhost:5000
echo   - http://192.168.10.225:5000
echo.
pause
