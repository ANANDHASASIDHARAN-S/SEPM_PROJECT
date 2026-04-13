@echo off
echo Resource Allocation & Workforce Planning System
echo ================================================
echo.

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/upgrade requirements
echo Installing requirements...
pip install -r requirements.txt -q

REM Initialize database if needed
if not exist resource_allocation.db (
    echo Initializing database with sample data...
    python run.py init-db
)

REM Start the application
echo.
echo Starting application...
echo Open http://localhost:5000 in your browser
echo.
python run.py
