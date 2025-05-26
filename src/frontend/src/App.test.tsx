import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import ErrorBoundary from './components/ErrorBoundary';
import { AuthProvider } from './contexts/AuthContext';

// Mock the auth context
jest.mock('./contexts/AuthContext', () => ({
  ...jest.requireActual('./contexts/AuthContext'),
  useAuth: () => ({
    state: {
      isAuthenticated: false,
      isLoading: false,
      user: null,
      error: null
    },
    login: jest.fn(),
    logout: jest.fn(),
    register: jest.fn()
  })
}));

// Mock the ADK service
jest.mock('./services/adkService', () => ({
  __esModule: true,
  default: {
    testConnection: jest.fn().mockResolvedValue({ connected: true })
  }
}));

// Mock subscription service
jest.mock('./services/subscriptionService', () => ({
  __esModule: true,
  default: {
    getSubscription: jest.fn().mockResolvedValue({
      tier: 'basic',
      features: []
    })
  }
}));

describe('App Component', () => {
  test('renders without crashing', () => {
    render(<App />);
  });

  test('redirects to login when not authenticated', async () => {
    render(<App />);
    
    await waitFor(() => {
      // Should redirect to login
      expect(window.location.pathname).toBe('/');
    });
  });

  test('error boundary catches errors', () => {
    // Mock console.error to avoid test noise
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    // Component that throws an error
    const ThrowError = () => {
      throw new Error('Test error');
    };
    
    const { getByText } = render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );
    
    expect(getByText(/something went wrong/i)).toBeInTheDocument();
    
    consoleSpy.mockRestore();
  });
});
