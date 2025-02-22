import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import ApiService, { ResearchTask } from '../api';

describe('ApiService', () => {
  let api: ApiService;
  let mockAxios: MockAdapter;

  beforeEach(() => {
    api = new ApiService();
    mockAxios = new MockAdapter(axios);
    localStorage.clear();
  });

  afterEach(() => {
    mockAxios.restore();
  });

  describe('authentication', () => {
    it('should login successfully', async () => {
      const mockToken = 'test-token';
      mockAxios.onPost('/token').reply(200, { access_token: mockToken });

      const token = await api.login('testuser', 'password');
      expect(token).toBe(mockToken);
    });

    it('should handle login failure', async () => {
      mockAxios.onPost('/token').reply(401, { detail: 'Invalid credentials' });

      await expect(api.login('testuser', 'wrong-password')).rejects.toThrow();
    });

    it('should get current user', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        role: 'researcher'
      };
      mockAxios.onGet('/api/user/me').reply(200, mockUser);

      const user = await api.getCurrentUser();
      expect(user).toEqual(mockUser);
    });
  });

  describe('research tasks', () => {
    const mockTask: ResearchTask = {
      id: 1,
      query: 'test query',
      status: 'completed',
      result: 'test result',
      created_at: '2025-02-22T12:00:00Z',
      updated_at: '2025-02-22T12:01:00Z'
    };

    it('should create research task', async () => {
      mockAxios.onPost('/api/research/tasks').reply(200, mockTask);

      const task = await api.createResearchTask('test query');
      expect(task).toEqual(mockTask);
    });

    it('should get research task by id', async () => {
      mockAxios.onGet('/api/research/tasks/1').reply(200, mockTask);

      const task = await api.getResearchTask(1);
      expect(task).toEqual(mockTask);
    });

    it('should list research tasks', async () => {
      const mockTasks = [mockTask];
      mockAxios.onGet('/api/research/tasks').reply(200, mockTasks);

      const tasks = await api.listResearchTasks();
      expect(tasks).toEqual(mockTasks);
    });

    it('should handle task not found', async () => {
      mockAxios.onGet('/api/research/tasks/999').reply(404, { detail: 'Task not found' });

      await expect(api.getResearchTask(999)).rejects.toThrow();
    });
  });

  describe('analytics', () => {
    const mockAnalytics = {
      processing_time_ms: 1500,
      token_count: 1000,
      source_count: 5
    };

    it('should get research analytics', async () => {
      mockAxios.onGet('/api/research/tasks/1/analytics').reply(200, mockAnalytics);

      const analytics = await api.getResearchAnalytics(1);
      expect(analytics).toEqual(mockAnalytics);
    });
  });

  describe('error handling', () => {
    it('should handle network errors', async () => {
      mockAxios.onGet('/api/health').networkError();

      await expect(api.healthCheck()).rejects.toThrow();
    });

    it('should handle API errors', () => {
      const error = {
        response: {
          data: {
            detail: 'Test error message'
          }
        }
      };

      const errorMessage = ApiService.handleError(error);
      expect(errorMessage).toBe('Test error message');
    });

    it('should handle unexpected errors', () => {
      const error = new Error('Unexpected error');
      const errorMessage = ApiService.handleError(error);
      expect(errorMessage).toBe('Unexpected error');
    });
  });
});