# Parallax Pal: AI-Powered Research Assistant 🔍

## Overview

Parallax Pal is an advanced AI research assistant that transforms complex research queries into structured, comprehensive insights. Unlike traditional chatbots, this tool methodically breaks down research questions, explores web sources, and synthesizes findings with unprecedented depth and precision.

## How Parallax Pal Works 🧠

1. **Input Research Query**: Provide a complex question or research topic
2. **Automated Analysis**: AI breaks down the query into focused research areas
3. **Web Exploration**: 
   - Generates targeted search queries
   - Retrieves and analyzes relevant web pages
   - Extracts key information systematically
4. **Knowledge Synthesis**: Compiles findings into a structured research document
5. **Continuous Refinement**: Iteratively explores new research angles

## Key Features 🚀

- **Intelligent Research Planning**: Automatically creates prioritized research focus areas
- **Systematic Web Exploration**: Performs targeted searches and content extraction
- **Comprehensive Documentation**: Generates detailed research documents with source URLs
- **Adaptive Learning**: Continuously refines research approach based on discovered information
- **Interactive Q&A**: Enables in-depth exploration of research findings



## Pricing & Licensing 💡

Parallax Pal offers flexible licensing options to suit various research and commercial needs: (DRAFT - IN WORKSHOPPING)

### Subscription Tiers

1. **Free Tier**: $0/month
   - Limited to 100 research queries per month
   - Limited to 3 continous research queries; output limited to 3 search iterations per query
   - Preset/fixed AI model
   - Basic generative AI chat features
   - Personal use granted (no commercial usage)
   - Ad-supported

2. **Academic/Research Tier*: $9.99/month* (only available to non-profit .org, .edu addresses)
   - Up to 500 research queries per month
   - Up to 25 continuous research queries per month (output limited to 3 search iterations per query)
   - 3 AI models, including 1 instruct-tuned model
   - Academic/non-profit use (no commercial usage)
   - 3-day free trial

3. **Professional Tier**: $29.99/month
   - Up to 2,500 research queries
   - 10 AI models; when signing up, you will be asked for some data regarding usage, this will only be used to gauge your choice of models and will not be maintained or stored in any way
   - Advanced research tools; including unlimited continuous research mode (limited to 5 search iterations per query), upgrade to .pdf output
   - Full commercial usage rights
   - 3-day free trial

4. **Enterprise Tier**: $99.99/month
   - Up to 5,000 research queries
   - 25 AI models; free 30-min consultation included to determine needs.
   - Full commercial usage rights
   - Unlimited queries with local model support
   - Priority support
   - Custom integrations (including coding IDE through Bolt.diy [CURRENTLY IN BETA])
   - 3-day free trial

5. **Perpetual License**: $3,500
   - One-time purchase for lifetime of usage of Parallax Pal
   - Free 30-minute consultation included to determine needs
   - Full commercial rights
   - Custom integrations
   - Priority input regarding integrations/implementations, with a private branch unlocking local model support
   - Access to source code/private GitHub

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

## License 

© 2025 Chris Dukes, Parallax Analytics. All Rights Reserved.

Detailed licensing terms available in the LICENSE file. Different usage rights apply based on selected subscription tier.

## Disclaimer ⚠️

This project is primarily for educational and research purposes. Users must comply with all API and service terms of use. Parallax Analytics shall be held indemnified in the event of any unethical, amoral, or illegal behavior with the usage of Parallax Pal. User accepts all risk of utilizing generative deep learning/artificial intelligence technology for any contextual and/or informational purposes.


### Licensing Options

- **Non-Commercial Use**: Personal usage only.
- **Academic/Non-Profit Use**: MIT license applies, please cite my GitHub, license, and disclaimer.
- **Commercial Use**: Professional and Enterprise tiers; full ownership of any generative product
- **Perpetual License**: Includes full ownership of any generative product
