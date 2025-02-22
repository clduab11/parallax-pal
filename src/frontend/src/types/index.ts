// Re-export subscription types with explicit naming
export type {
  SubscriptionPlan,
  Subscription,
  PaymentMethod,
  SubscriptionCheckoutSession,
  SubscriptionError,
  SubscriptionInterval,
  CreateSubscriptionRequest,
  UpdateSubscriptionRequest,
  AddPaymentMethodRequest
} from './subscription';

// Re-export user types with explicit naming
export type {
  User,
  UserRole,
  AuthResponse,
  LoginCredentials,
  RegisterData,
  PasswordResetRequest,
  PasswordResetConfirm,
  MfaSetupResponse,
  UserUpdateRequest,
  AuthContextState,
  AuthContextActions,
  AuthContextType
} from './user';

// Export SubscriptionStatus from user types to avoid conflict
export { type SubscriptionStatus } from './user';

// Re-export component types
export type {
  LoadingProps,
  ErrorMessageProps,
  ModalProps,
  FormField,
  RouteConfig,
  ThemeConfig
} from './components';

// Common API response types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: number;
}

export interface ApiError {
  message: string;
  code: string;
  status: number;
  details?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Environment configuration
export interface AppConfig {
  apiUrl: string;
  stripePublishableKey: string;
  environment: 'development' | 'staging' | 'production';
  features: {
    mfa: boolean;
    analytics: boolean;
    subscription: boolean;
  };
}

// Analytics events
export interface AnalyticsEvent {
  name: string;
  properties?: Record<string, any>;
  timestamp?: number;
  userId?: string | number;
}