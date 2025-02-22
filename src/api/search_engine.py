from typing import List, Dict, Any, Optional
import aiohttp
import asyncio
import logging
from datetime import datetime
from duckduckgo_search import DDGS
from urllib.parse import urlparse
from .monitoring import structured_logger
from .cache import cache
from .config import settings

logger = logging.getLogger(__name__)

class SearchError(Exception):
    """Custom exception for search-related errors"""
    pass

class EnhancedSearchEngine:
    """Asynchronous search engine with caching and monitoring"""

    def __init__(self):
        self.session = None
        self._ddgs = None
        self.max_results = settings.SEARCH_RESULTS_LIMIT
        self.timeout = settings.SEARCH_TIMEOUT

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    @property
    def ddgs(self):
        """Lazy initialization of DuckDuckGo search"""
        if self._ddgs is None:
            self._ddgs = DDGS()
        return self._ddgs

    async def _cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None

    async def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform search with caching and monitoring
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            exclude_domains: List of domains to exclude
            
        Returns:
            List of search results
        """
        cache_key = f"search_{hash(query)}_{max_results}"
        
        if settings.ENABLE_CACHING:
            cached = cache.get(cache_key)
            if cached:
                structured_logger.log("debug", "Cache hit for search",
                    query=query,
                    results_count=len(cached)
                )
                return cached

        try:
            start_time = datetime.now()
            results = []
            
            # Perform DuckDuckGo search
            search_results = self.ddgs.text(
                query,
                max_results=max_results or self.max_results
            )
            
            for result in search_results:
                if len(results) >= (max_results or self.max_results):
                    break
                    
                # Skip excluded domains
                if exclude_domains:
                    domain = urlparse(result['link']).netloc
                    if any(ex_domain in domain for ex_domain in exclude_domains):
                        continue
                
                results.append({
                    'url': result['link'],
                    'title': result['title'],
                    'snippet': result['body'],
                    'domain': urlparse(result['link']).netloc
                })

            processing_time = int(
                (datetime.now() - start_time).total_seconds() * 1000
            )
            
            structured_logger.log("info", "Search completed",
                query=query,
                results_count=len(results),
                processing_time_ms=processing_time
            )
            
            if settings.ENABLE_CACHING:
                cache.set(cache_key, results, timeout=3600)  # Cache for 1 hour
            
            return results
            
        except Exception as e:
            structured_logger.log("error", "Search failed",
                query=query,
                error=str(e)
            )
            raise SearchError(f"Search failed: {str(e)}")

    async def enhanced_search(
        self,
        query: str,
        context: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform enhanced search with context awareness
        
        Args:
            query: Search query
            context: Additional context to improve search
            max_results: Maximum number of results
            
        Returns:
            List of enhanced search results
        """
        try:
            # Perform initial search
            results = await self.search(query, max_results=max_results)
            
            if not context:
                return results
                
            # Enhance results with context
            enhanced_results = []
            for result in results:
                relevance_score = self._calculate_relevance(
                    result['snippet'],
                    query,
                    context
                )
                result['relevance_score'] = relevance_score
                enhanced_results.append(result)
            
            # Sort by relevance
            enhanced_results.sort(
                key=lambda x: x['relevance_score'],
                reverse=True
            )
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Enhanced search failed: {str(e)}")
            raise SearchError(f"Enhanced search failed: {str(e)}")

    def _calculate_relevance(
        self,
        content: str,
        query: str,
        context: str
    ) -> float:
        """Calculate relevance score for content"""
        # Basic relevance scoring - can be enhanced with ML
        query_terms = set(query.lower().split())
        context_terms = set(context.lower().split())
        content_terms = set(content.lower().split())
        
        query_matches = len(query_terms.intersection(content_terms))
        context_matches = len(context_terms.intersection(content_terms))
        
        # Weight query matches more heavily than context matches
        score = (query_matches * 2 + context_matches) / (
            len(query_terms) * 2 + len(context_terms)
        )
        
        return min(score, 1.0)

class SearchManager:
    """Manage search operations with retries and fallbacks"""
    
    def __init__(self):
        self.search_engine = EnhancedSearchEngine()
        self.max_retries = settings.MAX_RETRIES
        self.retry_delay = settings.RETRY_DELAY

    async def search_with_retries(
        self,
        query: str,
        context: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform search with automatic retries
        
        Args:
            query: Search query
            context: Optional context
            max_results: Maximum results
            
        Returns:
            List of search results
        """
        for attempt in range(self.max_retries):
            try:
                if context:
                    results = await self.search_engine.enhanced_search(
                        query,
                        context,
                        max_results
                    )
                else:
                    results = await self.search_engine.search(
                        query,
                        max_results
                    )
                return results
                
            except SearchError as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    logger.warning(
                        f"Search attempt {attempt + 1} failed. "
                        f"Retrying in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise

    async def cleanup(self):
        """Cleanup resources"""
        await self.search_engine._cleanup()

# Initialize global search manager instance
search_manager = SearchManager()