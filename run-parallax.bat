@echo off
setlocal enabledelayedexpansion

:: Change to the script's directory
cd /d "%~dp0"

:: Create logs directory if it doesn't exist
if not exist "logs" mkdir "logs"

echo Starting Parallax Pal...
echo ========================
echo.

:: Check Python version
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYTHON_VERSION=%%I
echo Detected Python version: %PYTHON_VERSION%
if "%PYTHON_VERSION:~0,1%" LSS "3" (
    echo Error: Python 3.8 or higher is required
    echo Current version: %PYTHON_VERSION%
    pause
    exit /b 1
)

:: Set Python environment variables
echo Setting up Python environment...
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1

:: Use local venv directory with proper quoting
set "VENV_DIR=%CD%\venv_new"
echo Virtual environment will be created at: "%VENV_DIR%"

:: Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%" 2>"logs\venv_error.log"
    if errorlevel 1 (
        echo Failed to create virtual environment.
        type "logs\venv_error.log"
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)

:: Install/upgrade pip and requirements
echo Installing requirements...
python -m pip install --upgrade pip
python -m pip install -r "requirements.txt"
if errorlevel 1 (
    echo Failed to install requirements
    pause
    exit /b 1
)

:: Clear the screen after installations
cls

:: Test Ollama connection
echo Testing Ollama connection...
curl -s http://host.docker.internal:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo Warning: Cannot connect to Ollama API at http://host.docker.internal:11434
    echo.
    echo Please ensure:
    echo 1. Docker Desktop is running with WSL 2 backend
    echo 2. Ollama container is running ^(docker ps ^| findstr ollama^)
    echo 3. If needed, start Ollama with: docker run -d -p 11434:11434 ollama/ollama
    echo.
    echo Note: The URL http://host.docker.internal:11434 is correct and should not be changed
    echo       to localhost or other variations, as it ensures proper Docker communication.
    echo.
    pause
    exit /b 1
)
echo Ollama connection successful

:: Run the main script
echo Starting Python script...
python "parallax-pal.py"
if errorlevel 1 (
    echo.
    echo An error occurred while running Parallax Pal.
    if exist "logs\error.log" type "logs\error.log"
    pause
    exit /b 1
)

:: Cleanup
call "%VENV_DIR%\Scripts\deactivate.bat"
echo.
pause