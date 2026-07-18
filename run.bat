@echo off
REM ========================================================
REM RUN SCRIPT for F and B Poultry Farm Limited
REM ========================================================
REM Just double-click this file to start the farm!
REM The website will open automatically in your browser.
REM ========================================================

title F and B Poultry Farm Limited

echo.
echo ============================================
echo   F and B Poultry Farm Limited
echo   Starting your poultry farm system...
echo ============================================
echo.

REM Go to backend folder
cd /d "%~dp0backend"

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed!
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python found!

REM Seeding database
echo.
echo Setting up database with sample products...
echo.
python seed_data.py

REM Start the server in the background
echo.
echo Starting server...
echo.

start "F and B Poultry Farm" /B cmd /c "python main.py"

REM Wait 3 seconds for server to start
timeout /t 3 /nobreak >nul

REM Open the browser automatically
echo Opening browser to http://localhost:5000 ...
start http://localhost:5000

echo.
echo ============================================
echo   SERVER IS RUNNING AT:
echo   http://localhost:5000
echo.
echo   Admin login: admin@fandb.com
echo   Password: admin123
echo.
echo   Close this window to stop the server.
echo ============================================
echo.

REM Keep the window open so user can see it
echo Press any key to stop the server...
pause >nul

REM Stop the server when user presses a key
taskkill /f /im python.exe >nul 2>&1