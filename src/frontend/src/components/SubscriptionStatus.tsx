import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import type { Subscription } from '../contexts/AuthContext';

interface SubscriptionDetailsProps {
  subscription: Subscription;
  onCancel: () => Promise<void>;
}

const SubscriptionDetails: React.FC<SubscriptionDetailsProps> = ({ subscription, onCancel }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'trialing':
        return 'bg-blue-100 text-blue-800';
      case 'past_due':
        return 'bg-yellow-100 text-yellow-800';
      case 'canceled':
      case 'unpaid':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-lg font-medium text-gray-900">{subscription.plan.name}</h3>
          <p className="mt-1 text-sm text-gray-500">
            ${subscription.plan.price}/{subscription.plan.interval}
          </p>
        </div>
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
            subscription.status
          )}`}
        >
          {subscription.status.charAt(0).toUpperCase() + subscription.status.slice(1)}
        </span>
      </div>

      <div className="mt-4 space-y-2">
        <p className="text-sm text-gray-600">
          Current period ends: {formatDate(subscription.current_period_end)}
        </p>
        {subscription.cancel_at_period_end && (
          <p className="text-sm text-red-600">
            Your subscription will be canceled at the end of the current period
          </p>
        )}
      </div>

      <div className="mt-6">
        {!subscription.cancel_at_period_end && subscription.status === 'active' && (
          <button
            onClick={onCancel}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            Cancel Subscription
          </button>
        )}
      </div>

      <div className="mt-4 border-t border-gray-200 pt-4">
        <h4 className="text-sm font-medium text-gray-900">Plan Features</h4>
        <ul className="mt-2 space-y-2">
          {Object.entries(subscription.plan.features).map(([feature, included]) => (
            <li key={feature} className="flex items-center text-sm text-gray-600">
              <span className={`mr-2 ${included ? 'text-green-500' : 'text-red-500'}`}>
                {included ? '✓' : '✕'}
              </span>
              {feature}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

const SubscriptionStatus: React.FC = () => {
  const { user, getSubscriptionStatus, cancelSubscription } = useAuth();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSubscription();
  }, []);

  const loadSubscription = async () => {
    try {
      const sub = await getSubscriptionStatus();
      setSubscription(sub);
    } catch (err) {
      setError('Failed to load subscription status');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    try {
      await cancelSubscription();
      await loadSubscription();
    } catch (err) {
      setError('Failed to cancel subscription');
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
      <div className="text-center text-red-600 bg-red-50 rounded-md p-4">
        {error}
      </div>
    );
  }

  if (!subscription) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">No active subscription</p>
        <button
          onClick={() => window.location.href = '/subscription/plans'}
          className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          View Plans
        </button>
      </div>
    );
  }

  return <SubscriptionDetails subscription={subscription} onCancel={handleCancel} />;
};

export default SubscriptionStatus;