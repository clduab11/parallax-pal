import os
import sys
import re
import logging
import msvcrt
from io import StringIO
from typing import Dict, List, Tuple, Union, Optional
from colorama import init, Fore, Style, Back
from dotenv import load_dotenv
from llm_wrapper import LLMWrapper, LLMError
from llm_response_parser import UltimateLLMResponseParser
from search_engine import EnhancedSelfImprovingSearch, SearchError
from web_scraper import MultiSearcher, WebScraperError, get_web_content, can_fetch
from contextlib import contextmanager
import threading
import time
import questionary
from rich.console import Console
from rich.progress import Progress, TextColumn
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.table import Table
from urllib.parse import urlparse

# Windows-specific imports and fallbacks
if os.name == 'nt':
    import msvcrt
else:
    import termios
    import tty

# Load environment variables from .env file
load_dotenv()

# Initialize colorama with strip=False to preserve ANSI sequences
init(strip=False)

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.debug("Starting ParallaxPal initialization...")

# Configure Windows console for UTF-8
if sys.platform == 'win32':
    logger.debug("Configuring Windows console...")
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleCP(65001)
    kernel32.SetConsoleOutputCP(65001)
    os.system('') # Enable ANSI escape sequences
    logger.debug("Windows console configured")

logger.debug("Initializing main components...")

def main():
    try:
        from llm_wrapper import LLMWrapper, LLMError
        from search_engine import EnhancedSelfImprovingSearch
        # Import research manager with Windows-specific handling
        if os.name == 'nt':
            # Use simplified input handling for Windows
            from research_manager import ResearchManager
            # Override the get_initial_input method for Windows
            def get_windows_input():
                print(f"{Fore.GREEN}📝 Enter your message (Press CTRL+Z and Enter to submit):{Style.RESET_ALL}")
                lines = []
                try:
                    while True:
                        try:
                            line = input()
                            if line:
                                lines.append(line)
                        except EOFError:  # CTRL+Z on Windows
                            break
                except KeyboardInterrupt:
                    print("\nOperation cancelled")
                    sys.exit(0)
                return " ".join(lines).strip()
            
            # Patch the ResearchManager class
            ResearchManager.get_initial_input = staticmethod(get_windows_input)
        else:
            from research_manager import ResearchManager
        
        from llm_response_parser import UltimateLLMResponseParser
        
        logger.debug("Starting main function")
        console = Console()
        
        try:
            logger.debug("Initializing LLM wrapper...")
            llm = LLMWrapper()
            logger.debug("LLM wrapper initialized successfully")
        except LLMError as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            console.print("[red]Error: Could not connect to Ollama. Please ensure Docker is running and Ollama container is active.[/red]")
            console.print("[yellow]You can start Ollama with: docker run -d -p 11434:11434 ollama/ollama[/yellow]")
            return
            
        logger.debug("Initializing components...")
        parser = UltimateLLMResponseParser()
        search_engine = EnhancedSelfImprovingSearch(llm, parser)
        manager = ResearchManager(llm, parser, search_engine)
        
        console.print("[green]ParallaxPal initialized successfully![/green]")
        console.print("[cyan]Enter your research query (starting with @):[/cyan]")
        
        try:
            query = input().strip()
            if not query.startswith('@'):
                console.print("[red]Query must start with @[/red]")
                return
                
            query = query[1:]  # Remove @ prefix
            manager.start_research(query)
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled by user[/yellow]")
        except Exception as e:
            logger.error(f"Error during research: {str(e)}")
            console.print(f"[red]An error occurred: {str(e)}[/red]")
            
    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        print(f"Critical error: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        print("\nApplication terminated by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        print(f"\nUnhandled error: {str(e)}")
    finally:
        # Ensure proper cleanup
        logger.debug("Performing final cleanup...")
        try:
            if 'llm' in locals():
                llm._cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
