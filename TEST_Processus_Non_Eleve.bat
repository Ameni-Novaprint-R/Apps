@echo off
REM Script de test pour verifier si un processus non-eleve peut etre cree

echo ============================================================
echo TEST : Creation d'un processus non-eleve
echo ============================================================
echo.

REM Verifier si ce processus est eleve
powershell -Command "$isElevated = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator); Write-Host 'Processus actuel eleve:' $isElevated"

echo.
echo Creation d'un processus via explorer.exe...
echo.

REM Creer un script batch temporaire qui verifie son elevation
set TEMP_BAT=%TEMP%\test_elevation_%RANDOM%.bat

(
echo @echo off
echo echo ============================================================
echo echo FENETRE TEST : Verification de l'elevation
echo echo ============================================================
echo echo.
echo powershell -Command "$isElevated = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()].IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator); Write-Host 'Ce processus est eleve:' $isElevated"
echo echo.
echo echo Si cette fenetre affiche "False", alors le processus non-eleve fonctionne !
echo echo.
echo pause
) > "%TEMP_BAT%"

REM Lancer via explorer.exe
start "" explorer.exe "%TEMP_BAT%"

echo.
echo Une nouvelle fenetre devrait s'ouvrir.
echo Verifiez dans cette fenetre si le processus est eleve ou non.
echo.
echo Appuyez sur une touche pour fermer cette fenetre...
pause >nul

REM Nettoyer
timeout /t 2 /nobreak >nul
del "%TEMP_BAT%" 2>nul
