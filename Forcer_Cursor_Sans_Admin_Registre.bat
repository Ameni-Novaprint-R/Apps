@echo off
title Forcer Cursor - RUNASINVOKER
echo [*] Demarrage du script... (fenetre visible 2 s)
timeout /t 2 /nobreak >nul
chcp 65001 >nul
echo.
echo ============================================================
echo Forcer Cursor a s'executer SANS droits administrateur
echo (ajoute RUNASINVOKER dans le registre pour Cursor.exe)
echo ============================================================
echo.

set "CURSOR_EXE=C:\Program Files\cursor\Cursor.exe"
if not exist "%CURSOR_EXE%" set "CURSOR_EXE=C:\Program Files\cursor\Cursor"
if not exist "%CURSOR_EXE%" set "CURSOR_EXE=%LocalAppData%\Programs\cursor\Cursor.exe"
if not exist "%CURSOR_EXE%" set "CURSOR_EXE=C:\Program Files\Cursor\Cursor.exe"
if not exist "%CURSOR_EXE%" (
  echo [ERREUR] Cursor introuvable.
  echo Modifiez ce .bat et definissez CURSOR_EXE au bon chemin.
  pause
  exit /b 1
)

echo Cursor : %CURSOR_EXE%
echo.
reg add "HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" /v "%CURSOR_EXE%" /t REG_SZ /d "RUNASINVOKER" /f
if errorlevel 1 (
  echo [ERREUR] Echec de l'ajout dans le registre.
  pause
  exit /b 1
)
REM Au cas ou le raccourci pointe vers "Cursor" sans .exe
if "%CURSOR_EXE%"=="C:\Program Files\cursor\Cursor.exe" (
  reg add "HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" /v "C:\Program Files\cursor\Cursor" /t REG_SZ /d "RUNASINVOKER" /f 2>nul
)

echo.
echo [OK] RUNASINVOKER a ete ajoute.
echo.
echo Desormais, Cursor doit demarrer SANS elevation meme si
echo "Executer en tant qu'administrateur" est coché ou si le
echo manifeste le demande.
echo.
echo Fermez Cursor puis relancez-le (raccourci habituel ou .vbs).
echo.
echo ============================================================
echo   APPUYEZ SUR UNE TOUCHE POUR FERMER CETTE FENETRE
echo ============================================================
pause >nul
