from typing import Dict, List, Optional, Any
import logging
from .llm_wrapper import LLMWrapper, LLMError, AIModel
from .llm_response_parser import UltimateLLMResponseParser
from .search_engine import EnhancedSelfImprovingSearch, SearchError
from .web_scraper import MultiSearcher, WebScraperError, get_web_content, can_fetch

logger = logging.getLogger(__name__)

class ResearchCore:
    """Core research functionality with multi-model AI analysis"""
    
    def __init__(self):
        self.llm = LLMWrapper()
        self.parser = UltimateLLMResponseParser()
        self.search_engine = EnhancedSelfImprovingSearch(self.llm, self.parser)
        
    async def process_research_query(
        self,
        query: str,
        use_ollama: bool = False,
        continuous_mode: bool = False,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Process a research query using multiple AI models
        
        Args:
            query: The research query to process
            use_ollama: Whether to include Ollama model in analysis
            continuous_mode: Whether to use continuous research mode
            max_iterations: Maximum number of research iterations
            
        Returns:
            Dict containing research results and metadata
        """
        try:
            logger.info(f"Starting multi-model research for query: {query}")
            
            # Initial search
            search_results = await self.search_engine.search(query)
            
            # Process and analyze results with multiple models
            analyzed_data = []
            web_results = []
            
            for result in search_results:
                content = await get_web_content(result['url'])
                if content:
                    # Store web result
                    web_results.append({
                        'title': result.get('title', ''),
                        'url': result['url'],
                        'snippet': content[:200] + '...',  # Preview snippet
                        'source': result.get('source', 'web')
                    })
                    
                    # Get analysis from all AI models
                    analyses = await self.llm.analyze_with_all_models(
                        query=query,
                        content=content,
                        url=result['url'],
                        use_ollama=use_ollama
                    )
                    
                    analyzed_data.append({
                        'url': result['url'],
                        'analyses': analyses
                    })
            
            # Generate synthesis using all models
            synthesis_result = await self.llm.synthesize(
                query=query,
                analyses=[
                    analysis 
                    for data in analyzed_data 
                    for analysis in data['analyses']
                ],
                use_ollama=use_ollama
            )
            
            # If in continuous mode, perform additional iterations
            if continuous_mode:
                for i in range(max_iterations - 1):
                    # Generate follow-up questions from all models
                    follow_up_results = await self.llm.generate_follow_up_questions(
                        synthesis=synthesis_result['synthesis'],
                        previous_queries=[query],
                        use_ollama=use_ollama
                    )
                    
                    # Select questions with highest confidence
                    best_questions = max(follow_up_results, key=lambda x: x['confidence'])
                    
                    # Process each follow-up
                    for follow_up in best_questions['questions'][:2]:  # Limit to top 2 follow-ups
                        sub_results = await self.search_engine.search(follow_up)
                        for result in sub_results:
                            content = await get_web_content(result['url'])
                            if content:
                                # Store web result
                                web_results.append({
                                    'title': result.get('title', ''),
                                    'url': result['url'],
                                    'snippet': content[:200] + '...',
                                    'source': result.get('source', 'web')
                                })
                                
                                # Get analysis from all models
                                analyses = await self.llm.analyze_with_all_models(
                                    query=follow_up,
                                    content=content,
                                    url=result['url'],
                                    use_ollama=use_ollama
                                )
                                
                                analyzed_data.append({
                                    'url': result['url'],
                                    'analyses': analyses
                                })
                    
                    # Update synthesis with new information
                    synthesis_result = await self.llm.synthesize(
                        query=query,
                        analyses=[
                            analysis 
                            for data in analyzed_data 
                            for analysis in data['analyses']
                        ],
                        use_ollama=use_ollama
                    )
            
            # Collect all model analyses
            ai_analyses = []
            for data in analyzed_data:
                for analysis in data['analyses']:
                    ai_analyses.append({
                        'model': analysis['model'],
                        'analysis': analysis['analysis'],
                        'confidence': analysis['confidence']
                    })
            
            return {
                'query': query,
                'synthesis': synthesis_result['synthesis'],
                'web_results': web_results,
                'ai_analyses': ai_analyses,
                'source_count': len(web_results),
                'continuous_mode': continuous_mode,
                'iterations': max_iterations if continuous_mode else 1,
                'models_used': [
                    model.value for model in [
                        AIModel.OPENAI,
                        AIModel.ANTHROPIC,
                        AIModel.GEMINI
                    ] + ([AIModel.OLLAMA] if use_ollama else [])
                ]
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