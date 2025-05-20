import requests
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urljoin
import time
import logging
import re
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Set, Tuple, NamedTuple, Any, Union
from duckduckgo_search import DDGS
from dotenv import load_dotenv
from llm_config import LLM_CONFIG_OLLAMA
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import mimetypes
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from dataclasses import dataclass, field
import random
from html import unescape
import hashlib

# Load environment variables first
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter with per-domain tracking"""
    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit
        self.last_request_times = defaultdict(float)
    
    def wait(self, domain: str) -> None:
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_times[domain]
        if time_since_last_request < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last_request)
        self.last_request_times[domain] = time.time()

class WebScraperError(Exception):
    """Custom exception for web scraping errors"""
    pass

@dataclass
class ScrapedContent:
    """Enhanced container for scraped content with metadata"""
    url: str
    content: str
    title: str = ""
    author: Optional[str] = None
    description: Optional[str] = None
    publication_date: Optional[str] = None
    site_name: Optional[str] = None
    access_time: str = field(default_factory=lambda: datetime.now().isoformat())
    content_type: str = "text/html"
    word_count: int = 0
    content_hash: str = ""
    status_code: int = 200
    is_valid: bool = True
    error_message: Optional[str] = None
    
    def __post_init__(self):
        # Calculate word count if not already set
        if self.content and not self.word_count:
            self.word_count = len(re.findall(r'\b\w+\b', self.content))
            
        # Generate content hash if not set
        if self.content and not self.content_hash:
            self.content_hash = hashlib.md5(self.content.encode('utf-8')).hexdigest()
            
        # Check validity
        if not self.content or self.word_count < 50:
            self.is_valid = False


class MultiSearcher:
    def __init__(self, user_agent: str = "ParallaxPal/1.0", rate_limit: float = 1.0,
                 timeout: int = 30, max_retries: int = 3, max_content_size: int = 5 * 1024 * 1024):
        """Initialize with improved configuration and resource management"""
        # Choose from multiple realistic user agents to avoid detection
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        # Create a session with random user agent
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive"
        })
        
        self.robot_parser = RobotFileParser()
        self.rate_limiter = RateLimiter(rate_limit)
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_content_size = max_content_size
        self.config = LLM_CONFIG_OLLAMA['search_apis']
        self.robots_cache: Dict[str, RobotFileParser] = {}
        
        # Create cache directory
        self.cache_dir = os.path.join(os.getcwd(), "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Tracking for rate limiting
        self.last_search_time = 0
        self.search_interval = 2.0  # seconds between searches

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self) -> None:
        """Clean up resources"""
        if self.session:
            self.session.close()

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        return urlparse(url).netloc

    def _check_robots(self, url: str) -> bool:
        """Check robots.txt with caching"""
        domain = self._get_domain(url)
        if domain not in self.robots_cache:
            rp = RobotFileParser()
            try:
                robots_url = f"https://{domain}/robots.txt"
                response = self.session.get(robots_url, timeout=self.timeout)
                if response.status_code == 200:
                    rp.parse(response.text.splitlines())
                else:
                    rp.allow_all = True
            except Exception:
                rp.allow_all = True
            self.robots_cache[domain] = rp
        return self.robots_cache[domain].can_fetch("ParallaxPal", url)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def _search_brave(self, query: str) -> List[Dict]:
        """Search using Brave Search API with retries"""
        if not (self.config['brave']['enabled'] and self.config['brave']['api_key']):
            return []

        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.config['brave']['api_key'].strip()
            }
            params = {
                'q': query,
                'count': self.config['brave']['max_results'],
                'text_format': 'raw',
                'search_lang': 'en'
            }

            response = self.session.get(
                url,
                headers=headers,
                params=params,
                timeout=self.config['brave']['timeout']
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            for r in data.get('web', {}).get('results', []):
                if r.get('url'):
                    results.append({
                        'title': r.get('title', 'No title'),
                        'href': r['url'],
                        'body': r.get('description', 'No description available')
                    })
            return results

        except Exception as e:
            logger.error(f"Brave search error: {str(e)}")
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def _search_tavily(self, query: str) -> List[Dict]:
        """Search using Tavily API with retries"""
        if not (self.config['tavily']['enabled'] and self.config['tavily']['api_key']):
            return []

        try:
            url = "https://api.tavily.com/search"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config['tavily']['api_key'].strip()}"
            }
            data = {
                "query": query,
                "max_results": self.config['tavily']['max_results'],
                "include_answer": True,
                "include_raw_content": True
            }

            response = self.session.post(
                url,
                headers=headers,
                json=data,
                timeout=self.config['tavily']['timeout']
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            for r in data.get('results', []):
                if r.get('url'):
                    results.append({
                        'title': r.get('title', 'No title'),
                        'href': r['url'],
                        'body': r.get('content', r.get('raw_content', 'No content available'))
                    })
            return results

        except Exception as e:
            logger.error(f"Tavily search error: {str(e)}")
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def _search_duckduckgo(self, query: str) -> List[Dict]:
        """Search using DuckDuckGo with retries"""
        if not self.config['duckduckgo']['enabled']:
            return []

        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(
                    query,
                    max_results=self.config['duckduckgo']['max_results']
                ):
                    if isinstance(r, dict) and r.get('link'):
                        results.append({
                            'title': r.get('title', 'No title'),
                            'href': r['link'],
                            'body': r.get('body', 'No description available')
                        })
            return results

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {str(e)}")
            return []

    def search_all_engines(self, query: str, time_range: str = 'none') -> List[Dict]:
        """Search using all configured search engines with deduplication"""
        if not isinstance(query, str):
            raise ValueError("Query must be a string")

        results = []
        seen_urls: Set[str] = set()

        # Collect results from all enabled search engines
        search_functions = [
            ('brave', self._search_brave),
            ('tavily', self._search_tavily),
            ('duckduckgo', self._search_duckduckgo)
        ]

        for engine_name, search_func in search_functions:
            try:
                engine_results = search_func(query)
                for result in engine_results:
                    url = result.get('href')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        results.append(result)
            except Exception as e:
                logger.error(f"{engine_name.capitalize()} search failed: {str(e)}")

        return results[:10]  # Return top 10 unique results

    def _is_valid_content_type(self, content_type: str) -> bool:
        """Check if content type is valid for scraping"""
        valid_types = {'text/html', 'application/xhtml+xml', 'text/plain'}
        return any(valid_type in content_type.lower() for valid_type in valid_types)

    def _clean_content(self, content: str) -> str:
        """Clean and normalize scraped content"""
        # Remove script and style elements
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
        
        # Remove HTML comments
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        # Remove extra whitespace
        content = ' '.join(content.split())
        
        return content[:self.max_content_size]  # Limit content size

    def _extract_metadata_from_soup(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from BeautifulSoup object"""
        metadata = {
            "title": "",
            "author": None,
            "description": None,
            "publication_date": None,
            "site_name": None
        }
        
        try:
            # Extract title
            if soup.title and soup.title.string:
                metadata["title"] = soup.title.string.strip()
            
            # Try extracting metadata from meta tags
            meta_tags = {
                # Format: meta_property: metadata_key
                "og:title": "title",
                "og:site_name": "site_name",
                "og:description": "description",
                "article:published_time": "publication_date",
                "article:author": "author",
                "author": "author",
                "description": "description",
                "twitter:title": "title",
                "twitter:description": "description",
                "article:published": "publication_date"
            }
            
            for tag in soup.find_all("meta"):
                # Check for property attribute
                if tag.get("property") and tag.get("content"):
                    if tag["property"] in meta_tags and not metadata[meta_tags[tag["property"]]]:
                        metadata[meta_tags[tag["property"]]] = tag["content"]
                
                # Check for name attribute
                if tag.get("name") and tag.get("content"):
                    if tag["name"] in meta_tags and not metadata[meta_tags[tag["name"]]]:
                        metadata[meta_tags[tag["name"]]] = tag["content"]
            
            # If title not found in meta, look for first h1
            if not metadata["title"]:
                h1 = soup.find("h1")
                if h1 and h1.text:
                    metadata["title"] = h1.text.strip()
            
            # Extract author from various places if not found in meta
            if not metadata["author"]:
                # Try common author patterns
                author_patterns = [
                    soup.find("a", {"rel": "author"}),
                    soup.find("span", {"class": "author"}),
                    soup.find("div", {"class": "author"}),
                    soup.find("p", {"class": "author"}),
                    soup.find("a", {"class": "author"})
                ]
                
                for pattern in author_patterns:
                    if pattern and pattern.text and len(pattern.text.strip()) > 0:
                        metadata["author"] = pattern.text.strip()
                        break
            
            # Extract site name from URL if not found
            if not metadata["site_name"]:
                parsed_url = urlparse(url)
                metadata["site_name"] = parsed_url.netloc.replace("www.", "")
            
            # Clean and normalize all values
            for key, value in metadata.items():
                if value and isinstance(value, str):
                    metadata[key] = re.sub(r'\s+', ' ', value).strip()
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {url}: {str(e)}")
            # Return base metadata with site name from URL
            parsed_url = urlparse(url)
            metadata["site_name"] = parsed_url.netloc.replace("www.", "")
            return metadata
    
    def _check_cache(self, url: str) -> Optional[ScrapedContent]:
        """Check if URL content is cached"""
        try:
            url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
            cache_file = os.path.join(self.cache_dir, f"{url_hash}.json")
            
            if os.path.exists(cache_file):
                # Check if cache is recent (less than 24 hours)
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < 86400:  # 24 hours in seconds
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return ScrapedContent(
                            url=data.get("url", url),
                            content=data.get("content", ""),
                            title=data.get("title", ""),
                            author=data.get("author"),
                            description=data.get("description"),
                            publication_date=data.get("publication_date"),
                            site_name=data.get("site_name"),
                            access_time=data.get("access_time", datetime.now().isoformat()),
                            content_type=data.get("content_type", "text/html"),
                            word_count=data.get("word_count", 0),
                            content_hash=data.get("content_hash", ""),
                            status_code=data.get("status_code", 200),
                            is_valid=data.get("is_valid", True),
                            error_message=data.get("error_message")
                        )
        except Exception as e:
            logger.error(f"Error checking cache for {url}: {str(e)}")
        
        return None
    
    def _save_to_cache(self, content: ScrapedContent) -> None:
        """Save scraped content to cache"""
        try:
            url_hash = hashlib.md5(content.url.encode('utf-8')).hexdigest()
            cache_file = os.path.join(self.cache_dir, f"{url_hash}.json")
            
            data = {
                "url": content.url,
                "content": content.content,
                "title": content.title,
                "author": content.author,
                "description": content.description,
                "publication_date": content.publication_date,
                "site_name": content.site_name,
                "access_time": content.access_time,
                "content_type": content.content_type,
                "word_count": content.word_count,
                "content_hash": content.content_hash,
                "status_code": content.status_code,
                "is_valid": content.is_valid,
                "error_message": content.error_message
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving cache for {content.url}: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def scrape_url(self, url: str) -> Optional[ScrapedContent]:
        """Scrape content from a single URL with improved error handling and metadata extraction"""
        # First check cache
        cached_content = self._check_cache(url)
        if cached_content:
            logger.info(f"Using cached content for {url}")
            return cached_content
        
        domain = self._get_domain(url)
        
        try:
            if not self._check_robots(url):
                logger.warning(f"URL not allowed by robots.txt: {url}")
                return ScrapedContent(
                    url=url,
                    content="",
                    is_valid=False,
                    error_message="URL not allowed by robots.txt"
                )

            self.rate_limiter.wait(domain)
            
            response = self.session.get(
                url,
                timeout=self.timeout,
                stream=True,  # Enable streaming
                headers={
                    # Add random referer to avoid blocking
                    "Referer": "https://www.google.com/"
                }
            )
            
            # Save status code for reporting
            status_code = response.status_code
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get('content-type', '').split(';')[0]
            if not self._is_valid_content_type(content_type):
                logger.warning(f"Invalid content type for {url}: {content_type}")
                return ScrapedContent(
                    url=url,
                    content="",
                    content_type=content_type,
                    status_code=status_code,
                    is_valid=False,
                    error_message=f"Invalid content type: {content_type}"
                )

            # Check content length
            content_length = int(response.headers.get('content-length', 0))
            if content_length > self.max_content_size:
                logger.warning(f"Content too large for {url}: {content_length} bytes")
                return ScrapedContent(
                    url=url,
                    content="",
                    content_type=content_type,
                    status_code=status_code,
                    is_valid=False,
                    error_message=f"Content too large: {content_length} bytes"
                )

            # Read content in chunks
            content = ''
            for chunk in response.iter_content(chunk_size=8192, decode_unicode=False):
                if chunk:
                    try:
                        # Try to decode chunk with different encodings
                        decoded_chunk = chunk.decode('utf-8', errors='replace')
                    except UnicodeDecodeError:
                        try:
                            decoded_chunk = chunk.decode('latin-1', errors='replace')
                        except UnicodeDecodeError:
                            decoded_chunk = chunk.decode('ascii', errors='replace')
                    
                    content += decoded_chunk
                    
                if len(content) > self.max_content_size:
                    logger.warning(f"Content exceeded max size while streaming: {url}")
                    break

            # Parse HTML with BeautifulSoup for better content extraction
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract metadata before cleaning
            metadata = self._extract_metadata_from_soup(soup, url)
            
            # Remove unwanted elements for cleaner text extraction
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe', 'noscript']):
                element.decompose()
            
            # Get main content - first try main article content
            main_content = None
            main_elements = soup.select('article, [role="main"], .main-content, #main-content, .post-content, .article-content')
            if main_elements:
                main_content = max(main_elements, key=lambda x: len(x.text.strip()))
            
            # If no main content found, use the body
            if not main_content or len(main_content.text.strip()) < 200:
                body = soup.body if soup.body else soup
                text = body.get_text(separator=' ', strip=True)
            else:
                text = main_content.get_text(separator=' ', strip=True)
            
            # Clean and normalize content
            cleaned_text = self._clean_content(text)
            
            # Create ScrapedContent object
            scraped_content = ScrapedContent(
                url=url,
                content=cleaned_text,
                title=metadata["title"],
                author=metadata["author"],
                description=metadata["description"],
                publication_date=metadata["publication_date"],
                site_name=metadata["site_name"],
                content_type=content_type,
                status_code=status_code,
                # Validate content
                is_valid=bool(cleaned_text and len(cleaned_text) >= 200)
            )
            
            # Cache the result
            self._save_to_cache(scraped_content)
            
            return scraped_content

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            error_content = ScrapedContent(
                url=url,
                content="",
                is_valid=False,
                error_message=str(e)
            )
            
            # Cache the error result too
            self._save_to_cache(error_content)
            
            return error_content

    def get_web_content(self, urls: List[str]) -> Dict[str, Union[str, ScrapedContent]]:
        """Get content from multiple URLs with parallel processing and enhanced error handling"""
        if not urls:
            return {}

        # Limit number of URLs to process
        urls = urls[:10]  # Process maximum 10 URLs at once
        
        # Check how many URLs we can process in parallel
        max_workers = min(5, len(urls))  # Use at most 5 workers
        
        content = {}
        scraped_contents = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(self.scrape_url, url): url
                for url in urls
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    if result and result.is_valid:
                        # Add to content dict for backwards compatibility
                        content[url] = result.content
                        # Also store full ScrapedContent objects
                        scraped_contents.append(result)
                except Exception as e:
                    logger.error(f"Error processing {url}: {str(e)}")

        # Add scraped_contents to the result for enhanced usage
        content["_scraped_contents"] = scraped_contents
        
        return content

def get_web_content(urls: List[str]) -> Dict[str, str]:
    """Helper function to get web content"""
    with MultiSearcher() as scraper:
        return scraper.get_web_content(urls)

def can_fetch(url: str) -> bool:
    """Helper function to check if URL can be fetched"""
    with MultiSearcher() as scraper:
        return scraper._check_robots(url)

# Export all necessary classes and functions
__all__ = ['MultiSearcher', 'WebScraperError', 'get_web_content', 'can_fetch']
