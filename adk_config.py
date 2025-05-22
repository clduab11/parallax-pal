"""
ADK Configuration for ParallaxMind

This file contains the configuration for the Google Cloud Agent Development Kit (ADK)
integration in ParallaxMind.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ADKConfig:
    """Configuration for ADK settings."""
    project_id: str = "parallaxmind"
    region: str = "us-central1"
    api_endpoint: str = "us-central1-aiplatform.googleapis.com"
    
    # Agent configuration
    orchestrator_agent_id: str = "orchestrator"
    max_agent_recursion_depth: int = 5
    
    # Model configuration
    primary_model: str = "gemini-1.5-pro"
    fallback_model: str = "claude-3-sonnet"
    
    # Tool settings
    tool_timeout_seconds: int = 30
    max_concurrent_tools: int = 5
    
    # Streaming settings
    enable_streaming: bool = True
    stream_chunk_size: int = 100
    
    # Development settings
    dev_mode: bool = True
    local_testing: bool = True
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary for ADK."""
        return {
            "project_id": self.project_id,
            "region": self.region,
            "api_endpoint": self.api_endpoint,
            "orchestrator_agent_id": self.orchestrator_agent_id,
            "max_agent_recursion_depth": self.max_agent_recursion_depth,
            "primary_model": self.primary_model,
            "fallback_model": self.fallback_model,
            "tool_timeout_seconds": self.tool_timeout_seconds,
            "max_concurrent_tools": self.max_concurrent_tools,
            "enable_streaming": self.enable_streaming,
            "stream_chunk_size": self.stream_chunk_size,
            "dev_mode": self.dev_mode,
            "local_testing": self.local_testing,
        }

# Default configuration instance
default_config = ADKConfig(
    project_id=os.environ.get("ADK_PROJECT_ID", "parallaxmind"),
    region=os.environ.get("ADK_REGION", "us-central1"),
    dev_mode=os.environ.get("ADK_DEV_MODE", "true").lower() == "true",
    local_testing=os.environ.get("ADK_LOCAL_TESTING", "true").lower() == "true",
)

def get_config() -> ADKConfig:
    """Get the current ADK configuration."""
    return default_config