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

export interface SocketEvents {
  connect: () => void;
  disconnect: () => void;
  research_update: (data: ResearchUpdateData) => void;
  research_query: (data: ResearchQueryData) => void;
}