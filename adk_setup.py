#!/usr/bin/env python3
"""
ADK Setup Script for ParallaxMind

This script initializes the ADK environment, downloads necessary models,
and configures the ADK components for ParallaxMind.

Usage:
  python adk_setup.py

Requirements:
  - Python 3.9+
  - Google Cloud SDK
  - ADK CLI (google-cloud-aiplatform[adk])
"""

import os
import sys
import subprocess
import argparse
import json
import yaml
from pathlib import Path

# Configuration
DEFAULT_CONFIG = {
    "project_id": "parallaxmind",
    "region": "us-central1",
    "model": "gemini-1.5-pro-latest",
    "dev_mode": True,
    "orchestrator_port": 8080,
    "log_level": "info",
    "timeout": 300
}

def check_prerequisites():
    """Check if all prerequisites are installed"""
    print("Checking prerequisites...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        print("Error: Python 3.9 or higher is required")
        sys.exit(1)
    
    # Check for Google Cloud SDK
    try:
        subprocess.run(["gcloud", "--version"], check=True, capture_output=True)
        print("✓ Google Cloud SDK is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Google Cloud SDK is not installed or not in PATH")
        print("Please install from: https://cloud.google.com/sdk/docs/install")
        sys.exit(1)
    
    # Check for ADK CLI
    try:
        subprocess.run(["pip", "show", "google-cloud-aiplatform"], check=True, capture_output=True)
        print("✓ Google Cloud AI Platform SDK is installed")
    except subprocess.CalledProcessError:
        print("Installing Google Cloud AI Platform SDK with ADK...")
        subprocess.run(["pip", "install", "-U", "google-cloud-aiplatform[adk]"], check=True)
    
    try:
        subprocess.run(["adk", "--version"], check=True, capture_output=True)
        print("✓ ADK CLI is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ADK CLI is not installed or not in PATH")
        print("Please install with: pip install -U google-cloud-aiplatform[adk]")
        sys.exit(1)

def initialize_adk_project(config):
    """Initialize the ADK project"""
    print(f"Initializing ADK project '{config['project_id']}'...")
    
    # Create project directory if it doesn't exist
    project_dir = Path(f"adk-{config['project_id']}")
    if not project_dir.exists():
        project_dir.mkdir(parents=True)
        print(f"Created project directory: {project_dir}")
    
    # Initialize ADK project
    try:
        subprocess.run(["adk", "init", config["project_id"]], check=True, cwd=project_dir)
        print(f"✓ Initialized ADK project: {config['project_id']}")
    except subprocess.CalledProcessError as e:
        # If already initialized, this is fine
        if "already initialized" in str(e.stderr):
            print(f"✓ ADK project already initialized: {config['project_id']}")
        else:
            print(f"Error initializing ADK project: {e}")
            sys.exit(1)
    
    # Configure ADK project
    subprocess.run(["adk", "config", "set", "project_id", config["project_id"]], check=True)
    subprocess.run(["adk", "config", "set", "region", config["region"]], check=True)
    print(f"✓ Configured ADK project: {config['project_id']} in {config['region']}")
    
    return project_dir

def create_adk_spec(project_dir, config):
    """Create ADK specification file"""
    print("Creating ADK specification file...")
    
    spec_file = project_dir / "adk-spec.yaml"
    
    # Create ADK specification
    spec = {
        "name": config["project_id"],
        "description": "ParallaxMind Multi-Agent Research Assistant",
        "model": config["model"],
        "tools": [
            {
                "name": "google_search",
                "description": "Search the web for information"
            },
            {
                "name": "code_exec",
                "description": "Execute Python code for data analysis"
            },
            {
                "name": "knowledge_graph",
                "description": "Generate and query knowledge graphs",
                "implementation": {
                    "type": "custom",
                    "path": "./tools/knowledge_graph_tool.py"
                }
            },
            {
                "name": "citation_generator",
                "description": "Generate properly formatted citations",
                "implementation": {
                    "type": "custom",
                    "path": "./tools/citation_tool.py"
                }
            },
            {
                "name": "content_extractor",
                "description": "Extract content from web pages",
                "implementation": {
                    "type": "custom",
                    "path": "./tools/content_extractor_tool.py"
                }
            }
        ],
        "agents": [
            {
                "name": "orchestrator",
                "description": "Main controller agent for research tasks",
                "tools": ["*"],
                "implementation": {
                    "type": "custom",
                    "path": "./agents/orchestrator_agent.py"
                }
            },
            {
                "name": "retrieval_agent",
                "description": "Specialized agent for information retrieval",
                "tools": ["google_search", "content_extractor"],
                "implementation": {
                    "type": "custom",
                    "path": "./agents/retrieval_agent.py"
                }
            },
            {
                "name": "analysis_agent",
                "description": "Specialized agent for content analysis",
                "tools": ["code_exec"],
                "implementation": {
                    "type": "custom",
                    "path": "./agents/analysis_agent.py"
                }
            },
            {
                "name": "knowledge_graph_agent",
                "description": "Specialized agent for knowledge graph generation",
                "tools": ["knowledge_graph", "code_exec"],
                "implementation": {
                    "type": "custom",
                    "path": "./agents/knowledge_graph_agent.py"
                }
            },
            {
                "name": "citation_agent",
                "description": "Specialized agent for citation management",
                "tools": ["citation_generator"],
                "implementation": {
                    "type": "custom",
                    "path": "./agents/citation_agent.py"
                }
            },
            {
                "name": "ui_agent",
                "description": "Specialized agent for UI interaction",
                "tools": [],
                "implementation": {
                    "type": "custom",
                    "path": "./agents/ui_agent.py"
                }
            }
        ]
    }
    
    # Write specification to file
    with open(spec_file, "w") as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False)
    
    print(f"✓ Created ADK specification file: {spec_file}")
    
    # Create empty implementation files
    tool_dir = project_dir / "tools"
    agent_dir = project_dir / "agents"
    
    for directory in [tool_dir, agent_dir]:
        if not directory.exists():
            directory.mkdir(parents=True)
    
    # Create tool implementation files
    for tool in spec["tools"]:
        if "implementation" in tool and tool["implementation"]["type"] == "custom":
            tool_path = project_dir / tool["implementation"]["path"]
            if not tool_path.parent.exists():
                tool_path.parent.mkdir(parents=True)
            
            if not tool_path.exists():
                with open(tool_path, "w") as f:
                    f.write(f"""#!/usr/bin/env python3
# {tool["name"]} tool implementation for ParallaxMind

from typing import Dict, Any

def run(params: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"
    Implementation of the {tool["name"]} tool
    
    Args:
        params: Tool parameters
        
    Returns:
        Tool results
    \"\"\"
    # TODO: Implement tool functionality
    return {{"result": f"Executed {tool["name"]} tool with params: {{params}}"}}
""")
    
    # Create agent implementation files
    for agent in spec["agents"]:
        if "implementation" in agent and agent["implementation"]["type"] == "custom":
            agent_path = project_dir / agent["implementation"]["path"]
            if not agent_path.parent.exists():
                agent_path.parent.mkdir(parents=True)
            
            if not agent_path.exists():
                with open(agent_path, "w") as f:
                    f.write(f"""#!/usr/bin/env python3
# {agent["name"]} agent implementation for ParallaxMind

from typing import Dict, Any, List

class {agent["name"].capitalize()}Agent:
    \"\"\"
    Implementation of the {agent["name"]} agent
    \"\"\"
    
    def __init__(self, config: Dict[str, Any]):
        \"\"\"Initialize the agent with configuration\"\"\"
        self.config = config
    
    async def process(self, message: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"
        Process a message from another agent or the user
        
        Args:
            message: The message to process
            context: The conversation context
            
        Returns:
            The agent's response
        \"\"\"
        # TODO: Implement agent functionality
        return {{
            "action": "respond",
            "content": f"{{agent["name"]}} agent processed message: {{message}}",
            "context": context
        }}
""")
    
    print(f"✓ Created skeleton implementation files for tools and agents")
    
    return spec_file

