@echo off
cd /d c:\Apps
echo ================================================================================
echo CREATION DE LA TABLE WEB_DROITS_ACCES
echo ================================================================================
echo.

REM Essayer avec sqlcmd avec options pour contourner SSL
set SQLCMD="C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE"

if exist %SQLCMD% (
    echo Execution du script SQL via sqlcmd...
    %SQLCMD% -S SRV-KBA1 -d novaprint_restored -E -C -i "creer_table_web_droits_acces.sql" -o "sql_output.txt"
    if %errorlevel% equ 0 (
        echo.
        echo ================================================================================
        echo SUCCES: Script execute!
        echo ================================================================================
        type sql_output.txt | findstr /V "Sqlcmd:"
    ) else (
        echo.
        echo ERREUR lors de l'execution SQL.
        echo Verifiez le fichier sql_output.txt pour les details.
        type sql_output.txt
    )
) else (
    echo sqlcmd.exe non trouve.
    echo.
    echo Veuillez executer le script SQL manuellement dans SQL Server Management Studio:
    echo   - Ouvrez SQL Server Management Studio
    echo   - Connectez-vous a SRV-KBA1
    echo   - Ouvrez le fichier: creer_table_web_droits_acces.sql
    echo   - Executez le script (F5)
)

echo.
pause
