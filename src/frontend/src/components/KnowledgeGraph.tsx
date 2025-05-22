import React, { useEffect, useRef, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: string;
  description?: string;
  confidence: number;
  size?: number;
  color?: string;
}

interface KnowledgeGraphEdge {
  source: string;
  target: string;
  label: string;
  type: string;
  weight: number;
  confidence: number;
}

interface KnowledgeGraphData {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  main_topic: string;
}

interface KnowledgeGraphProps {
  graphData: KnowledgeGraphData;
  height?: number;
}

const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({ 
  graphData, 
  height = 500 
}) => {
  const graphRef = useRef<any>(null);
  const [hoveredNode, setHoveredNode] = useState<KnowledgeGraphNode | null>(null);
  const [hoveredEdge, setHoveredEdge] = useState<KnowledgeGraphEdge | null>(null);
  const [highlightNodes, setHighlightNodes] = useState(new Set());
  const [highlightLinks, setHighlightLinks] = useState(new Set());
  
  // Transform the knowledge graph data to the format expected by react-force-graph
  const graphDataFormatted = {
    nodes: graphData.nodes.map(node => ({
      ...node,
      // Default size based on confidence
      size: node.size || (node.id === graphData.main_topic ? 15 : 8 + node.confidence * 5),
      // Color by node type and whether it's the main topic
      color: node.color || (
        node.id === graphData.main_topic ? 
          '#FFA726' : // Orange for main topic
          node.type === 'concept' ? 
            '#4CAF50' : // Green for concepts
            node.type === 'entity' ? 
              '#2196F3' : // Blue for entities
              '#9C27B0'  // Purple for other types
      )
    })),
    links: graphData.edges.map(edge => ({
      source: edge.source,
      target: edge.target,
      label: edge.label,
      type: edge.type,
      weight: edge.weight,
      confidence: edge.confidence,
      // Line width based on confidence and weight
      width: 1 + edge.confidence * edge.weight * 3,
      // Color by type
      color: edge.type === 'hierarchical' ? 
        'rgba(33, 150, 243, 0.6)' : // Blue for hierarchical
        edge.type === 'causal' ? 
          'rgba(233, 30, 99, 0.6)' : // Pink for causal
          'rgba(158, 158, 158, 0.6)'  // Gray for other types
    }))
  };

  useEffect(() => {
    // Set initial camera position
    if (graphRef.current) {
      const graph = graphRef.current;
      
      // Find the main topic node
      const mainNode = graphDataFormatted.nodes.find(node => node.id === graphData.main_topic);
      
      if (mainNode) {
        // Center the graph on the main topic
        // Use optional chaining since coordinates might not be available immediately
        const x = (mainNode as any).x || 0;
        const y = (mainNode as any).y || 0;
        graph.centerAt(x, y, 1000);
        graph.zoom(1.5, 1000);
      }
    }
  }, [graphData.main_topic]);

  const handleNodeHover = (node: KnowledgeGraphNode | null) => {
    setHoveredNode(node);
    
    if (node) {
      // Highlight connected nodes and links
      const highlightedNodes = new Set();
      const highlightedLinks = new Set();
      
      highlightedNodes.add(node);
      
      graphDataFormatted.links.forEach(link => {
        // Handle both string IDs and node objects
        const sourceId = typeof link.source === 'string' ? link.source : (link.source as any).id;
        const targetId = typeof link.target === 'string' ? link.target : (link.target as any).id;
        
        if (sourceId === node.id || targetId === node.id) {
          highlightedLinks.add(link);
          const relatedNode = sourceId === node.id ? link.target : link.source;
          highlightedNodes.add(relatedNode);
        }
      });
      
      setHighlightNodes(highlightedNodes);
      setHighlightLinks(highlightedLinks);
    } else {
      setHighlightNodes(new Set());
      setHighlightLinks(new Set());
    }
  };

  const handleLinkHover = (edge: KnowledgeGraphEdge | null) => {
    setHoveredEdge(edge);
  };

  const handleNodeClick = (node: KnowledgeGraphNode) => {
    // Focus on the clicked node
    if (graphRef.current) {
      const x = (node as any).x || 0;
      const y = (node as any).y || 0;
      graphRef.current.centerAt(x, y, 1000);
      graphRef.current.zoom(2, 1000);
    }
  };

  return (
    <div className="knowledge-graph-container" style={{ position: 'relative', height: `${height}px` }}>
      <ForceGraph2D
        ref={graphRef}
        graphData={graphDataFormatted}
        nodeLabel={node => `${node.label}`}
        linkLabel={link => `${link.label}`}
        nodeRelSize={6}
        nodeCanvasObject={(node, ctx, globalScale) => {
          const { id, color, label, size } = node;
          const x = (node as any).x || 0;
          const y = (node as any).y || 0;
          
          // Different radius for highlighted nodes
          const isHighlighted = highlightNodes.has(node);
          const r = size || (isHighlighted ? 8 : 5) / globalScale;
          
          // Draw node circle
          ctx.beginPath();
          ctx.fillStyle = color;
          ctx.arc(x, y, r, 0, 2 * Math.PI);
          ctx.fill();
          
          // Draw outline for highlighted nodes
          if (isHighlighted) {
            ctx.beginPath();
            ctx.strokeStyle = '#FFD54F';
            ctx.lineWidth = 2 / globalScale;
            ctx.arc(x, y, r + 1 / globalScale, 0, 2 * Math.PI);
            ctx.stroke();
          }
          
          // Draw label if either zoomed in or node is highlighted
          if (globalScale > 1.5 || isHighlighted || id === graphData.main_topic) {
            ctx.font = `${12 / globalScale}px Sans-Serif`;
            ctx.fillStyle = isHighlighted ? '#FFD54F' : '#FFF';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(label, x, y + r + 4 / globalScale);
          }
        }}
        linkCanvasObject={(link, ctx, globalScale) => {
          // Only custom draw highlighted links
          if (!highlightLinks.has(link) && hoveredEdge !== link) return;
          
          const { source, target, color, width } = link;
          
          // Draw custom link - handle both string IDs and node objects
          const start = { 
            x: typeof source === 'string' ? 0 : (source as any).x || 0, 
            y: typeof source === 'string' ? 0 : (source as any).y || 0 
          };
          const end = { 
            x: typeof target === 'string' ? 0 : (target as any).x || 0, 
            y: typeof target === 'string' ? 0 : (target as any).y || 0 
          };
          
          // Draw link
          ctx.beginPath();
          ctx.strokeStyle = color;
          ctx.lineWidth = width / globalScale;
          ctx.moveTo(start.x, start.y);
          ctx.lineTo(end.x, end.y);
          ctx.stroke();
          
          // Draw label for the link
          if (highlightLinks.has(link) || hoveredEdge === link) {
            const label = link.label;
            const midPoint = {
              x: start.x + (end.x - start.x) / 2,
              y: start.y + (end.y - start.y) / 2
            };
            
            ctx.font = `${10 / globalScale}px Sans-Serif`;
            ctx.fillStyle = '#FFF';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            // Background for label
            const textWidth = ctx.measureText(label).width;
            ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
            ctx.fillRect(
              midPoint.x - textWidth / 2 - 2 / globalScale,
              midPoint.y - 5 / globalScale,
              textWidth + 4 / globalScale,
              10 / globalScale
            );
            
            ctx.fillStyle = '#FFF';
            ctx.fillText(label, midPoint.x, midPoint.y);
          }
        }}
        linkDirectionalArrowLength={5}
        linkDirectionalArrowRelPos={0.8}
        linkCurvature={0.2}
        onNodeHover={handleNodeHover}
        onLinkHover={handleLinkHover}
        onNodeClick={handleNodeClick}
        cooldownTime={3000}
        linkWidth={link => highlightLinks.has(link) ? 3 : 1}
        nodeAutoColorBy="type"
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
      />
      
      {/* Node info panel */}
      {hoveredNode && (
        <div 
          className="node-info-panel"
          style={{
            position: 'absolute',
            top: '10px',
            right: '10px',
            background: 'rgba(30, 30, 30, 0.8)',
            borderRadius: '8px',
            padding: '12px',
            maxWidth: '250px',
            color: 'white',
            zIndex: 10,
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
          }}
        >
          <h3 style={{ margin: '0 0 8px 0', color: hoveredNode.color }}>{hoveredNode.label}</h3>
          {hoveredNode.description && (
            <p style={{ margin: '0 0 8px 0', fontSize: '14px' }}>{hoveredNode.description}</p>
          )}
          <div style={{ fontSize: '12px', opacity: 0.8 }}>
            <div>Type: {hoveredNode.type}</div>
            <div>Confidence: {Math.round(hoveredNode.confidence * 100)}%</div>
          </div>
        </div>
      )}
      
      {/* Controls and legend */}
      <div 
        className="graph-controls"
        style={{
          position: 'absolute',
          bottom: '10px',
          left: '10px',
          background: 'rgba(30, 30, 30, 0.8)',
          borderRadius: '8px',
          padding: '8px',
          color: 'white',
          fontSize: '12px',
          zIndex: 10
        }}
      >
        <div style={{ marginBottom: '6px' }}>
          <strong>Controls:</strong> Scroll to zoom, drag to pan
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#FFA726', marginRight: '4px' }}></div>
            <span>Main Topic</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#4CAF50', marginRight: '4px' }}></div>
            <span>Concept</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#2196F3', marginRight: '4px' }}></div>
            <span>Entity</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraph;