import React, { useEffect, useState, useRef } from 'react';
import '../styles/AssistantCharacter.css';

export type AssistantEmotion = 
  | 'neutral' 
  | 'happy' 
  | 'sad' 
  | 'excited' 
  | 'confused' 
  | 'focused' 
  | 'surprised' 
  | 'thoughtful';

export type AssistantState = 
  | 'idle' 
  | 'thinking' 
  | 'presenting' 
  | 'error';

interface AssistantCharacterProps {
  /** Current emotional state of the assistant */
  emotion: AssistantEmotion;
  
  /** Current functional state of the assistant */
  state: AssistantState;
  
  /** Optional speech bubble text */
  speechBubble?: string;
  
  /** Optional click handler */
  onClick?: () => void;
  
  /** Whether to display the character (defaults to true) */
  visible?: boolean;
  
  /** Position on screen */
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  
  /** Size of the character */
  size?: 'small' | 'medium' | 'large';
}

/**
 * Animated assistant character component with emotion states
 */
const AssistantCharacter: React.FC<AssistantCharacterProps> = ({
  emotion = 'neutral',
  state = 'idle',
  speechBubble,
  onClick,
  visible = true,
  position = 'bottom-right',
  size = 'medium',
}) => {
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const [animationSpeed, setAnimationSpeed] = useState(500); // ms per frame
  const [showSpeechBubble, setShowSpeechBubble] = useState(false);
  const characterRef = useRef<HTMLDivElement>(null);
  const frameCount = 4; // Number of animation frames
  
  // Set animation speed based on state
  useEffect(() => {
    switch (state) {
      case 'thinking':
        setAnimationSpeed(300); // Faster for thinking
        break;
      case 'presenting':
        setAnimationSpeed(800); // Slower for presenting
        break;
      case 'error':
        setAnimationSpeed(400); // Medium for error
        break;
      default:
        setAnimationSpeed(500); // Default speed
    }
  }, [state]);
  
  // Handle animation frames
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentFrame(prev => (prev + 1) % frameCount);
    }, animationSpeed);
    
    return () => clearInterval(interval);
  }, [animationSpeed]);
  
  // Handle speech bubble visibility
  useEffect(() => {
    if (speechBubble) {
      setShowSpeechBubble(true);
      
      // Auto-hide speech bubble after 5 seconds
      const timeout = setTimeout(() => {
        setShowSpeechBubble(false);
      }, 5000);
      
      return () => clearTimeout(timeout);
    } else {
      setShowSpeechBubble(false);
    }
  }, [speechBubble]);
  
  // Generate SVG for the character based on emotion and animation frame
  const renderCharacterSVG = () => {
    // Base character
    const baseCharacter = (
      <g className="character-base">
        <circle cx="50" cy="50" r="45" fill="#4A86E8" />
        <circle cx="50" cy="50" r="40" fill="#7EA6F4" />
      </g>
    );
    
    // Eyes based on emotion
    const eyesMap: Record<AssistantEmotion, React.JSX.Element> = {
      neutral: (
        <g className="eyes neutral">
          <circle cx="35" cy="40" r="5" fill="#fff" />
          <circle cx="65" cy="40" r="5" fill="#fff" />
        </g>
      ),
      happy: (
        <g className="eyes happy">
          <path d="M30,40 Q35,30 40,40" stroke="#fff" strokeWidth="3" fill="none" />
          <path d="M60,40 Q65,30 70,40" stroke="#fff" strokeWidth="3" fill="none" />
        </g>
      ),
      sad: (
        <g className="eyes sad">
          <path d="M30,45 Q35,55 40,45" stroke="#fff" strokeWidth="3" fill="none" />
          <path d="M60,45 Q65,55 70,45" stroke="#fff" strokeWidth="3" fill="none" />
        </g>
      ),
      excited: (
        <g className="eyes excited">
          <circle cx="35" cy="40" r="6" fill="#fff" />
          <circle cx="65" cy="40" r="6" fill="#fff" />
          <path d="M32,32 L38,28" stroke="#fff" strokeWidth="2" />
          <path d="M62,32 L68,28" stroke="#fff" strokeWidth="2" />
        </g>
      ),
      confused: (
        <g className="eyes confused">
          <circle cx="35" cy="40" r="5" fill="#fff" />
          <circle cx="65" cy="40" r="5" fill="#fff" />
          <path d="M25,30 Q35,25 40,35" stroke="#fff" strokeWidth="2" fill="none" />
        </g>
      ),
      focused: (
        <g className="eyes focused">
          <ellipse cx="35" cy="40" rx="6" ry="4" fill="#fff" />
          <ellipse cx="65" cy="40" rx="6" ry="4" fill="#fff" />
        </g>
      ),
      surprised: (
        <g className="eyes surprised">
          <circle cx="35" cy="40" r="7" fill="#fff" />
          <circle cx="65" cy="40" r="7" fill="#fff" />
        </g>
      ),
      thoughtful: (
        <g className="eyes thoughtful">
          <path d="M30,40 Q35,35 40,40" stroke="#fff" strokeWidth="3" fill="none" />
          <path d="M60,40 Q65,35 70,40" stroke="#fff" strokeWidth="3" fill="none" />
        </g>
      )
    };
    
    // Mouth animations based on emotion and frame
    // We'll create an animation by having 4 frames per emotion
    const getMouth = () => {
      // Define keyframes for each emotion
      const mouthMap: Record<AssistantEmotion, React.JSX.Element[]> = {
        neutral: [
          <path key="n1" d="M40,70 Q50,75 60,70" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="n2" d="M40,70 Q50,76 60,70" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="n3" d="M40,70 Q50,75 60,70" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="n4" d="M40,70 Q50,74 60,70" stroke="#fff" strokeWidth="3" fill="none" />
        ],
        happy: [
          <path key="h1" d="M30,65 Q50,85 70,65" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="h2" d="M30,65 Q50,87 70,65" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="h3" d="M30,65 Q50,86 70,65" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="h4" d="M30,65 Q50,84 70,65" stroke="#fff" strokeWidth="3" fill="none" />
        ],
        sad: [
          <path key="s1" d="M35,75 Q50,65 65,75" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="s2" d="M35,75 Q50,64 65,75" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="s3" d="M35,75 Q50,63 65,75" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="s4" d="M35,75 Q50,65 65,75" stroke="#fff" strokeWidth="3" fill="none" />
        ],
        excited: [
          <path key="e1" d="M30,65 Q50,90 70,65" stroke="#fff" strokeWidth="4" fill="none" />,
          <path key="e2" d="M30,65 Q50,92 70,65" stroke="#fff" strokeWidth="4" fill="none" />,
          <path key="e3" d="M30,65 Q50,91 70,65" stroke="#fff" strokeWidth="4" fill="none" />,
          <path key="e4" d="M30,65 Q50,89 70,65" stroke="#fff" strokeWidth="4" fill="none" />
        ],
        confused: [
          <path key="c1" d="M40,70 Q50,75 65,68" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="c2" d="M40,70 Q50,76 65,68" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="c3" d="M40,70 Q50,74 65,68" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="c4" d="M40,70 Q50,75 65,68" stroke="#fff" strokeWidth="3" fill="none" />
        ],
        focused: [
          <path key="f1" d="M40,70 L60,70" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="f2" d="M40,71 L60,71" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="f3" d="M40,72 L60,72" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="f4" d="M40,71 L60,71" stroke="#fff" strokeWidth="3" fill="none" />
        ],
        surprised: [
          <circle key="sp1" cx="50" cy="70" r="10" stroke="#fff" strokeWidth="3" fill="none" />,
          <circle key="sp2" cx="50" cy="70" r="11" stroke="#fff" strokeWidth="3" fill="none" />,
          <circle key="sp3" cx="50" cy="70" r="10" stroke="#fff" strokeWidth="3" fill="none" />,
          <circle key="sp4" cx="50" cy="70" r="9" stroke="#fff" strokeWidth="3" fill="none" />
        ],
        thoughtful: [
          <path key="t1" d="M40,70 L60,70" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="t2" d="M40,70 L60,71" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="t3" d="M40,71 L60,70" stroke="#fff" strokeWidth="3" fill="none" />,
          <path key="t4" d="M40,70 L60,70" stroke="#fff" strokeWidth="3" fill="none" />
        ]
      };
      
      return mouthMap[emotion][currentFrame];
    };
    
    // Additional animation effects based on state
    const getStateEffects = () => {
      switch (state) {
        case 'thinking':
          return (
            <g className="thinking-animation">
              {/* Thinking bubbles */}
              <circle 
                cx={75 + (currentFrame * 3)} 
                cy={30 - (currentFrame * 5)} 
                r={3 + currentFrame} 
                fill="#fff" 
                opacity={0.7 - (currentFrame * 0.1)} 
              />
              <circle 
                cx={85 + (currentFrame * 4)} 
                cy={20 - (currentFrame * 3)} 
                r={2 + (currentFrame % 2)} 
                fill="#fff" 
                opacity={0.6 - (currentFrame * 0.1)} 
              />
            </g>
          );
        case 'presenting':
          return (
            <g className="presenting-animation">
              {/* Sparkles or highlights */}
              <path 
                d={`M${90 - (currentFrame * 2)},${20 + (currentFrame * 2)} l5,-5 l-5,-5 l-5,5 z`} 
                fill="#FFEB3B" 
                opacity={0.7 + (currentFrame * 0.1)} 
              />
              <path 
                d={`M${15 + (currentFrame * 2)},${30 - (currentFrame)} l4,-4 l-4,-4 l-4,4 z`} 
                fill="#FFEB3B" 
                opacity={0.8 - (currentFrame * 0.1)} 
              />
            </g>
          );
        case 'error':
          return (
            <g className="error-animation">
              {/* Error symbol */}
              <path 
                d={`M${95 - (currentFrame)},5 l5,5 l-5,5 l5,5 l-5,5 l-5,-5 l-5,5 l-5,-5 l5,-5 l-5,-5 l5,-5 l5,5 z`} 
                fill="#FF5252" 
                opacity={0.7 + (currentFrame * 0.1)} 
                transform={`rotate(${currentFrame * 5}, 90, 15)`}
              />
            </g>
          );
        default:
          return null;
      }
    };
    
    // Combine all elements
    return (
      <svg width="100" height="100" viewBox="0 0 100 100" aria-label={`Assistant character showing ${emotion} emotion in ${state} state`}>
        {baseCharacter}
        {eyesMap[emotion]}
        {getMouth()}
        {getStateEffects()}
      </svg>
    );
  };
  
  if (!visible) {
    return null;
  }
  
  return (
    <div 
      className={`assistant-character-container ${position} ${size} ${state}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
      ref={characterRef}
      aria-label={`Assistant character. State: ${state}, Emotion: ${emotion}`}
    >
      {/* Speech bubble */}
      {(speechBubble && showSpeechBubble) && (
        <div 
          className={`speech-bubble ${position.includes('right') ? 'left' : 'right'}`}
          aria-live="polite"
        >
          {speechBubble}
        </div>
      )}
      
      {/* Character SVG */}
      <div className={`character ${emotion} ${state} ${isHovered ? 'hovered' : ''}`}>
        {renderCharacterSVG()}
      </div>
    </div>
  );
};

export default AssistantCharacter;