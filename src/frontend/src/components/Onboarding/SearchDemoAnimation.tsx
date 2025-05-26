import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Mic, Send } from 'lucide-react';

const SearchDemoAnimation: React.FC = () => {
  const [query, setQuery] = useState('');
  const [showVoice, setShowVoice] = useState(false);
  const [isTyping, setIsTyping] = useState(true);
  
  const demoQuery = "What are the latest breakthroughs in quantum computing?";
  
  useEffect(() => {
    // Simulate typing
    if (isTyping && query.length < demoQuery.length) {
      const timeout = setTimeout(() => {
        setQuery(demoQuery.slice(0, query.length + 1));
      }, 100);
      return () => clearTimeout(timeout);
    } else if (query.length === demoQuery.length) {
      setIsTyping(false);
    }
  }, [query, isTyping]);
  
  useEffect(() => {
    // Reset animation after completion
    if (!isTyping) {
      const timeout = setTimeout(() => {
        setQuery('');
        setIsTyping(true);
        setShowVoice(false);
      }, 3000);
      return () => clearTimeout(timeout);
    }
  }, [isTyping]);
  
  const handleVoiceDemo = () => {
    setShowVoice(true);
    setQuery('');
    setTimeout(() => {
      setQuery("How does artificial intelligence work?");
      setIsTyping(false);
    }, 1500);
  };
  
  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Search Bar */}
      <motion.div
        className="relative bg-gray-700 rounded-xl shadow-lg overflow-hidden"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center p-4">
          <Search className="w-6 h-6 text-gray-400 mr-3" />
          
          <div className="flex-1 relative">
            <input
              type="text"
              value={query}
              readOnly
              placeholder="Ask anything..."
              className="w-full bg-transparent text-white placeholder-gray-400 outline-none text-lg"
            />
            
            {/* Cursor */}
            {isTyping && (
              <motion.div
                className="absolute top-0 bottom-0 w-0.5 bg-purple-500"
                style={{ left: `${query.length * 0.6}ch` }}
                animate={{ opacity: [1, 0] }}
                transition={{ duration: 0.5, repeat: Infinity }}
              />
            )}
          </div>
          
          {/* Action Buttons */}
          <div className="flex items-center gap-2 ml-4">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={handleVoiceDemo}
              className="p-2 text-gray-400 hover:text-white transition-colors"
            >
              <Mic className="w-5 h-5" />
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              animate={{ 
                backgroundColor: query.length > 0 ? '#9333ea' : '#374151'
              }}
              className="p-2 rounded-lg text-white transition-all"
            >
              <Send className="w-5 h-5" />
            </motion.button>
          </div>
        </div>
        
        {/* Voice Indicator */}
        <AnimatePresence>
          {showVoice && (
            <motion.div
              initial={{ height: 0 }}
              animate={{ height: 'auto' }}
              exit={{ height: 0 }}
              className="bg-purple-600 bg-opacity-20 border-t border-purple-600"
            >
              <div className="p-3 flex items-center justify-center gap-2">
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                  className="w-3 h-3 bg-purple-500 rounded-full"
                />
                <span className="text-purple-300 text-sm">Listening...</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
      
      {/* Suggestion Pills */}
      <motion.div
        className="mt-4 flex flex-wrap gap-2 justify-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        {[
          "Climate change solutions",
          "AI in healthcare",
          "Space exploration updates",
          "Renewable energy tech"
        ].map((suggestion, index) => (
          <motion.button
            key={suggestion}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.6 + index * 0.1 }}
            whileHover={{ scale: 1.05, backgroundColor: '#6b46c1' }}
            className="px-4 py-2 bg-gray-700 text-gray-300 rounded-full text-sm hover:text-white transition-all"
          >
            {suggestion}
          </motion.button>
        ))}
      </motion.div>
      
      {/* Mode Selector */}
      <motion.div
        className="mt-6 flex justify-center gap-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
      >
        {['Quick', 'Comprehensive', 'Continuous'].map((mode, index) => (
          <motion.div
            key={mode}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.2 + index * 0.1 }}
            className="text-center"
          >
            <div className={`
              w-16 h-16 rounded-lg flex items-center justify-center mb-2
              ${index === 1 ? 'bg-purple-600' : 'bg-gray-700'}
            `}>
              {index === 0 && '⚡'}
              {index === 1 && '🔍'}
              {index === 2 && '♾️'}
            </div>
            <span className="text-xs text-gray-400">{mode}</span>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
};

export default SearchDemoAnimation;