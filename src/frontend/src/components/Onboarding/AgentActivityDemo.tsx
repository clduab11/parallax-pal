import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Brain, FileText, Network, BookOpen, CheckCircle } from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  icon: React.ReactNode;
  color: string;
  status: 'idle' | 'working' | 'completed';
  progress: number;
  message: string;
}

const AgentActivityDemo: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([
    {
      id: 'orchestrator',
      name: 'Orchestrator',
      icon: <Brain className="w-5 h-5" />,
      color: 'purple',
      status: 'idle',
      progress: 0,
      message: 'Ready to coordinate'
    },
    {
      id: 'retrieval',
      name: 'Retrieval Agent',
      icon: <Search className="w-5 h-5" />,
      color: 'blue',
      status: 'idle',
      progress: 0,
      message: 'Waiting for task'
    },
    {
      id: 'analysis',
      name: 'Analysis Agent',
      icon: <Brain className="w-5 h-5" />,
      color: 'green',
      status: 'idle',
      progress: 0,
      message: 'Standing by'
    },
    {
      id: 'citation',
      name: 'Citation Agent',
      icon: <BookOpen className="w-5 h-5" />,
      color: 'yellow',
      status: 'idle',
      progress: 0,
      message: 'Ready to cite'
    },
    {
      id: 'knowledge',
      name: 'Knowledge Graph',
      icon: <Network className="w-5 h-5" />,
      color: 'orange',
      status: 'idle',
      progress: 0,
      message: 'Graph builder ready'
    }
  ]);
  
  const [currentStep, setCurrentStep] = useState(0);
  const [isRunning, setIsRunning] = useState(true);
  
  const simulationSteps = [
    {
      agentId: 'orchestrator',
      status: 'working',
      progress: 20,
      message: 'Breaking down query...'
    },
    {
      agentId: 'orchestrator',
      status: 'working',
      progress: 40,
      message: 'Delegating to specialists...'
    },
    {
      agentId: 'retrieval',
      status: 'working',
      progress: 30,
      message: 'Searching sources...'
    },
    {
      agentId: 'retrieval',
      status: 'working',
      progress: 60,
      message: 'Found 15 relevant sources'
    },
    {
      agentId: 'retrieval',
      status: 'completed',
      progress: 100,
      message: 'Search complete ✓'
    },
    {
      agentId: 'analysis',
      status: 'working',
      progress: 25,
      message: 'Processing sources...'
    },
    {
      agentId: 'analysis',
      status: 'working',
      progress: 50,
      message: 'Extracting key insights...'
    },
    {
      agentId: 'analysis',
      status: 'working',
      progress: 75,
      message: 'Synthesizing findings...'
    },
    {
      agentId: 'analysis',
      status: 'completed',
      progress: 100,
      message: 'Analysis complete ✓'
    },
    {
      agentId: 'citation',
      status: 'working',
      progress: 50,
      message: 'Generating citations...'
    },
    {
      agentId: 'citation',
      status: 'completed',
      progress: 100,
      message: '15 citations ready ✓'
    },
    {
      agentId: 'knowledge',
      status: 'working',
      progress: 30,
      message: 'Extracting entities...'
    },
    {
      agentId: 'knowledge',
      status: 'working',
      progress: 70,
      message: 'Mapping relationships...'
    },
    {
      agentId: 'knowledge',
      status: 'completed',
      progress: 100,
      message: 'Graph complete ✓'
    },
    {
      agentId: 'orchestrator',
      status: 'working',
      progress: 80,
      message: 'Compiling results...'
    },
    {
      agentId: 'orchestrator',
      status: 'completed',
      progress: 100,
      message: 'Research complete! ✓'
    }
  ];
  
  useEffect(() => {
    if (isRunning && currentStep < simulationSteps.length) {
      const timeout = setTimeout(() => {
        const step = simulationSteps[currentStep];
        setAgents(prev => prev.map(agent => 
          agent.id === step.agentId
            ? { ...agent, status: step.status as 'idle' | 'working' | 'completed', progress: step.progress, message: step.message }
            : agent
        ));
        setCurrentStep(currentStep + 1);
      }, 800);
      
      return () => clearTimeout(timeout);
    } else if (currentStep >= simulationSteps.length) {
      // Reset after completion
      setTimeout(() => {
        setAgents(prev => prev.map(agent => ({
          ...agent,
          status: 'idle',
          progress: 0,
          message: agent.id === 'orchestrator' ? 'Ready to coordinate' : 'Waiting for task'
        })));
        setCurrentStep(0);
      }, 2000);
    }
  }, [currentStep, isRunning]);
  
  const getColorClasses = (color: string) => {
    const colors = {
      purple: 'bg-purple-600 border-purple-500',
      blue: 'bg-blue-600 border-blue-500',
      green: 'bg-green-600 border-green-500',
      yellow: 'bg-yellow-600 border-yellow-500',
      orange: 'bg-orange-600 border-orange-500'
    };
    return colors[color as keyof typeof colors] || colors.purple;
  };
  
  const getProgressColor = (color: string) => {
    const colors = {
      purple: 'bg-purple-500',
      blue: 'bg-blue-500',
      green: 'bg-green-500',
      yellow: 'bg-yellow-500',
      orange: 'bg-orange-500'
    };
    return colors[color as keyof typeof colors] || colors.purple;
  };
  
  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Agent Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {agents.map((agent) => (
          <motion.div
            key={agent.id}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`
              relative bg-gray-700 rounded-lg p-4 border-2 transition-all
              ${agent.status === 'working' ? 'border-opacity-100' : 'border-opacity-30'}
              ${agent.status === 'completed' ? 'bg-opacity-50' : ''}
              ${getColorClasses(agent.color)}
            `}
          >
            {/* Status Indicator */}
            <div className="absolute -top-2 -right-2">
              <AnimatePresence>
                {agent.status === 'working' && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    exit={{ scale: 0 }}
                    className="relative"
                  >
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                      className="w-6 h-6 border-2 border-white border-t-transparent rounded-full"
                    />
                  </motion.div>
                )}
                {agent.status === 'completed' && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center"
                  >
                    <CheckCircle className="w-4 h-4 text-white" />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            
            {/* Agent Info */}
            <div className="flex items-center gap-2 mb-2">
              <div className="text-white">{agent.icon}</div>
              <h3 className="text-white font-medium text-sm">{agent.name}</h3>
            </div>
            
            {/* Progress Bar */}
            <div className="h-2 bg-gray-600 rounded-full overflow-hidden mb-2">
              <motion.div
                className={`h-full ${getProgressColor(agent.color)}`}
                initial={{ width: 0 }}
                animate={{ width: `${agent.progress}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
            
            {/* Status Message */}
            <p className="text-xs text-gray-300 truncate">{agent.message}</p>
          </motion.div>
        ))}
      </div>
      
      {/* Central Coordination Visual */}
      <div className="mt-6 relative h-32">
        <svg className="absolute inset-0 w-full h-full">
          {/* Connection lines */}
          {agents.slice(1).map((agent, index) => (
            <motion.line
              key={agent.id}
              x1="50%"
              y1="50%"
              x2={`${25 + (index % 2) * 50}%`}
              y2={index < 2 ? "20%" : "80%"}
              stroke={agent.status === 'working' ? '#9333ea' : '#4b5563'}
              strokeWidth="2"
              strokeDasharray={agent.status === 'working' ? "5,5" : "0"}
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 1, delay: index * 0.2 }}
            >
              {agent.status === 'working' && (
                <animate
                  attributeName="stroke-dashoffset"
                  values="10;0"
                  dur="1s"
                  repeatCount="indefinite"
                />
              )}
            </motion.line>
          ))}
        </svg>
        
        {/* Central Orchestrator Node */}
        <motion.div
          className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
          animate={{
            scale: agents[0].status === 'working' ? [1, 1.1, 1] : 1
          }}
          transition={{ duration: 1, repeat: Infinity }}
        >
          <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center shadow-lg">
            <Brain className="w-8 h-8 text-white" />
          </div>
        </motion.div>
      </div>
      
      {/* Info Text */}
      <motion.div
        className="mt-6 text-center text-gray-300"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <p className="text-sm">
          Watch as agents work together to research your query
        </p>
        <p className="text-xs text-gray-500 mt-1">
          Each agent specializes in different aspects of research
        </p>
      </motion.div>
    </div>
  );
};

export default AgentActivityDemo;