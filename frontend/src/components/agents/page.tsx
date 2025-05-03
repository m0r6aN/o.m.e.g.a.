"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AgentCard } from "@/components/agents/agent-card";
import { Bot, Filter, Plus, RefreshCcw, Search } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import Link from "next/link";

// Sample agents data
const SAMPLE_AGENTS = [
  {
    id: "orchestrator",
    name: "Orchestrator",
    description: "Central coordination agent that manages workflow execution and agent communication.",
    status: "active" as const,
    type: "orchestrator",
    tags: ["core", "coordination", "workflow"],
    lastActivity: "2 minutes ago",
    capabilities: ["workflow_management", "agent_coordination", "task_delegation"],
  },
  {
    id: "prompt_optimizer",
    name: "Prompt Optimizer",
    description: "Improves prompts for clarity, specificity, and model compatibility using advanced NLP techniques.",
    status: "active" as const,
    type: "prompt_optimizer",
    tags: ["nlp", "optimization", "prompts"],
    lastActivity: "15 minutes ago",
    capabilities: ["prompt_analysis", "prompt_refinement", "style_adjustment"],
  },
  {
    id: "workflow_planner",
    name: "Workflow Planner",
    description: "Creates execution plans for complex tasks by breaking them down into manageable steps with dependencies.",
    status: "active" as const,
    type: "planner",
    tags: ["planning", "workflow", "optimization"],
    lastActivity: "25 minutes ago",
    capabilities: ["task_decomposition", "dependency_tracking", "parallel_execution"],
  },
  {
    id: "research",
    name: "Research Agent",
    description: "Conducts comprehensive research on topics by collecting, analyzing, and synthesizing information from multiple sources.",
    status: "inactive" as const,
    type: "researcher",
    tags: ["research", "information", "synthesis"],
    lastActivity: "1 hour ago",
    capabilities: ["web_search", "information_gathering", "content_summarization"],
  },
  {
    id: "math_solver",
    name: "Math Solver",
    description: "Solves complex mathematical problems using symbolic and numerical computation methods.",
    status: "active" as const,
    type: "solver",
    tags: ["math", "computation", "problem-solving"],
    lastActivity: "45 minutes ago",
    capabilities: ["equation_solving", "numerical_analysis", "calculus"],
  },
  {
    id: "weather",
    name: "Weather Agent",
    description: "Provides real-time weather information and forecasts for any location worldwide.",
    status: "pending" as const,
    type: "data_provider",
    tags: ["weather", "forecast", "data"],
    lastActivity: "2 hours ago",
    capabilities: ["weather_lookup", "forecast_prediction", "climate_analysis"],
  },
  {
    id: "code_generator",
    name: "Code Generator",
    description: "Generates high-quality code in multiple programming languages based on functional requirements.",
    status: "error" as const,
    type: "generator",
    tags: ["code", "programming", "development"],
    lastActivity: "3 hours ago",
    capabilities: ["code_generation", "code_refactoring", "code_review"],
  },
  {
    id: "financial_analyst",
    name: "Financial Analyst",
    description: "Analyzes financial data and provides insights, forecasts, and recommendations.",
    status: "active" as const,
    type: "analyst",
    tags: ["finance", "analysis", "forecasting"],
    lastActivity: "5 hours ago",
    capabilities: ["market_analysis", "stock_prediction", "portfolio_optimization"],
  },
];

