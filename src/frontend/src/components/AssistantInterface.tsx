import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import KnowledgeGraph from './KnowledgeGraph';
import AssistantCharacter from './AssistantCharacter';
import FollowUpPrompt from './FollowUpPrompt';
import { ResearchMode, UserSubscription } from '../types/terminal';
import websocketService from '../services/websocketService';
import api from '../services/api';

interface AssistantInterfaceProps {
  subscription: UserSubscription;
  onModeChange: (mode: ResearchMode) => void;
}

type AssistantState = 'idle' | 'thinking' | 'presenting' | 'error';
type AssistantEmotion = 'neutral' | 'happy' | 'sad' | 'excited' | 'confused' | 'focused' | 'surprised' | 'thoughtful';

interface ResearchResult {
  summary: string;
  sources: any[];
  knowledgeGraph?: any;
  followUpQuestions?: string[];
}

const AssistantInterface: React.FC<AssistantInterfaceProps> = ({ subscription, onModeChange }) => {
  const { state } = useAuth();
  const [query, setQuery] = useState('');
  const [continuousMode, setContinuousMode] = useState(false);
  const [assistantState, setAssistantState] = useState<AssistantState>('idle');
  const [assistantEmotion, setAssistantEmotion] = useState<AssistantEmotion>('neutral');
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [progress, setProgress] = useState(0);
  const [currentFocusArea, setCurrentFocusArea] = useState<string | null>(null);
  const [showKnowledgeGraph, setShowKnowledgeGraph] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryInputRef = useRef<HTMLInputElement>(null);
  const resultsPanelRef = useRef<HTMLDivElement>(null);

  // Configure WebSocket event handlers
  useEffect(() => {
    const handleProgressUpdate = (data: any) => {
      setProgress(data.progress_percent);
      setCurrentFocusArea(data.focus_area);
      
      // Update assistant state based on progress
      if (data.progress_percent < 20) {
        setAssistantState('thinking');
        setAssistantEmotion('focused');
      } else if (data.progress_percent >= 20 && data.progress_percent < 80) {
        setAssistantState('thinking');
        setAssistantEmotion('thoughtful');
      } else {
        setAssistantState('thinking');
        setAssistantEmotion('excited');
      }
    };

    const handleResearchComplete = (data: any) => {
      setAssistantState('presenting');
      setAssistantEmotion('happy');
      setResult({
        summary: data.research.summary,
        sources: data.research.sources,
        knowledgeGraph: data.knowledge_graph?.graph,
        followUpQuestions: data.followup_questions
      });
      
      // Scroll to results
      if (resultsPanelRef.current) {
        resultsPanelRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    };

    const handleError = (data: any) => {
      setAssistantState('error');
      setAssistantEmotion('sad');
      setError(data.error || 'An unknown error occurred');
    };

    // Register WebSocket listeners
    const removeProgressListener = websocketService.on('research_update', handleProgressUpdate);
    const removeErrorListener = websocketService.on('error', handleError);

    // Cleanup
    return () => {
      removeProgressListener();
      removeErrorListener();
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) return;
    
    // Reset state
    setResult(null);
    setError(null);
    setProgress(0);
    setCurrentFocusArea(null);
    setShowKnowledgeGraph(false);
    
    // Update assistant state
    setAssistantState('thinking');
    setAssistantEmotion('focused');
    
    try {
      // Send research request to API
      await api.post('/research', {
        query: query.trim(),
        continuous_mode: continuousMode,
        force_refresh: false
      });
      
      // Focus is handled by WebSocket responses
    } catch (error) {
      console.error('Research request failed:', error);
      setAssistantState('error');
      setAssistantEmotion('sad');
      setError('Failed to start research. Please try again.');
    }
  };

  const toggleKnowledgeGraph = () => {
    setShowKnowledgeGraph(!showKnowledgeGraph);
  };

  const handleFollowUpQuestion = (question: string) => {
    setQuery(question);
    // Auto-submit
    if (queryInputRef.current) {
      queryInputRef.current.value = question;
      handleSubmit(new Event('submit') as any);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      {/* Animated Assistant Character */}
      <div className="fixed bottom-8 right-8 z-50">
        <AssistantCharacter 
          state={assistantState}
          emotion={assistantEmotion}
          onClick={() => queryInputRef.current?.focus()}
        />
      </div>
      
      {/* Main Content */}
      <div className="max-w-6xl mx-auto">
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
            Starri
          </h1>
          <p className="text-gray-400">Your intelligent research assistant</p>
        </header>
        
        {/* Search Form */}
        <form onSubmit={handleSubmit} className="mb-8">
          <div className="relative">
            <input
              ref={queryInputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What would you like to research today?"
              className="w-full px-6 py-4 bg-gray-800 rounded-full text-white border border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="absolute right-4 top-4 flex items-center space-x-2">
              <label className="inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={continuousMode}
                  onChange={() => setContinuousMode(!continuousMode)}
                  className="sr-only peer"
                />
                <div className="relative h-6 w-11 bg-gray-700 rounded-full peer peer-checked:bg-blue-500 peer-focus:ring-2 peer-focus:ring-blue-500">
                  <div className="absolute left-[2px] top-[2px] bg-white rounded-full h-5 w-5 transition-transform peer-checked:translate-x-5"></div>
                </div>
                <span className="ml-2 text-sm text-gray-400">Thorough Research</span>
              </label>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 rounded-full hover:bg-blue-700 transition-colors"
              >
                Research
              </button>
            </div>
          </div>
        </form>
        
        {/* Progress Indicator */}
        {assistantState === 'thinking' && (
          <div className="mb-8 bg-gray-800 p-6 rounded-lg">
            <div className="flex justify-between mb-2">
              <span className="text-gray-400">Researching...</span>
              <span className="text-blue-400">{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-gray-700 h-2 rounded-full overflow-hidden">
              <div
                className="bg-blue-500 h-full transition-all duration-300 ease-out"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            {currentFocusArea && (
              <p className="mt-2 text-sm text-gray-400">
                Currently researching: {currentFocusArea}
              </p>
            )}
          </div>
        )}
        
        {/* Error Display */}
        {error && (
          <div className="mb-8 bg-red-900/30 border border-red-700 p-6 rounded-lg">
            <h3 className="text-red-400 font-bold mb-2">Research Error</h3>
            <p className="text-white">{error}</p>
            <button 
              onClick={() => handleSubmit(new Event('submit') as any)}
              className="mt-4 px-4 py-2 bg-red-700 rounded-md hover:bg-red-600 transition-colors"
            >
              Retry
            </button>
          </div>
        )}
        
        {/* Results Display */}
        {result && (
          <div ref={resultsPanelRef} className="mb-8 bg-gray-800 p-6 rounded-lg">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-white">Research Results</h2>
              <div>
                {result.knowledgeGraph && (
                  <button
                    onClick={toggleKnowledgeGraph}
                    className="px-4 py-2 bg-purple-600 rounded-md mr-2 hover:bg-purple-700 transition-colors"
                  >
                    {showKnowledgeGraph ? 'Hide' : 'Show'} Knowledge Graph
                  </button>
                )}
              </div>
            </div>
            
            {/* Knowledge Graph Visualization */}
            {showKnowledgeGraph && result.knowledgeGraph && (
              <div className="mb-6 bg-gray-900 p-4 rounded-lg h-96">
                <KnowledgeGraph graphData={result.knowledgeGraph} />
              </div>
            )}
            
            {/* Summary */}
            <div className="prose prose-invert max-w-none mb-6">
              <h3 className="text-blue-400">Summary</h3>
              <div className="whitespace-pre-line">{result.summary}</div>
            </div>
            
            {/* Sources */}
            <div className="mb-6">
              <h3 className="text-blue-400 mb-2">Sources</h3>
              <div className="max-h-60 overflow-y-auto bg-gray-900 rounded-lg p-4">
                <ul className="space-y-2">
                  {result.sources.map((source, index) => (
                    <li key={index} className="text-sm">
                      <a 
                        href={source.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:underline flex items-start"
                      >
                        <span className="mr-2">{index + 1}.</span>
                        <span>
                          {source.title} 
                          <span className="text-gray-500 block">
                            {source.site_name} • Reliability: {Math.round(source.reliability_score * 100)}%
                          </span>
                        </span>
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            
            {/* Follow-up Questions */}
            {result.followUpQuestions && result.followUpQuestions.length > 0 && (
              <div>
                <h3 className="text-blue-400 mb-2">Follow-up Questions</h3>
                <FollowUpPrompt 
                  questions={result.followUpQuestions} 
                  onSelectQuestion={handleFollowUpQuestion}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AssistantInterface;