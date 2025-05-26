import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import ResearchInterface from './components/ResearchInterface';
import GPUStatus from './components/GPUStatus';
import LoginForm from './components/auth/LoginForm';
import RegisterForm from './components/auth/RegisterForm';
import ProtectedRoute from './components/auth/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { UserSubscription } from './types/auth';
import subscriptionService from './services/subscriptionService';
import adkService from './services/adkService';

// Main dashboard component that requires authentication
const Dashboard: React.FC = () => {
  const { state } = useAuth();
  const [subscription, setSubscription] = useState<UserSubscription>({
    tier: 'basic',
    features: []
  });
  const [isLoading, setIsLoading] = useState(true);
  useEffect(() => {
    const loadSubscription = async () => {
      try {
        // Get subscription info from API
        const subscriptionInfo = await subscriptionService.getSubscriptionStatus();
        
        // Map subscription data to frontend format
        const mappedSubscription = subscriptionService.mapSubscriptionToUserFormat(subscriptionInfo);
        setSubscription(mappedSubscription);
      } catch (error) {
        console.error('Failed to load subscription:', error);
        // Fallback to free tier on error
        setSubscription({
          tier: 'free',
          features: []
        });
      } finally {
        setIsLoading(false);
      }
    };

    // Initialize ADK WebSocket with authentication
    const initializeWebSocket = async () => {
      if (state.accessToken) {
        try {
          await adkService.initializeWebSocket(state.accessToken);
          console.log('ADK WebSocket initialized');
        } catch (error) {
          console.error('WebSocket initialization failed:', error);
        }
      }
    };

    if (state.isAuthenticated && state.accessToken) {
      loadSubscription();
      initializeWebSocket();
    }

    // Cleanup WebSocket on unmount
    return () => {
      adkService.cleanup();
    };
  }, [state.isAuthenticated, state.accessToken]);


  // Show loading indicator while fetching subscription
  if (isLoading) {
    return (
      <div className="min-h-screen bg-terminal-black p-4 flex items-center justify-center">
        <div className="text-terminal-green animate-pulse">
          {'>'} Loading your dashboard...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-terminal-black p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <div className="terminal-window">
            <div className="terminal-header">
              <div className="terminal-dot terminal-dot-red"></div>
              <div className="terminal-dot terminal-dot-yellow"></div>
              <div className="terminal-dot terminal-dot-green"></div>
              <h1 className="text-xl ml-4">
                Starri - AI Research Assistant
              </h1>
            </div>
            <div className="text-sm opacity-70 flex justify-between">
              <span>System ready • {new Date().toLocaleString()}</span>
              <span>
                Logged in as <span className="text-terminal-green">{state.user?.username}</span> • 
                <span className="text-terminal-green ml-2">
                  {subscription.tier.charAt(0).toUpperCase() + subscription.tier.slice(1)} Tier
                </span>
              </span>
            </div>
          </div>
        </header>

        <main className="grid gap-6">
          {subscription.features.includes('ollama-access') && (
            <div className="terminal-window">
              <GPUStatus />
            </div>
          )}
          
          <div className="h-[700px] bg-terminal-black rounded-lg overflow-hidden border border-terminal-green border-opacity-30">
            <ResearchInterface />
          </div>
        </main>

        <footer className="mt-8 text-center text-terminal-green text-sm opacity-50">
          <p>Starri v2.0.0 • Powered by Google Cloud ADK + Gemini 2.5 Pro</p>
        </footer>
      </div>
    </div>
  );
};

// Main App with routing
const AppWithAuth: React.FC = () => {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<LoginForm />} />
          <Route path="/register" element={<RegisterForm />} />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
    </ErrorBoundary>
  );
};

export default AppWithAuth;