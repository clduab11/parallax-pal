import React, { useState } from 'react';
import '../styles/FollowUpPrompt.css';

interface FollowUpPromptProps {
  questions?: string[];
  onSelectQuestion?: (question: string) => void;
  onCustomQuestion?: (question: string) => void;
  isLoading?: boolean;
  // Legacy props for backward compatibility
  onYes?: () => void;
  onNo?: () => void;
  isVisible?: boolean;
}

const FollowUpPrompt: React.FC<FollowUpPromptProps> = ({
  questions = [],
  onSelectQuestion,
  onCustomQuestion,
  isLoading = false,
  // Legacy props
  onYes,
  onNo,
  isVisible = true
}) => {
  const [customInput, setCustomInput] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);

  // Legacy mode for backward compatibility
  const isLegacyMode = onYes && onNo;

  const handleCustomSubmit = () => {
    if (customInput.trim() && onCustomQuestion) {
      onCustomQuestion(customInput.trim());
      setCustomInput('');
      setShowCustomInput(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleCustomSubmit();
    }
  };

  if (!isVisible) return null;

  // Legacy mode rendering
  if (isLegacyMode) {
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
  }

  // New ADK mode rendering
  return (
    <div className="followup-prompt">
      <div className="followup-header">
        <h3>Continue Your Research</h3>
        <p>Explore these follow-up questions or ask your own:</p>
      </div>

      {isLoading ? (
        <div className="followup-loading">
          <div className="loading-spinner"></div>
          <p>Generating follow-up questions...</p>
        </div>
      ) : (
        <>
          {questions.length > 0 && (
            <div className="followup-questions">
              {questions.map((question, index) => (
                <button
                  key={index}
                  className="followup-question-btn"
                  onClick={() => onSelectQuestion?.(question)}
                >
                  <span className="question-icon">?</span>
                  {question}
                </button>
              ))}
            </div>
          )}

          <div className="followup-custom">
            {!showCustomInput ? (
              <button
                className="custom-question-btn"
                onClick={() => setShowCustomInput(true)}
              >
                <span className="plus-icon">+</span>
                Ask your own question
              </button>
            ) : (
              <div className="custom-input-container">
                <textarea
                  value={customInput}
                  onChange={(e) => setCustomInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="What would you like to explore next?"
                  className="custom-question-input"
                  rows={3}
                  autoFocus
                />
                <div className="custom-input-actions">
                  <button
                    onClick={handleCustomSubmit}
                    disabled={!customInput.trim()}
                    className="submit-custom-btn"
                  >
                    Ask Question
                  </button>
                  <button
                    onClick={() => {
                      setShowCustomInput(false);
                      setCustomInput('');
                    }}
                    className="cancel-custom-btn"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default FollowUpPrompt;