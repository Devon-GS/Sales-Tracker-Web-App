@echo off
REM Sales Tracker Startup Script for Windows

echo Starting Sales Tracker...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed. Please install Python 3.9 or higher.
    pause
    exit /b 1
)

REM Check if virtual environment exists, if not create it
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

REM Run the Flask app
echo.
echo ==========================================
echo Sales Tracker is starting...
echo Open your browser and go to: http://localhost:5000
echo Press Ctrl+C to stop the server
echo ==========================================
echo.

python app.py

pause
