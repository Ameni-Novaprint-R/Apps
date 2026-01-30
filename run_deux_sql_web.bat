@echo off
cd /d c:\Apps
echo ============================================================
echo 1. WEB_PROJETS (creer_table_web_projets)
echo ============================================================
python creer_table_web_projets.py
if errorlevel 1 (
    echo [ERREUR] creer_table_web_projets.py
    pause
    exit /b 1
)
echo.
echo ============================================================
echo 2. WEB_SECTIONS (creer_table_web_sections)
echo ============================================================
python creer_table_web_sections.py
if errorlevel 1 (
    echo [ERREUR] creer_table_web_sections.py
    pause
    exit /b 1
)
echo.
echo ============================================================
echo Les deux scripts ont ete executes.
echo ============================================================
pause
