import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

// Sample data structure for demonstration
const sampleData = {
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

const AgentNetworkGraph = ({ data = sampleData, width = 680, height = 400 }) => {
  const svgRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);

  useEffect(() => {
    if (!data || !data.nodes || !data.links || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Clear SVG for redraw

    // Create the graph's container
    const container = svg.append("g");

    // Set up the simulation
    const simulation = d3.forceSimulation(data.nodes)
      .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(40));

    // Add zoom capability
    const zoom = d3.zoom()
      .scaleExtent([0.5, 5])
      .on("zoom", (event) => {
        container.attr("transform", event.transform);
      });

    svg.call(zoom);

    // Draw links
    const link = container.append("g")
      .selectAll("line")
      .data(data.links)
      .enter()
      .append("line")
      .attr("stroke-width", d => Math.sqrt(d.value))
      .attr("stroke", "#aaa")
      .attr("opacity", 0.7);

    // Draw nodes
    const nodeGroup = container.append("g")
      .selectAll("g")
      .data(data.nodes)
      .enter()
      .append("g")
      .call(d3.drag()
        .on("start", dragStarted)
        .on("drag", dragging)
        .on("end", dragEnded))
      .on("mouseover", (event, d) => setHoveredNode(d))
      .on("mouseout", () => setHoveredNode(null));

    // Node circles
    nodeGroup.append("circle")
      .attr("r", 16)
      .attr("fill", d => getNodeColor(d))
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);

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

    // Update positions on simulation tick
    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      nodeGroup.attr("transform", d => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragStarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragging(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragEnded(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [data, width, height]);

  // Get node color based on type
  const getNodeColor = (node) => {
    return node.type === "agent" 
      ? "#3B82F6" // blue for agents
      : "#10B981"; // green for tools
  };

  // Get status indicator color
  const getStatusColor = (status) => {
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
