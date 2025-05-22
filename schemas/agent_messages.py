"""
Agent Communication Schemas for ParallaxMind

Defines structured message formats for agent communication using Pydantic models,
ensuring type safety and validation across agent interactions.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, HttpUrl

class ResearchFocusArea(BaseModel):
    """Represents a specific area of research focus."""
    area: str = Field(..., description="The specific focus area for research")
    priority: int = Field(3, ge=1, le=5, description="Priority from 1 (highest) to 5 (lowest)")
    source_query: Optional[str] = Field(None, description="Original query that generated this focus area")
    search_queries: List[str] = Field(default_factory=list, description="Specific search queries for this focus area")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When this focus area was created")

class ResearchStatus(str, Enum):
    """Possible statuses for a research task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Source(BaseModel):
    """Information about a research source with citation details."""
    url: HttpUrl = Field(..., description="Source URL")
    title: str = Field(..., description="Source title")
    author: Optional[str] = Field(None, description="Source author")
    publication_date: Optional[str] = Field(None, description="When source was published")
    site_name: Optional[str] = Field(None, description="Name of the website or publication")
    snippet: str = Field("", description="Brief extract from the source")
    content: Optional[str] = Field(None, description="Full extracted content if available")
    reliability_score: float = Field(0.5, ge=0, le=1, description="Estimated reliability (0-1)")
    access_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"), description="When source was accessed")
    citation: Optional[str] = Field(None, description="Formatted citation")

class ResearchRequest(BaseModel):
    """Request for research from the Orchestrator to Research Agents."""
    query: str = Field(..., description="The original research query")
    focus_areas: Optional[List[ResearchFocusArea]] = Field(None, description="Specific focus areas to research")
    continuous_mode: bool = Field(False, description="Whether to research all focus areas thoroughly")
    force_refresh: bool = Field(False, description="Whether to bypass cache")
    max_sources: int = Field(10, description="Maximum number of sources to process")
    request_id: str = Field(..., description="Unique identifier for this request")
    user_id: Optional[str] = Field(None, description="ID of user making the request")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When request was created")

class ResearchResponse(BaseModel):
    """Response from Research Agents to the Orchestrator."""
    request_id: str = Field(..., description="ID from the original request")
    summary: str = Field(..., description="Research summary")
    sources: List[Source] = Field(default_factory=list, description="Sources used")
    focus_areas: List[ResearchFocusArea] = Field(default_factory=list, description="Focus areas that were researched")
    status: ResearchStatus = Field(ResearchStatus.COMPLETED, description="Status of research")
    processing_time: float = Field(..., description="Time taken to process in seconds")
    confidence_score: float = Field(0.0, ge=0, le=1, description="Confidence in results (0-1)")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    cache_hit: bool = Field(False, description="Whether result was from cache")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When response was created")

class ProgressUpdate(BaseModel):
    """Progress update for streaming during research."""
    request_id: str = Field(..., description="ID from the original request")
    focus_area: Optional[str] = Field(None, description="Current focus area being researched")
    status: ResearchStatus = Field(..., description="Current status")
    progress_percent: float = Field(0.0, ge=0, le=100, description="Progress percentage (0-100)")
    message: str = Field(..., description="Progress message")
    sources_found: int = Field(0, description="Number of sources found so far")
    sources_processed: int = Field(0, description="Number of sources processed so far")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When update was created")

class CitationRequest(BaseModel):
    """Request to generate citations for sources."""
    sources: List[Source] = Field(..., description="Sources to generate citations for")
    style: str = Field("apa", description="Citation style (apa, mla, chicago, etc.)")
    request_id: str = Field(..., description="Unique identifier for this request")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When request was created")

class CitationResponse(BaseModel):
    """Response with generated citations."""
    request_id: str = Field(..., description="ID from the original request")
    sources: List[Source] = Field(..., description="Sources with citations added")
    bibliography: str = Field(..., description="Complete bibliography text")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When response was created")

class KnowledgeGraphNode(BaseModel):
    """Node in a knowledge graph."""
    id: str = Field(..., description="Unique identifier for this node")
    label: str = Field(..., description="Display label for the node")
    type: str = Field(..., description="Node type (concept, entity, etc.)")
    description: Optional[str] = Field(None, description="Brief description of node")
    sources: List[str] = Field(default_factory=list, description="Source URLs supporting this node")
    confidence: float = Field(1.0, ge=0, le=1, description="Confidence in this node (0-1)")

class KnowledgeGraphEdge(BaseModel):
    """Edge connecting nodes in a knowledge graph."""
    source: str = Field(..., description="ID of source node")
    target: str = Field(..., description="ID of target node")
    label: str = Field(..., description="Relationship label")
    type: str = Field(..., description="Relationship type")
    weight: float = Field(1.0, description="Edge weight/strength")
    sources: List[str] = Field(default_factory=list, description="Source URLs supporting this edge")
    confidence: float = Field(1.0, ge=0, le=1, description="Confidence in this edge (0-1)")

class KnowledgeGraphRequest(BaseModel):
    """Request to generate a knowledge graph."""
    query: str = Field(..., description="The original research query")
    research_response: Optional[ResearchResponse] = Field(None, description="Research response to build graph from")
    request_id: str = Field(..., description="Unique identifier for this request")
    max_nodes: int = Field(30, description="Maximum number of nodes to include")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When request was created")

class KnowledgeGraph(BaseModel):
    """Complete knowledge graph structure."""
    nodes: List[KnowledgeGraphNode] = Field(..., description="Nodes in the graph")
    edges: List[KnowledgeGraphEdge] = Field(..., description="Edges connecting nodes")
    main_topic: str = Field(..., description="ID of the central/main topic node")
    query: str = Field(..., description="Original query that generated this graph")

class KnowledgeGraphResponse(BaseModel):
    """Response with generated knowledge graph."""
    request_id: str = Field(..., description="ID from the original request")
    graph: KnowledgeGraph = Field(..., description="The knowledge graph")
    summary: str = Field(..., description="Text summary of the knowledge graph")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When response was created")

class UIRequest(BaseModel):
    """Request to the UI agent for visualization."""
    type: str = Field(..., description="Type of UI request (e.g., 'research', 'graph', 'followup')")
    content: Dict = Field(..., description="Content to visualize")
    request_id: str = Field(..., description="Unique identifier for this request")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When request was created")

class UIResponse(BaseModel):
    """Response from the UI agent with visualization data."""
    request_id: str = Field(..., description="ID from the original request")
    ui_elements: Dict = Field(..., description="UI elements to render")
    animations: Optional[List[Dict]] = Field(None, description="Animations to play")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When response was created")

class AgentMessage(BaseModel):
    """Generic message container for agent communication."""
    message_type: str = Field(..., description="Type of message")
    sender: str = Field(..., description="ID of the sending agent")
    receiver: str = Field(..., description="ID of the receiving agent")
    content: Union[
        ResearchRequest, 
        ResearchResponse, 
        ProgressUpdate,
        CitationRequest,
        CitationResponse,
        KnowledgeGraphRequest,
        KnowledgeGraphResponse,
        UIRequest,
        UIResponse,
        Dict
    ] = Field(..., description="Message content")
    message_id: str = Field(..., description="Unique message identifier")
    correlation_id: str = Field(..., description="ID for tracking related messages")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When message was created")