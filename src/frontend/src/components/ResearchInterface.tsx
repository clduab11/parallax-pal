import React, { useState, useEffect, useRef } from 'react';
import AssistantCharacter from './AssistantCharacter';
import KnowledgeGraph from './KnowledgeGraph';
import FollowUpPrompt from './FollowUpPrompt';
import { ResearchRequest, ResearchResponse, KnowledgeGraphData, AssistantState } from '../types/adk';
import adkService from '../services/adkService';
import '../styles/ResearchInterface.css';

const ResearchInterface: React.FC = () => {
  const [query, setQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [researchResults, setResearchResults] = useState<ResearchResponse | null>(null);
  const [graphData, setGraphData] = useState<KnowledgeGraphData | null>(null);
  const [followUpQuestions, setFollowUpQuestions] = useState<string[]>([]);
  const [assistantState, setAssistantState] = useState<AssistantState>({
    emotion: 'neutral',
    state: 'idle',
    showBubble: false
  });
  const [activeTab, setActiveTab] = useState<'summary' | 'sources' | 'graph'>('summary');
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [continuousMode, setContinuousMode] = useState<boolean>(true);
  const [forceRefresh, setForceRefresh] = useState<boolean>(false);

  const resultPanelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Connect to WebSocket when component mounts
    const connectWebSocket = async () => {
      try {
        const token = localStorage.getItem('accessToken');
        if (token) {
          await adkService.initializeWebSocket(token);
          console.log('ADK WebSocket initialized');
        }
        
        // Set up message handlers
        adkService.addEventListener('research_update', handleResearchUpdate);
        adkService.addEventListener('research_completed', handleResearchCompleted);
        adkService.addEventListener('knowledge_graph_update', handleKnowledgeGraphUpdate);
        adkService.addEventListener('error', handleError);
        adkService.addEventListener('followup_questions', handleFollowUpQuestions);
      } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
        setError('Failed to connect to research service. Please try again later.');
      }
    };

    connectWebSocket();

    // Cleanup WebSocket connection when component unmounts
    return () => {
      adkService.cleanup();
    };
  }, []);

  // Handle WebSocket message handlers
  const handleResearchUpdate = (data: any) => {
    setProgress(data.data.status.progress);
    setAssistantState(data.data.assistant_state);
  };

  const handleResearchCompleted = (data: any) => {
    setLoading(false);
    setResearchResults(data.data);
    setProgress(100);
    setAssistantState(data.data.assistant_state);
    
    // Get knowledge graph
    if (data.data.request_id) {
      fetchKnowledgeGraph(data.data.request_id);
      fetchFollowUpQuestions(data.data.request_id);
    }
  };

  const handleKnowledgeGraphUpdate = (data: any) => {
    setGraphData(data.data.partial_graph);
  };

  const handleError = (data: any) => {
    setLoading(false);
    setError(data.data.error_message);
    setAssistantState(data.data.assistant_state);
  };

  const handleFollowUpQuestions = (data: any) => {
    setFollowUpQuestions(data.data.questions);
  };

  // Fetch knowledge graph for research
  const fetchKnowledgeGraph = async (reqId: string) => {
    try {
      const response = await adkService.getKnowledgeGraph(reqId);
      setGraphData(response.data);
    } catch (error) {
      console.error('Failed to fetch knowledge graph:', error);
    }
  };

  // Fetch follow-up questions
  const fetchFollowUpQuestions = async (reqId: string) => {
    try {
      const response = await adkService.getFollowupQuestions(reqId);
      setFollowUpQuestions(response.data);
    } catch (error) {
      console.error('Failed to fetch follow-up questions:', error);
    }
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) return;
    
    setLoading(true);
    setError(null);
    setResearchResults(null);
    setGraphData(null);
    setFollowUpQuestions([]);
    setProgress(0);
    setActiveTab('summary');
    
    setAssistantState({
      emotion: 'excited',
      state: 'thinking',
      message: 'Researching your topic...',
      showBubble: true
    });
    
    try {
      const request: ResearchRequest = {
        query,
        continuous_mode: continuousMode,
        force_refresh: forceRefresh
      };
      
      const response = await adkService.startResearch(
        request.query,
        request.continuous_mode,
        request.force_refresh
      );
      setRequestId(response.data.request_id);
      
      // Result panel scroll to top
      if (resultPanelRef.current) {
        resultPanelRef.current.scrollTop = 0;
      }
    } catch (error: any) {
      console.error('Failed to submit research:', error);
      setLoading(false);
      setError(error.message || 'Failed to submit research. Please try again.');
      
      setAssistantState({
        emotion: 'sad',
        state: 'error',
        message: 'Sorry, something went wrong with the research.',
        showBubble: true
      });
    }
  };

  // Handle follow-up question click
  const handleFollowUpClick = (question: string) => {
    setQuery(question);
    handleSubmit(new Event('submit') as unknown as React.FormEvent);
  };

  // Render sources list
  const renderSources = () => {
    if (!researchResults) return null;
    
    const allSources: any[] = [];
    
    researchResults.focus_areas.forEach(area => {
      area.sources.forEach(source => {
        allSources.push({
          ...source,
          focusArea: area.topic
        });
      });
    });
    
    return (
      <div className="sources-list">
        {allSources.map((source, index) => (
          <div key={index} className="source-item">
            <div className="source-header">
              <h3>
                <a href={source.url} target="_blank" rel="noopener noreferrer">
                  {source.title}
                </a>
              </h3>
              <div className="source-meta">
                <span className="source-domain">{source.domain}</span>
                <span className="source-reliability" title={`Reliability: ${Math.round(source.reliability_score * 100)}%`}>
                  {Array(5).fill(0).map((_, i) => (
                    <span key={i} className={`star ${i < Math.round(source.reliability_score * 5) ? 'filled' : ''}`}>★</span>
                  ))}
                </span>
              </div>
            </div>
            <div className="source-focus-area">Focus area: {source.focusArea}</div>
            <p className="source-snippet">{source.snippet}</p>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="research-interface">
      <div className="research-sidebar">
        <AssistantCharacter
          emotion={assistantState.emotion}
          state={assistantState.state}
          speechBubble={assistantState.message}
          size="large"
          position="top-left"
        />
        
        <form onSubmit={handleSubmit} className="research-form">
          <div className="input-container">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What would you like to research?"
              disabled={loading}
              className="research-input"
            />
            <button type="submit" disabled={loading || !query.trim()} className="research-button">
              {loading ? 'Researching...' : 'Research'}
            </button>
          </div>
          
          <div className="search-options">
            <label className="option-label">
              <input
                type="checkbox"
                checked={continuousMode}
                onChange={(e) => setContinuousMode(e.target.checked)}
                disabled={loading}
              />
              <span>Comprehensive mode</span>
            </label>
            
            <label className="option-label">
              <input
                type="checkbox"
                checked={forceRefresh}
                onChange={(e) => setForceRefresh(e.target.checked)}
                disabled={loading}
              />
              <span>Ignore cache</span>
            </label>
          </div>
        </form>
        
        {loading && (
          <div className="research-progress">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
            <div className="progress-text">{progress}% Complete</div>
          </div>
        )}
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
        
        {followUpQuestions.length > 0 && (
          <FollowUpPrompt
            questions={followUpQuestions}
            onSelectQuestion={handleFollowUpClick}
          />
        )}
      </div>
      
      <div className="research-content" ref={resultPanelRef}>
        {researchResults && (
          <>
            <div className="research-tabs">
              <button
                className={`tab ${activeTab === 'summary' ? 'active' : ''}`}
                onClick={() => setActiveTab('summary')}
              >
                Summary
              </button>
              <button
                className={`tab ${activeTab === 'sources' ? 'active' : ''}`}
                onClick={() => setActiveTab('sources')}
              >
                Sources
              </button>
              <button
                className={`tab ${activeTab === 'graph' ? 'active' : ''}`}
                onClick={() => setActiveTab('graph')}
                disabled={!graphData}
              >
                Knowledge Graph
              </button>
            </div>
            
            <div className="research-panel">
              {activeTab === 'summary' && (
                <div className="summary-panel">
                  <h2>Research Summary</h2>
                  <div className="summary-content">
                    {researchResults.summary}
                  </div>
                  
                  <h3>Focus Areas</h3>
                  <div className="focus-areas">
                    {researchResults.focus_areas.map((area, index) => (
                      <div key={index} className="focus-area">
                        <h4>{area.topic}</h4>
                        <p>{area.summary}</p>
                        <div className="key-points">
                          <h5>Key Points</h5>
                          <ul>
                            {area.key_points.map((point, idx) => (
                              <li key={idx}>{point}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {activeTab === 'sources' && (
                <div className="sources-panel">
                  <h2>Sources</h2>
                  {renderSources()}
                </div>
              )}
              
              {activeTab === 'graph' && graphData && (
                <div className="graph-panel">
                  <h2>Knowledge Graph</h2>
                  <KnowledgeGraph 
                    graphData={graphData} 
                    height={600}
                  />
                </div>
              )}
            </div>
          </>
        )}
        
        {!researchResults && !loading && !error && (
          <div className="empty-state">
            <h2>Research Assistant</h2>
            <p>Enter a topic or question to start researching.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResearchInterface;