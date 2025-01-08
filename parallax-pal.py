import os
import sys
import re
import logging
from io import StringIO
from typing import Dict, List, Tuple, Union, Optional
from colorama import init, Fore, Style, Back
from llm_wrapper import LLMWrapper, LLMError
from llm_response_parser import UltimateLLMResponseParser
from search_engine import EnhancedSelfImprovingSearch, SearchError
from web_scraper import MultiSearcher, WebScraperError, get_web_content, can_fetch
from contextlib import contextmanager
import threading
import time
import questionary
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.table import Table
from urllib.parse import urlparse

# Initialize colorama
init()

# Set up logging with proper directory handling
log_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_directory, exist_ok=True)

# Configure logger with proper formatting and handling
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_file = os.path.join(log_directory, 'parallax_pal.log')
file_handler = logging.FileHandler(log_file, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
file_handler.setFormatter(formatter)
logger.handlers = []
logger.addHandler(file_handler)
logger.propagate = False

# Suppress other loggers
for name in ['root', 'duckduckgo_search', 'requests', 'urllib3']:
    other_logger = logging.getLogger(name)
    other_logger.setLevel(logging.WARNING)
    other_logger.handlers = []
    other_logger.propagate = False

class LoadingAnimation:
    def __init__(self, message: str):
        self.message = message
        self.is_running = False
        self.console = Console()

    def start(self):
        self.is_running = True
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        )
        self.progress.start()
        self.task = self.progress.add_task(self.message, total=None)

    def stop(self):
        self.is_running = False
        self.progress.stop()

class OutputRedirector:
    """Context manager for redirecting stdout and stderr with proper cleanup"""
    def __init__(self, stream: Optional[StringIO] = None):
        self.stream = stream or StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def __enter__(self) -> StringIO:
        sys.stdout = self.stream
        sys.stderr = self.stream
        return self.stream

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        if exc_type is not None:
            logger.error(f"Error in OutputRedirector: {str(exc_val)}")

class ParallaxPalError(Exception):
    """Base exception for ParallaxPal errors"""
    pass

class ParallaxPal:
    def __init__(self, llm: LLMWrapper, parser: UltimateLLMResponseParser, max_attempts: int = 5):
        """Initialize with proper error handling and validation"""
        if not isinstance(llm, LLMWrapper):
            raise ParallaxPalError("Invalid LLM wrapper provided")
        if not isinstance(parser, UltimateLLMResponseParser):
            raise ParallaxPalError("Invalid parser provided")
        if not isinstance(max_attempts, int) or max_attempts < 1:
            raise ParallaxPalError("Invalid max_attempts value")

        self.llm = llm
        self.parser = parser
        self.max_attempts = max_attempts
        self.continuous_mode = False
        self.paused = False
        self.current_topic: Optional[str] = None
        self.original_topic: Optional[str] = None
        self.search_engine = EnhancedSelfImprovingSearch(llm, parser)
        self.console = Console()
        
        logger.info("ParallaxPal initialized successfully")

    def display_search_results(self, results: List[Dict]) -> None:
        """Display search results in a rich formatted table"""
        table = Table(show_header=True, header_style="bold magenta", show_lines=True)
        table.add_column("Title", style="cyan", no_wrap=False)
        table.add_column("URL", style="blue")
        table.add_column("Summary", style="green")

        for result in results:
            url = result.get('href', '')
            domain = urlparse(url).netloc
            title = result.get('title', 'No title')
            summary = result.get('body', 'No description available')
            
            # Truncate long text
            if len(title) > 70:
                title = title[:67] + "..."
            if len(summary) > 100:
                summary = summary[:97] + "..."
                
            table.add_row(title, domain, summary)

        self.console.print(Panel(table, title="Search Results", border_style="blue"))

    def display_scraped_content(self, content: Dict[str, str]) -> None:
        """Display scraped content in a formatted panel"""
        if not content:
            return

        for url, text in content.items():
            domain = urlparse(url).netloc
            preview = text[:200] + "..." if len(text) > 200 else text
            self.console.print(Panel(
                Text(preview, style="green"),
                title=f"Content from {domain}",
                border_style="cyan"
            ))

    def select_model(self) -> None:
        """Initialize LLM - model selection is handled by LLMWrapper"""
        # Skip model selection as it's handled by LLMWrapper
        self.console.print("[bold cyan]Model selection is handled during LLM initialization[/bold cyan]")

    def formulate_followup_query(self, query: str, is_followup: bool = False) -> str:
        """Formulate or refine the search query"""
        if not is_followup:
            return query.strip()
            
        try:
            prompt = f"""
            Based on this query: "{query}"
            
            Formulate a clear and specific search query that will help find relevant information.
            Keep the query concise (2-5 words) and focused on the key concepts.
            
            Return only the search query, nothing else.
            """
            
            formulated = self.llm.generate(prompt, max_tokens=50).strip()
            return formulated if formulated else query
            
        except Exception as e:
            logger.error(f"Error formulating query: {str(e)}")
            return query

    def process_user_query(self, query: str, is_followup: bool = False) -> None:
        """Process a research query with improved visualization"""
        try:
            if not isinstance(query, str):
                raise ParallaxPalError("Query must be a string")

            if not query.strip():
                raise ParallaxPalError("Query cannot be empty")

            if query.startswith('@'):
                self.continuous_mode = True
                query = query[1:].strip()
                self.console.print(Panel(
                    "[bold cyan]Entering Continuous Research Mode[/bold cyan]\n" +
                    "Available commands:\n" +
                    "• Press 'P' to pause research\n" +
                    "• Press 'F' to finalize and synthesize findings\n" +
                    "• Press 'Q' to quit",
                    title="Research Controls",
                    border_style="cyan"
                ))

            # Show loading animation for search
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("🔍 Searching the web...", total=None)
                formulated_query = self.formulate_followup_query(query, is_followup)
                if formulated_query != query:
                    self.console.print(f"[yellow]Formulated query: {formulated_query}[/yellow]")
                
                self.current_topic = formulated_query
                results = self.search_engine.perform_search(formulated_query)

            # Display search results
            if results:
                self.display_search_results(results)

            # Show loading animation for content scraping
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("📑 Analyzing content...", total=None)
                selected_urls = self.search_engine.select_relevant_pages(results, formulated_query)
                scraped_content = self.search_engine.scrape_content(selected_urls)

            # Display scraped content
            if scraped_content:
                self.display_scraped_content(scraped_content)

            # Show loading animation for LLM processing
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("🤖 Synthesizing information...", total=None)
                result = self.search_engine.search_and_improve(formulated_query)

            # Display final result
            self.console.print(Panel(
                Markdown(result),
                title="Research Result",
                border_style="green"
            ))

            if self.continuous_mode and not self.paused:
                self.console.print("\n[bold cyan]Available commands: 'P' to pause • 'F' to finalize • 'Q' to quit[/bold cyan]")
                self.generate_followup_questions(result)

        except (ParallaxPalError, SearchError, LLMError, WebScraperError) as e:
            logger.error(f"Error processing query: {str(e)}")
            self.console.print(f"[bold red]Error: {str(e)}[/bold red]")
        except Exception as e:
            logger.error(f"Unexpected error in process_user_query: {str(e)}")
            self.console.print("[bold red]An unexpected error occurred. Please try again.[/bold red]")

    def generate_followup_questions(self, result: str) -> None:
        """Generate follow-up questions with improved visualization"""
        try:
            if not self.original_topic:
                logger.warning("No original topic found for follow-up questions")
                return

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("🤔 Generating follow-up questions...", total=None)
                
                prompt = f"""Based on the original topic "{self.original_topic}" and this research result:
{result}

Generate 3 follow-up questions that would deepen our understanding of the original topic.
Each question should:
1. Explore a different aspect of the topic
2. Stay focused on the original subject
3. Build upon the current findings
4. Help uncover new insights

Format each question with an @ prefix on a new line."""

                follow_up = self.llm.generate(
                    prompt,
                    max_tokens=200,
                    temperature=0.7
                )

            questions = [q.strip() for q in follow_up.split('\n') if q.strip().startswith('@')]
            if questions:
                table = Table(show_header=True, header_style="bold yellow")
                table.add_column("Follow-up Questions")
                for question in questions:
                    table.add_row(question)
                self.console.print(table)

                next_question = questions[0].strip()
                self.console.print(f"\n[bold cyan]Continuing with first follow-up question... (Press 'p' to pause)[/bold cyan]")
                self.current_topic = next_question[1:].strip()

        except LLMError as e:
            logger.error(f"Error generating follow-up questions: {str(e)}")
            self.console.print(f"[bold red]Error generating follow-up questions: {str(e)}[/bold red]")
        except Exception as e:
            logger.error(f"Unexpected error in generate_followup_questions: {str(e)}")
            self.console.print("[bold red]Error generating follow-up questions. Continuing with current topic.[/bold red]")

    def handle_command(self, cmd: str) -> bool:
        """Handle user commands and return True if command was handled"""
        if not cmd:
            return False
            
        cmd = cmd.lower()
        if cmd == 'h':
            self.show_help()
            return True
        elif cmd == 'q':
            return True
        elif cmd == 'p':
            self.paused = True
            self.console.print(Panel(
                "[bold yellow]Research Paused[/bold yellow]\n" +
                "• Press 'C' to continue research\n" +
                "• Press 'F' to finalize and synthesize findings\n" +
                "• Press 'Q' to quit",
                title="Pause Menu",
                border_style="yellow"
            ))
            return True
        elif cmd == 'c':
            self.paused = False
            self.console.print("[green]Research resumed.[/green]")
            return True
        elif cmd == 'm':
            self.llm.switch_model()
            return True
        elif cmd == 'g':
            self.llm.toggle_gpu()
            return True
        elif cmd == 'f':
            self.console.print("[yellow]Finalizing research...[/yellow]")
            self.finalize_research()
            return True
            
        return False

    def finalize_research(self) -> None:
        """Synthesize all findings from the continuous research session"""
        if not self.continuous_mode:
            self.console.print("[yellow]No continuous research session to finalize.[/yellow]")
            return
            
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("🤖 Synthesizing all research findings...", total=None)
                
                prompt = f"""Based on the original topic "{self.original_topic}" and current topic "{self.current_topic}",
                synthesize the key findings and insights from this research session.
                Focus on:
                1. Main discoveries and conclusions
                2. Connections between different aspects explored
                3. Potential implications or applications
                4. Areas that might need further investigation
                
                Format the response as a comprehensive research summary."""
                
                synthesis = self.llm.generate(
                    prompt,
                    max_tokens=500,
                    temperature=0.7
                )
            
            self.console.print(Panel(
                Markdown(synthesis),
                title="Research Summary",
                border_style="green"
            ))
            
            # Reset continuous mode after finalization
            self.continuous_mode = False
            self.paused = False
            
        except Exception as e:
            logger.error(f"Error finalizing research: {str(e)}")
            self.console.print("[bold red]Error synthesizing research findings.[/bold red]")

    def show_help(self) -> None:
        """Display help information with improved formatting"""
        help_table = Table(show_header=True, header_style="bold magenta")
        help_table.add_column("Command", style="yellow")
        help_table.add_column("Description", style="cyan")
        
        help_table.add_row("q", "Quit ParallaxPal")
        help_table.add_row("p", "Pause continuous research")
        help_table.add_row("c", "Continue research")
        help_table.add_row("f", "Finalize and synthesize research findings")
        help_table.add_row("h", "Show this help message")
        help_table.add_row("m", "Switch LLM model")
        help_table.add_row("g", "Toggle GPU acceleration")
        help_table.add_row("@", "Start continuous research mode")
        
        self.console.print(Panel(help_table, title="Available Commands", border_style="blue"))

