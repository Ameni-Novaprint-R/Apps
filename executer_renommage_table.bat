@echo off
cd /d c:\Apps
echo ================================================================================
echo RENOMMAGE DE WEB_DROITS_ACCES EN WEB_ACTIONS
echo ================================================================================
echo.

"C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE" -S "192.168.10.225" -d "novaprint_restored" -E -C -i "renommer_web_droits_acces_en_web_actions.sql"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo RENOMMAGE TERMINE AVEC SUCCES
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo ERREUR LORS DU RENOMMAGE
    echo ================================================================================
)

pause
