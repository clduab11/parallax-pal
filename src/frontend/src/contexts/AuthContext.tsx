import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
import { 
  AuthState, 
  AuthContextType, 
  LoginCredentials, 
  RegisterCredentials,
  AuthActionType,
  User,
  TokenResponse,
  JwtPayload
} from '../types/auth';
import api from '../services/api';

// Initial state for the auth context
const initialState: AuthState = {
  isAuthenticated: false,
  isLoading: false,
  user: null,
  error: null,
  accessToken: null,
  refreshToken: null,
};

// Create the auth context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Decode JWT without external libraries
const decodeJwt = (token: string): JwtPayload | null => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Failed to decode JWT', error);
    return null;
  }
};

// Check if token is expired
const isTokenExpired = (token: string): boolean => {
  const payload = decodeJwt(token);
  if (!payload) return true;
  
  const currentTime = Math.floor(Date.now() / 1000);
  return payload.exp < currentTime;
};

// Reducer function for auth state
const authReducer = (state: AuthState, action: AuthActionType): AuthState => {
  switch (action.type) {
    case 'LOGIN_REQUEST':
    case 'REGISTER_REQUEST':
      return {
        ...state,
        isLoading: true,
        error: null
      };
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        isLoading: false,
        user: action.payload.user,
        accessToken: action.payload.tokens.access_token,
        refreshToken: action.payload.tokens.refresh_token,
        error: null
      };
    case 'LOGIN_FAILURE':
    case 'REGISTER_FAILURE':
      return {
        ...state,
        isLoading: false,
        error: action.payload
      };
    case 'REGISTER_SUCCESS':
      return {
        ...state,
        isLoading: false,
        error: null
      };
    case 'LOGOUT':
      return {
        ...initialState
      };
    case 'REFRESH_TOKEN_SUCCESS':
      return {
        ...state,
        accessToken: action.payload
      };
    case 'REFRESH_TOKEN_FAILURE':
      return {
        ...initialState
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null
      };
    case 'SET_USER':
      return {
        ...state,
        user: action.payload
      };
    default:
      return state;
  }
};

// Auth Provider component
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Load auth state from local storage on initial render
  useEffect(() => {
    const loadAuthState = () => {
      const accessToken = localStorage.getItem('accessToken');
      const refreshToken = localStorage.getItem('refreshToken');
      const userJson = localStorage.getItem('user');
      
      if (accessToken && refreshToken && userJson) {
        // Check if access token is expired
        if (isTokenExpired(accessToken)) {
          // Token is expired, try to refresh
          refreshAccessToken();
        } else {
          // Token is valid, restore auth state
          const user = JSON.parse(userJson);
          dispatch({ 
            type: 'LOGIN_SUCCESS', 
            payload: { 
              user, 
              tokens: { 
                access_token: accessToken, 
                refresh_token: refreshToken,
                token_type: 'bearer'
              } 
            } 
          });
        }
      }
    };

    loadAuthState();
  }, []);

  // Save auth state to local storage whenever it changes
  useEffect(() => {
    if (state.isAuthenticated && state.accessToken && state.refreshToken && state.user) {
      localStorage.setItem('accessToken', state.accessToken);
      localStorage.setItem('refreshToken', state.refreshToken);
      localStorage.setItem('user', JSON.stringify(state.user));
    } else {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
    }
  }, [state.isAuthenticated, state.accessToken, state.refreshToken, state.user]);

  // Login handler
  const login = async (credentials: LoginCredentials) => {
    dispatch({ type: 'LOGIN_REQUEST' });
    try {
      // Convert credentials to form data for OAuth compatibility
      const formData = new FormData();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);

      const response = await api.post<TokenResponse>('/auth/login', formData);
      
      // Fetch user details
      api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
      const userResponse = await api.get<User>('/users/me');
      
      dispatch({ 
        type: 'LOGIN_SUCCESS', 
        payload: { 
          user: userResponse.data, 
          tokens: response.data 
        } 
      });
    } catch (error: any) {
      dispatch({ 
        type: 'LOGIN_FAILURE', 
        payload: error.response?.data?.detail || 'Authentication failed' 
      });
      throw error;
    }
  };

  // Register handler
  const register = async (credentials: RegisterCredentials) => {
    dispatch({ type: 'REGISTER_REQUEST' });
    try {
      await api.post('/auth/register', {
        username: credentials.username,
        email: credentials.email,
        password: credentials.password
      });
      dispatch({ type: 'REGISTER_SUCCESS' });
    } catch (error: any) {
      dispatch({ 
        type: 'REGISTER_FAILURE', 
        payload: error.response?.data?.detail || 'Registration failed' 
      });
      throw error;
    }
  };

  // Logout handler
  const logout = async () => {
    try {
      if (state.accessToken) {
        await api.post('/auth/logout');
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear auth state regardless of API response
      dispatch({ type: 'LOGOUT' });
      // Clear auth header
      delete api.defaults.headers.common['Authorization'];
    }
  };

  // Token refresh handler
  const refreshAccessToken = async (): Promise<boolean> => {
    if (!state.refreshToken) return false;
    
    try {
      const response = await api.post<TokenResponse>('/auth/refresh', {
        refresh_token: state.refreshToken
      });
      
      dispatch({ type: 'REFRESH_TOKEN_SUCCESS', payload: response.data.access_token });
      localStorage.setItem('accessToken', response.data.access_token);
      localStorage.setItem('refreshToken', response.data.refresh_token);
      
      // Update auth header
      api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
      
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      dispatch({ type: 'REFRESH_TOKEN_FAILURE' });
      return false;
    }
  };

  // Clear error message
  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  // Check if user is authenticated
  const isAuthenticated = useCallback(() => {
    if (!state.accessToken) return false;
    
    // Check if token is expired
    if (isTokenExpired(state.accessToken)) {
      // Token is expired, trigger refresh
      refreshAccessToken();
      return false;
    }
    
    return state.isAuthenticated;
  }, [state.accessToken, state.isAuthenticated]);

  // Get current access token
  const getAccessToken = useCallback(() => {
    return state.accessToken;
  }, [state.accessToken]);

  const value = {
    state,
    login,
    register,
    logout,
    refreshAccessToken,
    clearError,
    isAuthenticated,
    getAccessToken
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook to use the auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};