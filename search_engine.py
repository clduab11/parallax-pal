import logging
from typing import List, Dict, Optional, Set, Tuple, Any, NamedTuple, Union
from web_scraper import MultiSearcher, WebScraperError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import time
from io import StringIO
import re
import json
import hashlib
import urllib.parse
from datetime import datetime
from contextlib import contextmanager
from dataclasses import dataclass, field
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

class SearchError(Exception):
    """Custom exception for search-related errors"""
    pass

@dataclass
class Source:
    """Represents a research source with citation information"""
    url: str
    title: str
    author: Optional[str] = None
    publication_date: Optional[str] = None
    site_name: Optional[str] = None
    content: str = ""
    snippet: str = ""
    access_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    citation_style: str = "apa"
    reliability_score: float = 0.0
    content_hash: str = ""
    
    def __post_init__(self):
        # Generate content hash for verification if content exists
        if self.content and not self.content_hash:
            self.content_hash = hashlib.md5(self.content.encode('utf-8')).hexdigest()
        
        # Try to extract site name from URL if not provided
        if not self.site_name and self.url:
            try:
                parsed_url = urllib.parse.urlparse(self.url)
                self.site_name = parsed_url.netloc.replace('www.', '')
            except Exception:
                pass

    def generate_citation(self) -> str:
        """Generate a citation based on the selected style"""
        if self.citation_style == "apa":
            return self._generate_apa_citation()
        elif self.citation_style == "mla":
            return self._generate_mla_citation()
        else:
            return self._generate_apa_citation()  # Default to APA
    
    def _generate_apa_citation(self) -> str:
        """Generate APA style citation"""
        citation = ""
        
        # Author
        if self.author:
            citation += f"{self.author}. "
        
        # Date
        date_part = ""
        if self.publication_date:
            date_part = f"({self.publication_date}). "
        else:
            date_part = f"(n.d.). "  # No date
        citation += date_part
        
        # Title
        if self.title:
            citation += f"{self.title}. "
        
        # Site name
        if self.site_name:
            citation += f"{self.site_name}. "
        
        # URL and access date
        citation += f"Retrieved {self.access_date}, from {self.url}"
        
        return citation
    
    def _generate_mla_citation(self) -> str:
        """Generate MLA style citation"""
        citation = ""
        
        # Author
        if self.author:
            citation += f"{self.author}. "
        
        # Title
        if self.title:
            citation += f"\"{self.title}.\" "
        
        # Site name
        if self.site_name:
            citation += f"{self.site_name}, "
        
        # Date
        if self.publication_date:
            citation += f"{self.publication_date}, "
        
        # URL
        citation += f"{self.url}. "
        
        # Access date
        citation += f"Accessed {self.access_date}."
        
        return citation


