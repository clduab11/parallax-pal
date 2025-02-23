from typing import List, Dict, Any, Optional, Tuple
import aiohttp
import asyncio
import logging
import json
import os
from enum import Enum
from .config import settings
from .monitoring import structured_logger
from .cache import cache
from .gpu_manager import GPUManager

logger = logging.getLogger(__name__)

class LLMError(Exception):
    """Custom exception for LLM-related errors"""
    pass

class AIModel(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"

class LLMWrapper:
    """Asynchronous wrapper for multiple LLM interactions"""
    
    def __init__(self):
        # API Keys
        self.openai_api_key = settings.OPENAI_API_KEY
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY
        self.gemini_api_key = settings.GEMINI_API_KEY
        
        # Initialize GPU manager
        self.gpu_manager = GPUManager()
        recommended_model, _ = self.gpu_manager.get_recommended_model()
        
        # Model configurations
        self.model_configs = {
            AIModel.OPENAI: {
                "model": "gpt-4-turbo-preview",
                "max_tokens": 4000,
                "api_url": "https://api.openai.com/v1/chat/completions"
            },
            AIModel.ANTHROPIC: {
                "model": "claude-3-opus-20240229",
                "max_tokens": 4000,
                "api_url": "https://api.anthropic.com/v1/messages"
            },
            AIModel.GEMINI: {
                "model": "gemini-pro",
                "max_tokens": 4000,
                "api_url": "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
            },
            AIModel.OLLAMA: {
                "model": recommended_model,
                "max_tokens": 4000,
                "api_url": "http://localhost:11434/api/generate",
                "gpu_enabled": self.gpu_manager.has_nvidia_gpu
            }
        }
        
        self._sessions = {}
        
        # Log GPU status
        gpu_status = self.gpu_manager.get_gpu_status()
        if gpu_status["has_gpu"]:
            logger.info(f"Using NVIDIA GPU: {gpu_status['gpu_name']} with {gpu_status['total_vram']:.1f}GB VRAM")
            logger.info(f"Selected Ollama model: {recommended_model}")
        else:
            logger.info("No GPU detected, using CPU for Ollama inference")
        
    async def _ensure_session(self, model: AIModel):
        """Ensure aiohttp session exists for the specified model"""
        if model not in self._sessions:
            headers = {}
            if model == AIModel.OPENAI:
                headers["Authorization"] = f"Bearer {self.openai_api_key}"
            elif model == AIModel.ANTHROPIC:
                headers["x-api-key"] = self.anthropic_api_key
                headers["anthropic-version"] = "2024-01-01"
            elif model == AIModel.GEMINI:
                headers["Authorization"] = f"Bearer {self.gemini_api_key}"
            
            self._sessions[model] = aiohttp.ClientSession(headers=headers)
        return self._sessions[model]

    async def _cleanup(self):
        """Cleanup resources"""
        for session in self._sessions.values():
            await session.close()
        self._sessions.clear()

    async def _call_model(
        self,
        model: AIModel,
        prompt: str,
        max_tokens: Optional[int] = None
    ) -> Tuple[str, float]:
        """Make API call to specified model and return response with confidence"""
        session = await self._ensure_session(model)
        config = self.model_configs[model]
        
        try:
            if model == AIModel.OPENAI:
                payload = {
                    "model": config["model"],
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens or config["max_tokens"],
                    "temperature": 0.7
                }
                async with session.post(config["api_url"], json=payload) as response:
                    if response.status != 200:
                        raise LLMError(f"OpenAI API error: {await response.text()}")
                    result = await response.json()
                    return result['choices'][0]['message']['content'], 0.95

            elif model == AIModel.ANTHROPIC:
                payload = {
                    "model": config["model"],
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens or config["max_tokens"]
                }
                async with session.post(config["api_url"], json=payload) as response:
                    if response.status != 200:
                        raise LLMError(f"Anthropic API error: {await response.text()}")
                    result = await response.json()
                    return result['content'][0]['text'], 0.92

            elif model == AIModel.GEMINI:
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens or config["max_tokens"],
                        "temperature": 0.7
                    }
                }
                async with session.post(config["api_url"], json=payload) as response:
                    if response.status != 200:
                        raise LLMError(f"Gemini API error: {await response.text()}")
                    result = await response.json()
                    return result['candidates'][0]['content']['parts'][0]['text'], 0.90

            elif model == AIModel.OLLAMA:
                payload = {
                    "model": config["model"],
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_gpu": 1 if config.get("gpu_enabled", False) else 0
                    }
                }
                async with session.post(config["api_url"], json=payload) as response:
                    if response.status != 200:
                        raise LLMError(f"Ollama API error: {await response.text()}")
                    result = await response.json()
                    return result['response'], 0.85

        except Exception as e:
            logger.error(f"Error calling {model.value}: {str(e)}")
            raise LLMError(f"{model.value} call failed: {str(e)}")

    async def analyze_with_all_models(
        self,
        query: str,
        content: str,
        url: str,
        use_ollama: bool = False,
        max_tokens: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Analyze content using all available models"""
        cache_key = f"multi_analysis_{hash(f'{query}_{url}_{content[:100]}')})"
        
        if settings.ENABLE_CACHING:
            cached = cache.get(cache_key)
            if cached:
                structured_logger.log("debug", "Cache hit for multi-model analysis",
                    url=url,
                    query_length=len(query)
                )
                return cached
        
        models = [AIModel.OPENAI, AIModel.ANTHROPIC, AIModel.GEMINI]
        if use_ollama:
            models.append(AIModel.OLLAMA)
            
        prompt = f"""
        Analyze the following content in the context of this research query:
        
        QUERY: {query}
        
        CONTENT FROM {url}:
        {content[:4000]}  # Limit content length
        
        Provide a concise analysis focusing on relevance to the query.
        Include key insights and findings.
        """
        
        analyses = []
        tasks = [self._call_model(model, prompt, max_tokens) for model in models]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for model, result in zip(models, results):
            if isinstance(result, Exception):
                logger.error(f"Error in {model.value} analysis: {str(result)}")
                continue
                
            analysis, confidence = result
            analyses.append({
                "model": model.value,
                "analysis": analysis,
                "confidence": confidence
            })
        
        if settings.ENABLE_CACHING:
            cache.set(cache_key, analyses, timeout=3600)
        
        return analyses

    async def synthesize(
        self,
        query: str,
        analyses: List[Dict[str, Any]],
        use_ollama: bool = False
    ) -> Dict[str, Any]:
        """Synthesize multiple analyses into coherent findings"""
        try:
            analyses_text = "\n\n".join([
                f"Model: {analysis['model']}\nConfidence: {analysis['confidence']}\nAnalysis: {analysis['analysis']}"
                for analysis in analyses
            ])
            
            prompt = f"""
            Synthesize the following AI model analyses into coherent research findings.
            
            RESEARCH QUERY: {query}
            
            ANALYSES:
            {analyses_text}
            
            Provide a comprehensive synthesis that:
            1. Addresses the research query directly
            2. Integrates insights from multiple AI models
            3. Highlights key findings and patterns
            4. Notes any conflicting information between models
            5. Suggests areas for further research
            """
            
            models = [AIModel.OPENAI, AIModel.ANTHROPIC, AIModel.GEMINI]
            if use_ollama:
                models.append(AIModel.OLLAMA)
            
            tasks = [self._call_model(model, prompt) for model in models]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            valid_results = []
            for model, result in zip(models, results):
                if isinstance(result, Exception):
                    logger.error(f"Error in {model.value} synthesis: {str(result)}")
                    continue
                    
                synthesis, confidence = result
                valid_results.append({
                    "model": model.value,
                    "synthesis": synthesis,
                    "confidence": confidence
                })
            
            # Return the synthesis with the highest confidence
            best_synthesis = max(valid_results, key=lambda x: x["confidence"])
            return best_synthesis
                
        except Exception as e:
            logger.error(f"Error in synthesis: {str(e)}")
            raise LLMError(f"Synthesis failed: {str(e)}")

    async def generate_follow_up_questions(
        self,
        synthesis: str,
        previous_queries: List[str],
        use_ollama: bool = False,
        max_questions: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate follow-up research questions based on synthesis"""
        try:
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
            
            models = [AIModel.OPENAI, AIModel.ANTHROPIC, AIModel.GEMINI]
            if use_ollama:
                models.append(AIModel.OLLAMA)
            
            tasks = [self._call_model(model, prompt) for model in models]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            all_questions = []
            for model, result in zip(models, results):
                if isinstance(result, Exception):
                    logger.error(f"Error in {model.value} question generation: {str(result)}")
                    continue
                    
                content, confidence = result
                questions = [
                    line.replace("Q:", "").strip()
                    for line in content.split("\n")
                    if line.strip().startswith("Q:")
                ]
                
                all_questions.append({
                    "model": model.value,
                    "questions": questions[:max_questions],
                    "confidence": confidence
                })
            
            return all_questions
                
        except Exception as e:
            logger.error(f"Error generating follow-up questions: {str(e)}")
            raise LLMError(f"Question generation failed: {str(e)}")

    def get_gpu_status(self) -> Dict[str, Any]:
        """Get current GPU status and model recommendations"""
        gpu_status = self.gpu_manager.get_gpu_status()
        suitable_models = self.gpu_manager.get_suitable_models()
        recommended_model, vram_required = self.gpu_manager.get_recommended_model()
        
        return {
            "gpu_info": gpu_status,
            "current_model": self.model_configs[AIModel.OLLAMA]["model"],
            "recommended_model": recommended_model,
            "vram_required": vram_required,
            "suitable_models": suitable_models,
            "using_gpu": self.model_configs[AIModel.OLLAMA].get("gpu_enabled", False)
        }
    
    def update_ollama_model(self, model_name: str) -> None:
        """Update the Ollama model being used"""
        if model_name not in self.gpu_manager.MODEL_VRAM_REQUIREMENTS:
            raise LLMError(f"Unknown Ollama model: {model_name}")
            
        self.model_configs[AIModel.OLLAMA]["model"] = model_name
        logger.info(f"Updated Ollama model to: {model_name}")

# Initialize global LLM instance
llm = LLMWrapper()