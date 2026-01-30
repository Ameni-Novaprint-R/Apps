@echo off
cd /d c:\Apps
echo ================================================================================
echo VERIFICATION ET DEMARRAGE DE FLASK
echo ================================================================================
echo.

REM Vérifier Python
echo [1/4] Verification de Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERREUR] Python n'est pas trouve dans le PATH
    pause
    exit /b 1
) else (
    python --version
    echo   [OK] Python est disponible
)
echo.

REM Vérifier app.py
echo [2/4] Verification de app.py...
if not exist app.py (
    echo   [ERREUR] app.py n'existe pas dans c:\Apps
    pause
    exit /b 1
) else (
    echo   [OK] app.py existe
)
echo.

REM Arrêter Flask existant
echo [3/4] Arret des processus Flask existants...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    echo   Arret du processus PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo   [OK] Port 5000 libere
echo.

REM Tester l'import Python
echo [4/4] Test de l'import Python...
if exist venv\Scripts\activate.bat (
    echo   Test avec environnement virtuel...
    call venv\Scripts\activate.bat
    python -c "import flask; print('Flask version:', flask.__version__)" 2>&1
    if %errorlevel% neq 0 (
        echo   [ERREUR] Impossible d'importer Flask
        pause
        exit /b 1
    )
) else (
    echo   Test sans environnement virtuel...
    python -c "import flask; print('Flask version:', flask.__version__)" 2>&1
    if %errorlevel% neq 0 (
        echo   [ERREUR] Impossible d'importer Flask
        pause
        exit /b 1
    )
)
echo   [OK] Flask peut etre importe
echo.

REM Démarrer Flask
echo ================================================================================
echo DEMARRAGE DE FLASK
echo ================================================================================
echo.
if exist venv\Scripts\activate.bat (
    echo Demarrage avec environnement virtuel...
    start "Flask Server - c:\Apps" cmd /k "cd /d c:\Apps && call venv\Scripts\activate.bat && echo Flask demarre... && python app.py"
) else (
    echo Demarrage sans environnement virtuel...
    start "Flask Server - c:\Apps" cmd /k "cd /d c:\Apps && echo Flask demarre... && python app.py"
)

echo.
echo Flask a ete lance dans une nouvelle fenetre.
echo.
echo IMPORTANT: Regardez la fenetre qui vient de s'ouvrir pour voir:
echo   - Si Flask demarre correctement
echo   - S'il y a des erreurs
echo.
echo Attendez 10-15 secondes puis testez:
echo   http://localhost:5000/projet11/traitements
echo   http://192.168.10.225:5000/projet11/traitements
echo.
pause
