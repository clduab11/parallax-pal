import React, { useEffect, useRef, useState, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: string;
  description?: string;
  confidence: number;
  size?: number;
  color?: string;
  importance?: number;
  frequency?: number;
  x?: number;
  y?: number;
}

interface KnowledgeGraphEdge {
  source: string;
  target: string;
  label: string;
  type: string;
  weight: number;
  confidence: number;
  strength?: number;
  width?: number;
  color?: string;
}

interface KnowledgeGraphData {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  main_topic: string;
  clusters?: Array<{
    id: string;
    name: string;
    nodes: string[];
    color: string;
  }>;
  metrics?: {
    node_count: number;
    edge_count: number;
    density: number;
    most_connected_nodes: Array<[string, number]>;
  };
}

interface EnhancedKnowledgeGraphProps {
  graphData: KnowledgeGraphData;
  height?: number;
  width?: number;
  onNodeSelect?: (node: KnowledgeGraphNode) => void;
  onEdgeSelect?: (edge: KnowledgeGraphEdge) => void;
  interactive?: boolean;
  showClusters?: boolean;
  showMetrics?: boolean;
  colorScheme?: 'default' | 'semantic' | 'confidence' | 'importance';
}

const EnhancedKnowledgeGraph: React.FC<EnhancedKnowledgeGraphProps> = ({
  graphData,
  height = 600,
  width,
  onNodeSelect,
  onEdgeSelect,
  interactive = true,
  showClusters = true,
  showMetrics = false,
  colorScheme = 'semantic'
}) => {
  const graphRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredNode, setHoveredNode] = useState<KnowledgeGraphNode | null>(null);
  const [selectedNode, setSelectedNode] = useState<KnowledgeGraphNode | null>(null);
  const [hoveredEdge, setHoveredEdge] = useState<KnowledgeGraphEdge | null>(null);
  const [highlightNodes, setHighlightNodes] = useState(new Set());
  const [highlightLinks, setHighlightLinks] = useState(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredTypes, setFilteredTypes] = useState<Set<string>>(new Set());
  const [showControls, setShowControls] = useState(true);
  const [graphDimensions, setGraphDimensions] = useState({ width: width || 800, height });

  // Color schemes
  const colorSchemes = {
    default: {
      concept: '#4CAF50',
      entity: '#2196F3',
      person: '#FF9800',
      organization: '#9C27B0',
      location: '#00BCD4',
      technology: '#F44336',
      default: '#607D8B'
    },
    semantic: {
      concept: '#66BB6A',
      entity: '#42A5F5',
      person: '#FFA726',
      organization: '#AB47BC',
      location: '#26C6DA',
      technology: '#EF5350',
      default: '#78909C'
    },
    confidence: (confidence: number) => {
      const alpha = Math.max(0.3, confidence);
      return `rgba(33, 150, 243, ${alpha})`;
    },
    importance: (importance: number) => {
      const hue = Math.min(120, importance * 120); // 0 = red, 120 = green
      return `hsl(${hue}, 70%, 50%)`;
    }
  };

  // Get node color based on color scheme
  const getNodeColor = useCallback((node: KnowledgeGraphNode) => {
    if (node.color) return node.color;
    
    switch (colorScheme) {
      case 'confidence':
        return colorSchemes.confidence(node.confidence);
      case 'importance':
        return colorSchemes.importance(node.importance || 0.5);
      case 'semantic':
        return colorSchemes.semantic[node.type as keyof typeof colorSchemes.semantic] || colorSchemes.semantic.default;
      default:
        return colorSchemes.default[node.type as keyof typeof colorSchemes.default] || colorSchemes.default.default;
    }
  }, [colorScheme]);

  // Transform and filter graph data
  const processedGraphData = React.useMemo(() => {
    let filteredNodes = graphData.nodes;
    let filteredEdges = graphData.edges;

    // Apply search filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filteredNodes = filteredNodes.filter(node => 
        node.label.toLowerCase().includes(searchLower) ||
        node.description?.toLowerCase().includes(searchLower)
      );
      
      const nodeIds = new Set(filteredNodes.map(n => n.id));
      filteredEdges = filteredEdges.filter(edge => 
        nodeIds.has(edge.source) && nodeIds.has(edge.target)
      );
    }

    // Apply type filter
    if (filteredTypes.size > 0) {
      filteredNodes = filteredNodes.filter(node => !filteredTypes.has(node.type));
      
      const nodeIds = new Set(filteredNodes.map(n => n.id));
      filteredEdges = filteredEdges.filter(edge => 
        nodeIds.has(edge.source) && nodeIds.has(edge.target)
      );
    }

    return {
      nodes: filteredNodes.map(node => ({
        ...node,
        size: node.size || (node.id === graphData.main_topic ? 15 : 5 + (node.importance || node.confidence) * 10),
        color: getNodeColor(node)
      })),
      links: filteredEdges.map(edge => ({
        source: edge.source,
        target: edge.target,
        label: edge.label,
        type: edge.type,
        weight: edge.weight,
        confidence: edge.confidence,
        strength: edge.strength || edge.confidence * edge.weight,
        width: edge.width || 1 + edge.confidence * edge.weight * 2,
        color: edge.color || (
          edge.type === 'hierarchical' ? 'rgba(33, 150, 243, 0.6)' :
          edge.type === 'causal' ? 'rgba(233, 30, 99, 0.6)' :
          edge.type === 'associative' ? 'rgba(76, 175, 80, 0.6)' :
          'rgba(158, 158, 158, 0.6)'
        )
      }))
    };
  }, [graphData, searchTerm, filteredTypes, getNodeColor]);

  // Handle container resize
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setGraphDimensions({
          width: width || rect.width,
          height: height
        });
      }
    };

    const resizeObserver = new ResizeObserver(handleResize);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => resizeObserver.disconnect();
  }, [width, height]);

  // Handle node hover
  const handleNodeHover = useCallback((node: KnowledgeGraphNode | null) => {
    setHoveredNode(node);
    
    if (node) {
      const highlightedNodes = new Set([node]);
      const highlightedLinks = new Set();
      
      processedGraphData.links.forEach(link => {
        const sourceId = typeof link.source === 'string' ? link.source : (link.source as any).id;
        const targetId = typeof link.target === 'string' ? link.target : (link.target as any).id;
        
        if (sourceId === node.id || targetId === node.id) {
          highlightedLinks.add(link);
          const relatedNodeId = sourceId === node.id ? targetId : sourceId;
          const relatedNode = processedGraphData.nodes.find(n => n.id === relatedNodeId);
          if (relatedNode) highlightedNodes.add(relatedNode);
        }
      });
      
      setHighlightNodes(highlightedNodes);
      setHighlightLinks(highlightedLinks);
    } else {
      setHighlightNodes(new Set());
      setHighlightLinks(new Set());
    }
  }, [processedGraphData]);

  // Handle node click
  const handleNodeClick = useCallback((node: KnowledgeGraphNode) => {
    setSelectedNode(node);
    onNodeSelect?.(node);
    
    // Center on node
    if (graphRef.current && interactive) {
      const x = (node as any).x || 0;
      const y = (node as any).y || 0;
      graphRef.current.centerAt(x, y, 1000);
      graphRef.current.zoom(2, 1000);
    }
  }, [onNodeSelect, interactive]);

  // Handle edge hover
  const handleEdgeHover = useCallback((edge: KnowledgeGraphEdge | null) => {
    setHoveredEdge(edge);
  }, []);

  // Handle edge click
  const handleEdgeClick = useCallback((edge: KnowledgeGraphEdge) => {
    onEdgeSelect?.(edge);
  }, [onEdgeSelect]);

  // Get unique node types for filtering
  const nodeTypes = React.useMemo(() => {
    return Array.from(new Set(graphData.nodes.map(n => n.type)));
  }, [graphData.nodes]);

  // Reset graph view
  const resetView = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(1000);
    }
  }, []);

  // Focus on main topic
  const focusMainTopic = useCallback(() => {
    const mainNode = processedGraphData.nodes.find(n => n.id === graphData.main_topic);
    if (mainNode && graphRef.current) {
      const x = (mainNode as any).x || 0;
      const y = (mainNode as any).y || 0;
      graphRef.current.centerAt(x, y, 1000);
      graphRef.current.zoom(1.5, 1000);
    }
  }, [processedGraphData, graphData.main_topic]);

  return (
    <div 
      ref={containerRef}
      className="enhanced-knowledge-graph-container" 
      style={{ 
        position: 'relative', 
        width: '100%', 
        height: `${height}px`,
        background: '#1a1a1a',
        borderRadius: '8px',
        overflow: 'hidden'
      }}
    >
      {/* Graph */}
      <ForceGraph2D
        ref={graphRef}
        graphData={processedGraphData}
        width={graphDimensions.width}
        height={graphDimensions.height}
        nodeLabel={node => `
          <div style="background: rgba(0,0,0,0.8); padding: 8px; border-radius: 4px; color: white; max-width: 200px;">
            <strong>${node.label}</strong><br/>
            Type: ${node.type}<br/>
            Confidence: ${Math.round(node.confidence * 100)}%
            ${node.description ? `<br/><em>${node.description}</em>` : ''}
          </div>
        `}
        linkLabel={link => `
          <div style="background: rgba(0,0,0,0.8); padding: 6px; border-radius: 4px; color: white;">
            <strong>${link.label}</strong><br/>
            Type: ${link.type}<br/>
            Strength: ${Math.round(link.strength * 100)}%
          </div>
        `}
        nodeRelSize={4}
        nodeCanvasObject={(node, ctx, globalScale) => {
          const { label, size, color } = node;
          const x = (node as any).x || 0;
          const y = (node as any).y || 0;
          
          const isHighlighted = highlightNodes.has(node);
          const isSelected = selectedNode?.id === node.id;
          const r = (size || 5) / globalScale;
          
          // Draw node
          ctx.beginPath();
          ctx.fillStyle = color;
          ctx.arc(x, y, r, 0, 2 * Math.PI);
          ctx.fill();
          
          // Draw outline for special states
          if (isSelected || isHighlighted) {
            ctx.beginPath();
            ctx.strokeStyle = isSelected ? '#FFD700' : '#FFD54F';
            ctx.lineWidth = (isSelected ? 3 : 2) / globalScale;
            ctx.arc(x, y, r + 1 / globalScale, 0, 2 * Math.PI);
            ctx.stroke();
          }
          
          // Draw label conditionally
          if (globalScale > 1.2 || isHighlighted || isSelected || node.id === graphData.main_topic) {
            const fontSize = Math.max(10, 12 / globalScale);
            ctx.font = `${fontSize}px Inter, sans-serif`;
            ctx.fillStyle = isHighlighted || isSelected ? '#FFD54F' : '#FFFFFF';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            // Add text background
            const textWidth = ctx.measureText(label).width;
            ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            ctx.fillRect(
              x - textWidth / 2 - 4 / globalScale,
              y + r + 2 / globalScale,
              textWidth + 8 / globalScale,
              fontSize + 4 / globalScale
            );
            
            ctx.fillStyle = isHighlighted || isSelected ? '#FFD54F' : '#FFFFFF';
            ctx.fillText(label, x, y + r + fontSize / 2 + 4 / globalScale);
          }
        }}
        linkCanvasObject={(link, ctx, globalScale) => {
          const isHighlighted = highlightLinks.has(link);
          const isHovered = hoveredEdge === link;
          
          if (!isHighlighted && !isHovered) return;
          
          const { source, target, color, width, label } = link;
          const start = { 
            x: typeof source === 'string' ? 0 : (source as any).x || 0, 
            y: typeof source === 'string' ? 0 : (source as any).y || 0 
          };
          const end = { 
            x: typeof target === 'string' ? 0 : (target as any).x || 0, 
            y: typeof target === 'string' ? 0 : (target as any).y || 0 
          };
          
          // Draw enhanced link
          ctx.beginPath();
          ctx.strokeStyle = isHovered ? '#FFD700' : color;
          ctx.lineWidth = (width + (isHovered ? 2 : 0)) / globalScale;
          ctx.setLineDash(isHighlighted ? [5, 5] : []);
          ctx.moveTo(start.x, start.y);
          ctx.lineTo(end.x, end.y);
          ctx.stroke();
          ctx.setLineDash([]);
          
          // Draw label
          if (isHighlighted || isHovered) {
            const midPoint = {
              x: start.x + (end.x - start.x) / 2,
              y: start.y + (end.y - start.y) / 2
            };
            
            const fontSize = Math.max(8, 10 / globalScale);
            ctx.font = `${fontSize}px Inter, sans-serif`;
            ctx.fillStyle = '#FFFFFF';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            // Background
            const textWidth = ctx.measureText(label).width;
            ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
            ctx.fillRect(
              midPoint.x - textWidth / 2 - 3 / globalScale,
              midPoint.y - fontSize / 2 - 1 / globalScale,
              textWidth + 6 / globalScale,
              fontSize + 2 / globalScale
            );
            
            ctx.fillStyle = '#FFFFFF';
            ctx.fillText(label, midPoint.x, midPoint.y);
          }
        }}
        onNodeHover={handleNodeHover}
        onNodeClick={handleNodeClick}
        onLinkHover={handleEdgeHover}
        onLinkClick={handleEdgeClick}
        linkDirectionalArrowLength={6}
        linkDirectionalArrowRelPos={0.9}
        linkCurvature={0.15}
        cooldownTime={2000}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.4}
        enablePointerInteraction={interactive}
      />
      
      {/* Search and Controls */}
      {showControls && (
        <div style={{
          position: 'absolute',
          top: '15px',
          left: '15px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          zIndex: 10
        }}>
          {/* Search */}
          <div style={{
            background: 'rgba(0, 0, 0, 0.8)',
            borderRadius: '8px',
            padding: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                background: 'transparent',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                borderRadius: '4px',
                padding: '4px 8px',
                color: 'white',
                fontSize: '12px',
                width: '150px'
              }}
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'white',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                ✕
              </button>
            )}
          </div>
          
          {/* Controls */}
          <div style={{
            background: 'rgba(0, 0, 0, 0.8)',
            borderRadius: '8px',
            padding: '8px',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px'
          }}>
            <button
              onClick={resetView}
              style={{
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                borderRadius: '4px',
                color: 'white',
                padding: '4px 8px',
                fontSize: '11px',
                cursor: 'pointer'
              }}
            >
              Reset View
            </button>
            <button
              onClick={focusMainTopic}
              style={{
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                borderRadius: '4px',
                color: 'white',
                padding: '4px 8px',
                fontSize: '11px',
                cursor: 'pointer'
              }}
            >
              Focus Main
            </button>
          </div>
        </div>
      )}
      
      {/* Type Filter */}
      {showControls && (
        <div style={{
          position: 'absolute',
          top: '15px',
          right: '15px',
          background: 'rgba(0, 0, 0, 0.8)',
          borderRadius: '8px',
          padding: '8px',
          maxWidth: '200px',
          zIndex: 10
        }}>
          <div style={{ color: 'white', fontSize: '12px', marginBottom: '6px', fontWeight: 'bold' }}>
            Node Types
          </div>
          {nodeTypes.map(type => (
            <label key={type} style={{ display: 'block', color: 'white', fontSize: '11px', marginBottom: '2px' }}>
              <input
                type="checkbox"
                checked={!filteredTypes.has(type)}
                onChange={(e) => {
                  const newFilteredTypes = new Set(filteredTypes);
                  if (e.target.checked) {
                    newFilteredTypes.delete(type);
                  } else {
                    newFilteredTypes.add(type);
                  }
                  setFilteredTypes(newFilteredTypes);
                }}
                style={{ marginRight: '4px' }}
              />
              {type} ({graphData.nodes.filter(n => n.type === type).length})
            </label>
          ))}
        </div>
      )}
      
      {/* Node Details Panel */}
      {(hoveredNode || selectedNode) && (
        <div style={{
          position: 'absolute',
          bottom: '15px',
          right: '15px',
          background: 'rgba(0, 0, 0, 0.9)',
          borderRadius: '8px',
          padding: '12px',
          maxWidth: '280px',
          color: 'white',
          zIndex: 10,
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)'
        }}>
          {(() => {
            const node = selectedNode || hoveredNode;
            if (!node) return null;
            
            return (
              <>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  marginBottom: '8px',
                  gap: '8px'
                }}>
                  <div 
                    style={{ 
                      width: '12px', 
                      height: '12px', 
                      borderRadius: '50%', 
                      background: node.color,
                      border: selectedNode?.id === node.id ? '2px solid #FFD700' : 'none'
                    }}
                  />
                  <h3 style={{ margin: 0, fontSize: '14px' }}>{node.label}</h3>
                </div>
                
                {node.description && (
                  <p style={{ margin: '0 0 8px 0', fontSize: '12px', opacity: 0.9 }}>
                    {node.description}
                  </p>
                )}
                
                <div style={{ fontSize: '11px', opacity: 0.8 }}>
                  <div>Type: <span style={{ color: node.color }}>{node.type}</span></div>
                  <div>Confidence: {Math.round(node.confidence * 100)}%</div>
                  {node.importance && (
                    <div>Importance: {Math.round(node.importance * 100)}%</div>
                  )}
                  {node.frequency && (
                    <div>Frequency: {node.frequency}</div>
                  )}
                </div>
                
                {selectedNode?.id === node.id && (
                  <button
                    onClick={() => setSelectedNode(null)}
                    style={{
                      background: 'rgba(255, 255, 255, 0.1)',
                      border: '1px solid rgba(255, 255, 255, 0.3)',
                      borderRadius: '4px',
                      color: 'white',
                      padding: '4px 8px',
                      fontSize: '10px',
                      cursor: 'pointer',
                      marginTop: '8px'
                    }}
                  >
                    Close Details
                  </button>
                )}
              </>
            );
          })()}
        </div>
      )}
      
      {/* Metrics Panel */}
      {showMetrics && graphData.metrics && (
        <div style={{
          position: 'absolute',
          bottom: '15px',
          left: '15px',
          background: 'rgba(0, 0, 0, 0.8)',
          borderRadius: '8px',
          padding: '8px',
          color: 'white',
          fontSize: '11px',
          zIndex: 10
        }}>
          <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Graph Metrics</div>
          <div>Nodes: {graphData.metrics.node_count}</div>
          <div>Edges: {graphData.metrics.edge_count}</div>
          <div>Density: {(graphData.metrics.density * 100).toFixed(1)}%</div>
          {graphData.metrics.most_connected_nodes.length > 0 && (
            <div style={{ marginTop: '4px' }}>
              <div style={{ fontWeight: 'bold' }}>Most Connected:</div>
              {graphData.metrics.most_connected_nodes.slice(0, 3).map(([nodeId, connections]) => (
                <div key={nodeId} style={{ fontSize: '10px', opacity: 0.8 }}>
                  {graphData.nodes.find(n => n.id === nodeId)?.label || nodeId}: {connections}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EnhancedKnowledgeGraph;