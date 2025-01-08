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

def display_ascii_art():
    art = """
    ██████╗  █████╗ ██████╗  █████╗ ██╗     ██╗      █████╗ ██╗  ██╗██████╗  █████╗ ██╗
    ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██║     ██║     ██╔══██╗╚██╗██╔╝██╔══██╗██╔══██╗██║
    ██████╔╝███████║██████╔╝███████║██║     ██║     ███████║ ╚███╔╝ ██████╔╝███████║██║
    ██╔═══╝ ██╔══██║██╔══██╗██╔══██║██║     ██║     ██╔══██║ ██╔██╗ ██╔═══╝ ██╔══██║██║
    ██║     ██║  ██║██║  ██║██║  ██║███████╗███████╗██║  ██║██╔╝ ██╗██║     ██║  ██║███████╗
    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝
    ═══════════════════════════ Your AI Research Companion ═══════════════════════════
    """
    print(art)

def main():
    try:
        display_ascii_art()
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
        
        # Get console width for panel sizing
        console_width = console.width or 80
        panel_width = min(max(60, console_width - 4), 120)  # Keep width between 60 and 120 chars

        # Create welcome message with dynamic width
        welcome_text = Text()
        welcome_text.append("🤖 Welcome to ParallaxPal - Your AI Research Companion\n\n", style="bright_white")
        welcome_text.append("🎮 Controls:\n", style="cyan")
        welcome_text.append("• 'g' - Toggle GPU acceleration\n", style="yellow")
        welcome_text.append("• 'q' - Quit current research (saves progress)\n", style="yellow")
        welcome_text.append("• 'p' - Pause research and assess progress\n", style="yellow")
        welcome_text.append("• 's' - Show current research status\n\n", style="yellow")
        welcome_text.append("📝 Query Format:\n", style="cyan")
        welcome_text.append("• Start with @ for continuous research mode\n")
        welcome_text.append("• Regular query for single iteration mode\n\n")
        welcome_text.append("🚀 System is ready! Enter your research query...", style="green")

        # Display welcome message and controls with enhanced styling and dynamic width
        welcome_panel = Panel(
            welcome_text,
            title="[bold cyan]🔍 ParallaxPal Controls[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
            width=panel_width
        )
        console.print(welcome_panel)
        
        try:
            while True:
                # Handle keyboard input character by character
                query = ""
                print(f"{Fore.GREEN}📝 Enter your research query (Press Enter to submit):{Style.RESET_ALL}")
                while True:
                    if msvcrt.kbhit():
                        char = msvcrt.getch()
                        # Check for Enter key (carriage return)
                        if char in [b'\r', b'\n']:
                            print()  # Move to next line
                            break
                        # Check for backspace
                        elif char == b'\x08':
                            if query:
                                query = query[:-1]
                                # Clear the last character from console
                                print('\b \b', end='', flush=True)
                        # Check for special keys only when no query is being typed
                        elif not query and char.decode(errors='ignore').lower() == 'g':
                            print("\nToggling GPU acceleration...")
                            if llm.toggle_gpu():
                                print(f"{Fore.GREEN}GPU settings updated successfully{Style.RESET_ALL}")
                            print(f"{Fore.GREEN}📝 Enter your research query (Press Enter to submit):{Style.RESET_ALL}")
                        # Regular character input
                        elif char.isascii():
                            query += char.decode()
                            print(char.decode(), end='', flush=True)

                query = query.strip()
                
                continuous_mode = query.startswith('@')
                if continuous_mode:
                    query = query[1:]  # Remove @ prefix
                
                # Start research and handle summary display
                manager.start_research(query, continuous_mode)
                
                # Get and display the research summary
                console.print("\n🔄 [cyan]Synthesizing research findings...[/cyan]")
                summary = manager.terminate_research()
                
                if summary:
                    # Create a styled panel for the summary
                    summary_panel = Panel(
                        Text(summary, style="bright_white"),
                        title="[bold cyan]📊 Research Summary[/bold cyan]",
                        border_style="cyan",
                        padding=(1, 2)
                    )
                    console.print(summary_panel)
                
                # Ask if user wants to start a new research session
                if questionary.confirm("Would you like to start a new research session?").ask():
                    continue
                break
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Research interrupted - Generating final summary...[/yellow]")
            try:
                summary = manager.terminate_research()
                if summary:
                    console.print(Panel(
                        Text(summary, style="bright_white"),
                        title="[bold yellow]Final Summary (Interrupted)[/bold yellow]",
                        border_style="yellow",
                        padding=(1, 2)
                    ))
            except Exception as e:
                logger.error(f"Error generating final summary: {str(e)}")
                console.print("[red]Could not generate final summary[/red]")
        except Exception as e:
            logger.error(f"Error during research: {str(e)}")
            console.print(Panel(
                f"[red]An error occurred during research:[/red]\n{str(e)}",
                title="[bold red]Error[/bold red]",
                border_style="red"
            ))
            
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
