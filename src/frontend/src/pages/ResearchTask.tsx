import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useAuth } from '../contexts/AuthContext';

interface ResearchResult {
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

const ResearchTask: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const [task, setTask] = useState<ResearchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchTask();
    // Poll for updates if task is not completed
    const interval = setInterval(() => {
      if (task && ['pending', 'in_progress'].includes(task.status)) {
        fetchTask();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [taskId, task?.status]);

  const fetchTask = async () => {
    try {
      const response = await axios.get(`/api/research/tasks/${taskId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTask(response.data);
    } catch (error) {
      toast.error('Failed to fetch research task');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900">Task not found</h2>
      </div>
    );
  }

  const getStatusBadge = () => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-800',
      in_progress: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800'
    };

    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
          styles[task.status]
        }`}
      >
        {task.status}
      </span>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Research Task Details</h2>
            {getStatusBadge()}
          </div>

          <div className="border-t border-gray-200 py-4">
            <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium text-gray-500">Query</dt>
                <dd className="mt-1 text-sm text-gray-900">{task.query}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Created At</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {new Date(task.created_at).toLocaleString()}
                </dd>
              </div>
              {task.analytics && (
                <>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Processing Time</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {task.analytics.processing_time_ms}ms
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Sources Analyzed</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {task.analytics.source_count}
                    </dd>
                  </div>
                </>
              )}
            </dl>
          </div>

          {task.status === 'completed' && task.result && (
            <div className="mt-6">
              <h3 className="text-lg font-medium text-gray-900">Research Results</h3>
              <div className="mt-2 bg-gray-50 p-4 rounded-md">
                <pre className="whitespace-pre-wrap text-sm text-gray-700">
                  {task.result}
                </pre>
              </div>
            </div>
          )}

          {task.status === 'failed' && task.error_message && (
            <div className="mt-6">
              <div className="rounded-md bg-red-50 p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-5 w-5 text-red-400"
                      fill="none"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Error</h3>
                    <div className="mt-2 text-sm text-red-700">{task.error_message}</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="mt-6">
            <button
              onClick={() => navigate('/')}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResearchTask;