import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { LoginCredentials } from '../../types/auth';

interface LoginFormProps {
  onSuccess?: () => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
  const { login, state, clearError } = useAuth();
  const [credentials, setCredentials] = useState<LoginCredentials>({
    username: '',
    password: ''
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear any previous errors when user starts typing
    if (state.error) {
      clearError();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await login(credentials);
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      // Error is handled in the auth context
      console.error('Login failed', error);
    }
  };

  return (
    <div className="terminal-window p-4">
      <div className="terminal-header">
        <div className="terminal-dot terminal-dot-red"></div>
        <div className="terminal-dot terminal-dot-yellow"></div>
        <div className="terminal-dot terminal-dot-green"></div>
        <h2 className="text-lg ml-4">Login</h2>
      </div>
      
      <form onSubmit={handleSubmit} className="mt-4 space-y-4">
        <div>
          <label htmlFor="username" className="block text-terminal-green mb-1">
            Username:
          </label>
          <input
            type="text"
            id="username"
            name="username"
            value={credentials.username}
            onChange={handleChange}
            required
            className="w-full bg-terminal-dark border-terminal-green border p-2 text-terminal-green focus:outline-none focus:ring-1 focus:ring-terminal-green"
          />
        </div>
        
        <div>
          <label htmlFor="password" className="block text-terminal-green mb-1">
            Password:
          </label>
          <input
            type="password"
            id="password"
            name="password"
            value={credentials.password}
            onChange={handleChange}
            required
            className="w-full bg-terminal-dark border-terminal-green border p-2 text-terminal-green focus:outline-none focus:ring-1 focus:ring-terminal-green"
          />
        </div>
        
        {state.error && (
          <div className="text-red-500 bg-terminal-dark p-2 border border-red-500">
            Error: {state.error}
          </div>
        )}
        
        <div className="flex justify-between items-center">
          <button
            type="submit"
            disabled={state.isLoading}
            className={`
              bg-terminal-dark border border-terminal-green text-terminal-green py-2 px-4
              hover:bg-terminal-green hover:text-terminal-dark transition-colors
              ${state.isLoading ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          >
            {state.isLoading ? 'Authenticating...' : 'Login'}
          </button>
          
          <a href="/reset-password" className="text-terminal-green hover:underline text-sm">
            Forgot password?
          </a>
        </div>
        
        <div className="text-center mt-4">
          <span className="text-terminal-green">Don't have an account? </span>
          <a href="/register" className="text-terminal-green hover:underline">
            Register
          </a>
        </div>
      </form>
    </div>
  );
};

export default LoginForm;