def copy_existing_components(project_dir):
    """Copy existing ParallaxMind components to ADK project"""
    print("Copying existing ParallaxMind components...")
    
    # Map of source files to destination files in ADK project
    component_map = {
        "research_manager.py": "agents/analysis_agent.py",
        "search_engine.py": "agents/retrieval_agent.py",
        "strategic_analysis_parser.py": "agents/knowledge_graph_agent.py",
        "llm_wrapper.py": "agents/orchestrator_agent.py"
    }
    
    for source, dest in component_map.items():
        source_path = Path(source)
        dest_path = project_dir / dest
        
        if source_path.exists():
            # Read source file
            with open(source_path, "r") as f:
                content = f.read()
            
            # Modify content to adapt to ADK format
            # This is a simplistic approach - in a real implementation, 
            # you would need more sophisticated code transformation
            
            # Write to destination file
            with open(dest_path, "w") as f:
                f.write(f"""#!/usr/bin/env python3
# Adapted from {source} for ADK integration

{content}

# ADK Integration hooks

def adk_init(config):
    \"\"\"Initialize for ADK\"\"\"
    pass

def adk_process(message, context):
    \"\"\"Process message for ADK\"\"\"
    # TODO: Implement ADK processing
    return {{"response": "Not yet implemented"}}
""")
            
            print(f"✓ Adapted {source} to {dest}")
        else:
            print(f"! Warning: Source file {source} not found, skipping")
    
    print(f"✓ Copied and adapted existing components")

