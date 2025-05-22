/**
 * ADK Type definitions for Parallax Pal and Starri interface
 */

export interface ResearchRequest {
  query: string;
  continuous_mode?: boolean;
  force_refresh?: boolean;
  max_sources?: number;
  depth_level?: 'basic' | 'detailed' | 'comprehensive';
  focus_areas?: string[];
}

export interface Source {
  url: string;
  title: string;
  snippet: string;
  content?: string;
  reliability_score: number;
  last_updated?: string;
  domain: string;
  is_primary: boolean;
}

export interface FocusArea {
  topic: string;
  sources: Source[];
  summary: string;
  key_points: string[];
  completed: boolean;
}

export interface ResearchResponse {
  request_id: string;
  query: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  focus_areas: FocusArea[];
  summary: string;
  created_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: 'concept' | 'entity' | 'source' | 'topic';
  description?: string;
  confidence: number;
  size?: number;
  color?: string;
}

export interface KnowledgeGraphEdge {
  source: string;
  target: string;
  label: string;
  type: 'relates_to' | 'mentions' | 'cites' | 'elaborates';
  weight: number;
  confidence: number;
}

export interface KnowledgeGraphData {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  main_topic: string;
}

export interface Citation {
  source_id: string;
  source_url: string;
  citation_text: string;
  style: string;
  authors?: string[];
  title: string;
  published_date?: string;
  publisher?: string;
}

export interface AgentActivity {
  agent_id: string;
  agent_type: string;
  status: 'idle' | 'working' | 'completed' | 'error';
  action: string;
  progress: number;
  message?: string;
  started_at: string;
  completed_at?: string;
}

export interface AssistantState {
  emotion: 'neutral' | 'happy' | 'confused' | 'excited' | 'sad';
  state: 'idle' | 'thinking' | 'presenting' | 'error';
  message?: string;
  showBubble: boolean;
}

export interface ResearchStatus {
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  message: string;
  agent_activities: AgentActivity[];
}

export interface ADKWebSocketMessage {
  type: string;
  session_id?: string;
  request_id?: string;
  data?: any;
  timestamp: string;
}

export interface ResearchUpdateMessage extends ADKWebSocketMessage {
  type: 'research_update';
  data: {
    status: ResearchStatus;
    current_focus_area?: string;
    sources_found?: number;
    assistant_state: AssistantState;
  };
}

export interface ResearchCompletedMessage extends ADKWebSocketMessage {
  type: 'research_completed';
  data: {
    request_id: string;
    summary: string;
    focus_areas: FocusArea[];
    assistant_state: AssistantState;
  };
}

export interface KnowledgeGraphUpdateMessage extends ADKWebSocketMessage {
  type: 'knowledge_graph_update';
  data: {
    partial_graph: KnowledgeGraphData;
  };
}

export interface ErrorMessage extends ADKWebSocketMessage {
  type: 'error';
  data: {
    error_code: string;
    error_message: string;
    assistant_state: AssistantState;
  };
}

export interface FollowUpQuestionsMessage extends ADKWebSocketMessage {
  type: 'followup_questions';
  data: {
    questions: string[];
  };
}

export type ADKWebSocketEvent = 
  | ResearchUpdateMessage
  | ResearchCompletedMessage
  | KnowledgeGraphUpdateMessage
  | ErrorMessage
  | FollowUpQuestionsMessage;