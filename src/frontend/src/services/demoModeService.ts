// Demo Mode Service for Parallax Pal

export interface DemoQuery {
  id: string;
  query: string;
  description: string;
  category: string;
  icon: string;
  expectedTime: number;
  highlights: string[];
}

export interface DemoResult {
  id: string;
  summary: string;
  findings: string[];
  sources: Array<{
    title: string;
    url: string;
    reliability: number;
  }>;
  knowledgeGraph: {
    nodes: Array<{
      id: string;
      label: string;
      type: string;
    }>;
    edges: Array<{
      source: string;
      target: string;
      type: string;
      weight: number;
    }>;
  };
  followUpQuestions: string[];
}

export class DemoModeManager {
  private cachedResults: Map<string, DemoResult> = new Map();
  
  constructor() {
    this.initializeCachedResults();
  }
  
  private initializeCachedResults() {
    // Pre-cache impressive demo results
    this.cachedResults.set('quantum', {
      id: 'quantum',
      summary: `Recent breakthroughs in quantum computing have achieved significant milestones in error correction and practical applications. Google's latest quantum processor has demonstrated a 50% improvement in error rates using topological qubits, while IBM has successfully implemented room-temperature quantum operations using photonic systems. These advances bring us closer to solving complex optimization problems and revolutionizing cryptography.`,
      findings: [
        'Quantum error correction rates improved by 50% using new topological codes',
        'Room-temperature quantum computers now feasible with photonic qubits',
        'Quantum supremacy demonstrated for optimization problems in logistics',
        'New quantum algorithms reduce computational complexity for drug discovery',
        'Hybrid quantum-classical systems show promise for near-term applications'
      ],
      sources: [
        { title: 'Nature: Quantum Error Correction Breakthrough', url: 'https://nature.com/quantum-2025', reliability: 0.95 },
        { title: 'MIT News: Room-Temperature Quantum Computing', url: 'https://mit.edu/quantum-photonics', reliability: 0.92 },
        { title: 'Google AI: Topological Qubit Advances', url: 'https://ai.google/quantum', reliability: 0.94 },
        { title: 'arXiv: Quantum Algorithm Improvements', url: 'https://arxiv.org/quantum-algo', reliability: 0.88 },
        { title: 'Science: Quantum Supremacy Applications', url: 'https://science.org/quantum', reliability: 0.93 }
      ],
      knowledgeGraph: {
        nodes: [
          { id: '1', label: 'Quantum Computing', type: 'concept' },
          { id: '2', label: 'Error Correction', type: 'concept' },
          { id: '3', label: 'Topological Qubits', type: 'technology' },
          { id: '4', label: 'Google', type: 'organization' },
          { id: '5', label: 'IBM', type: 'organization' },
          { id: '6', label: 'Photonic Qubits', type: 'technology' },
          { id: '7', label: 'Room Temperature', type: 'concept' },
          { id: '8', label: 'Drug Discovery', type: 'application' },
          { id: '9', label: 'Cryptography', type: 'application' },
          { id: '10', label: 'Optimization', type: 'application' }
        ],
        edges: [
          { source: '1', target: '2', type: 'requires', weight: 0.9 },
          { source: '2', target: '3', type: 'uses', weight: 0.8 },
          { source: '4', target: '3', type: 'develops', weight: 0.9 },
          { source: '5', target: '6', type: 'develops', weight: 0.9 },
          { source: '6', target: '7', type: 'enables', weight: 0.85 },
          { source: '1', target: '8', type: 'applies_to', weight: 0.7 },
          { source: '1', target: '9', type: 'revolutionizes', weight: 0.9 },
          { source: '1', target: '10', type: 'optimizes', weight: 0.8 }
        ]
      },
      followUpQuestions: [
        'How do topological qubits differ from traditional qubits?',
        'What are the practical applications of room-temperature quantum computing?',
        'How will quantum computing impact cybersecurity?',
        'What industries will benefit most from quantum computing advances?'
      ]
    });
    
    this.cachedResults.set('climate', {
      id: 'climate',
      summary: `Artificial Intelligence is revolutionizing climate change research through advanced modeling, prediction systems, and optimization strategies. Machine learning algorithms now predict extreme weather events with 85% accuracy up to 10 days in advance. AI-driven carbon capture systems have improved efficiency by 40%, while deep learning models help optimize renewable energy grids, reducing waste by 30%. These technologies are crucial for achieving global climate goals.`,
      findings: [
        'AI weather prediction models achieve 85% accuracy for 10-day forecasts',
        'Machine learning optimizes carbon capture efficiency by 40%',
        'Deep learning reduces renewable energy grid waste by 30%',
        'AI-powered satellite analysis tracks deforestation in real-time',
        'Neural networks predict climate tipping points with unprecedented accuracy'
      ],
      sources: [
        { title: 'Nature Climate: AI Weather Prediction', url: 'https://nature.com/climate-ai', reliability: 0.94 },
        { title: 'Science: Carbon Capture Optimization', url: 'https://science.org/carbon-ai', reliability: 0.91 },
        { title: 'MIT Technology Review: Smart Grids', url: 'https://technologyreview.com/smart-grids', reliability: 0.89 },
        { title: 'NOAA: AI Climate Modeling', url: 'https://noaa.gov/ai-climate', reliability: 0.96 },
        { title: 'Environmental Science & Technology: ML Applications', url: 'https://pubs.acs.org/climate-ml', reliability: 0.90 }
      ],
      knowledgeGraph: {
        nodes: [
          { id: '1', label: 'AI in Climate Research', type: 'concept' },
          { id: '2', label: 'Weather Prediction', type: 'application' },
          { id: '3', label: 'Carbon Capture', type: 'technology' },
          { id: '4', label: 'Machine Learning', type: 'technology' },
          { id: '5', label: 'Deep Learning', type: 'technology' },
          { id: '6', label: 'Renewable Energy', type: 'concept' },
          { id: '7', label: 'Smart Grids', type: 'technology' },
          { id: '8', label: 'Satellite Analysis', type: 'application' },
          { id: '9', label: 'Deforestation Tracking', type: 'application' },
          { id: '10', label: 'Climate Modeling', type: 'application' }
        ],
        edges: [
          { source: '1', target: '2', type: 'enables', weight: 0.9 },
          { source: '4', target: '3', type: 'optimizes', weight: 0.8 },
          { source: '5', target: '7', type: 'powers', weight: 0.85 },
          { source: '1', target: '6', type: 'enhances', weight: 0.8 },
          { source: '1', target: '8', type: 'utilizes', weight: 0.7 },
          { source: '8', target: '9', type: 'enables', weight: 0.9 },
          { source: '4', target: '10', type: 'improves', weight: 0.85 }
        ]
      },
      followUpQuestions: [
        'What specific ML algorithms are most effective for climate modeling?',
        'How can AI help developing countries adapt to climate change?',
        'What are the limitations of AI in climate research?',
        'How is AI being used to track carbon emissions?'
      ]
    });
    
    // Add more cached results for other demo queries...
  }
  