export default function AgentsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string[]>([]);
  const [typeFilter, setTypeFilter] = useState<string[]>([]);
  
  // Get unique agent types for filter
  const agentTypes = Array.from(new Set(SAMPLE_AGENTS.map(agent => agent.type)));
  
  // Filter agents based on search and filters
  const filteredAgents = SAMPLE_AGENTS.filter(agent => {
    // Search filter
    const matchesSearch = 
      searchQuery === "" || 
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    // Status filter
    const matchesStatus = 
      statusFilter.length === 0 || 
      statusFilter.includes(agent.status);
    
    // Type filter
    const matchesType = 
      typeFilter.length === 0 || 
      typeFilter.includes(agent.type);
    
    return matchesSearch && matchesStatus && matchesType;
  });

  // Handle status filter changes
  const handleStatusFilterChange = (status: string) => {
    setStatusFilter(prev => {
      if (prev.includes(status)) {
        return prev.filter(s => s !== status);
      } else {
        return [...prev, status];
      }
    });
  };
  
  // Handle type filter changes
  const handleTypeFilterChange = (type: string) => {
    setTypeFilter(prev => {
      if (prev.includes(type)) {
        return prev.filter(t => t !== type);
      } else {
        return [...prev, type];
      }
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Agents</h1>
        <Link href="/agents/create">
          <Button>
            <Plus className="mr-2 h-4 w-4" /> Create Agent
          </Button>
        </Link>
      </div>
      
      <div className="flex flex-col md:flex-row gap-4 items-start md:items-center">
        {/* Search box */}
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search agents..."
            className="pl-8"
            value={searchQuery}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
          />
        </div>
        
        {/* Status filter */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="h-9">
              <Filter className="mr-2 h-4 w-4" />
              Status
              {statusFilter.length > 0 && (
                <span className="ml-1 rounded-full bg-primary w-4 h-4 text-[10px] flex items-center justify-center text-primary-foreground">
                  {statusFilter.length}
                </span>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-40">
            <DropdownMenuLabel>Filter by Status</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuCheckboxItem
              checked={statusFilter.includes("active")}
              onCheckedChange={() => handleStatusFilterChange("active")}
            >
              Active
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem
              checked={statusFilter.includes("inactive")}
              onCheckedChange={() => handleStatusFilterChange("inactive")}
            >
              Inactive
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem
              checked={statusFilter.includes("pending")}
              onCheckedChange={() => handleStatusFilterChange("pending")}
            >
              Pending
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem
              checked={statusFilter.includes("error")}
              onCheckedChange={() => handleStatusFilterChange("error")}
            >
              Error
            </DropdownMenuCheckboxItem>
          </DropdownMenuContent>
        </DropdownMenu>
        
        {/* Type filter */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="h-9">
              <Bot className="mr-2 h-4 w-4" />
              Type
              {typeFilter.length > 0 && (
                <span className="ml-1 rounded-full bg-primary w-4 h-4 text-[10px] flex items-center justify-center text-primary-foreground">
                  {typeFilter.length}
                </span>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-40">
            <DropdownMenuLabel>Filter by Type</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {agentTypes.map(type => (
              <DropdownMenuCheckboxItem
                key={type}
                checked={typeFilter.includes(type)}
                onCheckedChange={() => handleTypeFilterChange(type)}
              >
                {type.charAt(0).toUpperCase() + type.slice(1).replace("_", " ")}
              </DropdownMenuCheckboxItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
        
        {/* Refresh button */}
        <Button variant="ghost" size="icon" className="h-9 w-9">
          <RefreshCcw className="h-4 w-4" />
          <span className="sr-only">Refresh</span>
        </Button>
      </div>
      
      {/* Results count */}
      <div className="text-sm text-muted-foreground">
        Showing {filteredAgents.length} of {SAMPLE_AGENTS.length} agents
      </div>
      
      {/* Agents grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredAgents.map(agent => (
          <AgentCard
            key={agent.id}
            id={agent.id}
            name={agent.name}
            description={agent.description}
            status={agent.status}
            type={agent.type}
            tags={agent.tags}
            lastActivity={agent.lastActivity}
            capabilities={agent.capabilities}
          />
        ))}
      </div>
      
      {/* Empty state */}
      {filteredAgents.length === 0 && (
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <Bot className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium">No agents found</h3>
          <p className="text-sm text-muted-foreground mt-2">
            {searchQuery || statusFilter.length > 0 || typeFilter.length > 0
              ? "Try adjusting your filters or search query"
              : "Get started by creating your first agent"}
          </p>
          {!(searchQuery || statusFilter.length > 0 || typeFilter.length > 0) && (
            <Link href="/agents/create" className="mt-4">
              <Button>
                <Plus className="mr-2 h-4 w-4" /> Create Agent
              </Button>
            </Link>
          )}
        </div>
      )}
    </div>
  );
}