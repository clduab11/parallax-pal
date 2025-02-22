import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useAuth } from '../contexts/AuthContext';

interface ResearchTask {
  id: number;
  query: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  created_at: string;
  result?: string;
  error_message?: string;
}

const Dashboard: React.FC = () => {
  const [tasks, setTasks] = useState<ResearchTask[]>([]);
  const [newQuery, setNewQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const { token } = useAuth();

  // Fetch tasks on component mount
  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await axios.get('/api/research/tasks', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTasks(response.data);
    } catch (error) {
      toast.error('Failed to fetch research tasks');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newQuery.trim()) return;

    setSubmitting(true);
    try {
      const response = await axios.post(
        '/api/research/tasks',
        { query: newQuery },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success('Research task created successfully');
      setTasks([response.data, ...tasks]);
      setNewQuery('');
    } catch (error) {
      toast.error('Failed to create research task');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusColor = (status: ResearchTask['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Research Dashboard</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-gray-700">
              New Research Query
            </label>
            <div className="mt-1 flex rounded-md shadow-sm">
              <input
                type="text"
                id="query"
                value={newQuery}
                onChange={(e) => setNewQuery(e.target.value)}
                className="flex-1 min-w-0 block w-full px-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Enter your research query..."
                disabled={submitting}
              />
              <button
                type="submit"
                disabled={submitting}
                className={`ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                  submitting ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                {submitting ? 'Submitting...' : 'Submit'}
              </button>
            </div>
          </div>
        </form>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {tasks.map((task) => (
            <li key={task.id}>
              <Link
                to={`/research/${task.id}`}
                className="block hover:bg-gray-50 transition duration-150 ease-in-out"
              >
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="sm:flex sm:justify-between w-full">
                      <div>
                        <p className="text-sm font-medium text-blue-600 truncate">
                          {task.query}
                        </p>
                        <div className="mt-2 flex">
                          <span
                            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                              task.status
                            )}`}
                          >
                            {task.status}
                          </span>
                        </div>
                      </div>
                      <div className="mt-2 sm:mt-0">
                        <p className="text-sm text-gray-500">
                          Created: {new Date(task.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            </li>
          ))}
          {tasks.length === 0 && (
            <li className="px-4 py-8 text-center text-gray-500">
              No research tasks yet. Create one above to get started!
            </li>
          )}
        </ul>
      </div>
    </div>
  );
};

export default Dashboard;