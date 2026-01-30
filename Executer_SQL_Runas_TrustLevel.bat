@echo off
REM Script batch pour executer les scripts SQL via runas /trustlevel
REM Cette methode force l'execution sans elevation

echo ============================================================
echo EXECUTION DES SCRIPTS SQL VIA RUNAS TRUSTLEVEL
echo ============================================================
echo.

cd /d c:\Apps

REM Creer un script batch temporaire qui execute les scripts Python
set TEMP_BAT=%TEMP%\cursor_sql_runas_%RANDOM%.bat

(
echo @echo off
echo cd /d c:\Apps
echo echo ============================================================
echo echo EXECUTION DES SCRIPTS SQL ^(PROCESSUS NON-ELEVE^)
echo echo ============================================================
echo echo.
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
echo echo ============================================================
echo echo [SUCCES] Tous les scripts ont ete executes.
echo echo ============================================================
echo pause
echo exit /b 0
echo :error
echo echo ============================================================
echo echo [ERREUR] Certains scripts ont echoue.
echo echo ============================================================
echo pause
echo exit /b 1
) > "%TEMP_BAT%"

REM Utiliser runas /trustlevel:0x20000 pour executer sans elevation
REM 0x20000 = BasicUser (niveau de confiance basique, sans elevation)
echo Lancement via runas /trustlevel pour creer un processus non-eleve...
runas /trustlevel:0x20000 "cmd.exe /c \"%TEMP_BAT%\""

REM Attendre un peu
timeout /t 2 /nobreak >nul

echo.
echo Le script s'execute dans une nouvelle fenetre (processus non-eleve).
echo.
echo Appuyez sur une touche pour fermer cette fenetre...
pause >nul

REM Nettoyer le fichier temporaire apres un delai
timeout /t 5 /nobreak >nul
del "%TEMP_BAT%" 2>nul
