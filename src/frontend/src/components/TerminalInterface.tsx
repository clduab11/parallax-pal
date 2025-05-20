import React, { useState, useEffect, useRef, FormEvent, ChangeEvent } from 'react';
import FollowUpPrompt from './FollowUpPrompt';
import io from 'socket.io-client';
import type { SocketClient } from '../types/socket';
import {
  TerminalOutput,
  TerminalProps,
  ResearchQueryData,
  ResearchUpdateData,
  WebResult,
  AIAnalysis
} from '../types/terminal';

const BANNER_ART = `
██████╗  █████╗ ██████╗  █████╗ ██╗     ██╗      █████╗ ██╗  ██╗
██╔══██╗██╔══██╗██╔══██╗██╔══██╗██║     ██║     ██╔══██╗╚██╗██╔╝
██████╔╝███████║██████╔╝███████║██║     ██║     ███████║ ╚███╔╝ 
██╔═══╝ ██╔══██║██╔══██╗██╔══██║██║     ██║     ██╔══██║ ██╔██╗ 
██║     ██║  ██║██║  ██║██║  ██║███████╗███████╗██║  ██║██╔╝ ██╗
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝
██████╗  █████╗ ██╗     
██╔══██╗██╔══██╗██║     
██████╔╝███████║██║     
██╔═══╝ ██╔══██║██║     
██║     ██║  ██║███████╗
╚═╝     ╚═╝  ╚═╝╚══════╝`;

