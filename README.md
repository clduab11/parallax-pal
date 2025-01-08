Hi everyone! My name is Chris, and I recently started Parallax Analytics as a business to bridge the divide between the consumer and the technical professional; aka, translating the wizardy of AI and deep learning in general to help SMBs unleash their potential! I am not a coder by nature; my experience is limited to crash-coursing coding and all things artificial intelligence, Python, and deep/machine learning, and this is the first 1.0.0 culmination of my work that I'm proud to present! NOTE: This repository is private at this time, and I will remove and update this note when I'm ready to go public.

# Forthcoming Changes & Future Updates**!! (**: as time allows)
- Folder path to drop any local models you download (GGUF support first, followed by EXL2, potentially INT8, etc.)
- Output folder where Parallax Pal drops a .md summation of the conversation
- Full Mac/Linux support
- Full Docker implementation (limited to Ollama models or API calls)
- API routing for Together.ai/Openrouter.ai/Hyperbolic support, amongst others
- OpenAI-compatible endpoints for wide customization


# Parallax Pal 🔍

Hey there! 👋 Parallax Pal is your friendly AI research assistant, designed to help you dive deep into any topic with the power of local Large Language Models (LLMs) through Ollama. Unlike your average chatbot, Parallax Pal structures its research, breaking down complex questions into focused areas, systematically exploring each through web searches and content scraping, and then compiling its findings into a neat document. 📝

## How It Works ⚙️

1.  **Start with a Question:** Just ask Parallax Pal a question, like "What are the latest advancements in renewable energy?" 💡
2.  **Focused Research:** The LLM analyzes your question and creates several research areas, each with a priority.
3.  **Web Exploration:** Starting with the highest priority, Parallax Pal:
    *   Formulates targeted search queries.
    *   Performs web searches. 🌐
    *   Selects the most relevant web pages.
    *   Scrapes and extracts key information. ✂️
    *   Saves all content and source links into a research document. 📚
4.  **Iterative Learning:** After exploring all areas, Parallax Pal generates new focus areas based on what it has found, leading to some interesting and novel research paths. 🔄
5.  **Flexible Research:** You can let it research as long as you like, and stop it anytime with a command. It will then review all the content and provide a comprehensive summary. 🧐
6.  **Interactive Q&A:** After the summary, you can ask Parallax Pal specific questions about its findings. 💬

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

## Quick Start Guide 🚀

### Installation

#### For All Platforms:
1. **Clone the repository:**
    ```sh
    git clone https://github.com/clduab11/parallax-pal
    cd parallax-pal
    ```
2.  **Set up a virtual environment:**
    ```sh
    python -m venv venv
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    - Copy `.env.example` to `.env`
    - Get your API keys:
      - Tavily API key from [Tavily AI](https://tavily.com)
      - Brave API key from [Brave Search API](https://brave.com/search/api/)
    - Update `.env` with your API keys
    ```sh
    cp .env.example .env
    # Edit .env with your API keys
    ```

### Windows-Specific Installation

For Windows users, please refer to the [WINDOWS_SETUP.md](WINDOWS_SETUP.md) file for detailed installation instructions and troubleshooting tips.

Key Windows Considerations:
- Use Windows Terminal for best experience
- Docker configuration requires WSL 2 backend
- Virtual environment activation uses `venv\Scripts\activate`
- CTRL+Z may not work consistently - use 'q' command to quit
1.  **Configure Ollama:**
    - Make sure your Ollama instance is running and accessible at `http://host.docker.internal:11434` 🐳
    - Pull your preferred model using Ollama (e.g., `ollama pull llama2`)
    - It's recommended to use a model with a large context window for better research capabilities
    - Set the MODEL_NAME in your .env file to match your pulled model's name

2.  **Configure the LLM:**
    Parallax Pal will automatically detect and use the models available in your local Ollama instance. The configuration in `llm_config.py` handles:
    - Connection to your local Ollama instance
    - Model parameters (temperature, context window, etc.)
    - GPU settings (if enabled)
    
    You can adjust these settings in your .env file as needed.

## Usage 🚀

1.  **Ensure Ollama is running:** Make sure your Ollama instance is running and accessible at `http://host.docker.internal:11434`.
2.  **Run Parallax Pal:**
    There are two ways to launch the application:

    a. Using the batch file (recommended):
    ```sh
    run-parallax.bat
    ```
    This will open ParallaxPal in its own terminal window.

    b. Directly with Python:
    ```sh
    python parallax-pal.py
    ```

3.  **Start a research session:**
    *   Type `@` followed by your research query.
    *   Example: `@What are the ethical implications of AI in healthcare?`

4.  **During research, use these commands:**
    *   `P` to pause research and show available options
    *   `F` to finalize and synthesize research findings
    *   `Q` to quit research
5.  **After research:**
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
