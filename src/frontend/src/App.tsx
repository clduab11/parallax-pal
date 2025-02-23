import React, { useState } from 'react';
import TerminalInterface from './components/TerminalInterface';
import GPUStatus from './components/GPUStatus';
import { ResearchMode, UserSubscription } from './types/terminal';

const App: React.FC = () => {
  // Mock subscription - in production, this would come from your auth context
  const [subscription] = useState<UserSubscription>({
    tier: 'premium',
    features: ['continuous-research', 'ollama-access']
  });

  const handleModeChange = (mode: ResearchMode): void => {
    console.log(`Mode changed to: ${mode}`);
    // In production, you might want to persist this preference
  };

  return (
    <div className="min-h-screen bg-terminal-black p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <div className="terminal-window">
            <div className="terminal-header">
              <div className="terminal-dot terminal-dot-red"></div>
              <div className="terminal-dot terminal-dot-yellow"></div>
              <div className="terminal-dot terminal-dot-green"></div>
              <h1 className="text-xl ml-4">Parallax Pal Terminal</h1>
            </div>
            <div className="text-sm opacity-70">
              System ready • {new Date().toLocaleString()}
            </div>
          </div>
        </header>

        <main className="grid gap-6">
          {subscription.features.includes('ollama-access') && (
            <div className="terminal-window">
              <GPUStatus />
            </div>
          )}
          
          <div className="terminal-window h-[600px] overflow-hidden">
            <TerminalInterface 
              subscription={subscription}
              onModeChange={handleModeChange}
            />
          </div>
        </main>

        <footer className="mt-8 text-center text-terminal-green text-sm opacity-50">
          <p>Parallax Pal v1.0.0 • Running on React + FastAPI</p>
        </footer>
      </div>
    </div>
  );
};

export default App;
