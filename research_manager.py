#!/usr/bin/env python3
"""
Research Manager - A secure and efficient research automation system
Handles research task management, analysis, and user interaction with enhanced
security, error handling, and performance optimizations.
"""

import os
import sys
import threading
import time
import re
import json
import logging
import curses
import signal
import tempfile
from typing import List, Dict, Set, Optional, Tuple, Union
from dataclasses import dataclass
from queue import Queue
from datetime import datetime
from io import StringIO
from colorama import init, Fore, Style
from threading import Event, Lock
from urllib.parse import urlparse
from pathlib import Path

# Initialize colorama for cross-platform color support
if os.name == 'nt':  # Windows-specific initialization
    init(convert=True, strip=False, wrap=True)
else:
    init()

# Set up logging with rotation
log_directory = 'logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_file = os.path.join(log_directory, 'research_llm.log')
file_handler = logging.FileHandler(log_file, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.handlers = []
logger.addHandler(file_handler)
logger.propagate = False

# Suppress other loggers
for name in logging.root.manager.loggerDict:
    if name != __name__:
        logging.getLogger(name).disabled = True

@dataclass
class ResearchFocus:
    """Represents a specific area of research focus"""
    area: str
    priority: int
    source_query: str = ""
    timestamp: str = ""
    search_queries: List[str] = None

    def __post_init__(self):
        """Initialize with proper validation"""
        if not isinstance(self.area, str):
            raise ValueError("Area must be a string")
        if not isinstance(self.priority, int):
            raise ValueError("Priority must be an integer")
        if not 1 <= self.priority <= 5:
            raise ValueError("Priority must be between 1 and 5")
        
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.search_queries is None:
            self.search_queries = []

@dataclass
class AnalysisResult:
    """Contains the complete analysis result with validation"""
    original_question: str
    focus_areas: List[ResearchFocus]
    raw_response: str
    timestamp: str = ""
    confidence_score: float = 0.0

    def __post_init__(self):
        """Initialize with proper validation"""
        if not isinstance(self.original_question, str):
            raise ValueError("Original question must be a string")
        if not isinstance(self.focus_areas, list):
            raise ValueError("Focus areas must be a list")
        if not all(isinstance(fa, ResearchFocus) for fa in self.focus_areas):
            raise ValueError("All focus areas must be ResearchFocus instances")
        
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class TerminalUI:
    """Manages terminal display with enhanced safety and resource management"""
    def __init__(self):
        self.stdscr = None
        self.input_win = None
        self.output_win = None
        self.status_win = None
        self.max_y = 0
        self.max_x = 0
        self.input_buffer = ""
        self.is_setup = False
        self.old_terminal_settings = None
        self.should_terminate = Event()
        self.shutdown_event = Event()
        self.terminal_lock = threading.Lock()
        self.display_buffer = Queue(maxsize=1000)  # Prevent memory issues

class StrategicAnalysisParser:
    """Enhanced parser with improved pattern matching and validation"""
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.patterns = {
            'priority': re.compile(r'Priority:\s*(\d+)', re.IGNORECASE),
            'area': re.compile(r'^\d+\.\s*(.+?)(?=Priority:|$)', re.IGNORECASE | re.MULTILINE | re.DOTALL)
        }
        self.MAX_FOCUS_AREAS = 5
        self.MIN_AREA_LENGTH = 10
        self.MAX_AREA_LENGTH = 500
        self.VALID_PRIORITIES = set(range(1, 6))

    def parse_analysis(self, llm_response: str) -> Optional[AnalysisResult]:
        """Parse LLM response into a structured analysis result with validation"""
        try:
            # Clean and normalize the response
            cleaned_text = self._clean_text(llm_response)
            
            # Extract original question
            original_question = ""
            question_match = re.search(r'Original Question Analysis:\s*(.*?)(?=\n\n|$)', cleaned_text, re.IGNORECASE | re.DOTALL)
            if question_match:
                original_question = question_match.group(1).strip()
            
            # Extract research areas and priorities
            areas = []
            area_section = re.search(r'Research Gaps?:(.*?)(?=\n\n|$)', cleaned_text, re.IGNORECASE | re.DOTALL)
            if area_section:
                area_text = area_section.group(1)
                area_matches = re.finditer(r'(\d+)\.\s*([^.\n]+?)(?:\s*Priority:\s*(\d+))?(?=\n\d+\.|$)', area_text, re.DOTALL)
                
                for match in area_matches:
                    area = match.group(2).strip()
                    try:
                        priority = int(match.group(3)) if match.group(3) else 3
                        priority = max(1, min(5, priority))  # Clamp between 1-5
                    except (ValueError, TypeError):
                        priority = 3  # Default priority
                    
                    if len(area) >= self.MIN_AREA_LENGTH and len(area) <= self.MAX_AREA_LENGTH:
                        areas.append(ResearchFocus(
                            area=area,
                            priority=priority,
                            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))
            
            # Ensure we don't exceed maximum focus areas
            areas = areas[:self.MAX_FOCUS_AREAS]
            
            # If no valid areas found, return None
            if not areas:
                logger.warning("No valid research areas found in response")
                return None
            
            # Create analysis result
            result = AnalysisResult(
                original_question=original_question,
                focus_areas=areas,
                raw_response=llm_response,
                confidence_score=self._calculate_confidence(original_question, areas)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing analysis: {str(e)}")
            return None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for parsing"""
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = re.sub(r'[\n\r]+', '\n', text)  # Normalize line breaks
        return text.strip()
        
    def _calculate_confidence(self, question: str, areas: List[ResearchFocus]) -> float:
        """Calculate confidence score for the analysis"""
        score = 0.0
        
        # Question quality (0.3)
        if question and len(question.split()) >= 3:
            score += 0.3
            
        # Areas quality (0.7)
        if areas:
            # Number of areas (0.2)
            score += min(len(areas) / self.MAX_FOCUS_AREAS, 1.0) * 0.2
            
            # Priority distribution (0.2)
            priorities = set(area.priority for area in areas)
            score += len(priorities) / 5 * 0.2
            
            # Area content quality (0.3)
            valid_areas = sum(1 for area in areas 
                            if len(area.area.split()) >= 3 
                            and area.priority in self.VALID_PRIORITIES)
            score += (valid_areas / len(areas)) * 0.3
            
        return round(score, 2)

class ResearchManager:
    """Manages research process with enhanced security and performance"""
    def __init__(self, llm_wrapper, parser, search_engine, max_searches_per_cycle: int = 5):
        self.llm = llm_wrapper
        self.parser = parser
        self.search_engine = search_engine
        self.max_searches = max_searches_per_cycle
        
        # Enhanced thread safety
        self.interrupted = threading.Event()
        self.shutdown_event = Event()
        self.research_started = threading.Event()
        self.cleanup_lock = threading.Lock()
        
        # Initialize research state
        self.research_thread = None
        self.thinking = False
        self.research_paused = False
        self.searched_urls: Set[str] = set()
        self.current_focus = None
        self.original_query = ""
        self.focus_areas = []
        self.is_running = False
        
        # File management
        self.summary_dir = os.path.join(os.getcwd(), 'summaries')
        os.makedirs(self.summary_dir, exist_ok=True)
        self.document_path = None
        self.session_files = []
        
        # Initialize UI and parser
        self.ui = TerminalUI()
        self.strategic_parser = StrategicAnalysisParser()
        
        # Setup signal handlers with error handling
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except Exception as e:
            logger.error(f"Failed to set up signal handlers: {e}")
            raise

    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        logger.info(f"Received signal {signum}")
        self.interrupted.set()
        self.shutdown_event.set()
        if self.research_thread and self.research_thread.is_alive():
            logger.info("Stopping research thread...")
            self.terminate_research()

    def start_research(self, query: str, continuous_mode: bool = False) -> None:
        """Start the research process with the given query"""
        if not query or not isinstance(query, str):
            raise ValueError("Invalid research query")

        logger.info(f"Starting research for query: {query}")
        self.original_query = query
        self.is_running = True
        self.research_started.set()

        try:
            # Initialize research state
            self.focus_areas = []
            self.searched_urls.clear()
            self.thinking = True

            # Create research thread
            self.research_thread = threading.Thread(
                target=self._conduct_research,
                args=(query, continuous_mode),
                daemon=True
            )
            self.research_thread.start()

        except Exception as e:
            logger.error(f"Error starting research: {e}")
            self.is_running = False
            self.research_started.clear()
            raise

    def _conduct_research(self, query: str, continuous_mode: bool) -> None:
        """Internal method to conduct the research process"""
        try:
            logger.info(f"Starting research for query: {query}")
            
            # Format query for LLM analysis
            llm_response = self.llm.analyze_query(query)
            if not llm_response:
                raise ValueError("Failed to get LLM analysis")
            
            logger.info(f"LLM Response received:\n{llm_response}")

            # Parse the LLM response
            analysis = self.strategic_parser.parse_analysis(llm_response)
            if not analysis:
                # Don't throw error immediately, try to format the response
                formatted_response = f"""Original Question Analysis: {query}

Research Gaps:
1. Understanding and definition of the topic
   Priority: 1
2. Historical development and discoveries
   Priority: 2
3. Current applications and significance
   Priority: 3
"""
                logger.info(f"Attempting with formatted response:\n{formatted_response}")
                analysis = self.strategic_parser.parse_analysis(formatted_response)
                if not analysis:
                    raise ValueError("Failed to parse LLM response even after formatting")
                    
            if not analysis.focus_areas:
                raise ValueError("No research areas identified")

            logger.info(f"Successfully analyzed query with {len(analysis.focus_areas)} focus areas")

            self.focus_areas = analysis.focus_areas
            
            for focus in self.focus_areas:
                if self.interrupted.is_set():
                    logger.info("Research interrupted by user")
                    break
                    
                self.current_focus = focus
                try:
                    search_results = self.search_engine.search(
                        focus.source_query or query,
                        max_results=self.max_searches
                    )
                except Exception as search_error:
                    logger.error(f"Search error: {str(search_error)}")
                    continue
                
                if search_results:
                    for result in search_results:
                        if self.interrupted.is_set():
                            logger.info("Research interrupted during result processing")
                            break
                        if result.url not in self.searched_urls:
                            self.searched_urls.add(result.url)
                            try:
                                self._process_result(result)
                            except Exception as process_error:
                                logger.error(f"Error processing result from {result.url}: {str(process_error)}")
                                continue

                if not continuous_mode:
                    break

        except Exception as e:
            logger.error(f"Critical error in research process: {str(e)}", exc_info=True)
            raise
        finally:
            self.thinking = False
            self.current_focus = None
            logger.info("Research process completed")

    def _process_result(self, result) -> None:
        """Process a single search result"""
        try:
            # Extract relevant information
            summary = self.llm.summarize(result.content)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False,
                encoding='utf-8'
            ) as tmp:
                tmp.write(f"URL: {result.url}\n\n")
                tmp.write(f"Summary: {summary}\n\n")
                tmp.write(f"Raw Content:\n{result.content}")
                self.session_files.append(tmp.name)
                
        except Exception as e:
            logger.error(f"Error processing result from {result.url}: {e}")

    def terminate_research(self) -> Optional[str]:
        """Terminate the current research process and return a summary"""
        logger.info("Terminating research process...")
        self.interrupted.set()
        self.shutdown_event.set()
        
        try:
            if self.research_thread and self.research_thread.is_alive():
                self.research_thread.join(timeout=5.0)
                
            # Generate final summary
            summary = None
            if self.session_files:
                combined_content = ""
                for file_path in self.session_files:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            combined_content += f.read() + "\n\n"
                    except Exception as e:
                        logger.error(f"Error reading session file {file_path}: {e}")
                
                if combined_content:
                    summary = self.llm.generate_summary(
                        combined_content,
                        self.original_query
                    )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error during research termination: {e}")
            return None
        finally:
            self._cleanup()
            self.is_running = False
            self.research_started.clear()
            self.interrupted.clear()
            self.shutdown_event.clear()

    def _cleanup(self) -> None:
        """Clean up temporary files and resources"""
        with self.cleanup_lock:
            for file_path in self.session_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error removing temporary file {file_path}: {e}")
            self.session_files.clear()

    @staticmethod
    def get_initial_input() -> str:
        """Get the initial research query from the user"""
        try:
            print(f"\n{Fore.CYAN}📝 Enter your research query (Press Enter to submit):{Style.RESET_ALL}")
            query = input().strip()
            return query
        except (EOFError, KeyboardInterrupt):
            return ""

def main():
    """Main entry point with enhanced error handling and resource management"""
    try:
        from llm_wrapper import LLMWrapper
        from llm_response_parser import UltimateLLMResponseParser
        from search_engine import EnhancedSelfImprovingSearch
        
        logger.info("Initializing research system...")
        
        # Initialize components with proper error handling
        try:
            llm = LLMWrapper()
            parser = UltimateLLMResponseParser()
            search_engine = EnhancedSelfImprovingSearch(llm, parser)
            manager = ResearchManager(llm, parser, search_engine)
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            print(f"Error: Could not initialize research system: {e}")
            return 1
            
        logger.info("Research system initialized successfully")
        print(f"{Fore.GREEN}Research system initialized. Enter your research topic or 'quit' to exit.{Style.RESET_ALL}")
        
        while True:
            try:
                topic = ResearchManager.get_initial_input()
                if not topic or topic.lower() == 'quit':
                    break
                    
                continuous_mode = topic.startswith('@')
                if continuous_mode:
                    topic = topic[1:]
                    
                manager.start_research(topic, continuous_mode)
                summary = manager.terminate_research()
                
                if summary:
                    print(f"\n{Fore.GREEN}Research Summary:{Style.RESET_ALL}")
                    print(summary)
                    
                print(f"\n{Fore.GREEN}Research completed. Ready for next topic.{Style.RESET_ALL}\n")
                
# Only ask for new session after successful completion
                response = input(f"{Fore.CYAN}Would you like to start a new research session? (Y/n): {Style.RESET_ALL}").lower()
                if response != 'y' and response != '':
                    break
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Operation cancelled. Ready for next topic.{Style.RESET_ALL}")
                if 'manager' in locals():
                    manager.terminate_research()
                continue
                
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Research system shutting down.{Style.RESET_ALL}")
        if 'manager' in locals():
            manager.terminate_research()
    except Exception as e:
        logger.error(f"Critical error in main: {e}", exc_info=True)
        print(f"{Fore.RED}Critical error: {e}{Style.RESET_ALL}")
        return 1
    finally:
        # Ensure proper cleanup
        logger.info("Performing final cleanup...")
        try:
            if 'manager' in locals():
                manager._cleanup()
        except Exception as e:
            logger.error(f"Error during final cleanup: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
