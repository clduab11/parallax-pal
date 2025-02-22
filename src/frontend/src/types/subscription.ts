export interface SubscriptionPlan {
  id: number;
  name: string;
  description: string;
  price: number;
  interval: 'month' | 'year';
  features: Record<string, boolean>;
  stripe_price_id: string;
  is_active: boolean;
}

export interface Subscription {
  plan: SubscriptionPlan;
  status: 'active' | 'canceled' | 'past_due' | 'unpaid' | 'trialing';
  current_period_end: string;
  cancel_at_period_end: boolean;
  stripe_subscription_id: string;
}

export interface PaymentMethod {
  id: string;
  type: string;
  last4: string;
  exp_month: number;
  exp_year: number;
  is_default: boolean;
  stripe_payment_method_id: string;
}

export interface SubscriptionCheckoutSession {
  id: string;
  url: string;
}

export interface SubscriptionStatus {
  has_subscription: boolean;
  subscription: Subscription | null;
}

export interface SubscriptionError {
  code: string;
  message: string;
  param?: string;
}

export type SubscriptionInterval = 'month' | 'year';

export interface CreateSubscriptionRequest {
  plan_id: number;
  payment_method_id?: string;
}

export interface UpdateSubscriptionRequest {
  plan_id?: number;
  cancel_at_period_end?: boolean;
}

export interface AddPaymentMethodRequest {
  payment_method_id: string;
  set_default?: boolean;
}