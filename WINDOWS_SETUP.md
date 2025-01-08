# Windows Setup Guide

## Prerequisites

1. **Windows 10/11** (64-bit)
2. **Windows Terminal** (Recommended from Microsoft Store)
3. **Python 3.9+**
4. **Docker Desktop** (with WSL 2 backend enabled)

## Installation Steps

### 1. Set Up WSL (Recommended)
```powershell
wsl --install
wsl --set-default-version 2
```

### 2. Install Dependencies
```powershell
# Install Chocolatey package manager
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install required packages
choco install git python docker-desktop
```

### 3. Clone the Repository
```powershell
git clone https://github.com/clduab11/parallax-pal
cd parallax-pal
```

### 4. Set Up Virtual Environment
```powershell
python -m venv venv
venv\Scripts\activate
```

### 5. Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### 6. Configure Docker
1. Open Docker Desktop settings
2. Enable WSL 2 backend
3. Set resources (minimum 4GB RAM, 2 CPUs)
4. Add Docker Desktop to WSL integration

### 7. Configure Ollama
1. Start Docker Desktop
2. Run Ollama container:
```powershell
docker run -d -p 11434:11434 --name ollama ollama/ollama
```
3. Pull your preferred model:
```powershell
docker exec -it ollama ollama pull llama2
```
4. Verify Ollama is accessible:
```powershell
curl http://host.docker.internal:11434/api/tags
```

Note: The application is designed to work with Ollama at http://host.docker.internal:11434. This URL is correct and should not be changed to localhost, as it ensures proper communication between the application and the Ollama container.

## Running the Application

1. Activate virtual environment:
```powershell
venv\Scripts\activate
```

2. Start the application using the batch file:
```powershell
.\run-parallax.bat
```

## Known Limitations

1. **Terminal Input**:
   - Use Windows Terminal for best experience
   - CTRL+Z may not work consistently - use 'q' command to quit

2. **Keyboard Package**:
   - Limited functionality on Windows
   - May not detect all key combinations

3. **Readchar Package**:
   - May have issues with special keys
   - Use basic input where possible

4. **Curses Interface**:
   - May have display issues in cmd.exe
   - Use Windows Terminal for better support

## Troubleshooting

**Issue**: Terminal display issues
- Solution: Use Windows Terminal
- Alternative: Set environment variable:
```powershell
$env:TERM = 'xterm-256color'
```

**Issue**: Docker connection problems
- Solution: Verify Docker Desktop is running
- Check WSL integration settings
- Ensure Ollama container is running:
```powershell
docker ps | findstr ollama
```
- Test Ollama connection:
```powershell
curl http://host.docker.internal:11434/api/tags
```

**Issue**: Virtual environment activation fails
- Solution: Run PowerShell as Administrator
- Ensure execution policy is set:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Recommended Tools

1. **Windows Terminal** (from Microsoft Store)
2. **Visual Studio Code** with WSL extension
3. **Docker Desktop** with WSL 2 backend
4. **Postman** for API testing