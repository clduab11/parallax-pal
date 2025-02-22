import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { loadStripe } from '@stripe/stripe-js';
import type { PaymentMethod } from '../contexts/AuthContext';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || '');

interface PaymentMethodCardProps {
  method: PaymentMethod;
  onSetDefault: (id: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  isDefault: boolean;
}

const PaymentMethodCard: React.FC<PaymentMethodCardProps> = ({
  method,
  onSetDefault,
  onDelete,
  isDefault,
}) => (
  <div className="bg-white p-4 rounded-lg shadow border border-gray-200">
    <div className="flex justify-between items-center">
      <div>
        <p className="font-medium text-gray-900">
          {method.type === 'card' ? '•••• ' + method.last4 : method.type}
        </p>
        {method.type === 'card' && (
          <p className="text-sm text-gray-500">
            Expires {method.exp_month}/{method.exp_year}
          </p>
        )}
      </div>
      <div className="flex space-x-2">
        {!isDefault && (
          <button
            onClick={() => onSetDefault(method.id)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Make Default
          </button>
        )}
        <button
          onClick={() => onDelete(method.id)}
          className="text-sm text-red-600 hover:text-red-800"
          disabled={isDefault}
        >
          Delete
        </button>
      </div>
    </div>
    {isDefault && (
      <span className="mt-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
        Default
      </span>
    )}
  </div>
);

const PaymentMethods: React.FC = () => {
  const { getPaymentMethods, addPaymentMethod, removePaymentMethod, setDefaultPaymentMethod } = useAuth();
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPaymentMethods();
  }, []);

  const loadPaymentMethods = async () => {
    try {
      const methods = await getPaymentMethods();
      setPaymentMethods(methods);
    } catch (err) {
      setError('Failed to load payment methods');
    } finally {
      setLoading(false);
    }
  };

  const handleNewPaymentMethod = async () => {
    try {
      const stripe = await stripePromise;
      if (!stripe) {
        throw new Error('Stripe failed to load');
      }

      const { error: elementsError, paymentMethod } = await stripe.createPaymentMethod({
        type: 'card',
      });

      if (elementsError) {
        throw new Error(elementsError.message);
      }

      if (paymentMethod) {
        await addPaymentMethod(paymentMethod.id, paymentMethods.length === 0);
        await loadPaymentMethods();
      }
    } catch (err) {
      setError('Failed to add payment method');
    }
  };

  const handleSetDefault = async (paymentMethodId: string) => {
    try {
      await setDefaultPaymentMethod(paymentMethodId);
      await loadPaymentMethods();
    } catch (err) {
      setError('Failed to set default payment method');
    }
  };

  const handleDelete = async (paymentMethodId: string) => {
    try {
      await removePaymentMethod(paymentMethodId);
      await loadPaymentMethods();
    } catch (err) {
      setError('Failed to delete payment method');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[200px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h2 className="text-2xl font-bold text-gray-900">Payment Methods</h2>
          <p className="mt-2 text-sm text-gray-700">
            Manage your payment methods for subscription billing
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            onClick={handleNewPaymentMethod}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Add Payment Method
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-4 text-sm text-red-600 bg-red-50 rounded-md p-4">
          {error}
        </div>
      )}

      <div className="mt-8 space-y-4">
        {paymentMethods.map((method) => (
          <PaymentMethodCard
            key={method.id}
            method={method}
            onSetDefault={handleSetDefault}
            onDelete={handleDelete}
            isDefault={method.is_default}
          />
        ))}

        {paymentMethods.length === 0 && (
          <p className="text-center text-gray-500 py-8">
            No payment methods added yet
          </p>
        )}
      </div>
    </div>
  );
};

export default PaymentMethods;