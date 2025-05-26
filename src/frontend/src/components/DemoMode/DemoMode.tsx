import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Sparkles, 
  Play, 
  RefreshCw, 
  Info,
  ChevronRight,
  Zap,
  Brain,
  Globe
} from 'lucide-react';
import { DemoQuery, DemoModeManager } from '../../services/demoModeService';

interface DemoModeProps {
  onRunDemo: (query: string) => void;
  isActive: boolean;
}

const DEMO_QUERIES: DemoQuery[] = [
  {
    id: 'quantum',
    query: "What are the latest breakthroughs in quantum computing?",
    description: "Explore cutting-edge quantum research",
    category: "Technology",
    icon: "⚛️",
    expectedTime: 15,
    highlights: ["IBM quantum supremacy", "Google Sycamore", "Error correction advances"]
  },
  {
    id: 'climate',
    query: "How is AI being used in climate change research?",
    description: "Discover AI applications in environmental science",
    category: "Environment",
    icon: "🌍",
    expectedTime: 12,
    highlights: ["Weather prediction", "Carbon capture optimization", "Biodiversity monitoring"]
  },
  {
    id: 'biotech',
    query: "What are the emerging trends in biotechnology for 2025?",
    description: "Latest biotech innovations and applications",
    category: "Science",
    icon: "🧬",
    expectedTime: 18,
    highlights: ["CRISPR advances", "Synthetic biology", "Personalized medicine"]
  },
  {
    id: 'space',
    query: "Recent discoveries in exoplanet research and their implications",
    description: "Journey through the latest space exploration findings",
    category: "Space",
    icon: "🚀",
    expectedTime: 14,
    highlights: ["JWST discoveries", "Habitable zones", "Biosignatures"]
  },
  {
    id: 'neuroscience',
    query: "Breakthroughs in understanding consciousness and the brain",
    description: "Explore the mysteries of the mind",
    category: "Neuroscience",
    icon: "🧠",
    expectedTime: 16,
    highlights: ["Neural networks", "Consciousness theories", "Brain-computer interfaces"]
  },
  {
    id: 'energy',
    query: "Revolutionary renewable energy technologies in development",
    description: "Future of sustainable energy",
    category: "Energy",
    icon: "⚡",
    expectedTime: 13,
    highlights: ["Fusion breakthroughs", "Advanced solar", "Energy storage"]
  }
];