def create_config_file(config):
    """Create ADK configuration file"""
    print("Creating ADK configuration file...")
    
    config_path = Path("adk_config.py")
    
    with open(config_path, "w") as f:
        f.write(f"""#!/usr/bin/env python3
\"\"\"
ADK Configuration for ParallaxMind

This module contains configuration settings for the ADK integration.
\"\"\"

# ADK Project Configuration
PROJECT_ID = "{config['project_id']}"
REGION = "{config['region']}"
DEFAULT_MODEL = "{config['model']}"

# Development Mode
DEV_MODE = {'True' if config['dev_mode'] else 'False'}

# Service Configuration
ORCHESTRATOR_PORT = {config['orchestrator_port']}
LOG_LEVEL = "{config['log_level']}"
TIMEOUT = {config['timeout']}

# Model Configuration
MODEL_CONFIG = {{
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 4096
}}

# API Keys (should be loaded from environment variables in production)
API_KEYS = {{
    "google_search": "{{GOOGLE_SEARCH_API_KEY}}",
}}

# Tool Configuration
TOOL_CONFIG = {{
    "google_search": {{
        "engine_id": "{{GOOGLE_SEARCH_ENGINE_ID}}",
        "result_count": 10
    }},
    "knowledge_graph": {{
        "max_nodes": 100,
        "max_edges": 200
    }},
    "citation_generator": {{
        "default_style": "apa",
        "supported_styles": ["apa", "mla", "chicago", "ieee"]
    }}
}}

# Agent Configuration
AGENT_CONFIG = {{
    "orchestrator": {{
        "delegation_threshold": 0.75,
        "max_delegation_depth": 3
    }},
    "retrieval_agent": {{
        "max_sources": 20,
        "min_reliability_score": 0.6
    }},
    "analysis_agent": {{
        "max_focus_areas": 5,
        "summary_length": 500
    }},
    "knowledge_graph_agent": {{
        "max_entities": 50,
        "relationship_confidence_threshold": 0.7
    }},
    "citation_agent": {{
        "bibliography_format": "apa",
        "include_access_date": True
    }}
}}
""")
    
    print(f"✓ Created ADK configuration file: {config_path}")

def create_schema_files():
    """Create schema files for agent messages"""
    print("Creating schema files for agent messages...")
    
    schema_dir = Path("schemas")
    if not schema_dir.exists():
        schema_dir.mkdir(parents=True)
    
    agent_messages_path = schema_dir / "agent_messages.py"
    
    with open(agent_messages_path, "w") as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
Schema definitions for agent messages in ParallaxMind

This module contains Pydantic models that define the structure of messages
exchanged between agents in the ADK system.
\"\"\"

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime

# Enums
class ResearchDepthLevel(str, Enum):
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"

class ResearchStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    ERROR = "error"

class EmotionType(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    CONFUSED = "confused"
    EXCITED = "excited"
    SAD = "sad"

class UIState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    PRESENTING = "presenting"
    ERROR = "error"

# Base Models
class Source(BaseModel):
    \"\"\"A source of information\"\"\"
    url: HttpUrl
    title: str
    snippet: str
    content: Optional[str] = None
    reliability_score: float = Field(..., ge=0.0, le=1.0)
    last_updated: Optional[datetime] = None
    domain: str
    is_primary: bool = False

class FocusArea(BaseModel):
    \"\"\"A specific focus area within a research topic\"\"\"
    topic: str
    sources: List[Source] = []
    summary: str = ""
    key_points: List[str] = []
    completed: bool = False

class AgentActivity(BaseModel):
    \"\"\"Activity record for an agent\"\"\"
    agent_id: str
    agent_type: str
    status: AgentStatus
    action: str
    progress: float = Field(0.0, ge=0.0, le=100.0)
    message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

class AssistantState(BaseModel):
    \"\"\"State of the UI assistant\"\"\"
    emotion: EmotionType = EmotionType.NEUTRAL
    state: UIState = UIState.IDLE
    message: Optional[str] = None
    showBubble: bool = False

# Request/Response Models
class ResearchRequest(BaseModel):
    \"\"\"Request to start a research task\"\"\"
    query: str
    continuous_mode: bool = False
    force_refresh: bool = False
    max_sources: Optional[int] = 20
    depth_level: ResearchDepthLevel = ResearchDepthLevel.DETAILED
    focus_areas: Optional[List[str]] = None

class ResearchResponse(BaseModel):
    \"\"\"Response containing research results\"\"\"
    request_id: str
    query: str
    status: ResearchStatus
    progress: float = Field(0.0, ge=0.0, le=100.0)
    focus_areas: List[FocusArea] = []
    summary: str = ""
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class ResearchStatus(BaseModel):
    \"\"\"Status of a research request\"\"\"
    status: ResearchStatus
    progress: float = Field(0.0, ge=0.0, le=100.0)
    message: str = ""
    agent_activities: List[AgentActivity] = []

# Knowledge Graph Models
class KnowledgeGraphNode(BaseModel):
    \"\"\"Node in a knowledge graph\"\"\"
    id: str
    label: str
    type: str
    description: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    size: Optional[float] = None
    color: Optional[str] = None

class KnowledgeGraphEdge(BaseModel):
    \"\"\"Edge in a knowledge graph\"\"\"
    source: str
    target: str
    label: str
    type: str
    weight: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)

