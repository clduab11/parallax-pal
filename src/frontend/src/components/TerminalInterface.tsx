import React, { useState, useEffect, useRef, FormEvent, ChangeEvent } from 'react';
import io from 'socket.io-client';
import type { SocketClient } from '../types/socket';
import styles from '../styles/Terminal.module.css';
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
    <div className={styles.webResult}>
      <h3>{result.title}</h3>
      <div className={styles.url}>{result.url}</div>
      <div className={styles.snippet}>{result.snippet}</div>
      <div className={styles.source}>Source: {result.source}</div>
    </div>
  );

  const renderAIAnalysis = (analysis: AIAnalysis) => (
    <div className={styles.aiAnalysis}>
      <div className={styles.modelName}>
        {analysis.model.toUpperCase()}
        <span className={styles.confidence}>
          Confidence: {(analysis.confidence * 100).toFixed(1)}%
        </span>
      </div>
      <div className={styles.analysis}>{analysis.analysis}</div>
    </div>
  );

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
    <div className={styles.terminalContainer}>
      <div className={styles.terminalHeader}>
        <span>
          INTERFACE: {mode.toUpperCase()}
          {subscription.tier === 'premium' && (
            <span className={styles.premiumBadge}>PREMIUM</span>
          )}
        </span>
        <button
          className={`${styles.modeToggle} ${subscription.tier !== 'premium' ? styles.disabled : ''}`}
          onClick={handleModeToggle}
          disabled={subscription.tier !== 'premium'}
        >
          SWITCH INTERFACE
        </button>
      </div>

      <div 
        ref={outputContainerRef}
        className={styles.terminalOutput}
      >
        {outputs.map((output: TerminalOutput) => (
          <div 
            key={output.id} 
            className={`${styles.terminalLine} ${styles[output.type]}`}
          >
            <span className={styles.timestamp}>
              [{new Date(output.timestamp).toLocaleTimeString()}]
            </span>
            {output.text}
            {output.webResults && output.webResults.map((result, idx) => (
              <div key={idx}>{renderWebResult(result)}</div>
            ))}
            {output.aiAnalyses && output.aiAnalyses.map((analysis, idx) => (
              <div key={idx}>{renderAIAnalysis(analysis)}</div>
            ))}
          </div>
        ))}
        {isProcessing && (
          <div className={styles.processing}>PROCESSING QUERY ACROSS MULTIPLE MODELS...</div>
        )}
      </div>

      <form onSubmit={handleSubmit} className={styles.inputForm}>
        <span className={styles.prompt}>&gt;</span>
        <input 
          type="text"
          value={input}
          onChange={handleInputChange}
          className={styles.input}
          placeholder={`Enter query (${mode.toUpperCase()} MODE)...`}
          disabled={isProcessing}
        />
      </form>
    </div>
  );
};

export default TerminalInterface;