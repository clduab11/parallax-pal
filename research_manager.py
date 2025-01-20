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

    # [Previous TerminalUI methods remain unchanged]

class StrategicAnalysisParser:
    """Enhanced parser with improved validation, safety, and error handling"""
    def __init__(self, llm=None):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        self.parser_lock = threading.Lock()
        
        # Compile regex patterns for better performance
        self.patterns = {
            'priority': re.compile(r'Priority:\s*(\d+)', re.IGNORECASE),
            'area': re.compile(r'^\d+\.\s*(.+?)(?=Priority:|$)', re.IGNORECASE | re.MULTILINE | re.DOTALL)
        }
        
        # Constants for validation
        self.MAX_FOCUS_AREAS = 5
        self.MIN_AREA_LENGTH = 10
        self.MAX_AREA_LENGTH = 500
        self.VALID_PRIORITIES = set(range(1, 6))

    # [Previous StrategicAnalysisParser methods remain unchanged]

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
        self.strategic_parser = StrategicAnalysisParser(llm=self.llm)
        
        # Setup signal handlers with error handling
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except Exception as e:
            logger.error(f"Failed to set up signal handlers: {e}")
            raise

    # [Previous ResearchManager methods remain unchanged]

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
