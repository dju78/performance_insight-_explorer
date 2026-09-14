@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo   Performance Insight Explorer - Windows Setup
echo   Author: DARAMOLA OMOYELE
echo =======================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in system PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python detected:
python --version
echo.

:: Create virtual environment if not exists
if not exist "venv\" (
    echo [*] Creating virtual environment 'venv'...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Existing virtual environment found.
)

:: Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

:: Upgrade pip and install requirements
echo [*] Installing required Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies from requirements.txt
    pause
    exit /b 1
)

echo.
echo =======================================================
echo   Setup completed successfully!
echo   Run 'run_windows.bat' to launch the application.
echo =======================================================
echo.
pause
