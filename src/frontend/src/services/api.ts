import axios, { AxiosInstance } from 'axios';

// API response interfaces
export interface ResearchTask {
  id: number;
  query: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  result?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  analytics?: {
    processing_time_ms: number;
    token_count: number;
    source_count: number;
  };
}

export interface User {
  id: number;
  username: string;
  role: string;
}

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add authentication interceptor
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Add error interceptor
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async login(username: string, password: string): Promise<string> {
    const response = await this.api.post('/token', {
      username,
      password,
    });
    return response.data.access_token;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get('/api/user/me');
    return response.data;
  }

  // Research Tasks
  async createResearchTask(query: string): Promise<ResearchTask> {
    const response = await this.api.post('/api/research/tasks', { query });
    return response.data;
  }

  async getResearchTask(taskId: number): Promise<ResearchTask> {
    const response = await this.api.get(`/api/research/tasks/${taskId}`);
    return response.data;
  }

  async listResearchTasks(params?: {
    skip?: number;
    limit?: number;
  }): Promise<ResearchTask[]> {
    const response = await this.api.get('/api/research/tasks', { params });
    return response.data;
  }

  // Analytics
  async getResearchAnalytics(taskId: number): Promise<{
    processing_time_ms: number;
    token_count: number;
    source_count: number;
  }> {
    const response = await this.api.get(`/api/research/tasks/${taskId}/analytics`);
    return response.data;
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; version: string }> {
    const response = await this.api.get('/api/health');
    return response.data;
  }

  // Error handling helper
  static handleError(error: any): string {
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    if (error.message) {
      return error.message;
    }
    return 'An unexpected error occurred';
  }
}

// Export a singleton instance
export const apiService = new ApiService();

// Export the class for testing purposes
export default ApiService;