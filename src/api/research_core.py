from typing import Dict, List, Optional
import logging
from llm_wrapper import LLMWrapper, LLMError
from llm_response_parser import UltimateLLMResponseParser
from search_engine import EnhancedSelfImprovingSearch, SearchError
from web_scraper import MultiSearcher, WebScraperError, get_web_content, can_fetch

logger = logging.getLogger(__name__)

class ResearchCore:
    """Core research functionality extracted from the original CLI application"""
    
    def __init__(self):
        self.llm = LLMWrapper()
        self.parser = UltimateLLMResponseParser()
        self.search_engine = EnhancedSelfImprovingSearch(self.llm, self.parser)
        
    async def process_research_query(
        self,
        query: str,
        continuous_mode: bool = False,
        max_iterations: int = 3
    ) -> Dict[str, any]:
        """
        Process a research query and return results
        
        Args:
            query: The research query to process
            continuous_mode: Whether to use continuous research mode
            max_iterations: Maximum number of research iterations
            
        Returns:
            Dict containing research results and metadata
        """
        try:
            logger.info(f"Starting research for query: {query}")
            
            # Initial search
            search_results = await self.search_engine.search(query)
            
            # Process and analyze results
            analyzed_data = []
            for result in search_results:
                content = await get_web_content(result['url'])
                if content:
                    analysis = await self.llm.analyze(
                        query=query,
                        content=content,
                        url=result['url']
                    )
                    analyzed_data.append({
                        'url': result['url'],
                        'analysis': analysis
                    })
            
            # Generate synthesis
            synthesis = await self.llm.synthesize(
                query=query,
                analyses=analyzed_data
            )
            
            # If in continuous mode, perform additional iterations
            if continuous_mode:
                for i in range(max_iterations - 1):
                    # Generate follow-up questions
                    follow_ups = await self.llm.generate_follow_up_questions(
                        synthesis=synthesis,
                        previous_queries=[query]
                    )
                    
                    # Process each follow-up
                    for follow_up in follow_ups[:2]:  # Limit to top 2 follow-ups
                        sub_results = await self.search_engine.search(follow_up)
                        for result in sub_results:
                            content = await get_web_content(result['url'])
                            if content:
                                analysis = await self.llm.analyze(
                                    query=follow_up,
                                    content=content,
                                    url=result['url']
                                )
                                analyzed_data.append({
                                    'url': result['url'],
                                    'analysis': analysis
                                })
                    
                    # Update synthesis with new information
                    synthesis = await self.llm.synthesize(
                        query=query,
                        analyses=analyzed_data
                    )
            
            return {
                'query': query,
                'synthesis': synthesis,
                'sources': [data['url'] for data in analyzed_data],
                'source_count': len(analyzed_data),
                'continuous_mode': continuous_mode,
                'iterations': max_iterations if continuous_mode else 1
            }
            
        except Exception as e:
            logger.error(f"Error during research: {str(e)}")
            raise
        
    async def validate_sources(self, sources: List[str]) -> List[str]:
        """Validate and filter research sources"""
        valid_sources = []
        for source in sources:
            if await can_fetch(source):
                valid_sources.append(source)
        return valid_sources
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.llm._cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

# Initialize global research core instance
research_core = ResearchCore()