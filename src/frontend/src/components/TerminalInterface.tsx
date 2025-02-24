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

  // WebSocket connection
  useEffect(() => {
    const newSocket = io(process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:8000/ws');
    
    newSocket.on('connect', () => {
      addOutput('system', '[CONNECTION ESTABLISHED]');
    });

    newSocket.on('research_update', (data: ResearchUpdateData) => {
      if (data.type === 'error') {
        addOutput('error', data.message);
      } else if (data.webResults || data.aiAnalyses) {
        addOutput('web-result', data.message, data.webResults, data.aiAnalyses);
      } else {
        addOutput('output', data.message);
      }
      
      if (data.type === 'result') {
        setIsProcessing(false);
        setShowFollowUp(true);
      }
    });

    newSocket.on('disconnect', () => {
      addOutput('system', '[CONNECTION LOST]');
    });

    setSocket(newSocket as SocketClient);

    return () => {
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
      const queryData: ResearchQueryData = {
        query: input,
        mode,
        useOllama: mode === 'ollama' || (subscription.tier === 'premium' && mode === 'web')
      };
      socket.emit('research_query', queryData);
    } else {
      addOutput('error', '[ERROR] Research interface offline');
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