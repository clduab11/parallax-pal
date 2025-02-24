import React from 'react';

interface FollowUpPromptProps {
  onYes: () => void;
  onNo: () => void;
  isVisible: boolean;
}

const FollowUpPrompt: React.FC<FollowUpPromptProps> = ({ onYes, onNo, isVisible }) => {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-terminal-black border-2 border-terminal-green p-6 rounded-lg shadow-lg max-w-md w-full mx-4">
        <h3 className="text-terminal-amber text-lg font-bold mb-4">
          Would you like to look into anything else?
        </h3>
        <div className="flex justify-end gap-4">
          <button
            onClick={onYes}
            className="px-4 py-2 bg-terminal-green text-terminal-black rounded hover:bg-terminal-green-dark transition-colors duration-200"
          >
            Yes
          </button>
          <button
            onClick={onNo}
            className="px-4 py-2 border border-terminal-green text-terminal-green rounded hover:bg-terminal-green hover:text-terminal-black transition-colors duration-200"
          >
            No
          </button>
        </div>
      </div>
    </div>
  );
};

export default FollowUpPrompt;