const DemoMode: React.FC<DemoModeProps> = ({ onRunDemo, isActive }) => {
  const [selectedDemo, setSelectedDemo] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(true);
  const [runningDemo, setRunningDemo] = useState<string | null>(null);
  const [showInfo, setShowInfo] = useState(false);

  const handleRunDemo = useCallback((query: DemoQuery) => {
    setRunningDemo(query.id);
    setSelectedDemo(query.id);
    onRunDemo(query.query);
    
    // Track demo usage
    if (window.gtag) {
      window.gtag('event', 'demo_query_run', {
        query_id: query.id,
        category: query.category
      });
    }
    
    // Reset after expected time
    setTimeout(() => {
      setRunningDemo(null);
    }, query.expectedTime * 1000);
  }, [onRunDemo]);

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      Technology: 'from-purple-500 to-blue-500',
      Environment: 'from-green-500 to-teal-500',
      Science: 'from-pink-500 to-rose-500',
      Space: 'from-indigo-500 to-purple-500',
      Neuroscience: 'from-orange-500 to-red-500',
      Energy: 'from-yellow-500 to-orange-500'
    };
    return colors[category] || 'from-gray-500 to-gray-600';
  };

  if (!isActive) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="fixed bottom-4 right-4 z-40"
    >
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="bg-gray-900 rounded-2xl shadow-2xl border border-gray-700 overflow-hidden mb-4"
            style={{ width: '400px', maxHeight: '600px' }}
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-white" />
                  <h3 className="text-white font-semibold">Demo Mode</h3>
                </div>
                <button
                  onClick={() => setShowInfo(!showInfo)}
                  className="text-white/80 hover:text-white transition-colors"
                >
                  <Info className="w-5 h-5" />
                </button>
              </div>
              
              <AnimatePresence>
                {showInfo && (
                  <motion.p
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="text-white/90 text-sm mt-2"
                  >
                    Try these pre-configured queries to see Parallax Pal in action. 
                    Each demo showcases different agent capabilities.
                  </motion.p>
                )}
              </AnimatePresence>
            </div>

            {/* Demo Queries */}
            <div className="p-4 space-y-3 overflow-y-auto" style={{ maxHeight: '450px' }}>
              {DEMO_QUERIES.map((demo) => (
                <motion.div
                  key={demo.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  whileHover={{ scale: 1.02 }}
                  onClick={() => handleRunDemo(demo)}
                  className={`
                    relative cursor-pointer rounded-xl p-4 transition-all
                    ${selectedDemo === demo.id 
                      ? 'bg-gradient-to-r ' + getCategoryColor(demo.category) + ' text-white'
                      : 'bg-gray-800 hover:bg-gray-700'
                    }
                    ${runningDemo === demo.id ? 'animate-pulse' : ''}
                  `}
                >
                  {/* Running Indicator */}
                  {runningDemo === demo.id && (
                    <motion.div
                      className="absolute top-2 right-2"
                      animate={{ rotate: 360 }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    >
                      <RefreshCw className="w-4 h-4 text-white" />
                    </motion.div>
                  )}

                  <div className="flex items-start gap-3">
                    <div className="text-2xl">{demo.icon}</div>
                    <div className="flex-1">
                      <h4 className={`font-semibold mb-1 ${
                        selectedDemo === demo.id ? 'text-white' : 'text-white'
                      }`}>
                        {demo.query}
                      </h4>
                      <p className={`text-sm mb-2 ${
                        selectedDemo === demo.id ? 'text-white/90' : 'text-gray-400'
                      }`}>
                        {demo.description}
                      </p>
                      
                      {/* Category & Time */}
                      <div className="flex items-center gap-4 text-xs">
                        <span className={`px-2 py-1 rounded-full ${
                          selectedDemo === demo.id 
                            ? 'bg-white/20 text-white' 
                            : 'bg-gray-700 text-gray-300'
                        }`}>
                          {demo.category}
                        </span>
                        <span className={selectedDemo === demo.id ? 'text-white/80' : 'text-gray-500'}>
                          ~{demo.expectedTime}s
                        </span>
                      </div>

                      {/* Expected Highlights */}
                      {selectedDemo === demo.id && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          className="mt-3 pt-3 border-t border-white/20"
                        >
                          <p className="text-xs text-white/80 mb-1">Expected insights:</p>
                          <div className="flex flex-wrap gap-1">
                            {demo.highlights.map((highlight, idx) => (
                              <span
                                key={idx}
                                className="text-xs bg-white/20 px-2 py-1 rounded-full"
                              >
                                {highlight}
                              </span>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </div>
                    
                    <ChevronRight className={`w-5 h-5 transition-colors ${
                      selectedDemo === demo.id ? 'text-white' : 'text-gray-500'
                    }`} />
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Quick Stats */}
            <div className="border-t border-gray-700 p-4 bg-gray-800/50">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <Zap className="w-5 h-5 text-yellow-500 mx-auto mb-1" />
                  <p className="text-xs text-gray-400">Fast Results</p>
                </div>
                <div>
                  <Brain className="w-5 h-5 text-purple-500 mx-auto mb-1" />
                  <p className="text-xs text-gray-400">AI Powered</p>
                </div>
                <div>
                  <Globe className="w-5 h-5 text-blue-500 mx-auto mb-1" />
                  <p className="text-xs text-gray-400">Real Sources</p>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Toggle Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsExpanded(!isExpanded)}
        className={`
          bg-gradient-to-r from-purple-600 to-blue-600 text-white 
          rounded-full p-4 shadow-lg flex items-center gap-2
          ${runningDemo ? 'animate-pulse' : ''}
        `}
      >
        {runningDemo ? (
          <RefreshCw className="w-6 h-6 animate-spin" />
        ) : (
          <Play className="w-6 h-6" />
        )}
        <span className="font-medium pr-2">
          {runningDemo ? 'Running Demo...' : 'Demo Mode'}
        </span>
      </motion.button>
    </motion.div>
  );
};

export default DemoMode;