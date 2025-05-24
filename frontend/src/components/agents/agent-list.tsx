// src/components/agents/agent-list.tsx
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Skeleton } from '@/components/ui/skeleton';
import { Activity, MoreHorizontal, Play, Square, Plus, RefreshCw } from 'lucide-react';

// Define agent interface
interface Agent {
  id: string;
  name: string;
  description: string;
  type: string;
  protocol: string;
  status: 'active' | 'inactive' | 'pending';
  capabilities: string[];
  tags: string[];
  lastActive: string;
  version: string;
}

// Define a function to fetch agents
async function fetchAgents(): Promise<Agent[]> {
  const response = await fetch('/api/agents');
  if (!response.ok) {
    throw new Error('Failed to fetch agents');
  }
  return response.json();
}

export function AgentList() {
  const router = useRouter();
  const [filter, setFilter] = useState<string | null>(null);
  
  // Use react-query to fetch agents
  const { data: agents, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['agents'],
    queryFn: fetchAgents,
  });

  // Filter agents based on current filter
  const filteredAgents = React.useMemo(() => {
    if (!agents) return [];
    if (!filter) return agents;
    
    return agents.filter(agent => 
      agent.type === filter || 
      agent.tags.includes(filter) || 
      agent.capabilities.includes(filter)
    );
  }, [agents, filter]);

  // Handle starting an agent
  const handleStartAgent = async (agentId: string) => {
    try {
      const response = await fetch(`/api/agents/${agentId}/start`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to start agent');
      }
      
      // Refetch agents to update the list
      refetch();
    } catch (error) {
      console.error('Error starting agent:', error);
    }
  };

  // Handle stopping an agent
  const handleStopAgent = async (agentId: string) => {
    try {
      const response = await fetch(`/api/agents/${agentId}/stop`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to stop agent');
      }
      
      // Refetch agents to update the list
      refetch();
    } catch (error) {
      console.error('Error stopping agent:', error);
    }
  };

  // Handle viewing agent details
  const handleViewAgent = (agentId: string) => {
    router.push(`/agents/${agentId}`);
  };

  // Get available filters from agents' data
  const availableFilters = React.useMemo(() => {
    if (!agents) return [];
    
    const types = [...new Set(agents.map(agent => agent.type))];
    const tags = [...new Set(agents.flatMap(agent => agent.tags))];
    return [...types, ...tags];
  }, [agents]);

  // Get color for status badge
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500';
      case 'inactive':
        return 'bg-red-500';
      case 'pending':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, index) => (
          <Card key={index} className="shadow-md">
            <CardHeader className="pb-2">
              <Skeleton className="h-6 w-3/4 mb-2" />
              <Skeleton className="h-4 w-full" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-4 w-full mb-4" />
              <div className="flex flex-wrap gap-2 mt-2">
                <Skeleton className="h-6 w-16" />
                <Skeleton className="h-6 w-16" />
                <Skeleton className="h-6 w-16" />
              </div>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Skeleton className="h-10 w-20" />
              <Skeleton className="h-10 w-20" />
            </CardFooter>
          </Card>
        ))}
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <h3 className="text-lg font-semibold text-red-800">Error loading agents</h3>
        <p className="text-red-600">{error instanceof Error ? error.message : 'Unknown error'}</p>
        <Button 
          onClick={() => refetch()} 
          variant="outline" 
          className="mt-4"
        >
          <RefreshCw className="mr-2 h-4 w-4" /> Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight">Agents</h2>
        <div className="flex gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                {filter ? `Filter: ${filter}` : 'Filter'} 
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => setFilter(null)}>
                All Agents
              </DropdownMenuItem>
              {availableFilters.map((filterOption) => (
                <DropdownMenuItem 
                  key={filterOption}
                  onClick={() => setFilter(filterOption)}
                >
                  {filterOption}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          
          <Button onClick={() => router.push('/agents/create')}>
            <Plus className="mr-2 h-4 w-4" /> Create Agent
          </Button>
        </div>
      </div>

      {filteredAgents.length === 0 ? (
        <div className="text-center p-12 border border-dashed rounded-lg">
          <h3 className="font-medium text-lg mb-2">No agents found</h3>
          <p className="text-gray-500 mb-4">
            {filter 
              ? `No agents match the filter "${filter}"` 
              : "Get started by creating your first agent"}
          </p>
          <Button onClick={() => router.push('/agents/create')}>
            <Plus className="mr-2 h-4 w-4" /> Create Agent
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAgents.map((agent) => (
            <Card key={agent.id} className="shadow-md hover:shadow-lg transition-shadow">
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <CardTitle className="flex items-center gap-2">
                    {agent.name}
                    <Badge 
                      className={`${getStatusColor(agent.status)} text-white`}
                    >
                      {agent.status}
                    </Badge>
                  </CardTitle>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                      <DropdownMenuItem onClick={() => handleViewAgent(agent.id)}>
                        View Details
                      </DropdownMenuItem>
                      {agent.status === 'active' ? (
                        <DropdownMenuItem onClick={() => handleStopAgent(agent.id)}>
                          Stop Agent
                        </DropdownMenuItem>
                      ) : (
                        <DropdownMenuItem onClick={() => handleStartAgent(agent.id)}>
                          Start Agent
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                <CardDescription>{agent.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center mb-2 text-sm text-gray-500">
                  <Activity className="h-4 w-4 mr-1" />
                  Last active: {new Date(agent.lastActive).toLocaleString()}
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  <Badge variant="outline">{agent.type}</Badge>
                  <Badge variant="outline">{agent.protocol}</Badge>
                  {agent.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">{tag}</Badge>
                  ))}
                </div>
                <div className="mt-3">
                  <h4 className="text-sm font-semibold mb-1">Capabilities:</h4>
                  <div className="flex flex-wrap gap-1">
                    {agent.capabilities.slice(0, 3).map((capability) => (
                      <TooltipProvider key={capability}>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Badge variant="secondary" className="cursor-help">
                              {capability}
                            </Badge>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>{capability}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    ))}
                    {agent.capabilities.length > 3 && (
                      <Badge variant="secondary">
                        +{agent.capabilities.length - 3} more
                      </Badge>
                    )}
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => handleViewAgent(agent.id)}
                >
                  View Details
                </Button>
                {agent.status === 'active' ? (
                  <Button 
                    variant="destructive" 
                    size="sm"
                    onClick={() => handleStopAgent(agent.id)}
                  >
                    <Square className="mr-2 h-4 w-4" /> Stop
                  </Button>
                ) : (
                  <Button
                    variant="default"
                    size="sm"
                    onClick={() => handleStartAgent(agent.id)}
                  >
                    <Play className="mr-2 h-4 w-4" /> Start
                  </Button>
                )}
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}