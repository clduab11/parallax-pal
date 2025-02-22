import { Subscription } from './subscription';

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  last_login?: string;
  subscription_status?: SubscriptionStatus;
  subscription?: Subscription;
  stripe_customer_id?: string;
  mfa_enabled: boolean;
}

export type UserRole = 'admin' | 'researcher' | 'viewer';

export type SubscriptionStatus = 'active' | 'canceled' | 'past_due' | 'unpaid' | 'trialing';

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface LoginCredentials {
  username: string;
  password: string;
  mfa_code?: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  new_password: string;
  new_password_confirm: string;
}

export interface MfaSetupResponse {
  secret: string;
  qr_code: string;
}

export interface UserUpdateRequest {
  email?: string;
  username?: string;
  current_password?: string;
  new_password?: string;
  new_password_confirm?: string;
}

export interface AuthContextState {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}

export interface AuthContextActions {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  register: (data: RegisterData) => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  confirmPasswordReset: (data: PasswordResetConfirm) => Promise<void>;
  updateProfile: (data: UserUpdateRequest) => Promise<void>;
  setupMfa: () => Promise<MfaSetupResponse>;
  verifyMfa: (code: string) => Promise<void>;
  disableMfa: (code: string) => Promise<void>;
  refreshToken: () => Promise<void>;
}

export type AuthContextType = AuthContextState & AuthContextActions;