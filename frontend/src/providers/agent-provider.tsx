"use client";

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { useMcpAgents, useMcpTools } from '@/hooks/use-mcp';
import { Button } from '@/components/ui/button';
import { Settings, ZoomIn, ZoomOut, Maximize2, RefreshCw } from 'lucide-react';

// Define the node and link types for the graph
interface Node {
  id: string;
  type: 'agent' | 'tool';
  name: string;
  status: 'active' | 'inactive' | 'pending' | 'error';
}

interface Link {
  source: string;
  target: string;
  value: number;
}

interface GraphData {
  nodes: Node[];
  links: Link[];
}

// Sample data for demonstration
const sampleData: GraphData = {
  nodes: [
    { id: "orchestrator", type: "agent", name: "Orchestrator", status: "active" },
    { id: "prompt_optimizer", type: "agent", name: "Prompt Optimizer", status: "active" },
    { id: "workflow_planner", type: "agent", name: "Workflow Planner", status: "active" },
    { id: "research", type: "agent", name: "Research Agent", status: "inactive" },
    { id: "math_solver", type: "agent", name: "Math Solver", status: "active" },
    { id: "weather", type: "agent", name: "Weather Agent", status: "pending" },
    { id: "calculator", type: "tool", name: "Calculator Tool", status: "active" },
    { id: "translation", type: "tool", name: "Translation Tool", status: "active" },
    { id: "web_search", type: "tool", name: "Web Search Tool", status: "active" },
  ],
  links: [
    { source: "orchestrator", target: "prompt_optimizer", value: 5 },
    { source: "orchestrator", target: "workflow_planner", value: 8 },
    { source: "workflow_planner", target: "research", value: 3 },
    { source: "workflow_planner", target: "math_solver", value: 2 },
    { source: "workflow_planner", target: "weather", value: 1 },
    { source: "math_solver", target: "calculator", value: 4 },
    { source: "research", target: "web_search", value: 6 },
    { source: "research", target: "translation", value: 2 },
  ]
};

interface AgentNetworkGraphProps {
  width?: number;
  height?: number;
  useMockData?: boolean;
}

