@echo off
echo ========================================
echo Starting Draup Asset Management Application
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo Starting server...
    echo.
    echo Open your browser at: http://127.0.0.1:5000 (or check config.yaml)
    echo.
    echo Press Ctrl+C to stop the server
    echo.
    python app.py
    pause
) else (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please run setup.bat first to install Python and dependencies
    echo.
    pause
)

