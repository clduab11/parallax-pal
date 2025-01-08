import requests
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urljoin
import time
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Set
from duckduckgo_search import DDGS
from llm_config import LLM_CONFIG_OLLAMA
from tenacity import retry, stop_after_attempt, wait_exponential
import mimetypes
from collections import defaultdict
from contextlib import contextmanager

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

class MultiSearcher:
    def __init__(self, user_agent: str = "ParallaxPal/1.0", rate_limit: float = 1.0,
                 timeout: int = 30, max_retries: int = 3, max_content_size: int = 5 * 1024 * 1024):
        """Initialize with improved configuration and resource management"""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br"
        })
        self.robot_parser = RobotFileParser()
        self.rate_limiter = RateLimiter(rate_limit)
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_content_size = max_content_size
        self.config = LLM_CONFIG_OLLAMA['search_apis']
        self.robots_cache: Dict[str, RobotFileParser] = {}

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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def scrape_url(self, url: str) -> Optional[str]:
        """Scrape content from a single URL with improved error handling"""
        domain = self._get_domain(url)
        
        try:
            if not self._check_robots(url):
                logger.warning(f"URL not allowed by robots.txt: {url}")
                return None

            self.rate_limiter.wait(domain)
            
            response = self.session.get(
                url,
                timeout=self.timeout,
                stream=True  # Enable streaming
            )
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get('content-type', '').split(';')[0]
            if not self._is_valid_content_type(content_type):
                logger.warning(f"Invalid content type for {url}: {content_type}")
                return None

            # Check content length
            content_length = int(response.headers.get('content-length', 0))
            if content_length > self.max_content_size:
                logger.warning(f"Content too large for {url}: {content_length} bytes")
                return None

            # Read content in chunks
            content = ''
            for chunk in response.iter_content(chunk_size=8192, decode_unicode=True):
                if chunk:
                    content += chunk
                if len(content) > self.max_content_size:
                    logger.warning(f"Content exceeded max size while streaming: {url}")
                    break

            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe']):
                element.decompose()
            
            text = soup.get_text(separator=' ', strip=True)
            return self._clean_content(text)

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return None

    def get_web_content(self, urls: List[str]) -> Dict[str, str]:
        """Get content from multiple URLs with parallel processing"""
        if not urls:
            return {}

        content = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {
                executor.submit(self.scrape_url, url): url
                for url in urls
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    if result:
                        content[url] = result
                except Exception as e:
                    logger.error(f"Error processing {url}: {str(e)}")

        return content

def get_web_content(urls: List[str]) -> Dict[str, str]:
    """Helper function to get web content"""
    with MultiSearcher() as scraper:
        return scraper.get_web_content(urls)

def can_fetch(url: str) -> bool:
    """Helper function to check if URL can be fetched"""
    with MultiSearcher() as scraper:
        return scraper._check_robots(url)