def setup_keyboard_handler():
    """Set up platform-specific keyboard input handler"""
    try:
        if sys.platform == 'win32':
            import msvcrt
            return lambda: msvcrt.getch().decode().lower() if msvcrt.kbhit() else None
        else:
            import tty
            import termios
            
            def unix_handler():
                if sys.stdin.isatty():
                    fd = sys.stdin.fileno()
                    old_settings = termios.tcgetattr(fd)
                    try:
                        tty.setraw(sys.stdin.fileno())
                        ch = sys.stdin.read(1)
                        return ch.lower() if ch else None
                    finally:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                return None
                
            return unix_handler
            
    except ImportError as e:
        logger.error(f"Error setting up keyboard handler: {str(e)}")
        return lambda: None

def main():
    """Main entry point with improved visualization"""
    try:
        console = Console()
        
        # Show welcome animation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("🚀 Launching Parallax Pal...", total=None)
            time.sleep(1)  # Short pause for effect
            
        console.print(f"""{Fore.CYAN}
     ____                  _ _                ____       _
    |  _ \ __ _ _ __ __ _| | | __ ___  __  |  _ \ __ _| |
    | |_) / _` | '__/ _` | | |/ _` \ \/ /  | |_) / _` | |
    |  __/ (_| | | | (_| | | | (_| |>  <   |  __/ (_| | |
    |_|   \__,_|_|  \__,_|_|_|\__,_/_/\_\  |_|   \__,_|_|
        {Style.RESET_ALL}""")

        llm = LLMWrapper()
        parser = UltimateLLMResponseParser()
        pal = ParallaxPal(llm, parser)
        get_key = setup_keyboard_handler()

        # Initial model selection
        pal.select_model()

        console.print("[bold green]System initialized. Your research companion is ready![/bold green]")
        pal.show_help()
        console.print("[bold cyan]Note: Use @ for in-depth research with follow-up questions (e.g. '@quantum computing')[/bold cyan]")
        console.print("[bold cyan]      Or enter query directly for single-topic research (e.g. 'quantum computing')[/bold cyan]\n")

        while True:
            try:
                if not pal.continuous_mode or pal.paused:
                    console.print("[bold green]Enter your query (or @ for continuous mode):[/bold green]")
                    user_input = input().strip()

                    if pal.handle_command(user_input):
                        if user_input.lower() == 'q':
                            break
                        continue

                    if not user_input:
                        continue

                    pal.process_user_query(user_input, is_followup=False)
                else:
                    key = get_key()
                    if key in ['q', 'p', 'f']:
                        if pal.handle_command(key):
                            if key == 'q':
                                break
                        continue

                    pal.process_user_query(pal.current_topic, is_followup=True)

            except KeyboardInterrupt:
                console.print("\n[yellow]Operation cancelled. Ready for next topic.[/yellow]")
                pal.continuous_mode = False
                pal.paused = False
                continue
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                console.print("[bold red]An error occurred. Please try again.[/bold red]")
                continue

    except KeyboardInterrupt:
        console.print("\n[yellow]Research system shutting down.[/yellow]")
    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}", exc_info=True)
        console.print(f"[bold red]Critical error: {str(e)}[/bold red]")
    finally:
        logger.info("ParallaxPal shutting down")

if __name__ == "__main__":
    main()