class KnowledgeGraphData(BaseModel):
    \"\"\"Complete knowledge graph data\"\"\"
    nodes: List[KnowledgeGraphNode] = []
    edges: List[KnowledgeGraphEdge] = []
    main_topic: str

# Citation Models
class Citation(BaseModel):
    \"\"\"Citation for a source\"\"\"
    source_id: str
    source_url: HttpUrl
    citation_text: str
    style: str
    authors: Optional[List[str]] = None
    title: str
    published_date: Optional[str] = None
    publisher: Optional[str] = None

# WebSocket Message Models
class WebSocketMessage(BaseModel):
    \"\"\"Base WebSocket message\"\"\"
    type: str
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: str

class ResearchUpdateMessage(WebSocketMessage):
    \"\"\"Research update message\"\"\"
    type: str = "research_update"
    data: Dict[str, Any]

class ResearchCompletedMessage(WebSocketMessage):
    \"\"\"Research completed message\"\"\"
    type: str = "research_completed"
    data: Dict[str, Any]

class KnowledgeGraphUpdateMessage(WebSocketMessage):
    \"\"\"Knowledge graph update message\"\"\"
    type: str = "knowledge_graph_update"
    data: Dict[str, Any]

class ErrorMessage(WebSocketMessage):
    \"\"\"Error message\"\"\"
    type: str = "error"
    data: Dict[str, Any]

class FollowUpQuestionsMessage(WebSocketMessage):
    \"\"\"Follow-up questions message\"\"\"
    type: str = "followup_questions"
    data: Dict[str, Any]
""")
    
    print(f"✓ Created agent message schema file: {agent_messages_path}")

def setup_docker():
    """Create Docker files for ADK deployment"""
    print("Creating Docker files for ADK deployment...")
    
    docker_compose_path = Path("docker-compose.adk.yml")
    
    with open(docker_compose_path, "w") as f:
        f.write("""version: '3.8'

services:
  # ADK Orchestrator
  adk-orchestrator:
    build:
      context: .
      dockerfile: Dockerfile.adk
    ports:
      - "8080:8080"
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-credentials.json
      - PROJECT_ID=parallaxmind
      - REGION=us-central1
      - MODEL=gemini-1.5-pro-latest
      - LOG_LEVEL=info
      - DEV_MODE=true
    volumes:
      - ./adk-parallaxmind:/app/adk
      - ./credentials:/app/credentials
      - ./schemas:/app/schemas
      - ./adk_config.py:/app/adk_config.py
    networks:
      - parallaxmind-network
    restart: unless-stopped
    command: ["python", "-m", "adk", "run", "--agent", "orchestrator", "--port", "8080"]

  # Backend with ADK integration
  backend-adk:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - ADK_ENABLED=true
      - ADK_ORCHESTRATOR_URL=http://adk-orchestrator:8080
    volumes:
      - ./src:/app/src
      - ./schemas:/app/schemas
      - ./adk_config.py:/app/adk_config.py
    depends_on:
      - adk-orchestrator
    networks:
      - parallaxmind-network
    restart: unless-stopped

  # Frontend
  frontend-adk:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - REACT_APP_WS_URL=ws://localhost:8000
    depends_on:
      - backend-adk
    networks:
      - parallaxmind-network
    restart: unless-stopped

