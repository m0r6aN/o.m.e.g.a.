// src/hooks/use-mcp.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { Tool, Agent } from '@/types';
import { toast } from 'react-hot-toast';

// API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

// Fetch agents from MCP registry
async function fetchAgents(): Promise<Agent[]> {
  const response = await fetch(`${API_BASE_URL}/api/agents`);
  if (!response.ok) {
    throw new Error('Failed to fetch agents');
  }
  return response.json();
}

// Fetch tools from MCP registry
async function fetchTools(): Promise<Tool[]> {
  const response = await fetch(`${API_BASE_URL}/api/tools`);
  if (!response.ok) {
    throw new Error('Failed to fetch tools');
  }
  return response.json();
}

// Call a tool via MCP
async function callTool({ toolId, capability, parameters }: {
  toolId: string;
  capability: string;
  parameters: Record<string, any>;
}): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/tools/call`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ toolId, capability, parameters }),
  });
  if (!response.ok) {
    throw new Error('Failed to call tool');
  }
  return response.json();
}

// Original useMcp hook for backward compatibility
export function useMcp() {
  // Discover agents
  const discoverAgents = useQuery<Agent[], Error>({
    queryKey: ['agents'],
    queryFn: fetchAgents,
    staleTime: 5 * 60 * 1000
  });

  // Discover tools
  const discoverTools = useQuery<Tool[], Error>({
    queryKey: ['tools'],
    queryFn: fetchTools,
    staleTime: 5 * 60 * 1000
  });

  // Call a tool
  const callToolMutation = useMutation({
    mutationFn: callTool,
    onSuccess: () => {
      toast("Tool call executed successfully");
    },
    onError: (error) => {
      toast(error instanceof Error ? error.message : 'Failed to call tool');
    }
  });

  const subscribeToTaskUpdates = (callback: (taskId: string, status: string) => void) => {
    const ws = new WebSocket(`${API_BASE_URL.replace('http', 'ws')}/ws/tasks`);
    ws.onmessage = (event) => {
      const { taskId, status } = JSON.parse(event.data);
      callback(taskId, status);
    };
    return () => ws.close();
  };
  
  return {
    discoverAgents,
    discoverTools,
    callTool: callToolMutation.mutate,
    callToolStatus: callToolMutation.status,
    callToolError: callToolMutation.error,
    subscribeToTaskUpdates,
  };
}

// Discover all agents (new individual hook)
export function useDiscoverAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: fetchAgents,
    staleTime: 5 * 60 * 1000
  });
}

// Get a specific agent by ID
export function useAgentById(agentId: string) {
  return useQuery({
    queryKey: ['agent', agentId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch agent details');
      }
      return response.json() as Promise<Agent>;
    },
    enabled: !!agentId
  });
}

// Discover all tools (new individual hook)
export function useDiscoverTools() {
  return useQuery({
    queryKey: ['tools'],
    queryFn: fetchTools,
    staleTime: 5 * 60 * 1000
  });
}

// Get a specific tool by ID
export function useToolById(toolId: string) {
  return useQuery({
    queryKey: ['tool', toolId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/tools/${toolId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch tool details');
      }
      return response.json() as Promise<Tool>;
    },
    enabled: !!toolId
  });
}

// Register a new agent
export function useRegisterAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (agentData: Partial<Agent>) => {
      const response = await fetch(`${API_BASE_URL}/api/agents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(agentData),
      });
      if (!response.ok) {
        throw new Error('Failed to register agent');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      toast("Agent has been registered successfully");
    },
    onError: (error) => {
      toast(error instanceof Error ? error.message : 'Failed to register agent');
    }
  });
}

// Register a new tool
export function useRegisterTool() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (toolData: Partial<Tool>) => {
      const response = await fetch(`${API_BASE_URL}/api/tools`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(toolData),
      });
      if (!response.ok) {
        throw new Error('Failed to register tool');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tools'] });
      toast("Tool has been registered successfully");
    },
    onError: (error) => {
      toast(error instanceof Error ? error.message : 'Failed to register tool');
    }
  });
}

// Unregister an agent
export function useUnregisterAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (agentId: string) => {
      const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to unregister agent');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      toast("Agent has been unregistered successfully");
    },
    onError: (error) => {
      toast(error instanceof Error ? error.message : 'Failed to unregister agent');
    }
  });
}

// Unregister a tool
export function useUnregisterTool() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (toolId: string) => {
      const response = await fetch(`${API_BASE_URL}/api/tools/${toolId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to unregister tool');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tools'] });
      toast("Tool has been unregistered successfully");
    },
    onError: (error) => {
      toast(error instanceof Error ? error.message : 'Failed to unregister tool');
    }
  });
}

// Call a tool
export function useCallTool() {
  return useMutation({
    mutationFn: callTool,
    onSuccess: () => {
      toast("Tool call executed successfully");
    },
    onError: (error) => {
      toast(error instanceof Error ? error.message : 'Failed to call tool');
    }
  });
}

// Start an agent
export function useStartAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (agentId: string) => {
      const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}/start`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to start agent');
      }
      return response.json();
    },
    onSuccess: (_, agentId) => {
      queryClient.invalidateQueries({ queryKey: ['agent', agentId] });
      toast("Agent started successfully");
    },
    onError: (error) => {
      toast(error instanceof Error ? error.message : 'Failed to start agent');
    }
  });
}

// Stop an agent
export function useStopAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (agentId: string) => {
      const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}/stop`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to stop agent');
      }
      return response.json();
    },
    onSuccess: (_, agentId) => {
      queryClient.invalidateQueries({ queryKey: ['agent', agentId] });
      toast("Agent stopped successfully");
    },
    onError: (error) => {
      toast(error instanceof Error ? error.message : 'Failed to stop agent');
    }
  });
}

// Get agent tasks
export function useAgentTasks(agentId: string) {
  return useQuery({
    queryKey: ['agent-tasks', agentId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/agents/${agentId}/tasks`);
      if (!response.ok) {
        throw new Error('Failed to fetch agent tasks');
      }
      return response.json();
    },
    enabled: !!agentId
  });
}

// Filter tools by capability
export function useToolsByCapability(capability: string) {
  const { data: tools, isLoading, error } = useDiscoverTools();
  
  const filteredTools = tools?.filter(tool => 
    tool.capabilities.some(cap => cap.name === capability)
  ) || [];
  
  return {
    data: filteredTools,
    isLoading,
    error
  };
}

// Filter tools by tag
export function useToolsByTag(tag: string) {
  const { data: tools, isLoading, error } = useDiscoverTools();
  
  const filteredTools = tools?.filter(tool => 
    tool.tags.includes(tag)
  ) || [];
  
  return {
    data: filteredTools,
    isLoading,
    error
  };
}

// Get all unique tags from tools
export function useToolTags() {
  const { data: tools, isLoading, error } = useDiscoverTools();
  
  const tags = new Set<string>();
  
  if (tools) {
    tools.forEach(tool => {
      tool.tags.forEach(tag => tags.add(tag));
    });
  }
  
  return {
    data: Array.from(tags),
    isLoading,
    error
  };
}

// WebSocket subscription for real-time updates
export function useTaskUpdates(callback: (taskId: string, status: string) => void) {
  useEffect(() => {
    const ws = new WebSocket(`${API_BASE_URL.replace('http', 'ws')}/ws/tasks`);
    
    ws.onmessage = (event) => {
      const { taskId, status } = JSON.parse(event.data);
      callback(taskId, status);
    };
    
    return () => {
      ws.close();
    };
  }, [callback]);
}