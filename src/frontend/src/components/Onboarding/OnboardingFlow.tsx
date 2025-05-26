import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowRight, 
  Search, 
  Brain, 
  FileText, 
  Network, 
  Sparkles,
  CheckCircle,
  X
} from 'lucide-react';
import StarriWaveAnimation from './StarriWaveAnimation';
import SearchDemoAnimation from './SearchDemoAnimation';
import AgentActivityDemo from './AgentActivityDemo';
import ResultsPreview from './ResultsPreview';
import './Onboarding.css';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  demo: React.ReactNode;
  tips?: string[];
}

interface OnboardingFlowProps {
  onComplete: () => void;
  onSkip: () => void;
}

const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ onComplete, onSkip }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [isExiting, setIsExiting] = useState(false);

  const steps: OnboardingStep[] = [
    {
      id: 'meet-starri',
      title: "Meet Starri, Your Research Assistant",
      description: "Starri uses multiple AI agents to help you research any topic comprehensively. Each agent specializes in different aspects of research.",
      icon: <Brain className="w-12 h-12 text-purple-500" />,
      demo: <StarriWaveAnimation />,
      tips: [
        "Starri coordinates 5 specialized agents",
        "Real-time progress updates",
        "Personality changes based on research status"
      ]
    },
    {
      id: 'ask-anything',
      title: "Ask Anything",
      description: "Type or speak your research question. Starri will break it down and coordinate specialized agents to find the best information.",
      icon: <Search className="w-12 h-12 text-blue-500" />,
      demo: <SearchDemoAnimation />,
      tips: [
        "Use natural language queries",
        "Try voice input for hands-free research",
        "Add focus areas for targeted results"
      ]
    },
    {
      id: 'watch-agents',
      title: "Watch Agents Work",
      description: "See real-time progress as agents search, analyze, and synthesize information. Each agent has a specific role in the research process.",
      icon: <Network className="w-12 h-12 text-green-500" />,
      demo: <AgentActivityDemo />,
      tips: [
        "Retrieval Agent finds credible sources",
        "Analysis Agent synthesizes findings",
        "Citation Agent generates bibliographies",
        "Knowledge Graph Agent maps relationships"
      ]
    },
    {
      id: 'get-results',
      title: "Get Professional Results",
      description: "Receive comprehensive summaries, citations, and interactive knowledge graphs. Export in multiple formats.",
      icon: <FileText className="w-12 h-12 text-orange-500" />,
      demo: <ResultsPreview />,
      tips: [
        "Interactive knowledge graphs",
        "Export to PDF, Word, Notion",
        "Professional citations in multiple formats"
      ]
    },
    {
      id: 'pro-features',
      title: "Unlock Advanced Features",
      description: "Collaborate with others, use voice commands, and access premium export options with upgraded tiers.",
      icon: <Sparkles className="w-12 h-12 text-yellow-500" />,
      demo: <ProFeaturesShowcase />,
      tips: [
        "Voice interaction for hands-free research",
        "Collaborative research sessions",
        "Advanced export formats",
        "Priority processing"
      ]
    }
  ];

  useEffect(() => {
    // Check if user has seen onboarding before
    const hasSeenOnboarding = localStorage.getItem('onboarding_completed');
    if (hasSeenOnboarding === 'true') {
      onComplete();
    }
  }, [onComplete]);

  const handleNext = () => {
    setCompletedSteps(prev => new Set(prev).add(currentStep));
    
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    setIsExiting = true;
    localStorage.setItem('onboarding_completed', 'true');
    localStorage.setItem('onboarding_date', new Date().toISOString());
    
    // Track completion
    if (window.gtag) {
      window.gtag('event', 'onboarding_complete', {
        steps_viewed: completedSteps.size + 1,
        total_steps: steps.length
      });
    }
    
    setTimeout(() => {
      onComplete();
    }, 300);
  };

  const handleSkip = () => {
    setIsExiting = true;
    localStorage.setItem('onboarding_skipped', 'true');
    
    // Track skip
    if (window.gtag) {
      window.gtag('event', 'onboarding_skip', {
        skipped_at_step: currentStep,
        total_steps: steps.length
      });
    }
    
    setTimeout(() => {
      onSkip();
    }, 300);
  };

  const progress = ((currentStep + 1) / steps.length) * 100;

  return (
    <AnimatePresence>
      {!isExiting && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="bg-gray-900 rounded-2xl p-8 max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-purple-600 rounded-full flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white">Welcome to Parallax Pal</h1>
                  <p className="text-gray-400 text-sm">Let's get you started with AI-powered research</p>
                </div>
              </div>
              <button
                onClick={handleSkip}
                className="text-gray-400 hover:text-white transition-colors p-2"
                aria-label="Skip tutorial"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Progress Bar */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-2">
                {steps.map((step, index) => (
                  <div
                    key={step.id}
                    className="flex items-center"
                  >
                    <div
                      className={`
                        w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                        transition-all duration-300
                        ${index === currentStep 
                          ? 'bg-purple-600 text-white scale-110' 
                          : index < currentStep || completedSteps.has(index)
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-700 text-gray-400'
                        }
                      `}
                    >
                      {completedSteps.has(index) ? (
                        <CheckCircle className="w-5 h-5" />
                      ) : (
                        index + 1
                      )}
                    </div>
                    {index < steps.length - 1 && (
                      <div
                        className={`
                          h-1 w-full mx-2 rounded-full transition-all duration-300
                          ${index < currentStep 
                            ? 'bg-green-600' 
                            : 'bg-gray-700'
                          }
                        `}
                        style={{ width: '60px' }}
                      />
                    )}
                  </div>
                ))}
              </div>
              <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-purple-600 to-blue-600"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            </div>

            {/* Current Step */}
            <AnimatePresence mode="wait">
              <motion.div
                key={currentStep}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="mb-8"
              >
                <div className="text-center mb-6">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.1, type: "spring" }}
                    className="inline-block mb-4"
                  >
                    {steps[currentStep].icon}
                  </motion.div>
                  <h2 className="text-3xl font-bold text-white mb-3">
                    {steps[currentStep].title}
                  </h2>
                  <p className="text-gray-300 text-lg max-w-2xl mx-auto">
                    {steps[currentStep].description}
                  </p>
                </div>

                {/* Demo Area */}
                <div className="bg-gray-800 rounded-xl p-6 mb-6 min-h-[300px] flex items-center justify-center">
                  {steps[currentStep].demo}
                </div>

                {/* Tips */}
                {steps[currentStep].tips && (
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h3 className="text-sm font-semibold text-purple-400 mb-2">
                      💡 Quick Tips
                    </h3>
                    <ul className="space-y-1">
                      {steps[currentStep].tips.map((tip, index) => (
                        <li key={index} className="text-gray-300 text-sm flex items-start">
                          <span className="text-purple-400 mr-2">•</span>
                          {tip}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </motion.div>
            </AnimatePresence>

            {/* Navigation */}
            <div className="flex justify-between items-center">
              <button
                onClick={handlePrevious}
                disabled={currentStep === 0}
                className={`
                  px-6 py-2 rounded-lg font-medium transition-all
                  ${currentStep === 0
                    ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                    : 'bg-gray-800 text-white hover:bg-gray-700'
                  }
                `}
              >
                Previous
              </button>

              <div className="flex gap-2">
                {currentStep === steps.length - 1 ? (
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleComplete}
                    className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-8 py-2 rounded-lg font-medium flex items-center gap-2 shadow-lg"
                  >
                    Get Started
                    <Sparkles className="w-4 h-4" />
                  </motion.button>
                ) : (
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleNext}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors"
                  >
                    Next
                    <ArrowRight className="w-4 h-4" />
                  </motion.button>
                )}
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Demo Components (these would be separate files in production)

const ProFeaturesShowcase: React.FC = () => {
  return (
    <div className="grid grid-cols-2 gap-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-gray-700 rounded-lg p-4"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center">
            🎤
          </div>
          <h4 className="font-semibold text-white">Voice Commands</h4>
        </div>
        <p className="text-gray-300 text-sm">
          Simply speak your research questions for hands-free operation
        </p>
      </motion.div>
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-gray-700 rounded-lg p-4"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
            👥
          </div>
          <h4 className="font-semibold text-white">Collaboration</h4>
        </div>
        <p className="text-gray-300 text-sm">
          Work together on research projects in real-time
        </p>
      </motion.div>
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-gray-700 rounded-lg p-4"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-green-600 rounded-full flex items-center justify-center">
            📊
          </div>
          <h4 className="font-semibold text-white">Advanced Exports</h4>
        </div>
        <p className="text-gray-300 text-sm">
          Export to Notion, Word, PDF, and more formats
        </p>
      </motion.div>
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-gray-700 rounded-lg p-4"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-orange-600 rounded-full flex items-center justify-center">
            ⚡
          </div>
          <h4 className="font-semibold text-white">Priority Processing</h4>
        </div>
        <p className="text-gray-300 text-sm">
          Get faster results with premium tier access
        </p>
      </motion.div>
    </div>
  );
};

export default OnboardingFlow;