import os
import re
import sys
import requests
import json
import logging
import time
from typing import Optional, Generator, Any, Dict
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
        self.available_models = []
        self._initialized = False
        self.gpu_enabled = False
        self._session = requests.Session()  # Session for API calls
        self.llm_config = get_llm_config()  # Start with default Ollama config
        self.base_url = 'http://host.docker.internal:11434'  # Always use local Ollama endpoint
        
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def _fetch_ollama_models(self) -> list:
        """Fetch available models from Ollama server with retries"""
        try:
            response = self._session.get(
                f"{self.base_url}/api/tags",
                timeout=self.llm_config.get('timeout', 30)
            )
            response.raise_for_status()
            models = response.json().get('models', [])
            return [model['name'] for model in models]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Ollama models: {str(e)}")
            raise LLMError(f"Failed to fetch Ollama models: {str(e)}")

    def _parse_model_details(self, model_name: str) -> Dict[str, Any]:
        """Parse model name to extract details"""
        details = {
            'name': model_name,
            'size': 'Unknown',
            'type': 'Unknown',
            'quant': 'Unknown'
        }
        
        # Extract size if available (e.g., 3B, 7B, 14B)
        size_match = re.search(r'(\d+\.?\d*)b', model_name.lower())
        if size_match:
            details['size'] = f"{size_match.group(1)}B"
            
        # Extract quantization (e.g., Q4, Q5, Q6)
        quant_match = re.search(r'[qQ](\d+)_([KM])_([SML])', model_name)
        if quant_match:
            bits, speed, size = quant_match.groups()
            details['quant'] = f"Q{bits}"
            details['speed'] = {'K': 'Fast', 'M': 'Medium'}[speed]
            details['mem'] = {'S': 'Small', 'M': 'Medium', 'L': 'Large'}[size]
            
        return details

    def _check_gpu_support(self) -> None:
        """Check GPU support with proper error handling"""
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

    def _initialize_ollama(self) -> None:
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
                    "context_length": self.llm_config['n_ctx']  # Set 128K context window
                }
            }
            print(f"{Fore.CYAN}Initializing model with {self.llm_config['n_ctx']:,} token context window{Style.RESET_ALL}")
            
            if self.gpu_enabled and self.llm_config['gpu_settings']['memory_limit']:
                model_config["parameters"]["gpu_memory_limit"] = min(
                    self.llm_config['gpu_settings']['memory_limit'],
                    int(self.free_gpu_memory * 0.9 * 1024)
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
                                "parameters": {
                                    "gpu_layers": 0
                                }
                            },
                            timeout=self.llm_config.get('timeout', 360)
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

    def _display_model_selection(self) -> None:
        """Display available Ollama models with enhanced formatting"""
        print(f"\n{Fore.CYAN}Available Ollama Models:{Style.RESET_ALL}")
        print(f"GPU Acceleration: {Fore.GREEN if self.gpu_enabled else Fore.RED}"
              f"{'Enabled' if self.gpu_enabled else 'Disabled'}{Style.RESET_ALL}")
        
        if self.gpu_enabled:
            print(f"GPU Memory: {Fore.CYAN}{self.free_gpu_memory:.1f}GB free "
                  f"of {self.total_gpu_memory:.1f}GB{Style.RESET_ALL}")
        
        print("\nSelect a model by number:")
        
        for i, model in enumerate(self.available_models, 1):
            details = self._parse_model_details(model)
            size_info = f"{Fore.CYAN}[{details['size']}]{Style.RESET_ALL}" if details['size'] != 'Unknown' else ''
            quant_info = f"{Fore.GREEN}[{details['quant']}]{Style.RESET_ALL}" if details['quant'] != 'Unknown' else ''
            
            if 'speed' in details and 'mem' in details:
                perf_info = f"{Fore.YELLOW}[{details['speed']}/{details['mem']}]{Style.RESET_ALL}"
            else:
                perf_info = ''
                
            print(f"{Fore.YELLOW}{i}{Style.RESET_ALL}. {model} {size_info} {quant_info} {perf_info}")

        while True:
            try:
                if os.name == 'nt':  # Windows
                    import msvcrt
                    sys.stdout.write(f"\n{Fore.GREEN}Enter model number (1-{len(self.available_models)}): {Style.RESET_ALL}")
                    sys.stdout.flush()
                    
                    # Read input character by character
                    choice = ""
                    while True:
                        if msvcrt.kbhit():
                            char = msvcrt.getch().decode()
                            if char == '\r':  # Enter key
                                print()  # New line after input
                                break
                            elif char.isdigit():
                                choice += char
                                sys.stdout.write(char)
                                sys.stdout.flush()
                else:  # Unix-like systems
                    sys.stdout.write(f"\n{Fore.GREEN}Enter model number (1-{len(self.available_models)}): {Style.RESET_ALL}")
                    sys.stdout.flush()
                    choice = input().strip()

                if not choice:  # Handle empty input
                    continue

                choice_num = int(choice)
                if 1 <= choice_num <= len(self.available_models):
                    self.model_name = self.available_models[choice_num - 1]
                    print(f"\n{Fore.GREEN}Selected model: {self.model_name}{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED}Invalid choice. Please enter a number between "
                          f"1 and {len(self.available_models)}{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}Invalid input. Please enter a number.{Style.RESET_ALL}")
            except (KeyboardInterrupt, EOFError):
                print(f"\n{Fore.YELLOW}Input cancelled, please try again{Style.RESET_ALL}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Ollama with enhanced error handling and timeout management"""
        if not self._initialized:
            self.initialize()

        try:
            # Calculate approximate token count (rough estimate)
            approx_tokens = len(prompt.split())
            if approx_tokens > self.llm_config.get('n_ctx', 4096):
                raise LLMError(f"Prompt too long (approximately {approx_tokens} tokens)")

            # Calculate dynamic timeout based on prompt length
            base_timeout = self.llm_config.get('timeout', 30)
            dynamic_timeout = max(base_timeout, approx_tokens / 20)  # ~20 tokens per second processing
            
            # Add progress indicator for long generations
            if dynamic_timeout > 30:
                print(f"{Fore.YELLOW}Processing large prompt ({approx_tokens} tokens), this may take a moment...{Style.RESET_ALL}")

            try:
                response = self._session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        **kwargs
                    },
                    timeout=dynamic_timeout
                )
                response.raise_for_status()
                return response.json()['response']

            except requests.exceptions.Timeout:
                # Specific handling for timeout errors
                error_msg = f"Generation timed out after {dynamic_timeout}s. The prompt may be too complex."
                logger.error(error_msg)
                raise LLMError(error_msg)

            except requests.exceptions.ConnectionError:
                # Handle connection issues
                error_msg = "Connection to Ollama server failed. Please check if the server is running."
                logger.error(error_msg)
                raise LLMError(error_msg)

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during generation: {str(e)}")
            raise LLMError(f"Network error: {str(e)}")
        except json.JSONDecodeError:
            error_msg = "Invalid response from Ollama server"
            logger.error(error_msg)
            raise LLMError(error_msg)
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise LLMError(f"Generation failed: {str(e)}")

    def toggle_gpu(self) -> bool:
        """Toggle GPU acceleration with proper validation"""
        if not self.gpu_available:
            print(f"{Fore.RED}No NVIDIA GPU detected on this system{Style.RESET_ALL}")
            return False

        try:
            # Get initial GPU memory state
            initial_free_memory = self.free_gpu_memory

            while True:
                print(f"\n{Fore.CYAN}Current GPU Memory Status:{Style.RESET_ALL}")
                print(f"• Total Memory: {self.total_gpu_memory:.1f}GB")
                print(f"• Free Memory: {self.free_gpu_memory:.1f}GB")
                print(f"• Used Memory: {(self.total_gpu_memory - self.free_gpu_memory):.1f}GB")

                choice = input(f"\n{Fore.GREEN}GPU Acceleration? (Y/N): {Style.RESET_ALL}").lower()
                if choice in ['y', 'n']:
                    # If enabling GPU, first clean up any existing GPU memory
                    if choice == 'y':
                        print(f"\n{Fore.YELLOW}Cleaning up GPU memory...{Style.RESET_ALL}")
                        self._cleanup()  # Release any existing GPU allocations
                        self._check_gpu_support()  # Refresh GPU memory status
                        
                        memory_freed = self.free_gpu_memory - initial_free_memory
                        if memory_freed > 0:
                            print(f"{Fore.GREEN}Freed up {memory_freed:.1f}GB of GPU memory{Style.RESET_ALL}")
                    
                    self.gpu_enabled = (choice == 'y')
                    self.llm_config['gpu_settings']['enabled'] = self.gpu_enabled
                    print(f"\n{Fore.GREEN}GPU Acceleration: {'Enabled' if self.gpu_enabled else 'Disabled'}{Style.RESET_ALL}")
                    break
                print(f"{Fore.RED}Please enter Y or N{Style.RESET_ALL}")

            self._check_gpu_support()
            
            # Show final memory status
            print(f"\n{Fore.CYAN}GPU Memory Status After Change:{Style.RESET_ALL}")
            print(f"• Free Memory: {self.free_gpu_memory:.1f}GB")
            print(f"• Available for ParallaxPal: {(self.free_gpu_memory * 0.9):.1f}GB")
            
            if self.gpu_enabled:
                # Calculate safe memory limit (90% of free memory)
                gpu_mem_limit = int(self.free_gpu_memory * 0.9 * 1024)  # Convert to MB
                self.llm_config['gpu_settings']['memory_limit'] = gpu_mem_limit
                self.llm_config['gpu_layers'] = -1  # Use all available layers
            else:
                self.llm_config['gpu_layers'] = 0

            # Configure model with new GPU settings
            model_config = {
                "name": self.model_name,
                "parameters": {
                    "gpu_layers": self.llm_config['gpu_layers'],
                    "context_length": self.llm_config['n_ctx']  # Maintain 128K context window
                }
            }
            
            if self.gpu_enabled and self.llm_config['gpu_settings']['memory_limit']:
                model_config["parameters"]["gpu_memory_limit"] = self.llm_config['gpu_settings']['memory_limit']

            # Update model configuration in background
            self._session.delete(f"{self.base_url}/api/stop")
            response = self._session.post(
                f"{self.base_url}/api/pull",
                json=model_config,
                timeout=self.llm_config.get('timeout', 30)
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Error updating GPU settings: {str(e)}")
            print(f"{Fore.RED}Failed to update GPU settings: {str(e)}{Style.RESET_ALL}")
            return False

    def set_model(self, model_name: str) -> None:
        """Set the model name"""
        if model_name not in self.available_models:
            raise LLMError(f"Model {model_name} not available")
        self.model_name = model_name
        # Prompt for GPU acceleration after model selection
        self.toggle_gpu()

    def switch_model(self, new_model: str = None) -> bool:
        """Switch to a different model with validation"""
        try:
            if new_model:
                if new_model not in self.available_models:
                    raise LLMError(f"Model {new_model} not available")
                self.model_name = new_model
                print(f"\n{Fore.GREEN}Switched to model: {self.model_name}{Style.RESET_ALL}")
            else:
                self._display_model_selection()
            
            # Update model configuration without reinitialization
            model_config = {
                "name": self.model_name,
                "parameters": {
                    "gpu_layers": self.llm_config['gpu_layers'] if self.gpu_enabled else 0,
                    "context_length": self.llm_config['n_ctx']  # Maintain 128K context window
                }
            }
            print(f"{Fore.CYAN}Configuring model with {self.llm_config['n_ctx']:,} token context window{Style.RESET_ALL}")
            
            if self.gpu_enabled and self.llm_config['gpu_settings']['memory_limit']:
                model_config["parameters"]["gpu_memory_limit"] = min(
                    self.llm_config['gpu_settings']['memory_limit'],
                    int(self.free_gpu_memory * 0.9 * 1024)
                )
            
            # Update model in background
            self._session.delete(f"{self.base_url}/api/stop")
            response = self._session.post(
                f"{self.base_url}/api/pull",
                json=model_config,
                timeout=self.llm_config.get('timeout', 30)
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Error switching model: {str(e)}")
            print(f"{Fore.RED}Failed to switch model: {str(e)}{Style.RESET_ALL}")
            return False
