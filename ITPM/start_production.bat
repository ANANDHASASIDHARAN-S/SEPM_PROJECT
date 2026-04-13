@echo off
REM Start Script for ITPM Application - Production Use

setlocal enabledelayedexpansion

REM Navigate to application directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

REM Initialize database if needed
if not exist "resource_allocation.db" (
    echo Initializing database...
    python run.py init-db
)

REM Start Gunicorn
echo.
echo ========================================
echo Starting ITPM Application
echo ========================================
echo.
echo Server: http://localhost:8000
echo Workers: 4
echo.

gunicorn -w 4 -b 0.0.0.0:8000 --access-logfile - --error-logfile - "app:create_app()"
