@echo off
title E-Commerce Customer 360 & Predictive Churn Analytics
cd /d "%~dp0"

echo ===================================================================
echo   E-Commerce Customer 360 & Predictive Churn Analytics
echo   Powered by MongoDB & XGBoost
echo ===================================================================
echo.

:: Check if virtual environment exists
if not exist ".venv\Scripts\streamlit.exe" (
    echo [ERROR] Virtual environment not found at .venv\Scripts\streamlit.exe!
    echo Please make sure the virtual environment is set up.
    echo.
    pause
    exit /b 1
)

echo [INFO] Starting Streamlit Analytics Dashboard...
echo [INFO] The dashboard will open in your default browser at http://localhost:8501
echo [INFO] Press Ctrl+C in this terminal window to stop the server.
echo.

:: Launch Streamlit
call .venv\Scripts\streamlit.exe run app/dashboard.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application stopped or encountered an error.
    pause
)