networks:
  parallaxmind-network:
    driver: bridge
""")
    
    dockerfile_adk_path = Path("Dockerfile.adk")
    
    with open(dockerfile_adk_path, "w") as f:
        f.write("""FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && \\
    apt-get install -y --no-install-recommends \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install ADK and other requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir google-cloud-aiplatform[adk]

# Copy configuration files
COPY adk_config.py .
COPY schemas/ /app/schemas/

# Copy ADK project files
COPY adk-parallaxmind/ /app/adk/

# Set environment variables
ENV PYTHONPATH=/app
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-credentials.json
ENV ADK_PROJECT_DIR=/app/adk

# Expose port for ADK server
EXPOSE 8080

# Run ADK agent
CMD ["python", "-m", "adk", "run", "--agent", "orchestrator", "--port", "8080"]
""")
    
    print(f"✓ Created Docker files for ADK deployment")
    
    # Additional script for setting up the environment
    setup_script_path = Path("setup_adk_env.sh")
    
    with open(setup_script_path, "w") as f:
        f.write("""#!/bin/bash
# Setup script for ParallaxMind ADK environment

set -e

# Create required directories
mkdir -p credentials
mkdir -p adk-parallaxmind

# Check for Google Cloud credentials
if [ ! -f "credentials/google-credentials.json" ]; then
    echo "Google Cloud credentials not found. Please obtain credentials and save to credentials/google-credentials.json"
    echo "You can create credentials at: https://console.cloud.google.com/apis/credentials"
fi

# Create environment variables file
cat > .env.adk << EOF
# ADK Environment Variables
ADK_ENABLED=true
ADK_ORCHESTRATOR_URL=http://localhost:8080
PROJECT_ID=parallaxmind
REGION=us-central1
MODEL=gemini-1.5-pro-latest
LOG_LEVEL=info
DEV_MODE=true
EOF

echo "✓ Created .env.adk file"

# Initialize ADK project
python adk_setup.py

echo "✓ ADK environment setup complete!"
echo ""
echo "To start the ADK environment, run:"
echo "  docker-compose -f docker-compose.adk.yml up -d"
echo ""
echo "To run the orchestrator locally for testing:"
echo "  source .env.adk"
echo "  cd adk-parallaxmind"
echo "  adk run --agent orchestrator --port 8080"
""")
    
    # Make script executable
    setup_script_path.chmod(0o755)
    
    print(f"✓ Created setup script: {setup_script_path}")

def main():
    parser = argparse.ArgumentParser(description="Set up ADK environment for ParallaxMind")
    parser.add_argument("--project-id", help="ADK project ID", default=DEFAULT_CONFIG["project_id"])
    parser.add_argument("--region", help="GCP region", default=DEFAULT_CONFIG["region"])
    parser.add_argument("--model", help="Model to use", default=DEFAULT_CONFIG["model"])
    parser.add_argument("--dev-mode", help="Enable development mode", action="store_true", default=DEFAULT_CONFIG["dev_mode"])
    parser.add_argument("--port", help="Orchestrator port", type=int, default=DEFAULT_CONFIG["orchestrator_port"])
    args = parser.parse_args()
    
    # Create config from args
    config = {
        "project_id": args.project_id,
        "region": args.region,
        "model": args.model,
        "dev_mode": args.dev_mode,
        "orchestrator_port": args.port,
        "log_level": DEFAULT_CONFIG["log_level"],
        "timeout": DEFAULT_CONFIG["timeout"]
    }
    
    print("ParallaxMind ADK Setup")
    print("======================")
    print(f"Project ID: {config['project_id']}")
    print(f"Region: {config['region']}")
    print(f"Model: {config['model']}")
    print(f"Development Mode: {config['dev_mode']}")
    print(f"Orchestrator Port: {config['orchestrator_port']}")
    print("======================\n")
    
    check_prerequisites()
    project_dir = initialize_adk_project(config)
    spec_file = create_adk_spec(project_dir, config)
    copy_existing_components(project_dir)
    create_config_file(config)
    create_schema_files()
    setup_docker()
    
    print("\n✓ ADK environment setup complete!")
    print("\nNext steps:")
    print("1. Create Google Cloud credentials and save to credentials/google-credentials.json")
    print("2. Customize agent and tool implementations in the adk-parallaxmind directory")
    print("3. Run the following to start the ADK environment:")
    print("   docker-compose -f docker-compose.adk.yml up -d")
    print("\nFor local development:")
    print("   cd adk-parallaxmind")
    print("   adk run --agent orchestrator --port 8080")

if __name__ == "__main__":
    main()