import React, { useState } from 'react';
import TerminalInterface from './components/TerminalInterface';
import GPUStatus from './components/GPUStatus';
import { ResearchMode, UserSubscription } from './types/terminal';
import './styles/global.css';

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
    <div className="app-container">
      {subscription.features.includes('ollama-access') && (
        <GPUStatus />
      )}
      <TerminalInterface 
        subscription={subscription}
        onModeChange={handleModeChange}
      />
    </div>
  );
};

export default App;
