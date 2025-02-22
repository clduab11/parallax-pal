from typing import List, Dict, Any, Optional
import aiohttp
import asyncio
import logging
import json
import os
from .config import settings
from .monitoring import structured_logger
from .cache import cache

logger = logging.getLogger(__name__)

class LLMError(Exception):
    """Custom exception for LLM-related errors"""
    pass

class LLMWrapper:
    """Asynchronous wrapper for LLM interactions"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.MAX_TOKENS
        self._session = None
        
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

    async def _cleanup(self):
        """Cleanup resources"""
        if self._session:
            await self._session.close()
            self._session = None

    async def analyze(
        self,
        query: str,
        content: str,
        url: str,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Analyze content in context of query
        
        Args:
            query: Research query
            content: Content to analyze
            url: Source URL
            max_tokens: Optional token limit override
            
        Returns:
            Analysis result
        """
        cache_key = f"analysis_{hash(f'{query}_{url}_{content[:100]}')})"
        
        if settings.ENABLE_CACHING:
            cached = cache.get(cache_key)
            if cached:
                structured_logger.log("debug", "Cache hit for content analysis",
                    url=url,
                    query_length=len(query)
                )
                return cached
        
        try:
            await self._ensure_session()
            
            prompt = f"""
            Analyze the following content in the context of this research query:
            
            QUERY: {query}
            
            CONTENT FROM {url}:
            {content[:4000]}  # Limit content length
            
            Provide a concise analysis focusing on relevance to the query.
            Include key insights and findings.
            """
            
            async with self._session.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens or self.max_tokens,
                    "temperature": 0.7
                }
            ) as response:
                if response.status != 200:
                    error_detail = await response.text()
                    raise LLMError(f"API error: {error_detail}")
                    
                result = await response.json()
                analysis = result['choices'][0]['message']['content']
                
                if settings.ENABLE_CACHING:
                    cache.set(cache_key, analysis, timeout=3600)
                
                return analysis
                
        except Exception as e:
            logger.error(f"Error in content analysis: {str(e)}")
            raise LLMError(f"Analysis failed: {str(e)}")

    async def synthesize(
        self,
        query: str,
        analyses: List[Dict[str, str]]
    ) -> str:
        """
        Synthesize multiple analyses into coherent findings
        
        Args:
            query: Original research query
            analyses: List of analysis results with their sources
            
        Returns:
            Synthesized findings
        """
        try:
            await self._ensure_session()
            
            analyses_text = "\n\n".join([
                f"Source {i+1} ({analysis['url']}):\n{analysis['analysis']}"
                for i, analysis in enumerate(analyses)
            ])
            
            prompt = f"""
            Synthesize the following analyses into coherent research findings.
            
            RESEARCH QUERY: {query}
            
            ANALYSES:
            {analyses_text}
            
            Provide a comprehensive synthesis that:
            1. Addresses the research query directly
            2. Integrates insights from multiple sources
            3. Highlights key findings and patterns
            4. Notes any conflicting information
            5. Suggests areas for further research
            """
            
            async with self._session.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": self.max_tokens,
                    "temperature": 0.7
                }
            ) as response:
                if response.status != 200:
                    error_detail = await response.text()
                    raise LLMError(f"API error: {error_detail}")
                    
                result = await response.json()
                return result['choices'][0]['message']['content']
                
        except Exception as e:
            logger.error(f"Error in synthesis: {str(e)}")
            raise LLMError(f"Synthesis failed: {str(e)}")

    async def generate_follow_up_questions(
        self,
        synthesis: str,
        previous_queries: List[str],
        max_questions: int = 3
    ) -> List[str]:
        """
        Generate follow-up research questions based on synthesis
        
        Args:
            synthesis: Current research synthesis
            previous_queries: List of previous research queries
            max_questions: Maximum number of questions to generate
            
        Returns:
            List of follow-up questions
        """
        try:
            await self._ensure_session()
            
            previous_queries_text = "\n".join([
                f"- {query}" for query in previous_queries
            ])
            
            prompt = f"""
            Based on the following research synthesis and previous queries,
            generate {max_questions} focused follow-up questions for deeper research.
            
            PREVIOUS QUERIES:
            {previous_queries_text}
            
            CURRENT SYNTHESIS:
            {synthesis}
            
            Generate questions that:
            1. Address gaps in current findings
            2. Explore promising angles
            3. Seek clarification on inconsistencies
            4. Are specific and actionable
            
            Format each question on a new line, prefixed with "Q: "
            """
            
            async with self._session.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.8
                }
            ) as response:
                if response.status != 200:
                    error_detail = await response.text()
                    raise LLMError(f"API error: {error_detail}")
                    
                result = await response.json()
                content = result['choices'][0]['message']['content']
                
                # Extract questions from response
                questions = [
                    line.replace("Q:", "").strip()
                    for line in content.split("\n")
                    if line.strip().startswith("Q:")
                ]
                
                return questions[:max_questions]
                
        except Exception as e:
            logger.error(f"Error generating follow-up questions: {str(e)}")
            raise LLMError(f"Question generation failed: {str(e)}")

# Initialize global LLM instance
llm = LLMWrapper()