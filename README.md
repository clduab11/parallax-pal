# Parallax Pal: AI-Powered Research Assistant 🔍

## Overview

Parallax Pal is an advanced AI research assistant that transforms complex research queries into structured, comprehensive insights. Unlike traditional chatbots, this tool methodically breaks down research questions, explores web sources, and synthesizes findings with unprecedented depth and precision.

## Key Features 🚀

- **Intelligent Research Planning**: Automatically creates prioritized research focus areas
- **Systematic Web Exploration**: Performs targeted searches and content extraction
- **Comprehensive Documentation**: Generates detailed research documents with source URLs
- **Adaptive Learning**: Continuously refines research approach based on discovered information
- **Interactive Q&A**: Enables in-depth exploration of research findings

## How Parallax Pal Works 🧠

1. **Input Research Query**: Provide a complex question or research topic
2. **Automated Analysis**: AI breaks down the query into focused research areas
3. **Web Exploration**: 
   - Generates targeted search queries
   - Retrieves and analyzes relevant web pages
   - Extracts key information systematically
4. **Knowledge Synthesis**: Compiles findings into a structured research document
5. **Continuous Refinement**: Iteratively explores new research angles

## Getting Started 🛠️

### Prerequisites
- Python 3.9+
- Git
- Docker Desktop (with WSL 2 backend for Windows)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/clduab11/parallax-pal
cd parallax-pal
```

2. Set up virtual environment:
```bash
python -m venv venv
# Activate for Windows
venv\Scripts\activate
# Activate for Linux/macOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
- Copy `.env.example` to `.env`
- Add API keys for Tavily and Brave Search

### Usage

1. Ensure Ollama is running
2. Start a research session:
   - Use `@` followed by your research query
   - Example: `@What are the ethical implications of AI in healthcare?`

3. Research Commands:
   - `P`: Pause and show options
   - `F`: Finalize and synthesize research
   - `Q`: Quit research

## Contributing 🤝

Contributions are welcome! This is a prototype with significant potential for enhancement.

## License 

© 2025 Chris Dukes, Parallax Analytics. All Rights Reserved.

THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. UNAUTHORIZED USE, COPYING, MODIFICATION, DISTRIBUTION, OR REPRODUCTION IS STRICTLY PROHIBITED.

NOTICE: This project contains derivative work from TheBlewish's Automated-AI-Web-Research-Ollama.

## Disclaimer ⚠️

This project is for educational and research purposes. Users must comply with all API and service terms of use.
