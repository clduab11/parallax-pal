// Auth types
export interface User {
  id: number;
  username: string;
  role: string;
  email?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}

// Research types
export type ResearchStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

export interface ResearchTask {
  id: number;
  query: string;
  status: ResearchStatus;
  result?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  analytics?: ResearchAnalytics;
}

export interface ResearchAnalytics {
  processing_time_ms: number;
  token_count: number;
  source_count: number;
  created_at?: string;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// API Error types
export interface ApiError {
  status: number;
  message: string;
  details?: any;
}

// Route types
export interface LocationState {
  from: {
    pathname: string;
  };
}

// Config type
export interface Config {
  API_URL: string;
  MAX_RETRIES: number;
  POLLING_INTERVAL: number;
  TOKEN_STORAGE_KEY: string;
}

// Constants
export const DEFAULT_CONFIG: Config = {
  API_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  MAX_RETRIES: 3,
  POLLING_INTERVAL: 5000, // 5 seconds
  TOKEN_STORAGE_KEY: 'parallax_token'
};