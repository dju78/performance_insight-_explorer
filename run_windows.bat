@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo   Performance Insight Explorer
echo   Operational Performance - Data Quality - Analysis
echo   Author: DARAMOLA OMOYELE
echo =======================================================
echo.

:: Check virtual environment
if exist "venv\Scripts\activate.bat" (
    echo [*] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [!] No virtual environment found. Using system Python...
)

:: Check streamlit
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Streamlit is not installed. Please run 'setup_windows.bat' first.
    pause
    exit /b 1
)

echo [*] Launching Performance Insight Explorer in your browser...
echo [*] Application starting locally on port 8501...
echo.
streamlit run app.py

pause
