@echo off
cd /d c:\Apps
echo Arret de Flask...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo Demarrage de Flask...
if exist venv\Scripts\activate.bat (
    start "Flask Server" cmd /k "cd /d c:\Apps && call venv\Scripts\activate.bat && python app.py"
) else (
    start "Flask Server" cmd /k "cd /d c:\Apps && python app.py"
)
timeout /t 5 /nobreak >nul
echo Flask redemarre. Testez maintenant l'export PDF.
