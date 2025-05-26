import React, { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, 
  Clock, 
  Zap, 
  TrendingUp,
  BarChart3,
  Users,
  Database,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  ChevronUp,
  ChevronDown,
  Brain
} from 'lucide-react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface MetricsData {
  agentPerformance: {
    [agent: string]: {
      avgResponseTime: number;
      successRate: number;
      tasksCompleted: number;
      status: 'healthy' | 'degraded' | 'error';
    };
  };
  systemMetrics: {
    activeUsers: number;
    totalQueries: number;
    avgQueryTime: number;
    cacheHitRate: number;
    errorRate: number;
    throughput: number;
  };
  historicalData: {
    timestamps: string[];
    queries: number[];
    responseTime: number[];
    activeUsers: number[];
  };
}

interface PerformanceMetricsProps {
  onClose?: () => void;
  compact?: boolean;
}

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ 
  onClose, 
  compact = false 
}) => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d'>('24h');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSection, setExpandedSection] = useState<string | null>('system');

  // Fetch metrics data
  const fetchMetrics = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/metrics?range=${timeRange}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch metrics');
      }
      
      const data = await response.json();
      setMetrics(data);
      setError(null);
    } catch (err) {
      setError('Unable to load metrics');
      console.error('Metrics error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  if (isLoading && !metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-400">
        <AlertCircle className="w-12 h-12 mb-2" />
        <p>{error}</p>
        <button
          onClick={fetchMetrics}
          className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!metrics) return null;

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(31, 41, 55, 0.9)',
        borderColor: 'rgba(147, 51, 234, 0.5)',
        borderWidth: 1
      }
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(75, 85, 99, 0.3)'
        },
        ticks: {
          color: 'rgba(156, 163, 175, 1)'
        }
      },
      y: {
        grid: {
          color: 'rgba(75, 85, 99, 0.3)'
        },
        ticks: {
          color: 'rgba(156, 163, 175, 1)'
        }
      }
    }
  };

  const MetricCard: React.FC<{
    icon: React.ReactNode;
    label: string;
    value: string | number;
    trend?: string;
    status?: 'good' | 'warning' | 'error';
  }> = ({ icon, label, value, trend, status = 'good' }) => {
    const statusColors = {
      good: 'text-green-400',
      warning: 'text-yellow-400',
      error: 'text-red-400'
    };

    return (
      <motion.div
        whileHover={{ scale: 1.05 }}
        className="bg-gray-800 rounded-lg p-4 relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-20 h-20 bg-purple-600 opacity-10 rounded-full -mr-10 -mt-10" />
        
        <div className="flex items-center gap-3 mb-2 text-gray-400">
          {icon}
          <span className="text-sm font-medium">{label}</span>
        </div>
        
        <div className="text-2xl font-bold text-white">{value}</div>
        
        {trend && (
          <div className={`text-sm mt-1 ${
            trend.startsWith('+') ? statusColors.good : statusColors.error
          }`}>
            {trend}
          </div>
        )}
      </motion.div>
    );
  };

  if (compact) {
    // Compact view for embedding
    return (
      <div className="bg-gray-900 rounded-xl p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-white">System Status</h3>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-sm text-gray-400">Live</span>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <MetricCard
            icon={<Activity className="w-4 h-4" />}
            label="Active Users"
            value={metrics.systemMetrics.activeUsers}
          />
          <MetricCard
            icon={<Zap className="w-4 h-4" />}
            label="Avg Response"
            value={`${metrics.systemMetrics.avgQueryTime.toFixed(1)}s`}
          />
        </div>
      </div>
    );
  }

  // Full view
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="bg-gray-900 rounded-xl shadow-2xl max-w-6xl mx-auto overflow-hidden"
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-white">System Performance</h2>
            <p className="text-white/80 mt-1">Real-time metrics and agent health</p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex gap-2">
              {(['1h', '24h', '7d'] as const).map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-3 py-1 rounded-lg text-sm font-medium transition-all ${
                    timeRange === range
                      ? 'bg-white text-purple-600'
                      : 'bg-white/20 text-white hover:bg-white/30'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>
            
            {onClose && (
              <button
                onClick={onClose}
                className="text-white/80 hover:text-white transition-colors"
              >
                ✕
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* System Metrics Section */}
        <div className="mb-6">
          <button
            onClick={() => toggleSection('system')}
            className="flex items-center justify-between w-full mb-4 text-left"
          >
            <h3 className="text-xl font-semibold text-white flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-purple-400" />
              System Metrics
            </h3>
            {expandedSection === 'system' ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
          
          <AnimatePresence>
            {expandedSection === 'system' && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
              >
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <MetricCard
                    icon={<Activity className="w-5 h-5" />}
                    label="Active Users"
                    value={metrics.systemMetrics.activeUsers}
                    trend="+12% from last hour"
                  />
                  <MetricCard
                    icon={<Zap className="w-5 h-5" />}
                    label="Total Queries"
                    value={metrics.systemMetrics.totalQueries.toLocaleString()}
                    trend="+23% from yesterday"
                  />
                  <MetricCard
                    icon={<Clock className="w-5 h-5" />}
                    label="Avg Query Time"
                    value={`${metrics.systemMetrics.avgQueryTime.toFixed(1)}s`}
                    trend="-8% improvement"
                  />
                  <MetricCard
                    icon={<TrendingUp className="w-5 h-5" />}
                    label="Cache Hit Rate"
                    value={`${(metrics.systemMetrics.cacheHitRate * 100).toFixed(0)}%`}
                    trend="+5% from baseline"
                  />
                </div>

                {/* Charts */}
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Query Volume Chart */}
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-white font-medium mb-4">Query Volume</h4>
                    <div className="h-64">
                      <Line
                        data={{
                          labels: metrics.historicalData.timestamps.slice(-20),
                          datasets: [{
                            label: 'Queries',
                            data: metrics.historicalData.queries.slice(-20),
                            borderColor: 'rgb(147, 51, 234)',
                            backgroundColor: 'rgba(147, 51, 234, 0.1)',
                            tension: 0.4,
                            fill: true
                          }]
                        }}
                        options={chartOptions}
                      />
                    </div>
                  </div>

                  {/* Response Time Chart */}
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-white font-medium mb-4">Response Time</h4>
                    <div className="h-64">
                      <Line
                        data={{
                          labels: metrics.historicalData.timestamps.slice(-20),
                          datasets: [{
                            label: 'Response Time (s)',
                            data: metrics.historicalData.responseTime.slice(-20),
                            borderColor: 'rgb(59, 130, 246)',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            tension: 0.4,
                            fill: true
                          }]
                        }}
                        options={chartOptions}
                      />
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Agent Performance Section */}
        <div>
          <button
            onClick={() => toggleSection('agents')}
            className="flex items-center justify-between w-full mb-4 text-left"
          >
            <h3 className="text-xl font-semibold text-white flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-400" />
              Agent Performance
            </h3>
            {expandedSection === 'agents' ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
          
          <AnimatePresence>
            {expandedSection === 'agents' && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
              >
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(metrics.agentPerformance).map(([agent, data]) => (
                    <motion.div
                      key={agent}
                      whileHover={{ scale: 1.02 }}
                      className={`bg-gray-800 rounded-lg p-4 border-2 ${
                        data.status === 'healthy' 
                          ? 'border-green-500/30' 
                          : data.status === 'degraded'
                          ? 'border-yellow-500/30'
                          : 'border-red-500/30'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-white font-medium capitalize">{agent}</h4>
                        <div className={`w-3 h-3 rounded-full ${
                          data.status === 'healthy'
                            ? 'bg-green-400'
                            : data.status === 'degraded'
                            ? 'bg-yellow-400'
                            : 'bg-red-400'
                        }`} />
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-400">Avg Response</span>
                          <span className="text-white">{data.avgResponseTime.toFixed(2)}s</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-400">Success Rate</span>
                          <span className="text-white">{(data.successRate * 100).toFixed(0)}%</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-400">Tasks</span>
                          <span className="text-white">{data.tasksCompleted}</span>
                        </div>
                      </div>
                      
                      {/* Mini progress bar for success rate */}
                      <div className="mt-3 h-1 bg-gray-700 rounded-full overflow-hidden">
                        <motion.div
                          className={`h-full ${
                            data.successRate >= 0.9
                              ? 'bg-green-500'
                              : data.successRate >= 0.7
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                          }`}
                          initial={{ width: 0 }}
                          animate={{ width: `${data.successRate * 100}%` }}
                          transition={{ duration: 0.5 }}
                        />
                      </div>
                    </motion.div>
                  ))}
                </div>

                {/* Agent Status Summary */}
                <div className="mt-6 bg-gray-800 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-6">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-green-400 rounded-full" />
                        <span className="text-sm text-gray-400">
                          {Object.values(metrics.agentPerformance).filter(a => a.status === 'healthy').length} Healthy
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-yellow-400 rounded-full" />
                        <span className="text-sm text-gray-400">
                          {Object.values(metrics.agentPerformance).filter(a => a.status === 'degraded').length} Degraded
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-red-400 rounded-full" />
                        <span className="text-sm text-gray-400">
                          {Object.values(metrics.agentPerformance).filter(a => a.status === 'error').length} Error
                        </span>
                      </div>
                    </div>
                    
                    <button
                      onClick={fetchMetrics}
                      className="text-purple-400 hover:text-purple-300 transition-colors"
                    >
                      <RefreshCw className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
};

export default PerformanceMetrics;