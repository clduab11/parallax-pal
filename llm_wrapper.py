#!/usr/bin/env python3
"""LLM Wrapper - Handles interactions with language models"""

import os
import re
import sys
import requests
import json
import logging
import time
from typing import Optional, Generator, Any, Dict, List
from contextlib import contextmanager
from colorama import init, Fore, Style
from llm_config import get_llm_config
from tenacity import retry, stop_after_attempt, wait_exponential

# Initialize colorama
init()

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMError(Exception):
    """Custom exception for LLM-related errors"""
    pass

class LLMWrapper:
    def __init__(self, defer_init=False):
        """Initialize LLM wrapper with optional deferred initialization"""
        self.client = None
        self.model_name = None
        self.gpu_name = None
        self.total_gpu_memory = 0
        self.free_gpu_memory = 0
        self.gpu_available = False
        self.available_models = []
        self._initialized = False
        self.gpu_enabled = False
        self._session = requests.Session()
        self.llm_config = get_llm_config()
        self.base_url = 'http://host.docker.internal:11434'
        self.model_settings = {}  # Store per-model settings
        
        if not defer_init:
            self.initialize()
    def initialize(self):
        """Initialize the LLM with configuration"""
        try:
            if not self._initialized:
                self._initialize_ollama()
            self._initialized = True
            logger.info("Initialized LLM wrapper")
        except Exception as e:
            logger.error(f"Error initializing LLM wrapper: {str(e)}")
            self._cleanup()
            raise LLMError(f"Initialization failed: {str(e)}")

    def _initialize_ollama(self):
        """Initialize Ollama with proper error handling"""
        try:
            # Ensure we're using the local Ollama endpoint
            self.base_url = 'http://host.docker.internal:11434'
            self.available_models = self._fetch_ollama_models()
            
            if not self.available_models:
                raise LLMError("No Ollama models available")
            
            # Only show model selection if no model is selected
            if not self.model_name:
                self._display_model_selection()
            elif self.model_name not in self.available_models:
                raise LLMError(f"Selected model {self.model_name} not available")
            
            # Configure GPU settings
            self._check_gpu_support()
            self._session.delete(f"{self.base_url}/api/stop")
            
            model_config = {
                "name": self.model_name,
                "parameters": {
                    "gpu_layers": self.llm_config['gpu_layers'] if self.gpu_enabled else 0,
                    "context_length": self.llm_config['n_ctx']  # Set context window
                }
            }
            
            print(f"{Fore.CYAN}Initializing model with {self.llm_config['n_ctx']:,} token context window{Style.RESET_ALL}")
            
            if self.gpu_enabled and self.llm_config['gpu_settings']['memory_limit']:
                model_config["parameters"]["gpu_memory_limit"] = min(
                    self.llm_config['gpu_settings']['memory_limit'],
                    int(self.free_gpu_memory * 0.9 * 1024)  # Convert to MB and use 90% of free memory
                )
            
            # Initialize model in background
            response = self._session.post(
                f"{self.base_url}/api/pull",
                json=model_config,
                timeout=self.llm_config.get('timeout', 30)
            )
            response.raise_for_status()
            
        except Exception as e:
            raise LLMError(f"Ollama initialization failed: {str(e)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), reraise=True)
    def _fetch_ollama_models(self) -> list:
        """Fetch available models from Ollama server with retries"""
        try:
            # Check Docker and Ollama status
            try:
                self._check_docker_status()
            except Exception as docker_err:
                logger.error(f"Docker check failed: {str(docker_err)}")
                print(f"\n{Fore.RED}Error: Docker is not running or accessible.{Style.RESET_ALL}")
                print("Please ensure Docker Desktop is running and try again.")
                raise LLMError("Docker is not accessible") from docker_err

            response = self._session.get(
                f"{self.base_url}/api/tags",
                timeout=self.llm_config.get('timeout', 30)
            )

            if response.status_code == 404:
                print(f"\n{Fore.YELLOW}Starting Ollama container...{Style.RESET_ALL}")
                self._start_ollama_container()
                # Retry the request
                response = self._session.get(
                    f"{self.base_url}/api/tags",
                    timeout=self.llm_config.get('timeout', 30)
                )

            response.raise_for_status()
            models = response.json().get('models', [])
            
            if not models:
                print(f"\n{Fore.YELLOW}No models found. Pulling default model...{Style.RESET_ALL}")
                self._pull_default_model()
                # Retry one more time
                response = self._session.get(
                    f"{self.base_url}/api/tags",
                    timeout=self.llm_config.get('timeout', 30)
                )
                response.raise_for_status()
                models = response.json().get('models', [])

            return [model['name'] for model in models]

        except requests.exceptions.RequestException as e:
            error_msg = (f"\n{Fore.RED}Error: Could not connect to Ollama. "
                        f"Please ensure Docker is running and Ollama container is active.\n"
                        f"You can start Ollama with: docker run -d -p 11434:11434 ollama/ollama{Style.RESET_ALL}")
            print(error_msg)
            raise LLMError(error_msg)

    def _check_docker_status(self) -> None:
        """Check if Docker is running"""
        try:
            result = os.system("docker info > nul 2>&1" if os.name == 'nt' else "docker info > /dev/null 2>&1")
            if result != 0:
                raise LLMError("Docker is not running")
        except Exception as e:
            raise LLMError(f"Docker check failed: {str(e)}")

    def _start_ollama_container(self) -> None:
        """Start the Ollama container if not running"""
        try:
            # Check if container exists and is running
            result = os.system("docker ps | grep ollama > nul 2>&1" if os.name == 'nt' else "docker ps | grep ollama > /dev/null 2>&1")
            
            if result != 0:
                print(f"{Fore.CYAN}Starting Ollama container...{Style.RESET_ALL}")
                os.system("docker run -d -p 11434:11434 ollama/ollama")
                # Give it a moment to start
                time.sleep(5)
        except Exception as e:
            raise LLMError(f"Failed to start Ollama container: {str(e)}")

    def _pull_default_model(self) -> None:
        """Pull a default model if none are available"""
        try:
            print(f"{Fore.CYAN}Pulling default model (this may take a few minutes)...{Style.RESET_ALL}")
            response = self._session.post(
                f"{self.base_url}/api/pull",
                json={"name": "dolphin-phi"},
                timeout=600  # Longer timeout for model pull
            )
            response.raise_for_status()
            print(f"{Fore.GREEN}Default model pulled successfully{Style.RESET_ALL}")
        except Exception as e:
            raise LLMError(f"Failed to pull default model: {str(e)}")

    def _check_gpu_support(self) -> None:
        """Check GPU support with proper error handling"""
        self.gpu_available = False
        self.gpu_enabled = False
        try:
            gpu_info = os.popen('nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader').read().strip()
            self.gpu_available = bool(gpu_info)
            self.gpu_enabled = self.gpu_available and self.llm_config['gpu_settings']['enabled']

            if self.gpu_available:
                gpu_lines = gpu_info.split('\n')
                if gpu_lines:
                    gpu_name, total_memory, free_memory = gpu_lines[0].split(',')
                    self.gpu_name = gpu_name.strip()
                    self.total_gpu_memory = float(total_memory.strip().split()[0]) / 1024
                    self.free_gpu_memory = float(free_memory.strip().split()[0]) / 1024

                    logger.info(f"GPU detected: {self.gpu_name}")
                    logger.info(f"Total GPU memory: {self.total_gpu_memory:.1f}GB")
                    logger.info(f"Free GPU memory: {self.free_gpu_memory:.1f}GB")
                    
                    if self.gpu_enabled:
                        logger.info("GPU acceleration enabled")
                    else:
                        logger.info("GPU acceleration available but disabled")
                else:
                    raise LLMError("Could not parse GPU info")
            else:
                logger.info("No NVIDIA GPU detected")

        except Exception as e:
            self.gpu_available = False
            self.gpu_enabled = False
            logger.error(f"GPU check failed: {str(e)}")
            if "command not found" in str(e).lower():
                logger.error("nvidia-smi not found. Please install NVIDIA drivers.")
            elif "no devices were found" in str(e).lower():
                logger.error("No NVIDIA GPU devices found.")

    def configure_model_settings(self, model_name: str) -> None:
        """Configure settings for specific model"""
        # Model-specific embedding settings
        embedding_models = {
            'nomic-embed-text': {'dim': 768, 'normalized': True},
            'all-minilm': {'dim': 384, 'normalized': True},
            'bge-small': {'dim': 384, 'normalized': True}
        }

        # Model-specific tuning parameters
        tuning_params = {
            'dolphin': {
                'temperature': 0.7,
                'top_p': 0.9,
                'presence_penalty': 0.1,
                'frequency_penalty': 0.1,
                'stop': ['<|im_end|>', '<|im_start|>']
            },
            'deepseek': {
                'temperature': 0.8,
                'top_p': 0.95,
                'presence_penalty': 0.2,
                'frequency_penalty': 0.2,
                'stop': ['<|endoftext|>']
            }
        }
        
        self.model_settings[model_name] = {
            'embeddings': embedding_models.get('bge-small'),  # Default to bge-small
            'tuning': next((v for k, v in tuning_params.items() if k in model_name.lower()), 
                          tuning_params['dolphin'])  # Default to dolphin params
        }

    def _display_model_selection(self) -> None:
        """Display available Ollama models with enhanced formatting"""
        print(f"\n{Fore.CYAN}=== Model Configuration ==={Style.RESET_ALL}")
        print(f"\nGPU Acceleration: {Fore.GREEN if self.gpu_enabled else Fore.RED}"
              f"{'✓ Enabled' if self.gpu_enabled else '✗ Disabled'}{Style.RESET_ALL}")
        
        if self.gpu_enabled:
            print(f"\nGPU Memory: {Fore.CYAN}{self.free_gpu_memory:.1f}GB free "
                  f"of {self.total_gpu_memory:.1f}GB{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}Available Models:{Style.RESET_ALL}")
        
        for i, model in enumerate(self.available_models, 1):
            details = self._parse_model_details(model)
            size_info = f"{Fore.CYAN}[{details['size']}]{Style.RESET_ALL}"
            quant_info = f"{Fore.GREEN}[{details['quant']}]{Style.RESET_ALL}" if details['quant'] != 'Unknown' else '[Base]'
            
            if 'speed' in details and 'mem' in details:
                perf_info = f"{Fore.YELLOW}[{details['speed']}/{details['mem']}]{Style.RESET_ALL}"
            else:
                perf_info = '[Standard Performance]'

            model_name = model.split('/')[-1].split(':')[0]
            print(f"{Fore.YELLOW}{i:2d}{Style.RESET_ALL}. {model_name:<30} {size_info} {quant_info} {perf_info}")

        print(f"\n{Fore.CYAN}Embeddings: Using BGE-Small (384d) by default{Style.RESET_ALL}")

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Ollama with enhanced error handling and timeout management"""
        if not self._initialized:
            self.initialize()

        try:
            # Apply model-specific settings
            if self.model_name in self.model_settings:
                kwargs.update(self.model_settings[self.model_name]['tuning'])

            # Calculate approximate token count (rough estimate)
            approx_tokens = len(prompt.split())
            if approx_tokens > self.llm_config.get('n_ctx', 4096):
                raise LLMError(f"Prompt too long (approximately {approx_tokens} tokens)")

            # Calculate dynamic timeout based on prompt length
            base_timeout = self.llm_config.get('timeout', 30)
            dynamic_timeout = max(base_timeout, approx_tokens / 20)  # ~20 tokens per second processing
            
            # Add progress indicator for long generations
            if dynamic_timeout > base_timeout:
                print(f"{Fore.YELLOW}Processing large prompt ({approx_tokens} tokens), this may take a moment...{Style.RESET_ALL}")

            try:
                response = self._session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": kwargs.pop('stream', False),
                        **kwargs
                    },
                    timeout=dynamic_timeout
                )
                response.raise_for_status()
                result = response.json()
                
                # Handle different response formats
                if 'response' in result:
                    return result['response']
                elif 'choices' in result:
                    return result['choices'][0]['text']
                else:
                    raise LLMError("Unexpected response format from model")

            except requests.exceptions.Timeout as e:
                error_msg = f"Generation timed out after {dynamic_timeout}s. The prompt may be too complex."
                logger.error(error_msg)
                raise LLMError(error_msg) from e

            except requests.exceptions.ConnectionError as e:
                error_msg = "Connection to Ollama server failed. Please check if the server is running."
                logger.error(error_msg)
                raise LLMError(error_msg) from e

        except Exception as e:
            logger.error(f"Error in generate: {str(e)}")
            raise LLMError(f"Generation failed: {str(e)}")

    def get_embedding(self, text: str, model: str = "bge-small") -> List[float]:
        """Get embeddings for the given text"""
        if not self._initialized:
            self.initialize()

        try:
            # Determine embedding settings
            embed_settings = None
            for model_name, settings in self.model_settings.items():
                if model.lower() in model_name.lower():
                    embed_settings = settings['embeddings']
                    break
            
            if not embed_settings:
                # Use default bge-small settings
                embed_settings = {
                    'dim': 384,
                    'normalized': True
                }

            # Request embedding
            response = self._session.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": model,
                    "prompt": text
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            # Handle different response formats
            if 'embedding' in result:
                embedding = result['embedding']
            elif 'data' in result and len(result['data']) > 0:
                embedding = result['data'][0]['embedding']
            else:
                raise LLMError("No embedding found in response")

            # Validate embedding dimension
            if len(embedding) != embed_settings['dim']:
                raise LLMError(f"Incorrect embedding dimension. Expected {embed_settings['dim']}, got {len(embedding)}")

            return embedding

        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise LLMError(f"Embedding generation failed: {str(e)}")

    def _cleanup(self) -> None:
        """Cleanup resources with proper error handling and GPU memory release"""
        try:
            try:
                # First stop any running model
                self._session.delete(
                    f"{self.base_url}/api/stop",
                    timeout=5
                )
                
                # If GPU was enabled, reset GPU settings and track memory changes
                if self.gpu_enabled:
                    print(f"{Fore.YELLOW}Releasing GPU resources...{Style.RESET_ALL}")
                    initial_free_memory = self.free_gpu_memory
                    
                    # Reset GPU settings
                    self.gpu_enabled = False
                    self.llm_config['gpu_settings']['enabled'] = False
                    self.llm_config['gpu_layers'] = 0
                    
                    # Force model reload to release GPU memory
                    try:
                        self._session.post(
                            f"{self.base_url}/api/pull",
                            json={
                                "name": self.model_name,
                                "parameters": {"gpu_layers": 0}
                            },
                            timeout=self.llm_config.get('timeout', 30)
                        )
                        
                        # Check memory after release
                        self._check_gpu_support()
                        memory_freed = self.free_gpu_memory - initial_free_memory
                        
                        if memory_freed > 0:
                            print(f"{Fore.GREEN}Successfully released {memory_freed:.1f}GB of GPU memory{Style.RESET_ALL}")
                            print(f"{Fore.CYAN}Current free GPU memory: {self.free_gpu_memory:.1f}GB{Style.RESET_ALL}")
                            logger.info(f"GPU memory released: {memory_freed:.1f}GB")
                    except Exception as e:
                        logger.error(f"Error releasing GPU memory: {str(e)}")
                        
            except requests.RequestException as e:
                logger.warning(f"Error stopping Ollama model: {str(e)}")
                
            if self._session:
                self._session.close()
                
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()
