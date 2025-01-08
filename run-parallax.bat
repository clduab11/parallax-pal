@echo off
setlocal enabledelayedexpansion

:: Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

:: Install requirements
echo Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements.
    pause
    exit /b 1
)

:: Run the script
echo Starting Parallax Pal...
python parallax-pal.py
if errorlevel 1 (
    echo An error occurred while running Parallax Pal.
    pause
)

:: Deactivate virtual environment
deactivate

pause