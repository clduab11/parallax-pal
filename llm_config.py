# llm_config.py

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

def validate_api_configs(search_apis: Dict[str, Any]) -> None:
    """Validate that enabled search APIs have their required API keys configured."""
    for api_name, config in search_apis.items():
        if config["enabled"]:
            env_key = f"{api_name.upper()}_API_KEY"
            if not os.getenv(env_key):
                raise ValueError(f"API key for {api_name} is missing. Please set the {env_key} environment variable.")

# Enhanced LLM settings for Ollama
LLM_CONFIG_OLLAMA = {
    "llm_type": "ollama",
    "base_url": os.getenv('OLLAMA_BASE_URL', 'http://host.docker.internal:11434'),
    "timeout": int(os.getenv('OLLAMA_TIMEOUT', '420')),  # 7 minute timeout
    "model_name": os.getenv('MODEL_NAME', 'llama2'),
    "temperature": float(os.getenv('TEMPERATURE', '0.7')),
    "top_p": float(os.getenv('TOP_P', '0.9')),
    "n_ctx": int(os.getenv('N_CTX', '131072')),  # 128K context window for extended research sessions
    "stop": ["User:", "\n\n"],
    "gpu_layers": int(os.getenv('GPU_LAYERS', '0')),
    "gpu_settings": {
        "enabled": os.getenv('GPU_ENABLED', 'false').lower() == 'true',
        "max_layers": int(os.getenv('GPU_MAX_LAYERS', '-1')),
        "memory_limit": int(os.getenv('GPU_MEMORY_LIMIT', '0')) or None
    },

    # Available models
    "available_models": [
        "llama2",
        "mistral",
        "codellama",
        "neural-chat",
        "starling-lm"
    ],

    # Search API configurations
    "search_apis": {
        "tavily": {
            "enabled": os.getenv('TAVILY_ENABLED', 'true').lower() == 'true',
            "api_key": os.getenv('TAVILY_API_KEY'),
            "max_results": int(os.getenv('TAVILY_MAX_RESULTS', '5')),
            "timeout": int(os.getenv('TAVILY_TIMEOUT', '120')),
            "retry_count": int(os.getenv('TAVILY_RETRY_COUNT', '3')),
            "retry_delay": int(os.getenv('TAVILY_RETRY_DELAY', '2'))
        },
        "brave": {
            "enabled": os.getenv('BRAVE_ENABLED', 'true').lower() == 'true',
            "api_key": os.getenv('BRAVE_API_KEY'),
            "max_results": int(os.getenv('BRAVE_MAX_RESULTS', '5')),
            "timeout": int(os.getenv('BRAVE_TIMEOUT', '30')),
            "retry_count": int(os.getenv('BRAVE_RETRY_COUNT', '3')),
            "retry_delay": int(os.getenv('BRAVE_RETRY_DELAY', '2'))
        },
        "duckduckgo": {
            "enabled": os.getenv('DUCKDUCKGO_ENABLED', 'false').lower() == 'true',
            "max_results": int(os.getenv('DUCKDUCKGO_MAX_RESULTS', '5')),
            "timeout": int(os.getenv('DUCKDUCKGO_TIMEOUT', '30')),
            "retry_count": int(os.getenv('DUCKDUCKGO_RETRY_COUNT', '3')),
            "retry_delay": int(os.getenv('DUCKDUCKGO_RETRY_DELAY', '2'))
        }
    }
}

def get_llm_config(model_name: str = None) -> Dict[str, Any]:
    """Get Ollama LLM configuration with validation."""
    config = LLM_CONFIG_OLLAMA.copy()
    
    # If model name is provided, validate and update the config
    if model_name and model_name in config['available_models']:
        config['model_name'] = model_name
    
    # Validate search API configurations
    validate_api_configs(config["search_apis"])
    
    return config
