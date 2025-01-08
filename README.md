# Parallax Pal: AI-Powered Research Assistant 🔍

## Overview

Parallax Pal is an advanced AI research assistant that transforms complex research queries into structured, comprehensive insights. Unlike traditional chatbots, this tool methodically breaks down research questions, explores web sources, and synthesizes findings with unprecedented depth and precision.

## Pricing & Licensing 💡

Parallax Pal offers flexible licensing options to suit various research and commercial needs:

### Subscription Tiers

1. **Community Tier**: $0/month
   - Limited to 100 research queries
   - Single AI model
   - Basic features
   - Non-commercial use only

2. **Research Tier**: $9.99/month
   - Up to 1,000 research queries
   - 3 AI models
   - Advanced research tools
   - Academic and non-profit use
   - 30-day free trial

3. **Professional Tier**: $29.99/month
   - Up to 10,000 research queries
   - 10 AI models
   - Full commercial usage rights
   - Priority support
   - 30-day free trial

4. **Enterprise Tier**: $99.99/month
   - Unlimited research queries
   - 50 AI models
   - Full commercial usage rights
   - Dedicated support
   - Custom integrations
   - 30-day free trial

5. **Perpetual License**: $2,500
   - One-time purchase
   - Unlimited lifetime usage
   - Full commercial rights
   - Priority enterprise support

### Licensing Options

- **Non-Commercial Use**: Free and Research tiers
- **Commercial Use**: Professional and Enterprise tiers
- **Perpetual License**: Includes full commercial rights

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

Detailed licensing terms available in the LICENSE file. Different usage rights apply based on selected subscription tier.

## Disclaimer ⚠️

This project is primarily for educational and research purposes. Users must comply with all API and service terms of use.
