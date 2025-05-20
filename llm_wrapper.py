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
        """Initialize Ollama with enhanced error handling and GPU optimization"""
        try:
            # Use the configured base URL or default to Docker host
            self.base_url = self.llm_config.get('base_url', 'http://host.docker.internal:11434')
            
            # For non-Docker environments, try localhost as fallback
            if 'host.docker.internal' in self.base_url and not self._check_docker_running():
                logger.info("Switching to localhost for non-Docker environment")
                self.base_url = self.base_url.replace('host.docker.internal', 'localhost')
            
            logger.info(f"Using Ollama endpoint: {self.base_url}")
            
            # Fetch available models
            self.available_models = self._fetch_ollama_models()
            
            if not self.available_models:
                logger.warning("No Ollama models available - attempting to pull default model")
                self._pull_default_model()
                self.available_models = self._fetch_ollama_models()
                if not self.available_models:
                    raise LLMError("No Ollama models available after attempting to pull default model")
            
            # Only show model selection if no model is selected
            if not self.model_name:
                if 'dolphin-phi' in self.available_models:
                    # Set default model if available
                    self.model_name = 'dolphin-phi'
                    logger.info(f"Automatically selected model: {self.model_name}")
                else:
                    # Use first available model if default isn't available
                    self.model_name = self.available_models[0]
                    logger.info(f"Using first available model: {self.model_name}")
                
                self._display_model_selection()
            elif self.model_name not in self.available_models:
                logger.warning(f"Selected model {self.model_name} not available, attempting to pull it")
                try:
                    self._pull_specific_model(self.model_name)
                    # Refresh model list
                    self.available_models = self._fetch_ollama_models()
                    if self.model_name not in self.available_models:
                        raise LLMError(f"Failed to pull selected model {self.model_name}")
                except Exception as e:
                    logger.error(f"Failed to pull model {self.model_name}: {str(e)}")
                    # Fall back to available model
                    if self.available_models:
                        self.model_name = self.available_models[0]
                        logger.info(f"Falling back to available model: {self.model_name}")
                    else:
                        raise LLMError("No models available")
            
            # Configure model-specific settings
            self.configure_model_settings(self.model_name)
            
            # Configure GPU settings with improved detection and memory management
            self._check_gpu_support()
            
            # Stop any running model
            try:
                self._session.delete(f"{self.base_url}/api/stop", timeout=5)
            except Exception as e:
                logger.warning(f"Error stopping model: {str(e)}")
            
            # Prepare model configuration with optimized settings
            model_config = {
                "name": self.model_name,
                "parameters": {
                    "context_length": self.llm_config['n_ctx'],  # Set context window
                    "num_thread": os.cpu_count() or 4  # Use available CPU cores
                }
            }
            
            # Apply GPU settings if available and enabled
            if self.gpu_available and self.gpu_enabled:
                gpu_layers = self._calculate_optimal_gpu_layers()
                model_config["parameters"]["gpu_layers"] = gpu_layers
                
                logger.info(f"Enabling GPU acceleration with {gpu_layers} layers")
                print(f"{Fore.GREEN}Enabling GPU acceleration with {gpu_layers} layers{Style.RESET_ALL}")
                
                # Set memory limit if configured
                if self.llm_config['gpu_settings'].get('memory_limit'):
                    # Calculate safe memory limit (90% of free memory, converted to MB)
                    safe_memory_limit = int(min(
                        self.llm_config['gpu_settings']['memory_limit'],
                        self.free_gpu_memory * 0.9 * 1024  # Convert GB to MB
                    ))
                    
                    if safe_memory_limit > 0:
                        model_config["parameters"]["gpu_memory_limit"] = safe_memory_limit
                        logger.info(f"Setting GPU memory limit to {safe_memory_limit}MB")
            else:
                model_config["parameters"]["gpu_layers"] = 0
                if not self.gpu_available:
                    logger.info("No GPU available, using CPU only")
                elif not self.gpu_enabled:
                    logger.info("GPU available but disabled, using CPU only")
            
            # Log initialization details
            logger.info(f"Initializing model with {self.llm_config['n_ctx']:,} token context window")
            print(f"{Fore.CYAN}Initializing model '{self.model_name}' with {self.llm_config['n_ctx']:,} token context window{Style.RESET_ALL}")
            
            # Initialize model in background with appropriate timeout
            try:
                # Calculate dynamic timeout based on model size and operation
                size_factor = 1.0
                if '70b' in self.model_name.lower():
                    size_factor = 10.0
                elif '34b' in self.model_name.lower():
                    size_factor = 5.0
                elif '13b' in self.model_name.lower():
                    size_factor = 3.0
                elif '7b' in self.model_name.lower():
                    size_factor = 2.0
                
                pull_timeout = max(30, int(self.llm_config.get('timeout', 30) * size_factor))
                
                print(f"{Fore.YELLOW}Initializing model (timeout: {pull_timeout}s)...{Style.RESET_ALL}")
                response = self._session.post(
                    f"{self.base_url}/api/pull",
                    json=model_config,
                    timeout=pull_timeout
                )
                response.raise_for_status()
                
                print(f"{Fore.GREEN}Model initialized successfully{Style.RESET_ALL}")
                logger.info(f"Model {self.model_name} initialized successfully")
                
            except requests.exceptions.Timeout:
                logger.error(f"Timeout initializing model {self.model_name}")
                print(f"{Fore.RED}Timeout initializing model. You may need to increase the timeout setting.{Style.RESET_ALL}")
                raise LLMError(f"Timeout initializing model {self.model_name}")
            except Exception as e:
                logger.error(f"Error initializing model: {str(e)}")
                raise LLMError(f"Model initialization failed: {str(e)}")
            
        except Exception as e:
            logger.error(f"Ollama initialization failed: {str(e)}")
            raise LLMError(f"Ollama initialization failed: {str(e)}")
    
    def _check_docker_running(self) -> bool:
        """Check if Docker is running"""
        try:
            docker_check = os.system("docker ps > /dev/null 2>&1")
            return docker_check == 0
        except Exception:
            return False
            
    def _pull_specific_model(self, model_name: str) -> None:
        """Pull a specific model from Ollama registry"""
        try:
            print(f"{Fore.CYAN}Pulling model {model_name} (this may take several minutes)...{Style.RESET_ALL}")
            
            # Calculate timeout based on model size
            size_factor = 1.0
            if '70b' in model_name.lower():
                size_factor = 10.0
            elif '34b' in model_name.lower():
                size_factor = 5.0
            elif '13b' in model_name.lower():
                size_factor = 3.0
            elif '7b' in model_name.lower():
                size_factor = 2.0
                
            pull_timeout = max(60, int(self.llm_config.get('timeout', 60) * size_factor))
            
            response = self._session.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=pull_timeout
            )
            response.raise_for_status()
            print(f"{Fore.GREEN}Model {model_name} pulled successfully{Style.RESET_ALL}")
            logger.info(f"Model {model_name} pulled successfully")
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {str(e)}")
            raise LLMError(f"Failed to pull model {model_name}: {str(e)}")

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
        """Check GPU support with enhanced cross-platform detection and error handling"""
        self.gpu_available = False
        self.gpu_enabled = False
        self.gpu_name = "Unknown"
        self.total_gpu_memory = 0.0
        self.free_gpu_memory = 0.0
        self.gpu_vendor = "Unknown"
        
        # Try NVIDIA GPU detection first
        try:
            # Check if nvidia-smi exists and can be executed
            nvidia_smi_check = os.system("nvidia-smi --help > /dev/null 2>&1")
            if nvidia_smi_check == 0:
                # NVIDIA GPU detected, get detailed information
                gpu_info = os.popen('nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader').read().strip()
                
                if gpu_info:
                    gpu_lines = gpu_info.split('\n')
                    for gpu_line in gpu_lines:
                        parts = gpu_line.split(',')
                        if len(parts) >= 3:
                            # Get info from the first GPU for now (multi-GPU support could be added later)
                            self.gpu_name = parts[0].strip()
                            self.gpu_vendor = "NVIDIA"
                            
                            # Parse memory info
                            try:
                                total_memory_str = parts[1].strip()
                                free_memory_str = parts[2].strip()
                                
                                # Extract numeric values and convert MiB to GB
                                total_memory_val = float(total_memory_str.split()[0])
                                free_memory_val = float(free_memory_str.split()[0])
                                
                                # Convert MiB to GB (1024 MiB = 1 GB)
                                self.total_gpu_memory = total_memory_val / 1024
                                self.free_gpu_memory = free_memory_val / 1024
                                
                                # Get driver version if available
                                driver_version = parts[3].strip() if len(parts) > 3 else "Unknown"
                                
                                self.gpu_available = True
                                logger.info(f"NVIDIA GPU detected: {self.gpu_name}")
                                logger.info(f"Driver: {driver_version}")
                                logger.info(f"Total GPU memory: {self.total_gpu_memory:.2f}GB")
                                logger.info(f"Free GPU memory: {self.free_gpu_memory:.2f}GB")
                                
                                # Safety check - ensure we have sufficient free memory
                                # At least 1GB of free memory is required
                                if self.free_gpu_memory < 1.0:
                                    logger.warning(f"Low GPU memory: {self.free_gpu_memory:.2f}GB free - may cause issues")
                                
                                break  # Use the first GPU detected
                            except (ValueError, IndexError) as e:
                                logger.error(f"Error parsing GPU memory info: {str(e)}")
                        else:
                            logger.error(f"Invalid GPU info format: {gpu_line}")
            else:
                logger.info("nvidia-smi not found, checking for other GPU types...")
        except Exception as e:
            logger.error(f"Error checking for NVIDIA GPU: {str(e)}")
        
        # If no NVIDIA GPU found, try checking for Apple Metal support on macOS
        if not self.gpu_available and sys.platform == 'darwin':
            try:
                # Check for Metal support on macOS
                metal_check = os.system("system_profiler SPDisplaysDataType | grep 'Metal: Supported' > /dev/null 2>&1")
                if metal_check == 0:
                    # Metal is supported, get more information
                    gpu_info = os.popen("system_profiler SPDisplaysDataType | grep -A 10 'Metal:'").read().strip()
                    
                    # Try to extract GPU name
                    gpu_name_match = re.search(r'Chipset Model: (.+)', gpu_info)
                    if gpu_name_match:
                        self.gpu_name = gpu_name_match.group(1).strip()
                    
                    # For Metal, we can't easily get memory details, so estimate
                    # by checking total system memory and allocating 30%
                    try:
                        mem_info = os.popen("sysctl hw.memsize").read().strip()
                        mem_match = re.search(r'hw.memsize: (\d+)', mem_info)
                        if mem_match:
                            total_system_memory = float(mem_match.group(1)) / (1024**3)  # Convert bytes to GB
                            # Estimate GPU memory as 30% of system memory
                            estimated_gpu_memory = total_system_memory * 0.3
                            self.total_gpu_memory = estimated_gpu_memory
                            self.free_gpu_memory = estimated_gpu_memory * 0.8  # Assume 80% is free
                            
                            self.gpu_available = True
                            self.gpu_vendor = "Apple"
                            
                            logger.info(f"Apple Metal GPU detected: {self.gpu_name}")
                            logger.info(f"Estimated GPU memory: {self.total_gpu_memory:.2f}GB")
                            logger.info(f"Estimated free GPU memory: {self.free_gpu_memory:.2f}GB")
                    except Exception as e:
                        logger.error(f"Error estimating Apple GPU memory: {str(e)}")
            except Exception as e:
                logger.error(f"Error checking for Apple Metal GPU: {str(e)}")
        
        # Check for other GPU types here if needed in the future
        
        # Set GPU enabled state based on config and availability
        if self.gpu_available:
            self.gpu_enabled = self.llm_config['gpu_settings']['enabled']
            if self.gpu_enabled:
                logger.info("GPU acceleration enabled")
            else:
                logger.info("GPU acceleration available but disabled")
            
            # Calculate optimal GPU layers based on available memory
            if self.gpu_enabled:
                recommended_layers = self._calculate_optimal_gpu_layers()
                current_layers = self.llm_config.get('gpu_layers', 0)
                
                if current_layers <= 0 or current_layers > recommended_layers:
                    logger.info(f"Adjusting GPU layers from {current_layers} to {recommended_layers}")
                    self.llm_config['gpu_layers'] = recommended_layers
        else:
            logger.info("No compatible GPU detected")
            # Ensure GPU is disabled if not available
            self.gpu_enabled = False
            self.llm_config['gpu_settings']['enabled'] = False
            self.llm_config['gpu_layers'] = 0
    
    def _calculate_optimal_gpu_layers(self) -> int:
        """Calculate optimal number of GPU layers based on available memory and model size"""
        if not self.gpu_available or self.free_gpu_memory <= 0:
            return 0
            
        # Base memory requirements for common model sizes
        # This is a rough approximation and may need adjustment based on actual models
        model_size_mapping = {
            # Format: model_keyword: (base_layers, mem_per_layer_gb)
            'tiny': (8, 0.1),
            'small': (16, 0.2),
            'base': (24, 0.25),
            'large': (32, 0.3),
            'llama': (36, 0.4),
            'mistral': (28, 0.3),
            'mpt': (32, 0.35),
            '7b': (32, 0.4),
            '13b': (40, 0.5),
            '34b': (60, 0.7),
            '70b': (80, 0.9)
        }
        
        # Default values if no match is found
        base_layers = 24
        mem_per_layer = 0.25  # GB per layer
        
        # Try to find the best match for the current model
        if self.model_name:
            model_lower = self.model_name.lower()
            for keyword, (layers, mem_req) in model_size_mapping.items():
                if keyword in model_lower:
                    base_layers = layers
                    mem_per_layer = mem_req
                    break
        
        # Reserve 1GB for system operations
        available_memory = max(0, self.free_gpu_memory - 1.0)
        
        # Calculate max layers based on available memory
        max_layers_by_memory = int(available_memory / mem_per_layer)
        
        # Apply constraints from config
        max_layers_config = self.llm_config.get('gpu_settings', {}).get('max_layers', 1000)
        
        # Final calculation: min of base_layers, max_layers_by_memory, and config limit
        optimal_layers = min(base_layers, max_layers_by_memory)
        if max_layers_config > 0:  # Only apply if positive (negative means no limit)
            optimal_layers = min(optimal_layers, max_layers_config)
        
        # Ensure at least 1 layer if GPU is enabled and has memory
        return max(1, optimal_layers) if self.gpu_enabled and available_memory > 0 else 0

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

    def toggle_gpu(self) -> bool:
        """Toggle GPU acceleration on/off
        
        Returns:
            bool: True if operation was successful, False otherwise
        """
        try:
            # Check if GPU is available
            self._check_gpu_support()
            
            if not self.gpu_available:
                logger.warning("No GPU available for toggling")
                return False
                
            # Toggle GPU state
            new_state = not self.gpu_enabled
            
            if new_state:
                # Enabling GPU
                logger.info("Enabling GPU acceleration")
                print(f"{Fore.YELLOW}Enabling GPU acceleration...{Style.RESET_ALL}")
                self.gpu_enabled = True
                self.llm_config['gpu_settings']['enabled'] = True
                
                # Set appropriate GPU layers based on available memory
                gpu_layers = min(
                    self.llm_config.get('gpu_settings', {}).get('max_layers', 100),
                    max(1, int(self.free_gpu_memory / 2))  # Rough estimate: 1 layer per 2GB free memory
                )
                self.llm_config['gpu_layers'] = gpu_layers
                
                logger.info(f"Set GPU layers to {gpu_layers}")
                print(f"{Fore.CYAN}GPU layers set to {gpu_layers}{Style.RESET_ALL}")
            else:
                # Disabling GPU
                logger.info("Disabling GPU acceleration")
                print(f"{Fore.YELLOW}Disabling GPU acceleration...{Style.RESET_ALL}")
                self.gpu_enabled = False
                self.llm_config['gpu_settings']['enabled'] = False
                self.llm_config['gpu_layers'] = 0
            
            # Apply configuration change to model
            try:
                if self.model_name:
                    response = self._session.post(
                        f"{self.base_url}/api/pull",
                        json={
                            "name": self.model_name,
                            "parameters": {
                                "gpu_layers": self.llm_config['gpu_layers']
                            }
                        },
                        timeout=self.llm_config.get('timeout', 30)
                    )
                    response.raise_for_status()
                    
                    logger.info(f"Successfully updated model with GPU layers = {self.llm_config['gpu_layers']}")
                    print(f"{Fore.GREEN}GPU acceleration {'enabled' if new_state else 'disabled'}{Style.RESET_ALL}")
                    
                    if new_state:
                        # Check memory usage after enabling
                        self._check_gpu_support()
                        print(f"{Fore.CYAN}Available GPU memory: {self.free_gpu_memory:.1f}GB{Style.RESET_ALL}")
                    
                    return True
            except Exception as e:
                logger.error(f"Error updating model configuration: {str(e)}")
                print(f"{Fore.RED}Failed to update model: {str(e)}{Style.RESET_ALL}")
                # Revert changes on failure
                self.gpu_enabled = not new_state
                self.llm_config['gpu_settings']['enabled'] = not new_state
                self.llm_config['gpu_layers'] = 0 if not new_state else gpu_layers
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error toggling GPU: {str(e)}")
            return False

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
