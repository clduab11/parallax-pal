export type ResearchMode = 'quick' | 'comprehensive' | 'continuous';

export interface UserSubscription {
  tier: 'free' | 'basic' | 'pro' | 'enterprise';
  features: string[];
  expiresAt?: string;
  status?: 'active' | 'canceled' | 'past_due' | 'unpaid' | 'trialing';
}

export interface TerminalMessage {
  id: string;
  type: 'user' | 'assistant' | 'system' | 'error';
  content: string;
  timestamp: Date;
  metadata?: {
    mode?: ResearchMode;
    progress?: number;
    agent?: string;
  };
}

export interface ResearchSession {
  id: string;
  mode: ResearchMode;
  query: string;
  status: 'idle' | 'active' | 'completed' | 'error';
  results?: ResearchResult;
  startTime: Date;
  endTime?: Date;
}

export interface ResearchResult {
  summary: string;
  sources: Source[];
  findings: string[];
  knowledgeGraph?: {
    nodes: any[];
    edges: any[];
  };
  confidence: number;
}

export interface Source {
  title: string;
  url: string;
  reliability: number;
  excerpt?: string;
  publishedDate?: string;
}