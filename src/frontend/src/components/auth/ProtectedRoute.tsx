import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'admin' | 'researcher' | 'viewer';
}

/**
 * Protected route component that ensures users are authenticated
 * before accessing a route. Optionally checks for specific roles.
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requiredRole }) => {
  const { state, isAuthenticated, refreshAccessToken } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const location = useLocation();

  useEffect(() => {
    const checkAuth = async () => {
      // If not authenticated, try to refresh the token
      if (!isAuthenticated() && state.refreshToken) {
        await refreshAccessToken();
      }
      setIsLoading(false);
    };

    checkAuth();
  }, [isAuthenticated, refreshAccessToken, state.refreshToken]);

  // Show loading indicator while checking authentication
  if (isLoading) {
    return (
      <div className="terminal-window p-4 flex items-center justify-center">
        <div className="text-terminal-green">
          <div className="animate-pulse">
            > Authenticating...
          </div>
        </div>
      </div>
    );
  }

  // If not authenticated, redirect to login
  if (!isAuthenticated()) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If role is required but user doesn't have it, redirect to dashboard
  if (requiredRole && state.user?.role !== requiredRole) {
    return <Navigate to="/dashboard" replace />;
  }

  // If authenticated and has required role, render the children
  return <>{children}</>;
};

export default ProtectedRoute;