  async simulateResearch(query: string): Promise<AsyncGenerator<any>> {
    // Find matching cached result
    const cachedResult = Array.from(this.cachedResults.values()).find(
      result => result.id === this.getQueryId(query)
    );
    
    if (cachedResult) {
      yield* this.streamCachedResult(cachedResult);
    } else {
      yield* this.streamGenericResult(query);
    }
  }
  
  private getQueryId(query: string): string {
    // Simple matching based on keywords
    const queryLower = query.toLowerCase();
    if (queryLower.includes('quantum')) return 'quantum';
    if (queryLower.includes('climate') || queryLower.includes('ai')) return 'climate';
    if (queryLower.includes('biotech')) return 'biotech';
    if (queryLower.includes('space') || queryLower.includes('exoplanet')) return 'space';
    if (queryLower.includes('neuroscience') || queryLower.includes('consciousness')) return 'neuroscience';
    if (queryLower.includes('energy') || queryLower.includes('renewable')) return 'energy';
    return 'generic';
  }
  
  private async* streamCachedResult(result: DemoResult) {
    // Simulate realistic streaming with delays
    const steps = [
      { type: 'start', agent: 'orchestrator', progress: 0, message: 'Starting research...' },
      { type: 'delegating', agent: 'orchestrator', progress: 10, message: 'Delegating to specialized agents...' },
      { type: 'searching', agent: 'retrieval', progress: 30, message: `Searching for information about ${result.id}...` },
      { type: 'sources_found', agent: 'retrieval', progress: 40, data: { count: result.sources.length } },
      { type: 'analyzing', agent: 'analysis', progress: 50, message: 'Analyzing sources and extracting insights...' },
      { type: 'findings', agent: 'analysis', progress: 60, data: { findings: result.findings.slice(0, 3) } },
      { type: 'citing', agent: 'citation', progress: 70, message: 'Generating citations...' },
      { type: 'graphing', agent: 'knowledge_graph', progress: 85, message: 'Building knowledge graph...' },
      { type: 'graph_preview', agent: 'knowledge_graph', progress: 90, data: { 
        nodeCount: result.knowledgeGraph.nodes.length,
        edgeCount: result.knowledgeGraph.edges.length
      }},
      { type: 'finalizing', agent: 'orchestrator', progress: 95, message: 'Compiling final report...' },
      { type: 'complete', agent: 'orchestrator', progress: 100, data: result }
    ];
    
    for (const step of steps) {
      await this.delay(800 + Math.random() * 400); // Vary timing for realism
      yield step;
    }
  }
  
