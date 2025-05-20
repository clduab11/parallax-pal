import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { RegisterCredentials } from '../../types/auth';

interface RegisterFormProps {
  onSuccess?: () => void;
}

const RegisterForm: React.FC<RegisterFormProps> = ({ onSuccess }) => {
  const { register, state, clearError } = useAuth();
  const [credentials, setCredentials] = useState<RegisterCredentials>({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [validationError, setValidationError] = useState<string | null>(null);
  const [registrationSuccess, setRegistrationSuccess] = useState<boolean>(false);

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
    if (validationError) {
      setValidationError(null);
    }
  };

  const validateForm = (): boolean => {
    // Check if passwords match
    if (credentials.password !== credentials.confirmPassword) {
      setValidationError('Passwords do not match');
      return false;
    }
    
    // Check password strength (at least 8 characters with at least one number and one special character)
    const passwordRegex = /^(?=.*[0-9])(?=.*[!@#$%^&*])(?=.{8,})/;
    if (!passwordRegex.test(credentials.password)) {
      setValidationError('Password must be at least 8 characters and include at least one number and one special character');
      return false;
    }
    
    // Check email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(credentials.email)) {
      setValidationError('Please enter a valid email address');
      return false;
    }
    
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // First validate the form
    if (!validateForm()) {
      return;
    }
    
    try {
      await register(credentials);
      setRegistrationSuccess(true);
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      // Error is handled in auth context
      console.error('Registration failed', error);
    }
  };

  // Show success message if registration was successful
  if (registrationSuccess) {
    return (
      <div className="terminal-window p-4">
        <div className="terminal-header">
          <div className="terminal-dot terminal-dot-red"></div>
          <div className="terminal-dot terminal-dot-yellow"></div>
          <div className="terminal-dot terminal-dot-green"></div>
          <h2 className="text-lg ml-4">Registration Successful</h2>
        </div>
        
        <div className="mt-4 p-4 border border-terminal-green text-terminal-green">
          <p className="mb-4">
            Registration successful! Please check your email to verify your account.
          </p>
          <p>
            You will receive an email with a verification link. Click the link to activate your account.
          </p>
        </div>
        
        <div className="mt-4 text-center">
          <a 
            href="/login" 
            className="bg-terminal-dark border border-terminal-green text-terminal-green py-2 px-4 hover:bg-terminal-green hover:text-terminal-dark transition-colors"
          >
            Go to Login
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="terminal-window p-4">
      <div className="terminal-header">
        <div className="terminal-dot terminal-dot-red"></div>
        <div className="terminal-dot terminal-dot-yellow"></div>
        <div className="terminal-dot terminal-dot-green"></div>
        <h2 className="text-lg ml-4">Register</h2>
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
          <label htmlFor="email" className="block text-terminal-green mb-1">
            Email:
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={credentials.email}
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
        
        <div>
          <label htmlFor="confirmPassword" className="block text-terminal-green mb-1">
            Confirm Password:
          </label>
          <input
            type="password"
            id="confirmPassword"
            name="confirmPassword"
            value={credentials.confirmPassword}
            onChange={handleChange}
            required
            className="w-full bg-terminal-dark border-terminal-green border p-2 text-terminal-green focus:outline-none focus:ring-1 focus:ring-terminal-green"
          />
        </div>
        
        {(validationError || state.error) && (
          <div className="text-red-500 bg-terminal-dark p-2 border border-red-500">
            Error: {validationError || state.error}
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
            {state.isLoading ? 'Registering...' : 'Register'}
          </button>
        </div>
        
        <div className="text-center mt-4">
          <span className="text-terminal-green">Already have an account? </span>
          <a href="/login" className="text-terminal-green hover:underline">
            Login
          </a>
        </div>
      </form>
    </div>
  );
};

export default RegisterForm;