const TerminalInterface: React.FC<TerminalProps> = ({ subscription, onModeChange }) => {
  const [input, setInput] = useState<string>('');
  const [outputs, setOutputs] = useState<TerminalOutput[]>([]);
  const [socket, setSocket] = useState<SocketClient | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [mode, setMode] = useState<'web' | 'ollama'>('web');
  const [showFollowUp, setShowFollowUp] = useState<boolean>(false);
  const outputContainerRef = useRef<HTMLDivElement>(null);

  // Initialize with banner and welcome message
  useEffect(() => {
    const timestamp = new Date().toISOString();
    setOutputs([
      {
        id: Date.now(),
        type: 'system',
        text: BANNER_ART,
        timestamp
      },
      {
        id: Date.now() + 1,
        type: 'system',
        text: `PARALLAX ANALYTICS TERMINAL [Ver. 3.0.0]
INITIALIZING MULTI-MODEL RESEARCH INTERFACE...
LOADING USER PROFILE...
ACCESS LEVEL: ${subscription.tier.toUpperCase()}
${subscription.tier === 'premium' ? '\nOLLAMA GPU ACCELERATION: AVAILABLE' : ''}

STATUS: ALL SYSTEMS NOMINAL

Type 'help' for available commands.`,
        timestamp
      }
    ]);
  }, [subscription.tier]);

  // Enhanced WebSocket connection with error handling and reconnection
  useEffect(() => {
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const baseReconnectDelay = 2000; // Start with 2 seconds
    let reconnectTimer: NodeJS.Timeout | null = null;
    
    // Get any stored auth token
    const token = localStorage.getItem('auth_token') || '';
    
    // Create socket with connection options
    const socketUrl = process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:8000/ws';
    const connectionOptions = {
      reconnectionAttempts: maxReconnectAttempts,
      reconnectionDelay: baseReconnectDelay,
      reconnectionDelayMax: 10000, // 10 seconds max delay
      timeout: 10000, // 10 second connection timeout
      query: token ? { token } : {} // Include auth token if available
    };
    
    const newSocket = io(socketUrl, connectionOptions);
    
    // Connection established
    newSocket.on('connect', () => {
      reconnectAttempts = 0; // Reset reconnect counter on successful connection
      addOutput('system', '[CONNECTION ESTABLISHED]');
      
      // Send initial ping to verify connection
      newSocket.emit('ping', { timestamp: new Date().toISOString() });
    });
    
    // Connection failed
    newSocket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      
      if (reconnectAttempts === 0) {
        // Only show error on first attempt to avoid spamming
        addOutput('error', `[CONNECTION ERROR: ${error.message}]`);
      }
      
      reconnectAttempts++;
      
      if (reconnectAttempts > maxReconnectAttempts) {
        addOutput('error', '[WEBSOCKET CONNECTION FAILED] Please refresh the page to retry');
      } else {
        addOutput('system', `[RECONNECTING...] Attempt ${reconnectAttempts}/${maxReconnectAttempts}`);
      }
    });
    
    // Authentication status update
    newSocket.on('auth_status', (data: { authenticated: boolean, username?: string }) => {
      if (data.authenticated) {
        addOutput('system', `[AUTHENTICATED as ${data.username}]`);
      }
    });

    // Research updates (main event)
    newSocket.on('research_update', (data: ResearchUpdateData) => {
      if (data.type === 'error') {
        // Handle error updates
        addOutput('error', data.message);
        
        // Also end processing state if error occurs
        setIsProcessing(false);
      } else if (data.webResults || data.aiAnalyses) {
        // Handle results with web results or AI analyses
        addOutput('web-result', data.message, data.webResults, data.aiAnalyses);
      } else {
        // Handle regular updates
        addOutput('output', data.message);
      }
      
      // End processing state if this is a final result
      if (data.type === 'result') {
        setIsProcessing(false);
        setShowFollowUp(true);
      }
    });
    
    // Error event
    newSocket.on('error', (data: { message: string }) => {
      addOutput('error', `[SERVER ERROR] ${data.message}`);
    });
    
    // Keep-alive response
    newSocket.on('pong', () => {
      // Silent pong response - just keeps connection alive
    });

    // Connection closed
    newSocket.on('disconnect', (reason) => {
      addOutput('system', `[CONNECTION LOST: ${reason}]`);
      
      // Attempt to reconnect if not intentionally closed
      if (reason !== 'io client disconnect') {
        // Set up automatic reconnection with exponential backoff
        const reconnectDelay = Math.min(
          baseReconnectDelay * Math.pow(1.5, reconnectAttempts),
          10000 // Max 10 seconds
        );
        
        if (reconnectAttempts < maxReconnectAttempts) {
          addOutput('system', `[RECONNECTING IN ${reconnectDelay/1000}s...]`);
          
          reconnectTimer = setTimeout(() => {
            newSocket.connect();
          }, reconnectDelay);
        }
      }
    });

    // Store socket reference
    setSocket(newSocket as SocketClient);

    // Setup periodic ping to keep connection alive
    const pingInterval = setInterval(() => {
      if (newSocket.connected) {
        newSocket.emit('ping', { timestamp: new Date().toISOString() });
      }
    }, 30000); // Every 30 seconds

    // Cleanup on component unmount
    return () => {
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      clearInterval(pingInterval);
      newSocket.disconnect();
    };
  }, []);

  const addOutput = (
    type: TerminalOutput['type'],
    text: string,
    webResults?: WebResult[],
    aiAnalyses?: AIAnalysis[]
  ): void => {
    const timestamp = new Date().toISOString();
    setOutputs(prev => [...prev, { 
      id: Date.now(), 
      type,
      text,
      timestamp,
      webResults,
      aiAnalyses
    }]);
  };

  const handleModeToggle = (): void => {
    if (subscription.tier !== 'premium') {
      addOutput('error', '[ACCESS DENIED] Ollama interface requires PREMIUM clearance.');
      return;
    }
    const newMode = mode === 'web' ? 'ollama' : 'web';
    setMode(newMode);
    onModeChange(newMode);
    addOutput('system', `[SYSTEM] Interface switched to ${newMode.toUpperCase()} mode`);
  };

  const renderWebResult = (result: WebResult) => (
    <div className="bg-terminal-gray-dark border border-terminal-green p-4 rounded my-2">
      <h3 className="text-terminal-amber font-bold">{result.title}</h3>
      <div className="text-terminal-green opacity-70 text-sm">{result.url}</div>
      <div className="my-2 text-terminal-green">{result.snippet}</div>
      <div className="text-terminal-green opacity-50 text-sm">Source: {result.source}</div>
    </div>
  );

  const renderAIAnalysis = (analysis: AIAnalysis) => (
    <div className="bg-terminal-gray-dark border border-terminal-green p-4 rounded my-2">
      <div className="flex justify-between items-center mb-2">
        <span className="text-terminal-amber font-bold">{analysis.model.toUpperCase()}</span>
        <span className="text-terminal-green opacity-70">
          Confidence: {(analysis.confidence * 100).toFixed(1)}%
        </span>
      </div>
      <div className="text-terminal-green whitespace-pre-wrap">{analysis.analysis}</div>
    </div>
  );

  const handleFollowUpYes = () => {
    setShowFollowUp(false);
    addOutput('system', '\nWhat would you like to explore further?');
  };

  const handleFollowUpNo = () => {
    setShowFollowUp(false);
    addOutput('system', '\nThank you for using Parallax Pal. Type "help" if you need anything else.');
  };

  // Clear follow-up when starting new query
  useEffect(() => setShowFollowUp(false), [isProcessing]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (!input.trim()) return;

    const timestamp = new Date().toISOString();
    addOutput('input', `> ${input}`);

    if (input.toLowerCase() === 'help') {
      addOutput('system', `Available commands:
> help     : Display this information
> clear    : Clear terminal display
> mode     : Toggle research interface [PREMIUM]
> status   : Display system status
> exit     : Terminate session

Research queries are processed by multiple AI models:
- OpenAI GPT-4
- Anthropic Claude
- Google Gemini
${subscription.tier === 'premium' ? '- Ollama (GPU Accelerated)' : ''}`);
      setInput('');
      return;
    }

    if (input.toLowerCase() === 'clear') {
      setOutputs([]);
      setInput('');
      return;
    }

    if (input.toLowerCase() === 'mode') {
      handleModeToggle();
      setInput('');
      return;
    }

    if (input.toLowerCase() === 'status') {
      addOutput('system', `PARALLAX ANALYTICS SYSTEM STATUS
------------------------
Version    : 3.0.0
Mode       : ${mode.toUpperCase()}
Access     : ${subscription.tier.toUpperCase()}
Connection : ${socket?.connected ? 'ACTIVE' : 'INACTIVE'}
Models     : OpenAI, Anthropic, Gemini${subscription.tier === 'premium' ? ', Ollama' : ''}
Processing : ${isProcessing ? 'ACTIVE' : 'IDLE'}`);
      setInput('');
      return;
    }

    if (input.toLowerCase() === 'exit') {
      addOutput('system', 'TERMINATING SESSION...\n\nGoodbye.');
      setTimeout(() => window.close(), 1000);
      return;
    }

    setIsProcessing(true);

    if (socket) {
      try {
        // Check socket connection first
        if (!socket.connected) {
          addOutput('error', '[ERROR] WebSocket not connected. Attempting to reconnect...');
          socket.connect();
          
          // Give it a moment to connect
          setTimeout(() => {
            if (socket.connected) {
              // Now connected, try sending again
              const queryData: ResearchQueryData = {
                query: input,
                mode,
                useOllama: mode === 'ollama' || (subscription.tier === 'premium' && mode === 'web')
              };
              
              try {
                socket.emit('research_query', { 
                  event: 'research_query',
                  data: queryData
                });
              } catch (retryError) {
                console.error('Error sending query after reconnect:', retryError);
                addOutput('error', '[ERROR] Failed to send query. Please try again later.');
                setIsProcessing(false);
              }
            } else {
              // Still not connected
              addOutput('error', '[ERROR] Could not establish connection. Please refresh the page.');
              setIsProcessing(false);
            }
          }, 1000);
          
        } else {
          // Socket is connected, proceed normally
          const queryData: ResearchQueryData = {
            query: input,
            mode,
            useOllama: mode === 'ollama' || (subscription.tier === 'premium' && mode === 'web')
          };
          
          socket.emit('research_query', { 
            event: 'research_query',
            data: queryData
          });
          
          // Start tracking timeout in case server doesn't respond
          const timeoutTimer = setTimeout(() => {
            if (isProcessing) {
              addOutput('error', '[ERROR] Server did not respond in time. Your query may still be processing.');
            }
          }, 30000); // 30 second timeout
          
          // Clean up timeout when component unmounts or on next query
          return () => clearTimeout(timeoutTimer);
        }
      } catch (error) {
        console.error('Error sending research query:', error);
        addOutput('error', `[ERROR] Failed to send query: ${error instanceof Error ? error.message : 'Unknown error'}`);
        setIsProcessing(false);
      }
    } else {
      addOutput('error', '[ERROR] Research interface offline');
      setIsProcessing(false);
    }

    setInput('');
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>): void => {
    setInput(e.target.value);
  };

  // Auto-scroll to bottom when new output is added
  useEffect(() => {
    if (outputContainerRef.current) {
      outputContainerRef.current.scrollTop = outputContainerRef.current.scrollHeight;
    }
  }, [outputs]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex justify-between items-center p-2 border-b border-terminal-green">
        <span className="text-terminal-green">
          INTERFACE: {mode.toUpperCase()}
          {subscription.tier === 'premium' && (
            <span className="ml-2 px-2 py-1 bg-terminal-green text-terminal-black text-xs rounded">
              PREMIUM
            </span>
          )}
        </span>
        <button
          className={`px-4 py-1 border border-terminal-green rounded
            ${subscription.tier === 'premium' 
              ? 'hover:bg-terminal-green hover:text-terminal-black transition-colors duration-200' 
              : 'opacity-50 cursor-not-allowed'}`}
          onClick={handleModeToggle}
          disabled={subscription.tier !== 'premium'}
        >
          SWITCH INTERFACE
        </button>
      </div>

      <div 
        ref={outputContainerRef}
        className="flex-1 overflow-y-auto p-4 font-mono text-sm"
      >
        {outputs.map((output: TerminalOutput) => (
          <div 
            key={output.id} 
            className={`mb-2 ${
              output.type === 'error' ? 'text-red-500' :
              output.type === 'system' ? 'text-terminal-amber' :
              output.type === 'input' ? 'text-terminal-green font-bold' :
              'text-terminal-green'
            }`}
          >
            <span className="text-terminal-green opacity-50">
              [{new Date(output.timestamp).toLocaleTimeString()}]
            </span>
            <pre className="whitespace-pre-wrap font-mono mt-1">{output.text}</pre>
            {output.webResults && output.webResults.map((result, idx) => (
              <div key={idx}>{renderWebResult(result)}</div>
            ))}
            {output.aiAnalyses && output.aiAnalyses.map((analysis, idx) => (
              <div key={idx}>{renderAIAnalysis(analysis)}</div>
            ))}
          </div>
        ))}
        {isProcessing && (
          <div className="text-terminal-amber animate-pulse">
            PROCESSING QUERY ACROSS MULTIPLE MODELS...
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="p-2 border-t border-terminal-green">
        <div className="flex items-center">
          <span className="text-terminal-green mr-2">&gt;</span>
          <input 
            type="text"
            value={input}
            onChange={handleInputChange}
            className="terminal-input flex-1"
            placeholder={`Enter query (${mode.toUpperCase()} MODE)...`}
            disabled={isProcessing}
          />
        </div>

        <FollowUpPrompt
          isVisible={showFollowUp}
          onYes={handleFollowUpYes}
          onNo={handleFollowUpNo}
        />
      </form>
    </div>
  );
};

export default TerminalInterface;