import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { loadStripe } from '@stripe/stripe-js';
import type { SubscriptionPlan } from '../contexts/AuthContext';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || '');

const SubscriptionPlans: React.FC = () => {
  const { user, createCheckoutSession } = useAuth();
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const response = await fetch('/api/subscription/plans');
        const data = await response.json();
        setPlans(data);
      } catch (err) {
        setError('Failed to load subscription plans');
      } finally {
        setLoading(false);
      }
    };

    fetchPlans();
  }, []);

  const handleSubscribe = async (planId: number) => {
    try {
      const stripe = await stripePromise;
      if (!stripe) {
        throw new Error('Stripe failed to load');
      }

      const sessionId = await createCheckoutSession(planId);
      await stripe.redirectToCheckout({ sessionId });
    } catch (err) {
      setError('Failed to initiate checkout');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[200px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-600 p-4">
        {error}
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="text-center">
        <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
          Choose Your Plan
        </h2>
        <p className="mt-4 text-lg text-gray-500">
          Select the plan that best fits your research needs
        </p>
      </div>

      <div className="mt-12 grid gap-8 lg:grid-cols-3 lg:gap-x-8">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className="relative p-8 bg-white border border-gray-200 rounded-2xl shadow-sm flex flex-col"
          >
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-gray-900">{plan.name}</h3>
              <p className="mt-4 flex items-baseline text-gray-900">
                <span className="text-5xl font-extrabold tracking-tight">${plan.price}</span>
                <span className="ml-1 text-xl font-semibold">/{plan.interval}</span>
              </p>
              <p className="mt-6 text-gray-500">{plan.description}</p>

              <ul className="mt-6 space-y-4">
                {Object.entries(plan.features).map(([feature, included]) => (
                  <li key={feature} className="flex">
                    <span className={`${included ? 'text-green-500' : 'text-red-500'} mr-2`}>
                      {included ? '✓' : '✕'}
                    </span>
                    {feature}
                  </li>
                ))}
              </ul>
            </div>

            <button
              onClick={() => handleSubscribe(plan.id)}
              disabled={user?.subscription?.plan.id === plan.id}
              className={`mt-8 block w-full py-3 px-6 border border-transparent rounded-md text-center font-medium ${
                user?.subscription?.plan.id === plan.id
                  ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {user?.subscription?.plan.id === plan.id ? 'Current Plan' : 'Subscribe'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SubscriptionPlans;