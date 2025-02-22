import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios, { AxiosError } from 'axios';

export interface SubscriptionPlan {
  id: number;
  name: string;
  description: string;
  price: number;
  interval: 'month' | 'year';
  features: Record<string, any>;
}

export interface Subscription {
  plan: SubscriptionPlan;
  status: 'active' | 'canceled' | 'past_due' | 'unpaid' | 'trialing';
  current_period_end: string;
  cancel_at_period_end: boolean;
}

export interface PaymentMethod {
  id: string;
  type: string;
  last4: string;
  exp_month: number;
  exp_year: number;
  is_default: boolean;
}

interface User {
  id: number;
  username: string;
  role: string;
  subscription_status?: 'active' | 'canceled' | 'past_due' | 'unpaid' | 'trialing';
  subscription?: Subscription;
  stripe_customer_id?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  getSubscriptionStatus: () => Promise<Subscription | null>;
  getPaymentMethods: () => Promise<PaymentMethod[]>;
  addPaymentMethod: (paymentMethodId: string, setDefault?: boolean) => Promise<void>;
  removePaymentMethod: (paymentMethodId: string) => Promise<void>;
  setDefaultPaymentMethod: (paymentMethodId: string) => Promise<void>;
  createCheckoutSession: (planId: number) => Promise<string>;
  cancelSubscription: () => Promise<void>;
}

interface AuthProviderProps {
  children: ReactNode;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          // Configure axios defaults
          axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
          
          // Fetch user data
          const response = await axios.get('/api/user/me');
          setUser(response.data);
          setToken(storedToken);
        } catch (error) {
          console.error('Auth initialization failed:', error);
          localStorage.removeItem('token');
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (username: string, password: string) => {
    try {
      setError(null);
      setLoading(true);

      const response = await axios.post('/api/token', {
        username,
        password,
      });

      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      // Fetch user data after successful login
      const userResponse = await axios.get('/api/user/me');
      setUser(userResponse.data);
      setToken(access_token);
    } catch (error) {
      const axiosError = error as AxiosError;
      setError(axiosError.response?.data?.detail || 'Login failed');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  const getSubscriptionStatus = async () => {
    try {
      const response = await axios.get('/api/subscription/status');
      if (response.data.has_subscription) {
        setUser((prev: User | null) => prev ? { ...prev, subscription: response.data.subscription } : prev);
        return response.data.subscription;
      }
      return null;
    } catch (error) {
      console.error('Failed to fetch subscription status:', error);
      return null;
    }
  };

  const getPaymentMethods = async () => {
    const response = await axios.get('/api/payment-methods');
    return response.data;
  };

  const addPaymentMethod = async (paymentMethodId: string, setDefault = false) => {
    await axios.post('/api/payment-methods', {
      payment_method_id: paymentMethodId,
      set_default: setDefault,
    });
  };

  const removePaymentMethod = async (paymentMethodId: string) => {
    await axios.delete(`/api/payment-methods/${paymentMethodId}`);
  };

  const setDefaultPaymentMethod = async (paymentMethodId: string) => {
    await axios.post(`/api/payment-methods/${paymentMethodId}/set-default`);
  };

  const createCheckoutSession = async (planId: number) => {
    const response = await axios.post('/api/subscription/checkout', { plan_id: planId });
    return response.data.session_id;
  };

  const cancelSubscription = async () => {
    await axios.post('/api/subscription/cancel');
    const subscription = await getSubscriptionStatus();
    setUser((prev: User | null) => prev ? { ...prev, subscription } : prev);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        error,
        login,
        logout,
        getSubscriptionStatus,
        getPaymentMethods,
        addPaymentMethod,
        removePaymentMethod,
        setDefaultPaymentMethod,
        createCheckoutSession,
        cancelSubscription,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;