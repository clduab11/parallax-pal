export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'researcher' | 'viewer';
}

export interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  error: string | null;
  accessToken: string | null;
  refreshToken: string | null;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface AuthContextType {
  state: AuthState;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<boolean>;
  clearError: () => void;
  isAuthenticated: () => boolean;
  getAccessToken: () => string | null;
}

export interface JwtPayload {
  sub: string;    // Subject (usually username)
  exp: number;    // Expiration time
  iat: number;    // Issued at time
  jti: string;    // JWT ID
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string; 
  token_type: string;
}

export type AuthActionType = 
  | { type: 'LOGIN_REQUEST' }
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; tokens: TokenResponse } }
  | { type: 'LOGIN_FAILURE'; payload: string }
  | { type: 'REGISTER_REQUEST' }
  | { type: 'REGISTER_SUCCESS' }
  | { type: 'REGISTER_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'REFRESH_TOKEN_SUCCESS'; payload: string }
  | { type: 'REFRESH_TOKEN_FAILURE' }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SET_USER'; payload: User };

export interface SubscriptionInfo {
  has_subscription: boolean;
  subscription: {
    plan: {
      id: number;
      name: string;
      description: string;
      price: number;
      interval: string;
      features: Record<string, any>;
      allows_ollama: boolean;
    };
    status: 'active' | 'canceled' | 'past_due' | 'unpaid' | 'trialing';
    current_period_end: string;
    cancel_at_period_end: boolean;
  } | null;
}

export interface SubscriptionFeatures {
  gpu_acceleration: boolean;
  ollama_access: boolean;
  is_pro: boolean;
}