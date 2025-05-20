import api from './api';
import { SubscriptionInfo, SubscriptionFeatures } from '../types/auth';

/**
 * Service for managing user subscriptions
 */
export const subscriptionService = {
  /**
   * Get current user's subscription status
   */
  async getSubscriptionStatus(): Promise<SubscriptionInfo> {
    const response = await api.get<SubscriptionInfo>('/api/subscription/status');
    return response.data;
  },
  
  /**
   * Get user's subscription features
   */
  async getSubscriptionFeatures(): Promise<SubscriptionFeatures> {
    const response = await api.get<SubscriptionFeatures>('/subscription/features');
    return response.data;
  },
  
  /**
   * Create a checkout session for subscription
   */
  async createCheckoutSession(planId: number): Promise<{ session_id: string }> {
    const response = await api.post<{ session_id: string }>('/api/subscription/checkout', {
      plan_id: planId
    });
    return response.data;
  },
  
  /**
   * Cancel current subscription
   */
  async cancelSubscription(immediate: boolean = false): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/api/subscription/cancel', {
      immediate
    });
    return response.data;
  },
  
  /**
   * Reactivate a canceled subscription
   */
  async reactivateSubscription(): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/api/subscription/reactivate');
    return response.data;
  },
  
  /**
   * Get available subscription plans
   */
  async getSubscriptionPlans(): Promise<any[]> {
    const response = await api.get<any[]>('/api/subscription/plans');
    return response.data;
  },
  
  /**
   * Map subscription data to user-friendly format
   */
  mapSubscriptionToUserFormat(subscription: SubscriptionInfo): {
    tier: 'free' | 'basic' | 'pro' | 'enterprise';
    features: string[];
  } {
    if (!subscription.has_subscription) {
      return {
        tier: 'free',
        features: []
      };
    }
    
    // Get tier based on plan price
    let tier: 'free' | 'basic' | 'pro' | 'enterprise' = 'free';
    const price = subscription.subscription?.plan.price || 0;
    
    if (price >= 95.99) {
      tier = 'pro';
    } else if (price >= 35.99) {
      tier = 'basic';
    }
    
    // Convert features from API to frontend format
    const features: string[] = [];
    
    if (subscription.subscription?.plan.allows_ollama) {
      features.push('ollama-access');
    }
    
    if (price >= 95.99) {
      features.push('gpu-acceleration');
      features.push('continuous-research');
      features.push('advanced-visualization');
    } else if (price >= 35.99) {
      features.push('basic-analytics');
      features.push('email-support');
    }
    
    return {
      tier,
      features
    };
  }
};

export default subscriptionService;