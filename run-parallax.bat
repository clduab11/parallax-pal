@echo off
setlocal enabledelayedexpansion

:: Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

echo Starting Parallax Pal...
echo ========================
echo.

:: Set Python environment variables for proper encoding
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
set PYTHONUTF8=1

:: Use a new venv name to avoid conflicts
set VENV_DIR=venv_new

:: Create new virtual environment
echo Creating virtual environment...
python -m venv %VENV_DIR%
if errorlevel 1 (
    echo Failed to create virtual environment.
    if exist "logs\error.log" type logs\error.log
    pause
    exit /b 1
)

:: Wait for venv creation to complete
timeout /t 2 /nobreak >nul

:: Activate virtual environment
echo Activating virtual environment...
if exist "%VENV_DIR%\Scripts\activate.bat" (
    call %VENV_DIR%\Scripts\activate.bat
) else (
    echo Virtual environment activation script not found.
    echo Looking in: %CD%\%VENV_DIR%\Scripts\activate.bat
    pause
    exit /b 1
)

:: Verify activation
if not defined VIRTUAL_ENV (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

:: Install requirements with verbose output
echo Installing requirements...
python -m pip install --upgrade pip
echo Installing Python packages...
python -m pip install -v -r requirements.txt
echo Verifying installations...
python -c "import colorama, questionary, rich, dotenv" 2>nul
if errorlevel 1 (
    echo Error: Missing required Python packages
    echo Attempting to install specific packages...
    python -m pip install colorama questionary rich python-dotenv
)
if errorlevel 1 (
    echo Failed to install requirements.
    if exist "logs\error.log" type logs\error.log
    pause
    exit /b 1
)

:: Run the script with error handling
echo Starting Parallax Pal...
echo ========================
echo.

:: Test Ollama connection and container status
echo Testing Ollama connection...
docker ps | findstr ollama >nul 2>&1
if errorlevel 1 (
    echo Error: Ollama container is not running
    echo Starting Ollama container...
    docker run -d -p 11434:11434 --name ollama ollama/ollama
    timeout /t 5 /nobreak >nul
)

echo Verifying Ollama API access...
curl -s http://host.docker.internal:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo Error: Cannot connect to Ollama at http://host.docker.internal:11434
    echo Please ensure Docker is running and Ollama container is active.
    echo Checking Docker status...
    docker ps | findstr ollama
    echo.
    echo You can manually start Ollama with: docker run -d -p 11434:11434 ollama/ollama
    pause
    exit /b 1
)
echo Ollama connection successful

:: Ensure required model is pulled
echo Checking for required model...
docker exec ollama ollama list | findstr llama2 >nul 2>&1
if errorlevel 1 (
    echo Model llama2 not found. Pulling model...
    docker exec ollama ollama pull llama2
    if errorlevel 1 (
        echo Failed to pull model llama2
        pause
        exit /b 1
    )
)
echo Model check completed

:: Set environment variable for Windows terminal
echo Setting up Windows environment...
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1

:: Run Python with detailed output
echo Starting Python script...
python -u parallax-pal.py
if errorlevel 1 (
    echo.
    echo An error occurred while running Parallax Pal.
    echo Displaying error log:
    echo ===================
    if exist "logs\error.log" type logs\error.log
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

:: Deactivate virtual environment
if defined VIRTUAL_ENV (
    call %VENV_DIR%\Scripts\deactivate.bat
)

echo.
echo Press any key to exit...
pause >nul