const AgentNetworkGraph = ({ 
  width = 680, 
  height = 400,
  useMockData = true
}: AgentNetworkGraphProps) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoveredNode, setHoveredNode] = useState<Node | null>(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  
  // Fetch real data from MCP registry if not using mock data
  const { data: agents, isLoading: isLoadingAgents } = useMcpAgents();
  const { data: tools, isLoading: isLoadingTools } = useMcpTools();
  
  // Process real data into graph format
  const processRealData = (): GraphData => {
    const nodes: Node[] = [];
    const links: Link[] = [];
    
    // Add agents as nodes
    if (agents) {
      agents.forEach((agent: { id: any; name: any; last_heartbeat: number; }) => {
        nodes.push({
          id: agent.id,
          type: 'agent',
          name: agent.name,
          status: agent.last_heartbeat && Date.now() - agent.last_heartbeat < 60000 
            ? 'active' 
            : 'inactive'
        });
      });
    }
    
    // Add tools as nodes
    if (tools) {
      tools.forEach((tool: { id: any; name: any; last_heartbeat: number; }) => {
        nodes.push({
          id: tool.id,
          type: 'tool',
          name: tool.name,
          status: tool.last_heartbeat && Date.now() - tool.last_heartbeat < 60000 
            ? 'active' 
            : 'inactive'
        });
      });
    }
    
    // TODO: Add links based on actual usage patterns or predefined relationships
    // For now, we'll create some example links
    if (nodes.length > 1) {
      const agentNodes = nodes.filter(node => node.type === 'agent');
      const toolNodes = nodes.filter(node => node.type === 'tool');
      
      // Connect agents to tools
      agentNodes.forEach(agent => {
        toolNodes.forEach(tool => {
          // Just connect with a random probability for demonstration
          if (Math.random() > 0.7) {
            links.push({
              source: agent.id,
              target: tool.id,
              value: Math.ceil(Math.random() * 5)
            });
          }
        });
      });
      
      // Connect some agents to other agents
      if (agentNodes.length > 1) {
        for (let i = 0; i < agentNodes.length - 1; i++) {
          if (Math.random() > 0.5) {
            links.push({
              source: agentNodes[i].id,
              target: agentNodes[i + 1].id,
              value: Math.ceil(Math.random() * 5)
            });
          }
        }
      }
    }
    
    return { nodes, links };
  };
  
  // Decide which data to use
  const graphData = useMockData ? sampleData : processRealData();
  const isLoading = !useMockData && (isLoadingAgents || isLoadingTools);

  useEffect(() => {
    if (!svgRef.current || isLoading) return;
    
    // Select the SVG element
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Clear SVG for redraw
    
    // Create the graph's container with zoom capability
    const container = svg.append("g");
    
    // Set up the simulation
    const simulation = d3.forceSimulation(graphData.nodes as any)
      .force("link", d3.forceLink(graphData.links).id((d: any) => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(40));
    
    // Add zoom capability
    const zoom = d3.zoom()
      .scaleExtent([0.3, 3])
      .on("zoom", (event) => {
        container.attr("transform", event.transform);
        setZoomLevel(event.transform.k);
      });
    
    svg.call(zoom as any);
    
    // Draw links
    const link = container.append("g")
      .selectAll("line")
      .data(graphData.links)
      .enter()
      .append("line")
      .attr("stroke-width", d => Math.sqrt(d.value))
      .attr("stroke", "#aaa")
      .attr("opacity", 0.7);
    
    // Draw nodes
    const nodeGroup = container.append("g")
      .selectAll("g")
      .data(graphData.nodes)
      .enter()
      .append("g")
      .call(d3.drag()
        .on("start", dragStarted)
        .on("drag", dragging)
        .on("end", dragEnded) as any)
      .on("mouseover", (event, d) => setHoveredNode(d as Node))
      .on("mouseout", () => setHoveredNode(null));
    
    // Node circles
    nodeGroup.append("circle")
      .attr("r", 16)
      .attr("fill", d => getNodeColor(d as Node))
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);
    
    // Status indicators
    nodeGroup.append("circle")
      .attr("r", 4)
      .attr("cx", 10)
      .attr("cy", 10)
      .attr("fill", d => getStatusColor((d as Node).status));
    
    // Node labels
    nodeGroup.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", 30)
      .attr("font-size", "10px")
      .attr("fill", "#555")
      .text(d => (d as Node).name);
    
    // Node type icons (simplified)
    nodeGroup.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", 4)
      .attr("font-size", "12px")
      .attr("font-family", "sans-serif")
      .attr("fill", "white")
      .text(d => (d as Node).type === "agent" ? "A" : "T");
    
    // Update positions on simulation tick
    simulation.on("tick", () => {
      link
        .attr("x1", d => (d.source as any).x)
        .attr("y1", d => (d.source as any).y)
        .attr("x2", d => (d.target as any).x)
        .attr("y2", d => (d.target as any).y);
    
      nodeGroup.attr("transform", d => `translate(${(d as any).x},${(d as any).y})`);
    });
    
    // Drag functions
    function dragStarted(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }
    
    function dragging(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }
    
    function dragEnded(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
    
    return () => {
      simulation.stop();
    };
  }, [graphData, width, height, isLoading, useMockData]);
  
  // Get node color based on type
  const getNodeColor = (node: Node) => {
    return node.type === "agent" 
      ? "#3B82F6" // blue for agents
      : "#10B981"; // green for tools
  };
  
  // Get status indicator color
  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "#10B981"; // green
      case "inactive": return "#EF4444"; // red
      case "pending": return "#F59E0B"; // amber
      default: return "#9CA3AF"; // gray
    }
  };
  
  // Zoom in function
  const handleZoomIn = () => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      const zoom = d3.zoom().scaleExtent([0.3, 3]);
      svg.transition().call(zoom.scaleBy as any, 1.2);
    }
  };
  
  // Zoom out function
  const handleZoomOut = () => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      const zoom = d3.zoom().scaleExtent([0.3, 3]);
      svg.transition().call(zoom.scaleBy as any, 0.8);
    }
  };
  
  // Reset zoom function
  const handleResetZoom = () => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      const zoom = d3.zoom().scaleExtent([0.3, 3]);
      svg.transition().call(zoom.transform as any, d3.zoomIdentity);
    }
  };
  
  // Refresh function
  const handleRefresh = () => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      svg.selectAll("*").remove();
      // Re-render graph would happen via useEffect
    }
  };

  return (
    <div className="bg-card rounded-xl w-full">
      <div className="flex justify-between items-center mb-2 px-2">
        {hoveredNode && (
          <div className="text-sm px-2 py-1 rounded-md bg-muted">
            {hoveredNode.name} ({hoveredNode.type}) - {hoveredNode.status}
          </div>
        )}
        <div className="text-sm text-muted-foreground ml-auto mr-2">
          Zoom: {Math.round(zoomLevel * 100)}%
        </div>
        <div className="flex gap-1">
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleZoomIn}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleZoomOut}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleResetZoom}>
            <Maximize2 className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>
      
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : (
        <>
          <svg 
            ref={svgRef} 
            width={width} 
            height={height} 
            className="border border-border rounded-lg overflow-hidden"
          />
          <div className="mt-2 flex justify-center gap-6 text-xs px-2 py-1">
            <div className="flex items-center">
              <span className="w-3 h-3 rounded-full bg-blue-500 inline-block mr-1"></span>
              <span>Agent</span>
            </div>
            <div className="flex items-center">
              <span className="w-3 h-3 rounded-full bg-green-500 inline-block mr-1"></span>
              <span>Tool</span>
            </div>
            <div className="flex items-center">
              <span className="w-3 h-3 rounded-full bg-red-500 inline-block mr-1"></span>
              <span>Inactive</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AgentNetworkGraph;