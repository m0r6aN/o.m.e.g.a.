import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

// Define interfaces for your node and link data structures
interface NetworkNode {
  id: string;
  type: "agent" | "tool"; // Use specific literals if possible
  name: string;
  status: "active" | "inactive" | "pending"; // Use specific literals
  // D3 simulation will add these properties automatically:
  index?: number;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

interface NetworkLink {
  source: string; // D3 needs string IDs initially for the link force
  target: string;
  value: number;
  // D3 simulation might add these after initialization:
  // source: NetworkNode; (object reference)
  // target: NetworkNode; (object reference)
  // index?: number;
}

// Type for AgentNetworkGraph props (from agent-network-graph.tsx)
export interface AgentNetworkGraphProps {
  data?: { nodes: any[]; links: any[] };
  width?: number;
  height?: number;
  router?: any;
}

interface GraphData {
  nodes: NetworkNode[];
  links: NetworkLink[];
}

// Sample data structure using the interfaces (optional, but good for clarity)
const sampleData: GraphData = {
  // ... your nodes and links data ...
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

// Your component props using the interface
const AgentNetworkGraph = ({ data = sampleData, width = 680, height = 400 }: AgentNetworkGraphProps) => {
  const svgRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState<NetworkNode | null>(null); // Use NetworkNode 

  useEffect(() => {
    if (!data || !data.nodes || !data.links || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Clear SVG for redraw

    // Create the graph's container
    const container = svg.append("g");

    // Set up the simulation
    const simulation = d3.forceSimulation<NetworkNode>(data.nodes) // Tell simulation about NetworkNode
      .force("link", d3.forceLink<NetworkNode, NetworkLink>(data.links) // Tell link force about NetworkNode and NetworkLink
                      .id(d => d.id) // d is now correctly typed as NetworkNode
                      .distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(40));


    // Add zoom capability
    const zoom = d3.zoom()
      .scaleExtent([0.5, 5])
      .on("zoom", (event) => {
        container.attr("transform", event.transform);
      });

    svg.call(zoom as any);

    // Draw links
    const link = container.append("g")
      .selectAll<SVGLineElement, NetworkLink>("line") // Specify types for selection
      .data(data.links)
      .enter()
      .append("line")
      .attr("stroke-width", d => Math.sqrt(d.value)) // d is NetworkLink
      .attr("stroke", "#aaa")
      .attr("opacity", 0.7);

    // Draw nodes
    // Type the selection data explicitly
    const nodeGroup = container.append("g")
      .selectAll<SVGGElement, NetworkNode>("g") // Specify types for selection
      .data(data.nodes)
      .enter()
      .append("g")
      .call(d3.drag<SVGGElement, NetworkNode>() // Type the drag behavior
        .on("start", dragStarted)
        .on("drag", dragging)
        .on("end", dragEnded))
      .on("mouseover", (event, d) => setHoveredNode(d)) // d is NetworkNode
      .on("mouseout", () => setHoveredNode(null));

    // Node circles
    nodeGroup.append("circle")
      .attr("r", 16)
      .attr("fill", d => getNodeColor(d)) // Pass d (NetworkNode) to helper
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);

     // Status indicators
    nodeGroup.append("circle")
      .attr("r", 4)
      .attr("cx", 10)
      .attr("cy", 10)
      .attr("fill", d => getStatusColor(d.status)); // d is NetworkNode

    // Node labels
    nodeGroup.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", 30)
      .attr("font-size", "10px")
      .attr("fill", "#555")
      .text(d => d.name); // d is NetworkNode

    // Node type icons
    nodeGroup.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", 4)
      .attr("font-size", "12px")
      .attr("font-family", "sans-serif")
      .attr("fill", "white")
      .text(d => d.type === "agent" ? "A" : "T"); // d is NetworkNode

    // Status indicators
    nodeGroup.append("circle")
      .attr("r", 4)
      .attr("cx", 10)
      .attr("cy", 10)
      .attr("fill", d => getStatusColor(d.status));

    // Node labels
    nodeGroup.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", 30)
      .attr("font-size", "10px")
      .attr("fill", "#555")
      .text(d => d.name);

    // Node type icons (simplified)
    nodeGroup.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", 4)
      .attr("font-size", "12px")
      .attr("font-family", "sans-serif")
      .attr("fill", "white")
      .text(d => d.type === "agent" ? "A" : "T");

    // // Update positions on simulation tick
    // interface TickedLink extends d3.SimulationLinkDatum<NetworkNode> {
    //   // You might not need to extend this explicitly if source/target have x/y
    // }
    // simulation.on("tick", () => {
    //   link
    //     .attr("x1", d => (d.source as NetworkNode).x ?? 0) // Assert source/target type and handle potential undefined x/y
    //     .attr("y1", d => (d.source as NetworkNode).y ?? 0)
    //     .attr("x2", d => (d.target as NetworkNode).x ?? 0)
    //     .attr("y2", d => (d.target as NetworkNode).y ?? 0);

    //   nodeGroup.attr("transform", d => `translate(${d.x ?? 0},${d.y ?? 0})`); // Handle potential undefined x/y
    // });

  // --- UPDATE DRAG FUNCTIONS TO USE NetworkNode ---
  function dragStarted(event: d3.D3DragEvent<SVGGElement, NetworkNode, any>, d: NetworkNode) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x; // d is NetworkNode
    d.fy = d.y;
  }

  function dragging(event: d3.D3DragEvent<SVGGElement, NetworkNode, any>, d: NetworkNode) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragEnded(event: d3.D3DragEvent<SVGGElement, NetworkNode, any>, d: NetworkNode) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null; // Use null for fixed positions
    d.fy = null;
  }

    return () => {
      simulation.stop();
    };
  }, [data, width, height]);

  // Get node color based on type
  const getNodeColor = (node: NetworkNode) => { // Expect NetworkNode
    return node.type === "agent"
      ? "#3B82F6" // blue for agents
      : "#10B981"; // green for tools
  };

  // Get status indicator color
  const getStatusColor = (status: NetworkNode['status']) => { // Expect specific status type
    switch (status) {
      case "active": return "#10B981"; // green
      case "inactive": return "#EF4444"; // red
      case "pending": return "#F59E0B"; // amber
      default: return "#9CA3AF"; // gray
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 p-4 rounded-xl shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium">Agent Network</h3>
        {hoveredNode && (
          <div className="text-sm bg-gray-100 dark:bg-slate-800 px-2 py-1 rounded-md">
            {hoveredNode.name} ({hoveredNode.type}) - {hoveredNode.status}
          </div>
        )}
      </div>
      <svg ref={svgRef} width={width} height={height} className="border border-gray-200 dark:border-slate-700 rounded-lg overflow-hidden" />
      <div className="mt-4 flex justify-center gap-6 text-sm">
        <div className="flex items-center">
          <span className="w-3 h-3 rounded-full bg-blue-500 inline-block mr-2"></span>
          <span>Agent</span>
        </div>
        <div className="flex items-center">
          <span className="w-3 h-3 rounded-full bg-green-500 inline-block mr-2"></span>
          <span>Tool</span>
        </div>
        <div className="flex items-center">
          <span className="w-3 h-3 rounded-full bg-red-500 inline-block mr-2"></span>
          <span>Inactive</span>
        </div>
      </div>
    </div>
  );
};

export default AgentNetworkGraph;