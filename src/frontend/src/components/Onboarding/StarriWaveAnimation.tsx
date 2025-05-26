import React from 'react';
import { motion } from 'framer-motion';

const StarriWaveAnimation: React.FC = () => {
  return (
    <div className="relative w-64 h-64 mx-auto">
      {/* Starri Character */}
      <motion.div
        className="absolute inset-0 flex items-center justify-center"
        animate={{
          y: [0, -10, 0],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      >
        <div className="relative">
          {/* Body */}
          <motion.div
            className="w-32 h-32 bg-gradient-to-b from-purple-500 to-purple-700 rounded-full shadow-lg"
            animate={{
              scale: [1, 1.05, 1],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
          
          {/* Eyes */}
          <div className="absolute top-8 left-6 w-4 h-4 bg-white rounded-full">
            <motion.div
              className="w-2 h-2 bg-black rounded-full mt-1 ml-1"
              animate={{
                x: [0, 2, 0, -2, 0],
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            />
          </div>
          <div className="absolute top-8 right-6 w-4 h-4 bg-white rounded-full">
            <motion.div
              className="w-2 h-2 bg-black rounded-full mt-1 ml-1"
              animate={{
                x: [0, 2, 0, -2, 0],
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            />
          </div>
          
          {/* Smile */}
          <motion.div
            className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
            animate={{
              scaleX: [1, 1.2, 1],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            <svg width="40" height="20" viewBox="0 0 40 20">
              <path
                d="M5 10 Q20 20 35 10"
                fill="none"
                stroke="white"
                strokeWidth="3"
                strokeLinecap="round"
              />
            </svg>
          </motion.div>
          
          {/* Arms waving */}
          <motion.div
            className="absolute top-12 -left-8"
            animate={{
              rotate: [-20, 20, -20],
            }}
            transition={{
              duration: 1,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            <div className="w-16 h-4 bg-purple-600 rounded-full transform origin-right" />
          </motion.div>
          <motion.div
            className="absolute top-12 -right-8"
            animate={{
              rotate: [20, -20, 20],
            }}
            transition={{
              duration: 1,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            <div className="w-16 h-4 bg-purple-600 rounded-full transform origin-left" />
          </motion.div>
        </div>
      </motion.div>
      
      {/* Speech Bubble */}
      <motion.div
        className="absolute -top-16 left-1/2 transform -translate-x-1/2 bg-white text-gray-800 px-4 py-2 rounded-lg shadow-lg"
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.5, type: "spring" }}
      >
        <p className="text-sm font-medium">Hi! I'm Starri! 👋</p>
        <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 translate-y-full">
          <div className="w-0 h-0 border-l-8 border-r-8 border-t-8 border-transparent border-t-white" />
        </div>
      </motion.div>
      
      {/* Sparkles */}
      {[...Array(6)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-2 h-2 bg-yellow-400 rounded-full"
          style={{
            left: `${20 + i * 15}%`,
            top: `${10 + (i % 2) * 20}%`,
          }}
          animate={{
            opacity: [0, 1, 0],
            scale: [0, 1, 0],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            delay: i * 0.3,
            ease: "easeInOut"
          }}
        />
      ))}
    </div>
  );
};

export default StarriWaveAnimation;