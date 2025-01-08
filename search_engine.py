import logging
from typing import List, Dict, Optional, Set
from web_scraper import MultiSearcher, WebScraperError
from tenacity import retry, stop_after_attempt, wait_exponential
import time
from io import StringIO
import re
from contextlib import contextmanager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

class SearchError(Exception):
    """Custom exception for search-related errors"""
    pass

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
                    # Log results for debugging
                    for i, result in enumerate(valid_results[:self.MAX_DISPLAY_RESULTS], 1):
                        snippet = self._create_snippet(result.get('body', 'No description'))
                        logger.debug(
                            f"{i}. {result['title']}\n"
                            f"   URL: {result['href']}\n"
                            f"   Snippet: {snippet}"
                        )
                    
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

    def search_and_improve(self, query: str) -> str:
        """Main search and synthesis function with improved error handling"""
        try:
            # Validate query
            self._validate_query(query)
            
            # Perform search
            results = self.perform_search(query)
            if not results:
                return self.synthesize_final_answer(query)
            
            # Select relevant pages
            selected_urls = self.select_relevant_pages(results, query)
            if not selected_urls:
                return self.synthesize_final_answer(query)
            # Scrape content
            scraped_content = self.scrape_content(selected_urls)
            
            # Prepare content for synthesis
            content_for_synthesis = ""
            if "search_results" in scraped_content:
                # Use search result snippets if we couldn't scrape pages
                content_for_synthesis = "Based on search results:\n"
                for result in results[:5]:  # Use top 5 results
                    title = result.get('title', 'No title')
                    snippet = result.get('body', 'No description')
                    content_for_synthesis += f"\n- {title}\n  {snippet}\n"
            else:
                # Use scraped content if available
                content_for_synthesis = self.format_scraped_content(scraped_content)
                
            if not content_for_synthesis:
                return self.synthesize_final_answer(query)
                return self.synthesize_final_answer(query)
            
            # Generate synthesis prompt
            synthesis_prompt = f"""
Based on the following {'search results' if 'search_results' in scraped_content else 'research content'}, provide a comprehensive answer to the query: "{query}"

{'Search Results' if 'search_results' in scraped_content else 'Research Content'}:
{content_for_synthesis}

Instructions:
1. Synthesize the information into a clear, well-organized response
2. Focus on directly answering the query
3. Include relevant details and context
4. Be objective and accurate
5. {'Use the search result summaries to provide the best possible answer' if 'search_results' in scraped_content else 'Use the detailed content to provide a thorough answer'}
6. Acknowledge any limitations or uncertainties in the available information

Response:
"""
            
            # Generate response with retry
            try:
                response = self.llm.generate(
                    synthesis_prompt,
                    max_tokens=1000,
                    temperature=0.7
                )
                return response.strip()
            except Exception as e:
                logger.error(f"Error generating synthesis: {str(e)}")
                return self.synthesize_final_answer(query)
            
        except Exception as e:
            logger.error(f"Error in search and improve: {str(e)}")
            return self.synthesize_final_answer(query)

    def synthesize_final_answer(self, user_query: str) -> str:
        """Generate final answer with improved error handling"""
        try:
            prompt = f"""
After multiple search attempts, we couldn't find a fully satisfactory answer to the user's question: "{user_query}"

Please provide the best possible answer you can, acknowledging any limitations or uncertainties.
If appropriate, suggest ways the user might refine their question or where they might find more information.

Respond in a clear, concise, and informative manner.
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
            
        return ("I apologize but after multiple attempts I wasn't able to find a satisfactory answer to your question. "
                "Please try rephrasing your question or breaking it down into smaller more specific queries.")