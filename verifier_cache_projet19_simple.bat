@echo off
REM ========================================
REM Script pour verifier que les fichiers __pycache__ 
REM du projet 19 ont bien ete supprimes
REM A executer depuis C:\Apps
REM ========================================

echo ========================================
echo VERIFICATION DU CACHE PYTHON - PROJET 19
echo ========================================
echo.

REM Aller dans le repertoire du projet
cd /d "%~dp0"
echo Repertoire: %CD%
echo.

REM Verifier que nous sommes dans C:\Apps
echo %CD% | findstr /i "C:\\Apps" >nul
if errorlevel 1 (
    echo [ERREUR] Vous devez executer ce script depuis C:\Apps
    echo Repertoire actuel: %CD%
    echo.
    echo Veuillez executer:
    echo   cd C:\Apps
    echo   verifier_cache_projet19_simple.bat
    echo.
    pause
    exit /b 1
)

set ERREUR=0

REM Verifier routes\__pycache__
echo [1] Verification de routes\__pycache__...
if exist "routes\__pycache__" (
    echo [ATTENTION] routes\__pycache__ existe encore!
    dir /b "routes\__pycache__"
    dir /b "routes\__pycache__" 2>nul | findstr /i "projet19" >nul
    if not errorlevel 1 (
        echo [ERREUR] Fichiers projet19 trouves!
        set ERREUR=1
    )
) else (
    echo [OK] routes\__pycache__ n'existe pas
)
echo.

REM Verifier __pycache__ racine
echo [2] Verification de __pycache__ a la racine...
if exist "__pycache__" (
    echo [ATTENTION] __pycache__ existe encore!
    dir /b "__pycache__"
    dir /b "__pycache__\db.cpython-*.pyc" 2>nul | find /c /v "" >nul
    if not errorlevel 1 (
        echo [ERREUR] db.cpython-*.pyc existe encore!
        set ERREUR=1
    )
) else (
    echo [OK] __pycache__ n'existe pas
)
echo.

REM Recherche globale - version corrigee
echo [3] Recherche globale de fichiers projet19.pyc...
set FICHIERS_TROUVES=0
for /f "delims=" %%f in ('dir /s /b *projet19*.pyc 2^>nul ^| findstr /v /i "venv"') do (
    echo [ERREUR] Fichier trouve: %%f
    set ERREUR=1
    set FICHIERS_TROUVES=1
)
if %FICHIERS_TROUVES% EQU 0 (
    echo [OK] Aucun fichier projet19.pyc trouve
)
echo.

echo ========================================
echo RESUME
echo ========================================
echo.

if %ERREUR% EQU 0 (
    echo [SUCCES] Tous les fichiers __pycache__ du projet 19 ont ete supprimes!
    echo Vous pouvez redemarrer Flask avec: python app.py
) else (
    echo [ATTENTION] Des fichiers __pycache__ du projet 19 existent encore!
    echo Relancez: nettoyer_cache_projet19_complet.bat
)

echo.
pause
