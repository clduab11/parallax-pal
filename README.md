# Parallax Pal! 🔍

Hey there! 👋 Parallax Pal is your friendly AI research assistant, designed to help you dive deep into any topic with the power of local Large Language Models (LLMs) through Ollama. Unlike your average chatbot, Parallax Pal structures its research, breaking down complex questions into focused areas, systematically exploring each through web searches and content scraping, and then compiling its findings into a neat document. 📝

## How It Works ⚙️

1. **Start with a Question:** Just ask Parallax Pal a question, like "What are the latest advancements in renewable energy?" 💡
2. **Focused Research:** The LLM analyzes your question and creates several research areas, each with a priority.
3. **Web Exploration:** Starting with the highest priority, Parallax Pal:
    *   Formulates targeted search queries.
    *   Performs web searches. 🌐
    *   Selects the most relevant web pages.
    *   Scrapes and extracts key information. ✂️
    *   Saves all content and source links into a research document. 📚
4. **Iterative Learning:** After exploring all areas, Parallax Pal generates new focus areas based on what it has found, leading to some interesting and novel research paths. 🔄
5. **Flexible Research:** You can let it research as long as you like, and stop it anytime with a command. It will then review all the content and provide a comprehensive summary. 🧐
6. **Interactive Q&A:** After the summary, you can ask Parallax Pal specific questions about its findings. 💬

Parallax Pal isn't just a chatbot; it's an automated research assistant that methodically investigates topics and keeps a detailed research trail. It can perform hundreds of searches and content retrievals quickly, giving you a full text document with lots of content and a summary, ready for your questions.

## Features ✨

*   Automated research planning with prioritized focus areas. 🎯
*   Systematic web searching and content analysis. 🕸️
*   Detailed research document with all content and source URLs. 🔗
*   Research summary generation. 📝
*   Post-research Q&A capability. 🤔
*   Self-improving search mechanism. 🚀
*   Rich console output with status indicators. 🚦
*   Comprehensive answer synthesis using web-sourced information. 🧠
*   Research conversation mode for exploring findings. 🗣️

## Installation and Setup Guide 🚀

### Prerequisites

*   **Python 3.9+**
*   **Git**
*   **Docker Desktop** (with WSL 2 backend enabled for Windows users)

### Installation Steps

#### For All Platforms:

1. **Clone the repository:**

    ```sh
    git clone https://github.com/clduab11/parallax-pal
    cd parallax-pal
    ```
2. **Set up a virtual environment:**

    ```sh
    python -m venv venv
    source venv/bin/activate  # For Linux/macOS
    venv\Scripts\activate  # For Windows
    ```
3. **Install dependencies:**

    ```sh
    pip install -r requirements.txt
    ```
4. **Set up environment variables:**
    *   Copy `.env.example` to `.env`
    *   Get your API keys:
        *   Tavily API key from [Tavily AI](https://tavily.com)
        *   Brave API key from [Brave Search API](https://brave.com/search/api/)
    *   Update `.env` with your API keys

    ```sh
    cp .env.example .env
    # Edit .env with your API keys
    ```

#### Windows-Specific Installation

For Windows users, follow these additional steps:

1. **Set Up WSL (Recommended):**

    ```powershell
    wsl --install
    wsl --set-default-version 2
    ```
2. **Install Chocolatey package manager:**

    ```powershell
    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    ```
3. **Install required packages:**

    ```powershell
    choco install docker-desktop
    ```
4. **Configure Docker:**
    *   Open Docker Desktop settings
    *   Enable WSL 2 backend
    *   Set resources (minimum 4GB RAM, 2 CPUs)
    *   Add Docker Desktop to WSL integration
5. **Configure Ollama:**
    *   Start Docker Desktop
    *   Run Ollama container:

    ```powershell
    docker run -d -p 11434:11434 --name ollama ollama/ollama
    ```
    *   Pull your preferred model:

    ```powershell
    docker exec -it ollama ollama pull llama2
    ```
    *   Verify Ollama is accessible:

    ```powershell
    curl http://host.docker.internal:11434/api/tags
    ```

**Note:** The application is designed to work with Ollama at `http://host.docker.internal:11434`. This URL is correct and should not be changed to `localhost`, as it ensures proper communication between the application and the Ollama container.

### Running the Application

1. **Activate virtual environment:**

    ```powershell
    venv\Scripts\activate  # For Windows
    source venv/bin/activate  # For Linux/macOS
    ```
2. **Start the application using the batch file (Windows):**

    ```powershell
    .\run-parallax.bat
    ```
    Or directly with Python (All Platforms):
    ```sh
    python parallax-pal.py
    ```

### Known Limitations (Windows)

*   **Terminal Input:**
    *   Use Windows Terminal for best experience
    *   CTRL+Z may not work consistently - use 'q' command to quit
*   **Keyboard Package:**
    *   Limited functionality on Windows
    *   May not detect all key combinations
*   **Readchar Package:**
    *   May have issues with special keys
    *   Use basic input where possible
*   **Curses Interface:**
    *   May have display issues in cmd.exe
    *   Use Windows Terminal for better support

### Troubleshooting (Windows)

**Issue:** Terminal display issues

*   Solution: Use Windows Terminal
*   Alternative: Set environment variable:

```powershell
$env:TERM = 'xterm-256color'
```

**Issue:** Docker connection problems

*   Solution: Verify Docker Desktop is running
*   Check WSL integration settings
*   Ensure Ollama container is running:

```powershell
docker ps | findstr ollama
```

*   Test Ollama connection:

```powershell
curl http://host.docker.internal:11434/api/tags
```

**Issue:** Virtual environment activation fails

*   Solution: Run PowerShell as Administrator
*   Ensure execution policy is set:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Recommended Tools (Windows)

*   **Windows Terminal** (from Microsoft Store)
*   **Visual Studio Code** with WSL extension
*   **Docker Desktop** with WSL 2 backend
*   **Postman** for API testing

## Usage 🚀

1. **Ensure Ollama is running:** Make sure your Ollama instance is running and accessible at `http://host.docker.internal:11434`.
2. **Start a research session:**
    *   Type `@` followed by your research query.
    *   Example: `@What are the ethical implications of AI in healthcare?`
3. **During research, use these commands:**
    *   `P` to pause research and show available options
    *   `F` to finalize and synthesize research findings
    *   `Q` to quit research
4. **After research:**
    *   Wait for the summary and review the findings.
    *   Enter conversation mode to ask questions.
    *   Access the detailed research content in the research session text file.

## Contributing 🤝

Contributions are welcome! This is a prototype with lots of room for improvements and new features.

## License 📜

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements 🙏

This project is a derivative work of TheBlewish's Automated-AI-Web-Research-Ollama.

## Disclaimer ⚠️

This project is for educational purposes only. Ensure you comply with the terms of service of all APIs and services used.
