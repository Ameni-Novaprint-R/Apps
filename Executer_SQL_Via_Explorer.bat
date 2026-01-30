@echo off
REM Script batch pour executer les scripts SQL via un processus non-eleve
REM Utilise explorer.exe pour lancer un nouveau processus sans elevation

echo ============================================================
echo EXECUTION DES SCRIPTS SQL VIA PROCESSUS NON-ELEVE
echo ============================================================
echo.

cd /d c:\Apps

REM Creer un script batch temporaire qui execute les scripts Python
set TEMP_BAT=%TEMP%\cursor_sql_%RANDOM%.bat

(
echo @echo off
echo set __COMPAT_LAYER=RunAsInvoker
echo cd /d c:\Apps
echo echo [DEBUT] creer_table_web_projets.py
echo python creer_table_web_projets.py
echo if errorlevel 1 ^(
echo     echo [ERREUR] creer_table_web_projets.py
echo     goto :error
echo ^)
echo echo.
echo echo [DEBUT] creer_table_web_sections.py
echo python creer_table_web_sections.py
echo if errorlevel 1 ^(
echo     echo [ERREUR] creer_table_web_sections.py
echo     goto :error
echo ^)
echo echo.
echo echo [SUCCES] Tous les scripts ont ete executes.
echo pause
echo exit /b 0
echo :error
echo echo [ERREUR] Certains scripts ont echoue.
echo pause
echo exit /b 1
) > "%TEMP_BAT%"

REM Utiliser explorer.exe pour lancer le batch (explorer.exe cree un processus non-eleve)
echo Lancement via explorer.exe pour creer un processus non-eleve...
start "" explorer.exe "%TEMP_BAT%"

REM Attendre un peu pour que le processus se lance
timeout /t 2 /nobreak >nul

echo.
echo Le script s'execute dans une nouvelle fenetre (processus non-eleve).
echo La fenetre se fermera automatiquement apres l'execution.
echo.
echo Appuyez sur une touche pour fermer cette fenetre...
pause >nul

REM Nettoyer le fichier temporaire apres un delai
timeout /t 5 /nobreak >nul
del "%TEMP_BAT%" 2>nul
