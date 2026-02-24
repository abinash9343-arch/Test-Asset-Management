@echo off
echo ========================================
echo Draup Asset Management - Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Python is installed
    python --version
    echo.
    echo Installing dependencies...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if %errorlevel% == 0 (
        echo.
        echo ========================================
        echo Setup Complete!
        echo ========================================
        echo.
        echo To start the application, run:
        echo   python app.py
        echo.
        echo Then open your browser at: http://localhost:5000
        echo.
    ) else (
        echo.
        echo [ERROR] Failed to install dependencies
        echo Please check your internet connection and try again
    )
) else (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python first:
    echo 1. Download from: https://www.python.org/downloads/
    echo 2. During installation, check "Add Python to PATH"
    echo 3. Run this script again
    echo.
    echo Or install from Microsoft Store:
    echo   - Open Microsoft Store
    echo   - Search for "Python 3.11" or "Python 3.12"
    echo   - Click Install
    echo.
    pause
)