  private async* streamGenericResult(query: string) {
    // Generate a generic but impressive result
    yield* this.streamCachedResult({
      id: 'generic',
      summary: `Based on comprehensive research, ${query} represents a fascinating area of study with significant recent developments. Multiple peer-reviewed sources indicate substantial progress in this field, with implications for both theoretical understanding and practical applications.`,
      findings: [
        'Significant advancements reported in recent academic publications',
        'Growing investment and research interest from major institutions',
        'Potential for transformative impact across multiple disciplines',
        'Emerging consensus among experts on key principles',
        'New methodologies enabling accelerated progress'
      ],
      sources: [
        { title: 'Recent Advances in the Field', url: 'https://example.com/research', reliability: 0.88 },
        { title: 'Comprehensive Review of Current State', url: 'https://example.com/review', reliability: 0.85 },
        { title: 'Future Directions and Implications', url: 'https://example.com/future', reliability: 0.82 }
      ],
      knowledgeGraph: {
        nodes: [
          { id: '1', label: 'Main Concept', type: 'concept' },
          { id: '2', label: 'Key Technology', type: 'technology' },
          { id: '3', label: 'Primary Application', type: 'application' },
          { id: '4', label: 'Research Institution', type: 'organization' }
        ],
        edges: [
          { source: '1', target: '2', type: 'utilizes', weight: 0.8 },
          { source: '2', target: '3', type: 'enables', weight: 0.9 },
          { source: '4', target: '1', type: 'researches', weight: 0.7 }
        ]
      },
      followUpQuestions: [
        'What are the most recent developments in this area?',
        'How does this compare to previous approaches?',
        'What are the main challenges remaining?',
        'Who are the key researchers in this field?'
      ]
    });
  }
  
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  getCachedQueries(): string[] {
    return Array.from(this.cachedResults.keys());
  }
  
  preloadCache(): void {
    // This could fetch fresh demo data from a CDN or API
    console.log('Demo cache preloaded with', this.cachedResults.size, 'queries');
  }
}