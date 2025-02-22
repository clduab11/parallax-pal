from typing import Optional, Dict, List, Any
import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import validators
import time
from .monitoring import structured_logger
from .config import settings

logger = logging.getLogger(__name__)

class WebScraperError(Exception):
    """Custom exception for web scraping errors"""
    pass

class RateLimitExceeded(WebScraperError):
    """Exception for rate limit violations"""
    pass

class WebScraper:
    """Asynchronous web scraper with rate limiting and monitoring"""
    
    def __init__(self):
        self.session = None
        self.rate_limit = settings.RATE_LIMIT_REQUESTS
        self.rate_period = settings.RATE_LIMIT_PERIOD
        self.requests = []
        self.user_agent = (
            "Mozilla/5.0 (compatible; ParallaxPal/1.0; "
            "+https://parallaxanalytics.com/bot)"
        )

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": self.user_agent}
            )

    async def _cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None

    def _check_rate_limit(self, domain: str):
        """Check if rate limit is exceeded for domain"""
        current_time = time.time()
        # Remove old requests
        self.requests = [
            r for r in self.requests
            if current_time - r["timestamp"] < self.rate_period
        ]
        
        # Count requests for this domain
        domain_requests = len([
            r for r in self.requests
            if r["domain"] == domain
        ])
        
        if domain_requests >= self.rate_limit:
            raise RateLimitExceeded(
                f"Rate limit exceeded for domain {domain}"
            )

    async def _make_request(
        self,
        url: str,
        timeout: int = 30
    ) -> str:
        """Make HTTP request with rate limiting"""
        domain = urlparse(url).netloc
        self._check_rate_limit(domain)
        
        await self._ensure_session()
        
        try:
            async with self.session.get(url, timeout=timeout) as response:
                self.requests.append({
                    "timestamp": time.time(),
                    "domain": domain
                })
                
                if response.status == 429:  # Too Many Requests
                    raise RateLimitExceeded(
                        f"Server rate limit exceeded for {domain}"
                    )
                    
                if response.status != 200:
                    raise WebScraperError(
                        f"HTTP {response.status} error for {url}"
                    )
                    
                return await response.text()
                
        except asyncio.TimeoutError:
            raise WebScraperError(f"Timeout accessing {url}")
        except Exception as e:
            raise WebScraperError(f"Error accessing {url}: {str(e)}")

    async def scrape(
        self,
        url: str,
        selectors: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Scrape content from URL with optional CSS selectors
        
        Args:
            url: URL to scrape
            selectors: Dict of CSS selectors to extract specific content
            
        Returns:
            Dict containing scraped content
        """
        if not validators.url(url):
            raise WebScraperError(f"Invalid URL: {url}")
            
        try:
            start_time = time.time()
            html = await self._make_request(url)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.select('script, style, nav, footer, iframe'):
                element.decompose()
            
            result = {
                "url": url,
                "title": soup.title.string if soup.title else None,
                "text": soup.get_text(separator=' ', strip=True)
            }
            
            # Extract content using provided selectors
            if selectors:
                result["selected_content"] = {}
                for key, selector in selectors.items():
                    elements = soup.select(selector)
                    result["selected_content"][key] = [
                        el.get_text(separator=' ', strip=True)
                        for el in elements
                    ]
            
            processing_time = int((time.time() - start_time) * 1000)
            
            structured_logger.log("info", "Content scraped successfully",
                url=url,
                processing_time_ms=processing_time,
                content_length=len(result["text"])
            )
            
            return result
            
        except Exception as e:
            structured_logger.log("error", "Scraping failed",
                url=url,
                error=str(e)
            )
            raise

class MultiScraper:
    """Manage multiple parallel scraping operations"""
    
    def __init__(self, max_concurrent: int = 5):
        self.scraper = WebScraper()
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def scrape_urls(
        self,
        urls: List[str],
        selectors: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs concurrently
        
        Args:
            urls: List of URLs to scrape
            selectors: Optional CSS selectors to extract specific content
            
        Returns:
            List of scraping results
        """
        async def _scrape_with_semaphore(url: str) -> Optional[Dict[str, Any]]:
            async with self.semaphore:
                try:
                    return await self.scraper.scrape(url, selectors)
                except WebScraperError as e:
                    logger.warning(f"Failed to scrape {url}: {str(e)}")
                    return None
        
        tasks = [_scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors and failed requests
        valid_results = [
            result for result in results
            if isinstance(result, dict)
        ]
        
        structured_logger.log("info", "Batch scraping completed",
            total_urls=len(urls),
            successful=len(valid_results),
            failed=len(urls) - len(valid_results)
        )
        
        return valid_results

    async def cleanup(self):
        """Cleanup resources"""
        await self.scraper._cleanup()

# Initialize global scraper instance
scraper = WebScraper()