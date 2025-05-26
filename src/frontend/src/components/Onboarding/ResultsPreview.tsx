import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { FileText, Download, Share2, Eye, BookOpen, Network } from 'lucide-react';

const ResultsPreview: React.FC = () => {
  const [activeTab, setActiveTab] = useState('summary');
  
  const tabs = [
    { id: 'summary', label: 'Summary', icon: <FileText className="w-4 h-4" /> },
    { id: 'sources', label: 'Sources', icon: <BookOpen className="w-4 h-4" /> },
    { id: 'graph', label: 'Graph', icon: <Network className="w-4 h-4" /> }
  ];
  
  const mockSources = [
    { title: 'Nature: Quantum Computing Breakthrough', reliability: 0.95, domain: 'nature.com' },
    { title: 'MIT News: New Quantum Algorithm', reliability: 0.92, domain: 'mit.edu' },
    { title: 'arXiv: Quantum Error Correction', reliability: 0.88, domain: 'arxiv.org' }
  ];
  
  const mockFindings = [
    'Quantum error correction rates improved by 50% using new topological codes',
    'Room-temperature quantum computers now feasible with photonic qubits',
    'Quantum supremacy demonstrated for optimization problems'
  ];
  
  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Tab Navigation */}
      <div className="flex gap-2 mb-4 justify-center">
        {tabs.map((tab) => (
          <motion.button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg transition-all
              ${activeTab === tab.id 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }
            `}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {tab.icon}
            <span className="text-sm font-medium">{tab.label}</span>
          </motion.button>
        ))}
      </div>
      
      {/* Content Area */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="bg-gray-700 rounded-xl p-6 min-h-[300px]"
      >
        {activeTab === 'summary' && (
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Research Summary</h3>
            <div className="space-y-4">
              <p className="text-gray-300 leading-relaxed">
                Recent breakthroughs in quantum computing have achieved significant milestones 
                in error correction and practical applications. Researchers have demonstrated 
                room-temperature quantum operations using photonic qubits, marking a major 
                advancement toward accessible quantum computing.
              </p>
              
              <div>
                <h4 className="text-white font-medium mb-2">Key Findings:</h4>
                <ul className="space-y-2">
                  {mockFindings.map((finding, index) => (
                    <motion.li
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-start gap-2 text-gray-300"
                    >
                      <span className="text-purple-400 mt-1">•</span>
                      <span className="text-sm">{finding}</span>
                    </motion.li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'sources' && (
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Verified Sources</h3>
            <div className="space-y-3">
              {mockSources.map((source, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-gray-800 rounded-lg p-4"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="text-white font-medium mb-1">{source.title}</h4>
                      <p className="text-gray-400 text-sm">{source.domain}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-400">Reliability</div>
                      <div className="text-lg font-semibold text-green-400">
                        {(source.reliability * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                  <div className="mt-2 h-2 bg-gray-600 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-green-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${source.reliability * 100}%` }}
                      transition={{ duration: 0.5, delay: 0.2 + index * 0.1 }}
                    />
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}
        
        {activeTab === 'graph' && (
          <div className="relative h-[300px] flex items-center justify-center">
            {/* Mock Knowledge Graph */}
            <svg className="w-full h-full">
              {/* Central Node */}
              <motion.circle
                cx="50%"
                cy="50%"
                r="40"
                fill="#9333ea"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring" }}
              />
              <text x="50%" y="50%" textAnchor="middle" fill="white" fontSize="12" dy=".3em">
                Quantum Computing
              </text>
              
              {/* Connected Nodes */}
              {[
                { x: "20%", y: "30%", label: "Error Correction", delay: 0.1 },
                { x: "80%", y: "30%", label: "Photonic Qubits", delay: 0.2 },
                { x: "20%", y: "70%", label: "Algorithms", delay: 0.3 },
                { x: "80%", y: "70%", label: "Applications", delay: 0.4 }
              ].map((node, index) => (
                <g key={index}>
                  <motion.line
                    x1="50%"
                    y1="50%"
                    x2={node.x}
                    y2={node.y}
                    stroke="#6b7280"
                    strokeWidth="2"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{ duration: 0.5, delay: node.delay }}
                  />
                  <motion.circle
                    cx={node.x}
                    cy={node.y}
                    r="30"
                    fill="#1f2937"
                    stroke="#6b7280"
                    strokeWidth="2"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: node.delay + 0.2, type: "spring" }}
                  />
                  <motion.text
                    x={node.x}
                    y={node.y}
                    textAnchor="middle"
                    fill="white"
                    fontSize="10"
                    dy=".3em"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: node.delay + 0.3 }}
                  >
                    {node.label}
                  </motion.text>
                </g>
              ))}
            </svg>
            
            <motion.div
              className="absolute bottom-4 right-4 text-gray-400 text-sm"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1 }}
            >
              Interactive knowledge graph
            </motion.div>
          </div>
        )}
      </motion.div>
      
      {/* Export Options */}
      <motion.div
        className="mt-4 flex justify-center gap-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors"
        >
          <Download className="w-4 h-4" />
          <span className="text-sm">Export</span>
        </motion.button>
        
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors"
        >
          <Share2 className="w-4 h-4" />
          <span className="text-sm">Share</span>
        </motion.button>
        
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors"
        >
          <Eye className="w-4 h-4" />
          <span className="text-sm">Preview</span>
        </motion.button>
      </motion.div>
    </div>
  );
};

export default ResultsPreview;