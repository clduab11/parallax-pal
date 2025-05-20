export type OutputType = 'input' | 'output' | 'error' | 'system' | 'web-result' | 'ai-analysis';
export type ResearchMode = 'web' | 'ollama';
export type SubscriptionTier = 'basic' | 'premium';
export type AIModel = 'openai' | 'anthropic' | 'gemini' | 'ollama';

export interface WebResult {
  title: string;
  url: string;
  snippet: string;
  source: string;
}

export interface AIAnalysis {
  model: AIModel;
  analysis: string;
  confidence: number;
}

export interface TerminalOutput {
  id: number;
  type: OutputType;
  text: string;
  timestamp: string;
  webResults?: WebResult[];
  aiAnalyses?: AIAnalysis[];
}

export interface ResearchQueryData {
  query: string;
  mode: ResearchMode;
  useOllama?: boolean;
}

export interface ResearchUpdateData {
  message: string;
  type: 'progress' | 'result' | 'error';
  timestamp: string;
  webResults?: WebResult[];
  aiAnalyses?: AIAnalysis[];
}

export interface UserSubscription {
  tier: SubscriptionTier;
  features: string[];
}

export interface TerminalState {
  outputs: TerminalOutput[];
  isProcessing: boolean;
  mode: ResearchMode;
  subscription: UserSubscription | null;
}

export interface TerminalProps {
  subscription: UserSubscription;
  onModeChange: (mode: ResearchMode) => void;
}

export interface AuthStatus {
  authenticated: boolean;
  username?: string;
}

export interface PingPongData {
  timestamp: string;
}

export interface ErrorData {
  message: string;
  code?: number;
}

export interface SocketEvents {
  // Standard Socket.IO events
  connect: () => void;
  disconnect: (reason: string) => void;
  connect_error: (error: Error) => void;
  
  // Custom application events
  research_update: (data: ResearchUpdateData) => void;
  research_query: (data: ResearchQueryData) => void;
  
  // Authentication events
  auth_status: (data: AuthStatus) => void;
  
  // Error events
  error: (data: ErrorData) => void;
  
  // Keep-alive events
  ping: (data: PingPongData) => void;
  pong: (data: PingPongData) => void;
}