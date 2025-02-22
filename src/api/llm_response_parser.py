from typing import Dict, List, Any, Optional, Union
import json
import re
import logging
from datetime import datetime
from .monitoring import structured_logger
from .cache import cache
from .config import settings

logger = logging.getLogger(__name__)

class ParserError(Exception):
    """Custom exception for parsing errors"""
    pass

class ResponseParser:
    """Parser for LLM response processing with caching and monitoring"""

    def __init__(self):
        self.cache_enabled = settings.ENABLE_CACHING
        self.cache_ttl = settings.CACHE_TTL

    async def parse_analysis(
        self,
        response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse research analysis response
        
        Args:
            response: Raw LLM response
            metadata: Optional metadata for context
            
        Returns:
            Parsed analysis with structured data
        """
        if not response:
            raise ParserError("Empty response received")

        cache_key = f"analysis_parse_{hash(response)}"
        if self.cache_enabled:
            cached = cache.get(cache_key)
            if cached:
                return cached

        try:
            # Extract key findings
            findings = self._extract_findings(response)
            
            # Extract sources and citations
            sources = self._extract_sources(response)
            
            # Extract recommendations
            recommendations = self._extract_recommendations(response)
            
            result = {
                "findings": findings,
                "sources": sources,
                "recommendations": recommendations,
                "raw_response": response,
                "metadata": metadata or {},
                "parsed_at": datetime.utcnow().isoformat()
            }
            
            if self.cache_enabled:
                cache.set(cache_key, result, timeout=self.cache_ttl)
                
            structured_logger.log("info", "Response parsed successfully",
                findings_count=len(findings),
                sources_count=len(sources)
            )
            
            return result
            
        except Exception as e:
            structured_logger.log("error", "Response parsing failed",
                error=str(e)
            )
            raise ParserError(f"Failed to parse analysis: {str(e)}")

    async def parse_synthesis(
        self,
        response: str,
        analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Parse research synthesis response
        
        Args:
            response: Raw LLM synthesis
            analyses: List of individual analyses
            
        Returns:
            Parsed synthesis with structured data
        """
        cache_key = f"synthesis_parse_{hash(response)}"
        if self.cache_enabled:
            cached = cache.get(cache_key)
            if cached:
                return cached

        try:
            # Extract main themes
            themes = self._extract_themes(response)
            
            # Extract conclusions
            conclusions = self._extract_conclusions(response)
            
            # Identify gaps and conflicts
            gaps = self._identify_gaps(response, analyses)
            conflicts = self._identify_conflicts(response, analyses)
            
            result = {
                "themes": themes,
                "conclusions": conclusions,
                "gaps": gaps,
                "conflicts": conflicts,
                "source_analyses": [
                    analysis.get("findings", [])
                    for analysis in analyses
                ],
                "raw_synthesis": response,
                "synthesized_at": datetime.utcnow().isoformat()
            }
            
            if self.cache_enabled:
                cache.set(cache_key, result, timeout=self.cache_ttl)
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse synthesis: {str(e)}")
            raise ParserError(f"Synthesis parsing failed: {str(e)}")

    def _extract_findings(self, text: str) -> List[str]:
        """Extract key findings from text"""
        findings = []
        
        # Look for findings in various formats
        patterns = [
            r"(?:Key )?Finding[s]?:?\s*([^\n]+)",
            r"•\s*([^\n]+)",
            r"\d+\.\s*([^\n]+)"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            findings.extend([
                match.group(1).strip()
                for match in matches
                if match.group(1).strip()
            ])
            
        return list(set(findings))  # Remove duplicates

    def _extract_sources(self, text: str) -> List[Dict[str, str]]:
        """Extract sources and citations"""
        sources = []
        
        # Match URLs
        urls = re.finditer(
            r'(?:https?://)?(?:[\w-]+\.)+[\w-]+(?:/[\w-]+)*/?',
            text
        )
        
        # Match citations
        citations = re.finditer(
            r'\[([^\]]+)\]|\(([^\)]+)\)',
            text
        )
        
        for url in urls:
            sources.append({
                "type": "url",
                "value": url.group(0)
            })
            
        for citation in citations:
            sources.append({
                "type": "citation",
                "value": citation.group(1) or citation.group(2)
            })
            
        return sources

    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from text"""
        recommendations = []
        
        patterns = [
            r"Recommendation[s]?:?\s*([^\n]+)",
            r"Suggest(?:ion|ed):?\s*([^\n]+)",
            r"(?:Should|Could):?\s*([^\n]+)"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            recommendations.extend([
                match.group(1).strip()
                for match in matches
                if match.group(1).strip()
            ])
            
        return list(set(recommendations))

    def _extract_themes(self, text: str) -> List[str]:
        """Extract main themes from synthesis"""
        themes = []
        
        patterns = [
            r"Theme[s]?:?\s*([^\n]+)",
            r"Key Point[s]?:?\s*([^\n]+)",
            r"Main Topic[s]?:?\s*([^\n]+)"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            themes.extend([
                match.group(1).strip()
                for match in matches
                if match.group(1).strip()
            ])
            
        return list(set(themes))

    def _extract_conclusions(self, text: str) -> List[str]:
        """Extract conclusions from synthesis"""
        conclusions = []
        
        patterns = [
            r"Conclusion[s]?:?\s*([^\n]+)",
            r"In summary:?\s*([^\n]+)",
            r"Overall:?\s*([^\n]+)"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            conclusions.extend([
                match.group(1).strip()
                for match in matches
                if match.group(1).strip()
            ])
            
        return list(set(conclusions))

    def _identify_gaps(
        self,
        synthesis: str,
        analyses: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify research gaps"""
        gaps = []
        
        patterns = [
            r"Gap[s]?:?\s*([^\n]+)",
            r"Missing:?\s*([^\n]+)",
            r"Unknown:?\s*([^\n]+)",
            r"Unclear:?\s*([^\n]+)"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, synthesis, re.IGNORECASE)
            gaps.extend([
                match.group(1).strip()
                for match in matches
                if match.group(1).strip()
            ])
            
        return list(set(gaps))

    def _identify_conflicts(
        self,
        synthesis: str,
        analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Identify conflicts between sources"""
        conflicts = []
        
        patterns = [
            r"Conflict[s]?:?\s*([^\n]+)",
            r"Contradict(?:ion|s):?\s*([^\n]+)",
            r"Disagree(?:ment)?:?\s*([^\n]+)"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, synthesis, re.IGNORECASE)
            for match in matches:
                conflict = match.group(1).strip()
                if conflict:
                    conflicts.append({
                        "description": conflict,
                        "sources": self._extract_sources(conflict)
                    })
                    
        return conflicts

# Initialize global parser instance
response_parser = ResponseParser()