class EnhancedSelfImprovingSearch:
    def __init__(self, llm_wrapper, parser, max_retries: int = 3,
                 max_results: int = 10, snippet_length: int = 200,
                 max_content_per_url: int = 50000):
        """Initialize with improved configuration and resource management"""
        self.llm = llm_wrapper
        self.parser = parser
        self.max_retries = max_retries
        self.MAX_DISPLAY_RESULTS = max_results
        self.SNIPPET_LENGTH = snippet_length
        self.MAX_CONTENT_PER_URL = max_content_per_url
        self.seen_urls: Set[str] = set()
        
        # Initialize source reliability data
        self.domain_reliability = self._load_domain_reliability()
        
        # Create cache directory if it doesn't exist
        self.cache_dir = os.path.join(os.getcwd(), "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _load_domain_reliability(self) -> Dict[str, float]:
        """Load domain reliability data with fallback"""
        try:
            # Define built-in reliability data for common domains
            built_in_reliability = {
                "wikipedia.org": 0.75,  # Generally reliable but can be edited by anyone
                "britannica.com": 0.9,  # Well-established encyclopedia
                "nature.com": 0.95,  # Prestigious scientific journal
                "sciencemag.org": 0.95,  # Prestigious scientific journal
                "nih.gov": 0.95,  # U.S. National Institutes of Health
                "cdc.gov": 0.95,  # U.S. Centers for Disease Control
                "who.int": 0.95,  # World Health Organization
                "mit.edu": 0.9,  # Massachusetts Institute of Technology
                "harvard.edu": 0.9,  # Harvard University
                "stanford.edu": 0.9,  # Stanford University
                "bbc.com": 0.8,  # Reputable news source
                "bbc.co.uk": 0.8,  # Reputable news source
                "reuters.com": 0.85,  # Reputable news agency
                "apnews.com": 0.85,  # Associated Press
                "npr.org": 0.8,  # National Public Radio
                "nytimes.com": 0.8,  # New York Times
                "washingtonpost.com": 0.8,  # Washington Post
                "wsj.com": 0.8,  # Wall Street Journal
                "un.org": 0.9,  # United Nations
                "europa.eu": 0.9,  # European Union
                "nasa.gov": 0.95,  # NASA
                "arxiv.org": 0.85,  # Preprint repository for scientific papers
                "ssrn.com": 0.85,  # Social Science Research Network
                "acm.org": 0.9,  # Association for Computing Machinery
                "ieee.org": 0.9  # Institute of Electrical and Electronics Engineers
            }
            
            # Try to load custom reliability data from file
            reliability_file = os.path.join(os.getcwd(), "data", "domain_reliability.json")
            if os.path.exists(reliability_file):
                with open(reliability_file, "r") as f:
                    custom_reliability = json.load(f)
                    # Merge with built-in data, giving priority to custom values
                    built_in_reliability.update(custom_reliability)
            
            return built_in_reliability
            
        except Exception as e:
            logger.error(f"Error loading domain reliability data: {str(e)}")
            # Return basic reliability data as fallback
            return {
                "wikipedia.org": 0.75,
                "britannica.com": 0.9,
                "nih.gov": 0.95,
                "cdc.gov": 0.95
            }

    @contextmanager
    def _create_searcher(self):
        """Context manager for MultiSearcher instance"""
        searcher = None
        try:
            searcher = MultiSearcher()
            yield searcher
        finally:
            if searcher:
                searcher.cleanup()

    def _validate_query(self, query: str) -> bool:
        """Validate search query"""
        if not isinstance(query, str):
            raise SearchError("Query must be a string")
        if not query.strip():
            raise SearchError("Query cannot be empty")
        if len(query) > 1000:
            raise SearchError("Query too long (max 1000 characters)")
        return True

    def _create_snippet(self, body: str) -> str:
        """Create a clean snippet from content"""
        if not isinstance(body, str):
            body = str(body)
        
        # Clean the text
        body = re.sub(r'\s+', ' ', body)
        body = body.strip()
        
        # Create snippet
        if len(body) > self.SNIPPET_LENGTH:
            return body[:self.SNIPPET_LENGTH] + '...'
        return body

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def perform_search(self, query: str, time_range: str = 'none') -> List[Dict]:
        """Perform search with improved error handling and validation"""
        try:
            self._validate_query(query)
            
            logger.info(f"Performing search for query: {query}")
            logger.info(f"Time range: {time_range}")
            
            with self._create_searcher() as searcher:
                results = searcher.search_all_engines(query, time_range)
                
                # Filter and validate results
                valid_results = []
                for result in results:
                    if not all(key in result for key in ['href', 'title']):
                        continue
                    if not result['href'] or not result['title']:
                        continue
                    if result['href'] in self.seen_urls:
                        continue
                        
                    self.seen_urls.add(result['href'])
                    valid_results.append(result)
                
                if valid_results:
                    # Create and display results table
                    from rich.console import Console
                    from rich.table import Table
                    from rich.panel import Panel
                    from rich.text import Text

                    console = Console()
                    
                    # Create table with dynamic width
                    table = Table(
                        title="Search Results",
                        expand=True,
                        show_header=True,
                        header_style="bold cyan"
                    )
                    
                    # Add columns with flexible widths
                    table.add_column("#", style="cyan", width=3)
                    table.add_column("Title", style="blue")
                    table.add_column("Source", style="green")
                    table.add_column("Preview", style="white")
                    
                    # Add results to table
                    for i, result in enumerate(valid_results[:self.MAX_DISPLAY_RESULTS], 1):
                        snippet = self._create_snippet(result.get('body', 'No description'))
                        url = result['href']
                        source = url.split('/')[2].replace('www.', '')
                        
                        table.add_row(
                            str(i),
                            result['title'],
                            source,
                            snippet[:100] + "..." if len(snippet) > 100 else snippet
                        )
                    
                    # Create controls panel
                    controls = Text()
                    controls.append("\n🔍 ", style="yellow")
                    controls.append("Controls: ", style="bold yellow")
                    controls.append("'q' to quit, 'p' to pause\n", style="yellow")
                    
                    # Display results
                    console.print("\n")
                    console.print(Panel(table, border_style="cyan"))
                    console.print(controls)
                    
                    logger.info(f"Found {len(valid_results)} valid results")
                    return valid_results[:self.MAX_DISPLAY_RESULTS]
                
                logger.warning("No valid results found")
                return []
                
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise SearchError(f"Search failed: {str(e)}")

    def select_relevant_pages(self, results: List[Dict], query: str) -> List[str]:
        """Select most relevant pages with improved validation"""
        if not results:
            return []
            
        try:
            selected_urls = []
            with self._create_searcher() as searcher:
                for result in results:
                    url = result.get('href')
                    if not url:
                        continue
                        
                    if url in self.seen_urls:
                        continue
                        
                    if not searcher._check_robots(url):
                        logger.warning(f"URL not allowed by robots.txt: {url}")
                        continue
                        
                    selected_urls.append(url)
                    if len(selected_urls) >= 5:  # Limit to top 5 results
                        break
                        
            logger.info(f"Selected {len(selected_urls)} relevant pages")
            return selected_urls
            
        except Exception as e:
            logger.error(f"Error selecting relevant pages: {str(e)}")
            return []

    def _validate_content(self, content: str) -> bool:
        """Validate scraped content"""
        if not content:
            return False
        if len(content) > self.MAX_CONTENT_PER_URL:
            return False
        if not re.search(r'\w', content):  # Check for at least one word character
            return False
        return True

    def scrape_content(self, urls: List[str]) -> Dict[str, str]:
        """Scrape content with improved validation and error handling"""
        if not urls:
            return {}
            
        valid_content = {}
        logger.info("Scraping content from selected URLs")
        
        for url in urls:
            try:
                with self._create_searcher() as searcher:
                    content = searcher.get_web_content([url])
                    if not content:
                        continue
                        
                    text = content.get(url)
                    if not self._validate_content(text):
                        logger.warning(f"Invalid content from {url}")
                        continue
                        
                    # Clean and truncate content
                    cleaned_text = re.sub(r'\s+', ' ', text).strip()
                    valid_content[url] = cleaned_text[:self.MAX_CONTENT_PER_URL]
                    logger.info(f"Successfully scraped: {url}")
                    
            except Exception as e:
                logger.warning(f"Error scraping {url}: {str(e)}")
                continue
        
        if valid_content:
            return valid_content
        
        # If we couldn't get any content, use search result snippets
        return {
            "search_results": "Based on the search results, I can provide a general answer."
        }

    def format_scraped_content(self, scraped_content: Dict[str, str]) -> str:
        """Format scraped content with improved memory efficiency"""
        if not scraped_content:
            logger.warning("No content to format")
            return ""
            
        try:
            # Use StringIO for memory-efficient string building
            with StringIO() as output:
                total_size = 0
                
                for url, content in scraped_content.items():
                    if not content:
                        logger.warning(f"Empty content found for URL: {url}")
                        continue
                        
                    # Clean content
                    cleaned_content = re.sub(r'\s+', ' ', content).strip()
                    
                    # Check size limits
                    content_size = len(cleaned_content)
                    if total_size + content_size > self.MAX_CONTENT_PER_URL:
                        remaining_space = max(0, self.MAX_CONTENT_PER_URL - total_size)
                        if remaining_space > 0:
                            cleaned_content = cleaned_content[:remaining_space]
                        else:
                            break
                    
                    output.write(f"Content from {url}:\n")
                    output.write(f"{cleaned_content}\n\n")
                    
                    total_size += content_size
                
                formatted_content = output.getvalue()
                logger.info(f"Successfully formatted content from {len(scraped_content)} sources")
                return formatted_content
                
        except Exception as e:
            logger.error(f"Error formatting content: {str(e)}")
            return ""

    def _calculate_reliability_score(self, url: str) -> float:
        """Calculate reliability score for a URL based on domain and other factors"""
        try:
            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc.replace('www.', '')
            
            # Find the most specific matching domain
            reliability_score = 0.5  # Default score
            matched_domain = None
            
            for known_domain, score in self.domain_reliability.items():
                if domain.endswith(known_domain) and (matched_domain is None or len(known_domain) > len(matched_domain)):
                    reliability_score = score
                    matched_domain = known_domain
            
            # Adjust score based on other factors
            
            # HTTPS boost
            if parsed_url.scheme == 'https':
                reliability_score += 0.05
                reliability_score = min(reliability_score, 0.99)  # Cap at 0.99
            
            # Domain TLD adjustments
            if domain.endswith('.edu') or domain.endswith('.gov') or domain.endswith('.org'):
                reliability_score += 0.1
                reliability_score = min(reliability_score, 0.99)  # Cap at 0.99
            
            return reliability_score
            
        except Exception as e:
            logger.error(f"Error calculating reliability score: {str(e)}")
            return 0.5  # Default score on error
    
    def _extract_publication_metadata(self, url: str, content: str) -> Dict[str, str]:
        """Extract publication metadata from content"""
        metadata = {
            "author": None,
            "publication_date": None,
            "site_name": None
        }
        
        try:
            # Extract site name from URL
            parsed_url = urllib.parse.urlparse(url)
            metadata["site_name"] = parsed_url.netloc.replace('www.', '')
            
            # Try to extract publication date using regex patterns
            date_patterns = [
                r'published\s+(?:on\s+)?([A-Za-z]+\s+\d{1,2},?\s+\d{4})',  # Published on January 1, 2023
                r'date:\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',  # Date: January 1, 2023
                r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})',  # 1 January 2023
                r'([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})'  # January 1st, 2023
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, content, re.IGNORECASE)
                if date_match:
                    metadata["publication_date"] = date_match.group(1)
                    break
            
            # Try to extract author information
            author_patterns = [
                r'by\s+([A-Za-z\s\.\-]+)(?:\s*,|\s+on|\s+\|)',  # By John Doe, 
                r'author(?:s)?(?:\:|\s+)\s*([A-Za-z\s\.\-]+)'  # Author: John Doe
            ]
            
            for pattern in author_patterns:
                author_match = re.search(pattern, content, re.IGNORECASE)
                if author_match:
                    metadata["author"] = author_match.group(1).strip()
                    break
                    
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return metadata
    
    def search(self, query: str, max_results: int = 5) -> List[Source]:
        """Search for information and return structured source objects with citations"""
        try:
            # Validate query
            self._validate_query(query)
            
            # Calculate cache key based on query
            cache_key = hashlib.md5(query.encode('utf-8')).hexdigest()
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            
            # Check if we have cached results
            if os.path.exists(cache_file):
                try:
                    # Check if cache is fresh (less than 24 hours old)
                    cache_age = time.time() - os.path.getmtime(cache_file)
                    if cache_age < 86400:  # 24 hours in seconds
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            # Try to load cached data
                            cache_data = json.load(f)
                            
                            # Validate cache data structure
                            if isinstance(cache_data, list) and len(cache_data) > 0:
                                # Convert cache data to Source objects
                                sources = []
                                for item in cache_data:
                                    sources.append(Source(
                                        url=item.get('url', ''),
                                        title=item.get('title', ''),
                                        author=item.get('author'),
                                        publication_date=item.get('publication_date'),
                                        site_name=item.get('site_name'),
                                        content=item.get('content', ''),
                                        snippet=item.get('snippet', ''),
                                        access_date=item.get('access_date', datetime.now().strftime("%Y-%m-%d")),
                                        reliability_score=item.get('reliability_score', 0.5),
                                        content_hash=item.get('content_hash', '')
                                    ))
                                
                                logger.info(f"Using cached search results for query: {query}")
                                return sources[:max_results]
                except Exception as cache_error:
                    logger.error(f"Error reading cache: {str(cache_error)}")
            
            # Perform search
            search_results = self.perform_search(query)
            if not search_results:
                return []
            
            # Select relevant pages
            selected_urls = self.select_relevant_pages(search_results[:max_results * 2], query)
            if not selected_urls:
                return []
            
            # Scrape content
            scraped_content = self.scrape_content(selected_urls)
            if not scraped_content and "search_results" not in scraped_content:
                return []
            
            # Create Source objects with metadata and reliability scores
            sources = []
            
            if "search_results" in scraped_content:
                # Create sources from search results if content scraping failed
                for i, result in enumerate(search_results[:max_results]):
                    if 'href' not in result or 'title' not in result:
                        continue
                        
                    url = result['href']
                    title = result['title']
                    snippet = result.get('body', '')[:self.SNIPPET_LENGTH]
                    
                    reliability_score = self._calculate_reliability_score(url)
                    
                    sources.append(Source(
                        url=url,
                        title=title,
                        snippet=snippet,
                        reliability_score=reliability_score
                    ))
            else:
                # Create sources from scraped content
                for url, content in scraped_content.items():
                    # Find matching title from search results
                    title = next((r['title'] for r in search_results if r.get('href') == url), "Unknown Title")
                    
                    # Create snippet
                    snippet = self._create_snippet(content)
                    
                    # Calculate reliability score
                    reliability_score = self._calculate_reliability_score(url)
                    
                    # Extract metadata
                    metadata = self._extract_publication_metadata(url, content)
                    
                    # Generate content hash
                    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
                    
                    sources.append(Source(
                        url=url,
                        title=title,
                        author=metadata["author"],
                        publication_date=metadata["publication_date"],
                        site_name=metadata["site_name"],
                        content=content,
                        snippet=snippet,
                        reliability_score=reliability_score,
                        content_hash=content_hash
                    ))
            
            # Sort sources by reliability score
            sources.sort(key=lambda s: s.reliability_score, reverse=True)
            
            # Cache the results
            try:
                cache_data = []
                for source in sources:
                    cache_data.append({
                        "url": source.url,
                        "title": source.title,
                        "author": source.author,
                        "publication_date": source.publication_date,
                        "site_name": source.site_name,
                        "content": source.content,
                        "snippet": source.snippet,
                        "access_date": source.access_date,
                        "reliability_score": source.reliability_score,
                        "content_hash": source.content_hash
                    })
                
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
            except Exception as cache_error:
                logger.error(f"Error writing cache: {str(cache_error)}")
            
            return sources[:max_results]
            
        except Exception as e:
            logger.error(f"Error in search: {str(e)}")
            return []
    
    def search_and_improve(self, query: str) -> Dict[str, Any]:
        """Enhanced search and synthesis function with source tracking and citations
        
        Returns a dictionary containing:
        - answer: The synthesized answer
        - sources: List of sources used
        - citations: Formatted citations
        - reliability: Overall reliability score
        """
        try:
            # Validate query
            self._validate_query(query)
            
            # Get sources
            sources = self.search(query)
            if not sources:
                # No sources found - return a fallback answer
                fallback = self.synthesize_final_answer(query)
                return {
                    "answer": fallback,
                    "sources": [],
                    "citations": [],
                    "reliability": 0.0
                }
            
            # Prepare content for synthesis
            content_for_synthesis = ""
            citations = []
            citation_markers = {}
            
            # Prepare citations and content
            for i, source in enumerate(sources, 1):
                # Generate citation
                citation = source.generate_citation()
                citations.append(citation)
                
                # Create citation marker
                marker = f"[{i}]"  # [1], [2], etc.
                citation_markers[source.url] = marker
                
                # Add content with citation marker
                if source.content:
                    content_for_synthesis += f"\n{marker} From {source.title} ({source.url}):\n{source.content[:2000]}\n\n"
                else:
                    content_for_synthesis += f"\n{marker} From {source.title} ({source.url}):\n{source.snippet}\n\n"
            
            # Calculate overall reliability
            if sources:
                overall_reliability = sum(s.reliability_score for s in sources) / len(sources)
            else:
                overall_reliability = 0.0
            
            # Generate synthesis prompt with citation instructions
            synthesis_prompt = f"""
Based on the following research content, provide a comprehensive answer to the query: "{query}"

Research Content:
{content_for_synthesis}

Instructions:
1. Synthesize the information into a clear, well-organized response
2. Focus on directly answering the query with factual information
3. Use the citation markers [1], [2], etc. when referencing information from specific sources
4. Include relevant details and context from the sources
5. Be objective and accurate
6. Acknowledge any limitations or uncertainties in the available information
7. If sources disagree, present multiple perspectives with their respective citations

Overall source reliability: {overall_reliability:.2f}/1.00

Response:
"""
            
            # Generate response with retry
            try:
                response = self.llm.generate(
                    synthesis_prompt,
                    max_tokens=1500,
                    temperature=0.7
                )
                
                # Create result dictionary
                result = {
                    "answer": response.strip(),
                    "sources": [{
                        "url": s.url,
                        "title": s.title,
                        "reliability": s.reliability_score
                    } for s in sources],
                    "citations": citations,
                    "reliability": overall_reliability
                }
                
                return result
                
            except Exception as e:
                logger.error(f"Error generating synthesis: {str(e)}")
                fallback = self.synthesize_final_answer(query)
                return {
                    "answer": fallback,
                    "sources": [{
                        "url": s.url,
                        "title": s.title,
                        "reliability": s.reliability_score
                    } for s in sources],
                    "citations": citations,
                    "reliability": overall_reliability
                }
            
        except Exception as e:
            logger.error(f"Error in search and improve: {str(e)}")
            fallback = self.synthesize_final_answer(query)
            return {
                "answer": fallback,
                "sources": [],
                "citations": [],
                "reliability": 0.0
            }

    def synthesize_final_answer(self, user_query: str) -> str:
        """Generate final answer with improved error handling and specific recommendations"""
        try:
            # Extract key terms for recommendations
            key_terms = re.findall(r'\b\w{4,}\b', user_query.lower())
            key_terms = [term for term in key_terms if term not in {
                'what', 'when', 'where', 'which', 'who', 'whose', 'whom', 'why', 'how',
                'does', 'could', 'would', 'should', 'about', 'with', 'from', 'have', 'this'
            }]
            
            prompt = f"""
After extensive research, I couldn't find sufficient reliable information to fully answer the user's question: "{user_query}"

Please provide the best possible answer you can based on general knowledge, acknowledging the limitations.

Then, offer specific suggestions on:
1. How the user might refine their question to get better results
2. Alternative phrasings that might yield better information
3. More specific sub-questions that might be more answerable
4. Reliable sources they could consult directly

Key terms identified in the query: {', '.join(key_terms) if key_terms else 'None identified'}

Respond in a clear, helpful, and informative manner.
"""
            response = self.llm.generate(
                prompt,
                max_tokens=1024,
                temperature=0.7
            )
            if response:
                return response.strip()
                
        except Exception as e:
            logger.error(f"Error in synthesize_final_answer: {str(e)}")
            
        return (
            "I apologize, but I couldn't find reliable information to answer your question adequately. "
            "This could be due to the question's complexity or limited available sources.\n\n"
            "You might try:\n"
            "- Rephrasing your question with more specific terms\n"
            "- Breaking it down into smaller, more focused questions\n"
            "- Specifying a time period or context if applicable\n"
            "- Consulting specialized sources on this topic"
        )