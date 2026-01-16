@echo off
REM ========================================
REM Script pour verifier que les fichiers __pycache__ 
REM du projet 19 ont bien ete supprimes
REM ========================================

echo ========================================
echo VERIFICATION DU CACHE PYTHON - PROJET 19
echo ========================================
echo.

REM Aller dans le repertoire du projet
cd /d "%~dp0"
echo Repertoire de travail: %CD%
echo.

set ERREUR_TROUVEE=0

REM Verifier routes\__pycache__
echo [1] Verification de routes\__pycache__...
if exist "routes\__pycache__" (
    echo [ATTENTION] routes\__pycache__ existe encore!
    echo.
    echo Contenu de routes\__pycache__:
    dir /b "routes\__pycache__"
    echo.
    echo Recherche de fichiers contenant "projet19"...
    dir /b "routes\__pycache__" 2>nul | findstr /i "projet19" >nul
    if errorlevel 1 (
        echo [OK] Aucun fichier projet19 trouve dans routes\__pycache__
    ) else (
        echo [ERREUR] Des fichiers projet19 existent encore dans routes\__pycache__!
        set ERREUR_TROUVEE=1
    )
) else (
    echo [OK] routes\__pycache__ n'existe pas - Cache supprime
)
echo.

REM Verifier __pycache__ a la racine
echo [2] Verification de __pycache__ a la racine...
if exist "__pycache__" (
    echo [ATTENTION] __pycache__ existe encore!
    echo.
    echo Contenu de __pycache__:
    dir /b "__pycache__"
    echo.
    echo Verification des fichiers db.cpython-*.pyc (utilise par projet19)...
    dir /b "__pycache__\db.cpython-*.pyc" 2>nul >nul
    if errorlevel 1 (
        echo [OK] db.cpython-*.pyc n'existe pas
    ) else (
        echo [ERREUR] db.cpython-*.pyc existe encore!
        set ERREUR_TROUVEE=1
    )
) else (
    echo [OK] __pycache__ n'existe pas - Cache supprime
)
echo.

REM Recherche globale de fichiers .pyc contenant "projet19"
echo [3] Recherche globale de fichiers .pyc contenant "projet19"...
dir /s /b *projet19*.pyc 2>nul | findstr /v /i "venv" >nul
if errorlevel 1 (
    echo [OK] Aucun fichier projet19.pyc trouve
) else (
    echo [ERREUR] Des fichiers projet19.pyc existent encore!
    dir /s /b *projet19*.pyc 2>nul | findstr /v /i "venv"
    set ERREUR_TROUVEE=1
)
echo.

REM Verification finale
echo ========================================
echo RESUME DE LA VERIFICATION
echo ========================================
echo.

if %ERREUR_TROUVEE% EQU 1 (
    echo [ATTENTION] Certains fichiers __pycache__ du projet 19 existent encore!
    echo.
    echo Relancez le script de nettoyage:
    echo nettoyer_cache_projet19_complet.bat
) else (
    echo [SUCCES] Tous les fichiers __pycache__ du projet 19 ont ete supprimes!
    echo.
    echo Vous pouvez maintenant redemarrer le serveur Flask
    echo avec: python app.py
)

echo.
pause
