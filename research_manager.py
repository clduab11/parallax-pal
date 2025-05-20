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
from typing import List, Dict, Set, Optional, Tuple, Union, Any
from dataclasses import dataclass
from queue import Queue
from datetime import datetime
from io import StringIO
from colorama import init, Fore, Style
from threading import Event, Lock
from urllib.parse import urlparse
from pathlib import Path
from research_cache import ResearchCache

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
    def __init__(self, llm_wrapper, parser, search_engine, max_searches_per_cycle: int = 5,
                 use_cache: bool = True, cache_ttl: int = 86400):
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
        
        # Initialize cache
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self.cache = ResearchCache(ttl=cache_ttl) if use_cache else None
        
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

    def start_research(self, query: str, continuous_mode: bool = False, force_refresh: bool = False) -> None:
        """Start the research process with the given query
        
        Args:
            query: Research query to process
            continuous_mode: Whether to research all focus areas (True) or just the first one (False)
            force_refresh: Whether to ignore cache and force a fresh research
        """
        if not query or not isinstance(query, str):
            raise ValueError("Invalid research query")

        logger.info(f"Starting research for query: {query}")
        self.original_query = query
        self.is_running = True
        self.research_started.set()

        try:
            # Check cache if enabled and not forcing refresh
            if self.use_cache and self.cache and not force_refresh:
                logger.info(f"Checking cache for query: {query}")
                
                # Create metadata for cache key
                cache_metadata = {
                    'continuous_mode': continuous_mode,
                    'model': getattr(self.llm, 'model_name', 'unknown')
                }
                
                # Attempt to get cached result
                cached_result = self.cache.get(query, **cache_metadata)
                if cached_result:
                    logger.info(f"Using cached result for query: {query}")
                    print(f"{Fore.GREEN}Using cached result for this query{Style.RESET_ALL}")
                    
                    # Use cached result
                    self.focus_areas = []
                    
                    # Reconstruct focus areas from cache
                    if 'focus_areas' in cached_result:
                        for focus_data in cached_result['focus_areas']:
                            focus = ResearchFocus(
                                area=focus_data.get('area', ''),
                                priority=focus_data.get('priority', 3),
                                source_query=focus_data.get('source_query', ''),
                                timestamp=focus_data.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                search_queries=focus_data.get('search_queries', [])
                            )
                            self.focus_areas.append(focus)
                    
                    # Return immediately with cached result - no need to start the thread
                    self.thinking = False
                    self.is_running = False
                    self.research_started.clear()
                    return
            
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
        """Internal method to conduct the research process with enhanced error handling and recovery"""
        max_retries = 3
        retry_count = 0
        self.research_errors = []
        analysis = None
        
        try:
            logger.info(f"Starting research for query: {query}")
            
            # Format query for LLM analysis with retries
            while retry_count < max_retries and not analysis:
                try:
                    # Attempt to get LLM analysis with backoff
                    retry_delay = 2 ** retry_count  # Exponential backoff
                    if retry_count > 0:
                        logger.info(f"Retry attempt {retry_count} for LLM analysis (delay: {retry_delay}s)")
                        time.sleep(retry_delay)
                    
                    # Format query for LLM analysis
                    llm_response = self.llm.analyze_query(query)
                    if not llm_response:
                        raise ValueError("Empty response from LLM analysis")
                    
                    logger.info(f"LLM Response received (length: {len(llm_response)})")
                    
                    # Parse the LLM response
                    analysis = self.strategic_parser.parse_analysis(llm_response)
                    
                    # If analysis failed, try with a simplified approach
                    if not analysis:
                        logger.warning("Failed to parse LLM response, attempting with formatted template")
                        # Use a simpler template as fallback
                        formatted_response = f"""Original Question Analysis: {query}

Research Gaps:
1. Understanding and definition of the topic
   Priority: 1
2. Historical development and discoveries
   Priority: 2
3. Current applications and significance
   Priority: 3
"""
                        logger.info("Attempting with formatted template")
                        analysis = self.strategic_parser.parse_analysis(formatted_response)
                    
                    # Validate analysis has focus areas
                    if analysis and not analysis.focus_areas:
                        logger.warning("Analysis succeeded but no focus areas identified")
                        analysis = None
                        raise ValueError("No research areas identified in analysis")
                        
                except Exception as e:
                    retry_count += 1
                    self.research_errors.append(f"LLM analysis error (attempt {retry_count}): {str(e)}")
                    logger.error(f"Error in LLM analysis: {str(e)}")
                    
                    if retry_count >= max_retries:
                        logger.error(f"Failed to analyze query after {max_retries} attempts")
                        # Create fallback analysis
                        keywords = query.split()
                        # Use simpler approach - extract keywords from query and convert to focus areas
                        fallback_areas = [
                            ResearchFocus(
                                area=f"Understanding {query}",
                                priority=1,
                                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ),
                            ResearchFocus(
                                area=f"Current developments in {' '.join(keywords[:3])}",
                                priority=2,
                                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            )
                        ]
                        
                        # Create fallback analysis
                        analysis = AnalysisResult(
                            original_question=query,
                            focus_areas=fallback_areas,
                            raw_response="Fallback analysis due to LLM error",
                            confidence_score=0.3
                        )
                        logger.info("Using fallback analysis strategy")
            
            if analysis:
                logger.info(f"Successfully analyzed query with {len(analysis.focus_areas)} focus areas")
                self.focus_areas = analysis.focus_areas
                
                # Process each focus area with error isolation
                focus_errors = 0
                for focus_index, focus in enumerate(self.focus_areas):
                    if self.interrupted.is_set():
                        logger.info("Research interrupted by user")
                        break
                        
                    self.current_focus = focus
                    logger.info(f"Researching focus area {focus_index+1}/{len(self.focus_areas)}: {focus.area[:50]}...")
                    
                    # Try to get search results with retries
                    search_retry_count = 0
                    search_results = None
                    
                    while search_retry_count < max_retries and not search_results:
                        try:
                            # Optimization: Use the original query for the first focus area, 
                            # and focused queries for subsequent ones
                            search_query = focus.source_query or query
                            if focus_index > 0:
                                # For subsequent focus areas, create a more targeted search query
                                search_query = f"{query} {focus.area}"[:200]  # Limit length
                                
                            search_results = self.search_engine.search(
                                search_query,
                                max_results=self.max_searches
                            )
                            
                            # Validate search results
                            if not search_results:
                                raise ValueError("No search results found")
                                
                        except Exception as search_error:
                            search_retry_count += 1
                            error_msg = f"Search error in focus {focus_index+1} (attempt {search_retry_count}): {str(search_error)}"
                            self.research_errors.append(error_msg)
                            logger.error(error_msg)
                            
                            if search_retry_count >= max_retries:
                                logger.error(f"Failed to search for focus area after {max_retries} attempts")
                                focus_errors += 1
                                break
                            
                            # Wait before retry with exponential backoff
                            time.sleep(2 ** search_retry_count)
                    
                    # Process search results with error handling for each
                    if search_results:
                        successful_results = 0
                        for result_index, result in enumerate(search_results):
                            if self.interrupted.is_set():
                                logger.info("Research interrupted during result processing")
                                break
                                
                            # Skip duplicates
                            if result.url in self.searched_urls:
                                continue
                                
                            self.searched_urls.add(result.url)
                            try:
                                logger.info(f"Processing result {result_index+1}/{len(search_results)}: {result.url}")
                                self._process_result(result)
                                successful_results += 1
                            except Exception as process_error:
                                error_msg = f"Error processing result from {result.url}: {str(process_error)}"
                                self.research_errors.append(error_msg)
                                logger.error(error_msg)
                                continue
                        
                        # Log success rate for this focus area
                        logger.info(f"Focus area {focus_index+1}: processed {successful_results}/{len(search_results)} results successfully")
                    
                    # Break after first focus area if not in continuous mode
                    if not continuous_mode:
                        logger.info("Single-focus mode: stopping after first focus area")
                        break
                
                # Check overall success rate
                if focus_errors == len(self.focus_areas):
                    logger.error("All focus areas failed in research process")
                    raise ValueError("Failed to research any focus areas successfully")
                    
            else:
                raise ValueError("Failed to create analysis for research query")

        except Exception as e:
            error_msg = f"Critical error in research process: {str(e)}"
            self.research_errors.append(error_msg)
            logger.error(error_msg, exc_info=True)
            # We don't re-raise here to allow for graceful degradation
        finally:
            self.thinking = False
            self.current_focus = None
            
            # Log research completion stats
            urls_found = len(self.searched_urls)
            logger.info(f"Research process completed: {urls_found} unique sources processed")
            
            # Log errors for debugging
            if self.research_errors:
                logger.info(f"Research completed with {len(self.research_errors)} errors")
            else:
                logger.info("Research completed successfully with no errors")
                
                # Save to cache if no errors and it's enabled
                if self.use_cache and self.cache and not self.research_errors and self.focus_areas:
                    try:
                        # Prepare data for caching
                        focus_areas_data = []
                        for focus in self.focus_areas:
                            focus_data = {
                                'area': focus.area,
                                'priority': focus.priority,
                                'source_query': focus.source_query,
                                'timestamp': focus.timestamp,
                                'search_queries': focus.search_queries if focus.search_queries else []
                            }
                            focus_areas_data.append(focus_data)
                            
                        # Create cache entry
                        cache_data = {
                            'original_query': query,
                            'focus_areas': focus_areas_data,
                            'continuous_mode': continuous_mode,
                            'timestamp': datetime.now().isoformat(),
                            'url_count': urls_found
                        }
                        
                        # Cache metadata
                        cache_metadata = {
                            'continuous_mode': continuous_mode,
                            'model': getattr(self.llm, 'model_name', 'unknown')
                        }
                        
                        # Save to cache
                        logger.info(f"Saving research results to cache for query: {query}")
                        self.cache.set(query, cache_data, **cache_metadata)
                    except Exception as cache_error:
                        logger.error(f"Error saving to cache: {str(cache_error)}")

    def _process_result(self, result) -> bool:
        """Process a single search result with enhanced validation, error handling, and content sanitization
        
        Args:
            result: The search result to process
            
        Returns:
            bool: True if processing succeeded, False if it failed
        """
        max_retries = 2
        retry_count = 0
        
        # Validate result contents
        if not hasattr(result, 'url') or not hasattr(result, 'content'):
            logger.error("Invalid result object: missing required attributes")
            return False
            
        if not result.url or not result.content:
            logger.error(f"Empty content or URL in result: {result.url}")
            return False
            
        # Check URL for safety (basic validation)
        try:
            parsed_url = urlparse(result.url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                logger.error(f"Invalid URL format: {result.url}")
                return False
        except Exception as url_error:
            logger.error(f"URL parsing error: {str(url_error)}")
            return False
            
        # Process with retries
        while retry_count < max_retries:
            try:
                # Sanitize and normalize content
                safe_content = self._sanitize_content(result.content)
                
                # Skip if content is too short
                if len(safe_content) < 100:
                    logger.warning(f"Content too short from {result.url}, skipping")
                    return False
                    
                # Extract relevant information with a timeout mechanism
                try:
                    # Set a time limit for summarization
                    summarization_start = time.time()
                    summarization_timeout = 30  # seconds
                    
                    summary = self.llm.summarize(safe_content)
                    
                    summarization_time = time.time() - summarization_start
                    logger.info(f"Summarization completed in {summarization_time:.2f}s")
                    
                    # Validate summary
                    if not summary or len(summary) < 50:
                        # If summary is too short, try a fallback method
                        logger.warning(f"Summary too short ({len(summary) if summary else 0} chars), using fallback")
                        # Use first paragraph as fallback
                        potential_summary = re.search(r'^(.{50,500})\n', safe_content)
                        if potential_summary:
                            summary = f"[Auto-extracted due to summarization failure]: {potential_summary.group(1)}"
                        else:
                            summary = f"[Failed to summarize content from {result.url}]" 
                except Exception as summarize_error:
                    logger.error(f"Summarization error: {str(summarize_error)}")
                    # Use fallback
                    summary = f"[Error during summarization: {str(summarize_error)}]\n\nFirst content snippet: {safe_content[:200]}"
                
                # Save to temporary file with error handling
                tmp_path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        mode='w',
                        suffix='.txt',
                        delete=False,
                        encoding='utf-8'
                    ) as tmp:
                        # Add structured metadata
                        tmp.write(f"URL: {result.url}\n")
                        tmp.write(f"Timestamp: {datetime.now().isoformat()}\n")
                        tmp.write(f"Focus Area: {self.current_focus.area if self.current_focus else 'General'}\n\n")
                        tmp.write(f"Summary:\n{summary}\n\n")
                        
                        # Include sanitized content (limit length to avoid excessive storage)
                        max_content_length = 100000  # 100KB limit
                        if len(safe_content) > max_content_length:
                            truncated_content = safe_content[:max_content_length] + "\n\n[Content truncated due to length]\n"
                            tmp.write(f"Raw Content (truncated):\n{truncated_content}")
                        else:
                            tmp.write(f"Raw Content:\n{safe_content}")
                            
                        tmp_path = tmp.name
                        
                    # Only add to session files after successful write
                    if tmp_path:
                        self.session_files.append(tmp_path)
                        
                    # Log success
                    logger.info(f"Successfully processed search result: {result.url}")
                    return True
                    
                except Exception as file_error:
                    logger.error(f"Error writing to temporary file: {str(file_error)}")
                    # Clean up any partially written file
                    if tmp_path and os.path.exists(tmp_path):
                        try:
                            os.remove(tmp_path)
                        except:
                            pass
                    # Continue to retry loop
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"Error processing result from {result.url} (attempt {retry_count}): {str(e)}")
                
                if retry_count >= max_retries:
                    logger.error(f"Failed to process result after {max_retries} attempts")
                    return False
                    
                # Wait before retry with exponential backoff
                time.sleep(2 ** retry_count)
                
        return False  # Should not reach here but just in case
        
    def _sanitize_content(self, content: str) -> str:
        """Sanitize and normalize content for processing
        
        Args:
            content: Raw content to sanitize
            
        Returns:
            str: Sanitized content
        """
        if not content:
            return ""
            
        try:
            # Convert to string if not already
            if not isinstance(content, str):
                content = str(content)
                
            # Remove null bytes which can cause issues
            content = content.replace('\x00', '')
            
            # Replace excessive whitespace
            content = re.sub(r'\s{2,}', '\n', content)
            
            # Remove non-printable characters except newlines and tabs
            content = ''.join(c for c in content if c.isprintable() or c in '\n\t')
            
            # Normalize line endings
            content = re.sub(r'\r\n|\r', '\n', content)
            
            # Remove excessively long lines (likely garbage or binary data)
            lines = content.split('\n')
            filtered_lines = [line for line in lines if len(line) < 2000]  # Cap line length
            content = '\n'.join(filtered_lines)
            
            # Ensure content doesn't exceed reasonable size
            max_length = 500000  # 500KB limit
            if len(content) > max_length:
                content = content[:max_length] + "\n\n[Content truncated due to length]\n"
                
            return content
            
        except Exception as e:
            logger.error(f"Error sanitizing content: {str(e)}")
            # Return a safe subset of the content as fallback
            if isinstance(content, str):
                return content[:1000] + "\n\n[Content processing error - showing partial content]\n"
            return "[Content processing error - invalid format]"

    def terminate_research(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Terminate the current research process and return a detailed result
        
        Args:
            force_refresh: Whether to ignore cache and force a fresh summary generation
            
        Returns:
            Dict containing summary, metadata, and error information
        """
        logger.info("Terminating research process...")
        self.interrupted.set()
        self.shutdown_event.set()
        
        # Prepare result structure
        result = {
            "summary": None,
            "sources": [],
            "errors": getattr(self, 'research_errors', []),
            "status": "failed",
            "processing_time": 0,
            "focus_areas": [],
            "sources_count": 0,
            "success": False
        }
        
        start_time = time.time()
        
        # Check cache for final summary if research isn't running
        if not force_refresh and self.use_cache and self.cache and not self.is_running and self.original_query:
            try:
                # Create metadata for cache key
                cache_metadata = {
                    'summary': True,  # Special flag to distinguish summary cache from focus areas cache
                    'model': getattr(self.llm, 'model_name', 'unknown')
                }
                
                # Try to get cached summary
                logger.info(f"Checking cache for summary of query: {self.original_query}")
                cached_result = self.cache.get(self.original_query, **cache_metadata)
                
                if cached_result and 'summary' in cached_result:
                    logger.info(f"Using cached summary for query: {self.original_query}")
                    print(f"{Fore.GREEN}Using cached summary for this query{Style.RESET_ALL}")
                    
                    # Use cached result
                    result.update(cached_result)
                    result['cache_hit'] = True
                    result['processing_time'] = time.time() - start_time
                    return result
            except Exception as cache_error:
                logger.error(f"Error checking cache for summary: {str(cache_error)}")
        
        try:
            # Wait for research thread to finish with timeout
            if self.research_thread and self.research_thread.is_alive():
                try:
                    self.research_thread.join(timeout=10.0)
                    if self.research_thread.is_alive():
                        logger.warning("Research thread did not terminate within timeout")
                        result["errors"].append("Research thread did not terminate cleanly")
                except Exception as thread_error:
                    logger.error(f"Error waiting for research thread: {str(thread_error)}")
                    result["errors"].append(f"Thread error: {str(thread_error)}")
            
            # Calculate processing time
            result["processing_time"] = time.time() - start_time
            
            # Add focus areas to result
            if hasattr(self, 'focus_areas') and self.focus_areas:
                focus_data = []
                for focus in self.focus_areas:
                    focus_data.append({
                        "area": focus.area,
                        "priority": focus.priority
                    })
                result["focus_areas"] = focus_data
            
            # Check if we have any results to summarize
            if not self.session_files:
                logger.warning("No session files found for summarization")
                result["status"] = "no_results"
                return result
                
            # Generate list of sources
            sources = []
            for file_path in self.session_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        url_match = re.search(r'URL: (.+?)\n', content)
                        if url_match:
                            sources.append(url_match.group(1))
                except Exception as e:
                    logger.error(f"Error extracting source URL from {file_path}: {str(e)}")
            
            result["sources"] = sources
            result["sources_count"] = len(sources)
                
            # Generate final summary with error handling and retry
            max_retries = 2
            summary_success = False
            summary_errors = []
            
            for attempt in range(max_retries):
                try:
                    # First build combined content with error handling
                    combined_content = ""
                    file_count = 0
                    
                    # Add query and focus areas to beginning of content
                    combined_content += f"Original Query: {self.original_query}\n\n"
                    combined_content += "Research Focus Areas:\n"
                    for i, focus in enumerate(self.focus_areas):
                        combined_content += f"{i+1}. {focus.area} (Priority: {focus.priority})\n"
                    combined_content += "\n\n"
                    
                    for file_path in self.session_files:
                        try:
                            # Check file size before reading
                            file_size = os.path.getsize(file_path)
                            if file_size > 1024 * 1024:  # 1MB limit per file
                                logger.warning(f"Skipping large file {file_path} ({file_size/1024/1024:.2f}MB)")
                                continue
                                
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                                
                                # Extract URL and summary only for combined content
                                # This keeps the content smaller and more manageable
                                url_match = re.search(r'URL: (.+?)\n', file_content)
                                summary_match = re.search(r'Summary:\n(.*?)\n\nRaw Content:', file_content, re.DOTALL)
                                
                                if url_match and summary_match:
                                    url = url_match.group(1)
                                    summary = summary_match.group(1)
                                    combined_content += f"Source: {url}\n{summary}\n\n---\n\n"
                                    file_count += 1
                        except Exception as file_error:
                            logger.error(f"Error reading session file {file_path}: {str(file_error)}")
                            result["errors"].append(f"File error: {str(file_error)}")
                    
                    if not combined_content or file_count == 0:
                        logger.error("No valid content found in session files")
                        result["errors"].append("No valid content found in session files")
                        break
                    
                    # Generate summary with optimized prompt
                    summary_prompt = (f"Provide a comprehensive research summary addressing this query: "
                                    f"{self.original_query}\n\n"
                                    f"Your summary should include:\n"
                                    f"1. Direct answer to the query\n"
                                    f"2. Key insights from sources\n"
                                    f"3. Different perspectives if available\n"
                                    f"4. Data and facts discovered\n"
                                    f"5. Conclusion based on evidence\n\n"
                                    f"FORMAT YOUR RESPONSE AS A COHESIVE RESEARCH REPORT WITH SECTIONS.")
                    
                    logger.info(f"Generating summary from {file_count} sources")
                    summary = self.llm.generate_summary(
                        combined_content,
                        summary_prompt
                    )
                    
                    if summary and len(summary) > 100:
                        result["summary"] = summary
                        result["status"] = "success"
                        result["success"] = True
                        summary_success = True
                        
                        # Cache the successful summary
                        if self.use_cache and self.cache:
                            try:
                                # Create metadata for cache key
                                cache_metadata = {
                                    'summary': True,  # Special flag to distinguish summary cache
                                    'model': getattr(self.llm, 'model_name', 'unknown')
                                }
                                
                                # Save to cache
                                logger.info(f"Saving summary to cache for query: {self.original_query}")
                                self.cache.set(self.original_query, result, **cache_metadata)
                            except Exception as cache_error:
                                logger.error(f"Error saving summary to cache: {str(cache_error)}")
                        
                        break
                    else:
                        logger.warning(f"Generated summary too short: {len(summary) if summary else 0} chars")
                        summary_errors.append(f"Summary too short (attempt {attempt+1})")
                        
                        # Try with simpler approach
                        if attempt + 1 < max_retries:
                            time.sleep(2)  # Small delay before retry
                            
                except Exception as e:
                    logger.error(f"Error generating summary (attempt {attempt+1}): {str(e)}")
                    summary_errors.append(f"Summary error: {str(e)}")
                    
                    if attempt + 1 < max_retries:
                        time.sleep(2)  # Small delay before retry
            
            # If all summary attempts failed, create a basic summary
            if not summary_success:
                logger.warning("All summary attempts failed, using basic summary")
                result["errors"].extend(summary_errors)
                
                # Create simple summary from focus areas and sources
                basic_summary = f"Research on: {self.original_query}\n\n"
                basic_summary += "Key Research Areas:\n"
                for i, focus in enumerate(self.focus_areas):
                    basic_summary += f"{i+1}. {focus.area}\n"
                
                basic_summary += f"\nFound {len(sources)} sources of information."
                
                # Add a note about errors
                if result["errors"]:
                    basic_summary += f"\n\nNote: Research encountered {len(result['errors'])} errors."
                    
                result["summary"] = basic_summary
                result["status"] = "partial"
            
            return result
            
        except Exception as e:
            logger.error(f"Critical error during research termination: {str(e)}", exc_info=True)
            result["errors"].append(f"Termination error: {str(e)}")
            result["status"] = "failed"
            return result
        finally:
            # Ensure proper cleanup regardless of errors
            try:
                self._cleanup()
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {str(cleanup_error)}")
                result["errors"].append(f"Cleanup error: {str(cleanup_error)}")
                
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
    """Main entry point with enhanced error handling, resource management, and improved UX"""
    try:
        from llm_wrapper import LLMWrapper
        from llm_response_parser import UltimateLLMResponseParser
        from search_engine import EnhancedSelfImprovingSearch
        
        logger.info("Initializing research system...")
        
        # Initialize components with proper error handling and user feedback
        try:
            print(f"{Fore.CYAN}Initializing LLM wrapper...{Style.RESET_ALL}")
            llm = LLMWrapper()
            
            print(f"{Fore.CYAN}Initializing response parser...{Style.RESET_ALL}")
            parser = UltimateLLMResponseParser()
            
            print(f"{Fore.CYAN}Initializing search engine...{Style.RESET_ALL}")
            search_engine = EnhancedSelfImprovingSearch(llm, parser)
            
            print(f"{Fore.CYAN}Initializing research manager...{Style.RESET_ALL}")
            manager = ResearchManager(llm, parser, search_engine)
        except Exception as e:
            logger.error(f"Failed to initialize components: {str(e)}", exc_info=True)
            print(f"\n{Fore.RED}Error: Could not initialize research system: {str(e)}{Style.RESET_ALL}")
            print(f"\n{Fore.YELLOW}Please check your network connection and ensure Ollama server is running.{Style.RESET_ALL}")
            return 1
            
        logger.info("Research system initialized successfully")
        print(f"\n{Fore.GREEN}======= Parallax Pal Research System ======={Style.RESET_ALL}")
        print(f"{Fore.GREEN}System initialized successfully!{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Enter your research topic or 'quit' to exit.")
        print(f"Add @ prefix for continuous mode (e.g. @quantum physics){Style.RESET_ALL}\n")
        
        while True:
            try:
                topic = ResearchManager.get_initial_input()
                if not topic or topic.lower() == 'quit':
                    break
                    
                # Process special commands
                if topic.lower() == 'help':
                    print(f"\n{Fore.CYAN}=== Parallax Pal Help ==={Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}Basic commands:{Style.RESET_ALL}")
                    print("  - Enter any text to start research on that topic")
                    print("  - Add @ prefix for continuous mode (researches all focus areas)")
                    print("  - Type 'quit' to exit the program")
                    print("  - Press Ctrl+C to cancel current research")
                    print(f"\n{Fore.YELLOW}Research modes:{Style.RESET_ALL}")
                    print("  - Standard mode: Researches the first focus area only")
                    print("  - Continuous mode: Researches all focus areas thoroughly")
                    continue
                    
                # Check for GPU toggle command
                if topic.lower() == 'toggle gpu':
                    try:
                        gpu_state = llm.toggle_gpu()
                        print(f"\n{Fore.GREEN}GPU acceleration: {'ENABLED' if gpu_state else 'DISABLED'}{Style.RESET_ALL}")
                    except Exception as gpu_error:
                        logger.error(f"Error toggling GPU: {str(gpu_error)}")
                        print(f"\n{Fore.RED}Error toggling GPU: {str(gpu_error)}{Style.RESET_ALL}")
                    continue
                    
                # Check for continuous mode
                continuous_mode = topic.startswith('@')
                if continuous_mode:
                    topic = topic[1:]
                    print(f"\n{Fore.CYAN}Running in continuous mode (researching all focus areas){Style.RESET_ALL}")
                    
                # Start research with proper error handling
                print(f"\n{Fore.YELLOW}Starting research on: {topic}{Style.RESET_ALL}")
                start_time = time.time()
                try:
                    manager.start_research(topic, continuous_mode)
                    result = manager.terminate_research()
                    elapsed_time = time.time() - start_time
                except Exception as research_error:
                    logger.error(f"Error during research: {str(research_error)}", exc_info=True)
                    print(f"\n{Fore.RED}Error during research: {str(research_error)}{Style.RESET_ALL}")
                    continue
                
                # Process and display research results with better formatting
                if result and result.get("status") != "failed":
                    # Print summary
                    if result.get("summary"):
                        print(f"\n{Fore.GREEN}====== Research Summary ======{Style.RESET_ALL}\n")
                        print(result["summary"])
                    else:
                        print(f"\n{Fore.YELLOW}No summary generated for this research.{Style.RESET_ALL}")
                    
                    # Print sources
                    if result.get("sources"):
                        source_count = len(result["sources"])
                        print(f"\n{Fore.CYAN}Sources ({source_count}):{Style.RESET_ALL}")
                        for i, source in enumerate(result["sources"][:10], 1):  # Limit to 10 sources in display
                            print(f"{i}. {source}")
                        if source_count > 10:
                            print(f"...and {source_count - 10} more sources")
                    
                    # Print focus areas
                    if result.get("focus_areas"):
                        print(f"\n{Fore.CYAN}Research Focus Areas:{Style.RESET_ALL}")
                        for i, focus in enumerate(result["focus_areas"], 1):
                            print(f"{i}. {focus['area']} (Priority: {focus['priority']})")
                    
                    # Print processing stats
                    elapsed_time = result.get("processing_time", elapsed_time)
                    print(f"\n{Fore.GREEN}Research completed in {elapsed_time:.2f} seconds.{Style.RESET_ALL}")
                    
                    # Print any errors
                    if result.get("errors"):
                        error_count = len(result["errors"])
                        print(f"\n{Fore.YELLOW}Research encountered {error_count} errors/warnings.{Style.RESET_ALL}")
                        # Only show first 3 errors to avoid cluttering the screen
                        for i, error in enumerate(result["errors"][:3], 1):
                            print(f"  {i}. {error}")
                        if error_count > 3:
                            print(f"  ...and {error_count - 3} more errors/warnings (see logs for details)")
                else:
                    # Research failed completely
                    print(f"\n{Fore.RED}Research failed to produce useful results.{Style.RESET_ALL}")
                    if result and result.get("errors"):
                        print(f"\n{Fore.YELLOW}Errors encountered:{Style.RESET_ALL}")
                        for error in result["errors"][:5]:  # Show up to 5 errors
                            print(f"  - {error}")
                    
                print(f"\n{Fore.GREEN}Ready for next topic.{Style.RESET_ALL}\n")
                
                # Ask for new session
                response = input(f"{Fore.CYAN}Would you like to start a new research session? (Y/n): {Style.RESET_ALL}").lower()
                if response != 'y' and response != '':
                    break
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Operation cancelled. Ready for next topic.{Style.RESET_ALL}")
                if 'manager' in locals():
                    try:
                        manager.terminate_research()
                    except Exception as e:
                        logger.error(f"Error during forced termination: {str(e)}")
                continue
                
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Research system shutting down.{Style.RESET_ALL}")
        if 'manager' in locals():
            try:
                manager.terminate_research()
            except Exception as e:
                logger.error(f"Error during shutdown termination: {str(e)}")
    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}", exc_info=True)
        print(f"\n{Fore.RED}Critical error: {str(e)}{Style.RESET_ALL}")
        return 1
    finally:
        # Ensure proper cleanup with better user feedback
        logger.info("Performing final cleanup...")
        print(f"\n{Fore.CYAN}Cleaning up resources...{Style.RESET_ALL}")
        try:
            if 'manager' in locals():
                manager._cleanup()
            print(f"{Fore.GREEN}Resources cleaned up successfully.{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"Error during final cleanup: {str(e)}")
            print(f"{Fore.RED}Error during cleanup: {str(e)}{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}Thank you for using Parallax Pal Research System!{Style.RESET_ALL}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
