// src/components/agents/agent-detail.tsx
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Card, 
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle 
} from '@/components/ui/card';
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from '@/components/ui/tabs';
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Activity,
  ArrowLeft,
  Play,
  Square,
  Trash2,
  RefreshCw,
  Edit,
  Code,
  History,
  Settings,
  Server,
  Link,
  Terminal
} from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

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
  endpoints: {
    base_url: string;
    a2a_card?: string;
    mcp_endpoint?: string;
  };
  metadata: {
    created: string;
    updated: string;
    author: string;
    processor: string;
    memory: string;
  };
  logs: {
    timestamp: string;
    level: 'info' | 'warn' | 'error';
    message: string;
  }[];
  connections: {
    id: string;
    name: string;
    type: string;
    direction: 'inbound' | 'outbound';
    status: 'active' | 'inactive';
  }[];
}

// Define tasks interface
interface Task {
  id: string;
  agentId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created: string;
  updated: string;
  input: Record<string, any>;
  output?: Record<string, any>;
}

// Fetch a single agent by ID
async function fetchAgent(id: string): Promise<Agent> {
  const response = await fetch(`/api/agents/${id}`);
  if (!response.ok) {
    throw new Error('Failed to fetch agent details');
  }
  return response.json();
}

// Fetch tasks for an agent
async function fetchAgentTasks(id: string): Promise<Task[]> {
  const response = await fetch(`/api/agents/${id}/tasks`);
  if (!response.ok) {
    throw new Error('Failed to fetch agent tasks');
  }
  return response.json();
}

interface AgentDetailProps {
  agentId: string;
}

export function AgentDetail({ agentId }: AgentDetailProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('overview');
  
  // Fetch agent details
  const { 
    data: agent, 
    isLoading: isAgentLoading, 
    isError: isAgentError,
    error: agentError,
    refetch: refetchAgent 
  } = useQuery({
    queryKey: ['agent', agentId],
    queryFn: () => fetchAgent(agentId),
  });

  // Fetch agent tasks
  const {
    data: tasks,
    isLoading: isTasksLoading,
    isError: isTasksError,
    error: tasksError,
    refetch: refetchTasks
  } = useQuery({
    queryKey: ['agent-tasks', agentId],
    queryFn: () => fetchAgentTasks(agentId),
  });

  // Start agent mutation
  const startAgentMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`/api/agents/${agentId}/start`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to start agent');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent', agentId] });
    },
  });

  // Stop agent mutation
  const stopAgentMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`/api/agents/${agentId}/stop`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to stop agent');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent', agentId] });
    },
  });

  // Delete agent mutation
  const deleteAgentMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`/api/agents/${agentId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to delete agent');
      }
      return response.json();
    },
    onSuccess: () => {
      router.push('/agents');
    },
  });

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
  if (isAgentLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <Skeleton className="h-8 w-1/3" />
        </div>
        
        <Card>
          <CardHeader>
            <Skeleton className="h-8 w-1/4 mb-2" />
            <Skeleton className="h-4 w-3/4" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  if (isAgentError) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
          <h3 className="text-lg font-semibold text-red-800">Error loading agent details</h3>
          <p className="text-red-600">
            {agentError instanceof Error ? agentError.message : 'Unknown error'}
          </p>
          <Button 
            onClick={() => refetchAgent()} 
            variant="outline" 
            className="mt-4"
          >
            <RefreshCw className="mr-2 h-4 w-4" /> Try Again
          </Button>
        </div>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        
        <div className="p-6 bg-amber-50 border border-amber-200 rounded-lg">
          <h3 className="text-lg font-semibold text-amber-800">Agent not found</h3>
          <p className="text-amber-600">
            The agent you're looking for doesn't exist or has been removed.
          </p>
          <Button 
            onClick={() => router.push('/agents')} 
            variant="outline" 
            className="mt-4"
          >
            View All Agents
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-center">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              {agent.name}
              <Badge 
                className={`${getStatusColor(agent.status)} text-white`}
              >
                {agent.status}
              </Badge>
            </h1>
            <p className="text-gray-500">{agent.description}</p>
          </div>
        </div>
        
        <div className="flex gap-2">
          {agent.status === 'active' ? (
            <Button
              variant="destructive"
              onClick={() => stopAgentMutation.mutate()}
              disabled={stopAgentMutation.isPending}
            >
              {stopAgentMutation.isPending ? (
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Square className="mr-2 h-4 w-4" />
              )}
              Stop Agent
            </Button>
          ) : (
            <Button
              variant="default"
              onClick={() => startAgentMutation.mutate()}
              disabled={startAgentMutation.isPending}
            >
              {startAgentMutation.isPending ? (
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Play className="mr-2 h-4 w-4" />
              )}
              Start Agent
            </Button>
          )}
          
          <Button
            variant="outline"
            onClick={() => router.push(`/agents/${agentId}/edit`)}
          >
            <Edit className="mr-2 h-4 w-4" />
            Edit
          </Button>
          
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" className="text-red-500 border-red-200">
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete the agent "{agent.name}" and all its associated data.
                  This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  className="bg-red-500 hover:bg-red-600"
                  onClick={() => deleteAgentMutation.mutate()}
                  disabled={deleteAgentMutation.isPending}
                >
                  {deleteAgentMutation.isPending ? 'Deleting...' : 'Delete'}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-5 w-full md:w-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="tasks">Tasks</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
          <TabsTrigger value="connections">Connections</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>
        
        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agent Information</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Type</h3>
                  <p className="mt-1">{agent.type}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Protocol</h3>
                  <p className="mt-1">{agent.protocol}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Version</h3>
                  <p className="mt-1">{agent.version}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Last Active</h3>
                  <p className="mt-1">{new Date(agent.lastActive).toLocaleString()}</p>
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {agent.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">{tag}</Badge>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Capabilities</h3>
                <div className="flex flex-wrap gap-2">
                  {agent.capabilities.map((capability) => (
                    <Badge key={capability} variant="outline">{capability}</Badge>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Metadata</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <span className="text-xs text-gray-500">Created</span>
                    <p className="text-sm">{new Date(agent.metadata.created).toLocaleString()}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">Updated</span>
                    <p className="text-sm">{new Date(agent.metadata.updated).toLocaleString()}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">Author</span>
                    <p className="text-sm">{agent.metadata.author}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">Processor</span>
                    <p className="text-sm">{agent.metadata.processor}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">Memory</span>
                    <p className="text-sm">{agent.metadata.memory}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Endpoints</CardTitle>
              <CardDescription>Connection details for this agent</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                  <div className="flex items-center">
                    <Server className="h-4 w-4 mr-2 text-gray-500" />
                    <span className="text-sm font-medium">Base URL</span>
                  </div>
                  <code className="bg-gray-100 px-2 py-1 rounded text-sm">
                    {agent.endpoints.base_url}
                  </code>
                </div>
                
                {agent.endpoints.a2a_card && (
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                    <div className="flex items-center">
                      <Link className="h-4 w-4 mr-2 text-gray-500" />
                      <span className="text-sm font-medium">A2A Agent Card</span>
                    </div>
                    <code className="bg-gray-100 px-2 py-1 rounded text-sm">
                      {agent.endpoints.a2a_card}
                    </code>
                  </div>
                )}
                
                {agent.endpoints.mcp_endpoint && (
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                    <div className="flex items-center">
                      <Terminal className="h-4 w-4 mr-2 text-gray-500" />
                      <span className="text-sm font-medium">MCP Endpoint</span>
                    </div>
                    <code className="bg-gray-100 px-2 py-1 rounded text-sm">
                      {agent.endpoints.mcp_endpoint}
                    </code>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        {/* Tasks Tab */}
        <TabsContent value="tasks" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Recent Tasks</CardTitle>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => refetchTasks()}
                disabled={isTasksLoading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isTasksLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {isTasksLoading ? (
                <div className="space-y-4">
                  {Array.from({ length: 3 }).map((_, index) => (
                    <div key={index} className="p-4 border rounded-md">
                      <div className="flex justify-between mb-4">
                        <Skeleton className="h-5 w-1/3" />
                        <Skeleton className="h-5 w-1/4" />
                      </div>
                      <Skeleton className="h-4 w-full mb-2" />
                      <Skeleton className="h-4 w-3/4" />
                    </div>
                  ))}
                </div>
              ) : isTasksError ? (
                <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
                  <h3 className="text-lg font-semibold text-red-800">Error loading tasks</h3>
                  <p className="text-red-600">
                    {tasksError instanceof Error ? tasksError.message : 'Unknown error'}
                  </p>
                  <Button 
                    onClick={() => refetchTasks()} 
                    variant="outline" 
                    className="mt-4"
                  >
                    <RefreshCw className="mr-2 h-4 w-4" /> Try Again
                  </Button>
                </div>
              ) : !tasks || tasks.length === 0 ? (
                <div className="text-center p-12 border border-dashed rounded-lg">
                  <h3 className="font-medium text-lg mb-2">No tasks found</h3>
                  <p className="text-gray-500 mb-4">
                    This agent hasn't processed any tasks yet.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {tasks.map((task) => (
                    <div 
                      key={task.id} 
                      className="p-4 border rounded-md hover:border-primary hover:bg-gray-50 transition-colors cursor-pointer"
                      onClick={() => router.push(`/tasks/${task.id}`)}
                    >
                      <div className="flex justify-between mb-2">
                        <div className="font-medium">Task ID: {task.id.slice(0, 8)}...</div>
                        <div className="flex items-center">
                          <Badge 
                            className={
                              task.status === 'completed' ? 'bg-green-100 text-green-800' :
                              task.status === 'failed' ? 'bg-red-100 text-red-800' :
                              task.status === 'running' ? 'bg-blue-100 text-blue-800' :
                              'bg-yellow-100 text-yellow-800'
                            }
                          >
                            {task.status}
                          </Badge>
                        </div>
                      </div>
                      <div className="text-sm text-gray-500 flex justify-between">
                        <span>Created: {new Date(task.created).toLocaleString()}</span>
                        <span>Updated: {new Date(task.updated).toLocaleString()}</span>
                      </div>
                      <div className="mt-2 text-sm">
                        <code className="bg-gray-100 p-2 block rounded text-xs overflow-hidden text-ellipsis">
                          {JSON.stringify(task.input, null, 2).slice(0, 100)}...
                        </code>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
            <CardFooter>
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => router.push(`/agents/${agentId}/tasks`)}
              >
                View All Tasks
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        {/* Logs Tab */}
        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Agent Logs</CardTitle>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => refetchAgent()}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {!agent.logs || agent.logs.length === 0 ? (
                <div className="text-center p-12 border border-dashed rounded-lg">
                  <h3 className="font-medium text-lg mb-2">No logs available</h3>
                  <p className="text-gray-500 mb-4">
                    No log entries have been recorded for this agent.
                  </p>
                </div>
              ) : (
                <div className="bg-black text-green-400 p-4 rounded-md font-mono text-sm overflow-y-auto max-h-96">
                  {agent.logs.map((log, index) => (
                    <div key={index} className="mb-1">
                      <span className="opacity-70">[{new Date(log.timestamp).toLocaleString()}]</span>{' '}
                      <span 
                        className={
                          log.level === 'error' ? 'text-red-400' :
                          log.level === 'warn' ? 'text-yellow-400' :
                          'text-green-400'
                        }
                      >
                        [{log.level.toUpperCase()}]
                      </span>{' '}
                      <span>{log.message}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
            <CardFooter>
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => router.push(`/agents/${agentId}/logs`)}
              >
                View Full Logs
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        {/* Connections Tab */}
        <TabsContent value="connections" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agent Connections</CardTitle>
              <CardDescription>
                View connections between this agent and other agents or tools
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!agent.connections || agent.connections.length === 0 ? (
                <div className="text-center p-12 border border-dashed rounded-lg">
                  <h3 className="font-medium text-lg mb-2">No connections</h3>
                  <p className="text-gray-500 mb-4">
                    This agent doesn't have any connections to other agents or tools.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {agent.connections.map((connection) => (
                    <div 
                      key={connection.id} 
                      className="p-4 border rounded-md hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex justify-between mb-2">
                        <div className="font-medium">{connection.name}</div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{connection.type}</Badge>
                          <Badge 
                            variant={connection.status === 'active' ? 'default' : 'secondary'}
                          >
                            {connection.status}
                          </Badge>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <Badge 
                          variant="outline" 
                          className={
                            connection.direction === 'inbound' 
                              ? 'border-blue-200 text-blue-700'
                              : 'border-purple-200 text-purple-700'
                          }
                        >
                          {connection.direction === 'inbound' ? '← Inbound' : 'Outbound →'}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agent Settings</CardTitle>
              <CardDescription>
                Configure settings for this agent
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid gap-2">
                  <label className="text-sm font-medium">Agent Name</label>
                  <input
                    type="text"
                    className="p-2 border rounded-md"
                    defaultValue={agent.name}
                    disabled
                  />
                  <p className="text-xs text-gray-500">
                    To change the agent name, use the Edit button
                  </p>
                </div>
                
                <div className="grid gap-2">
                  <label className="text-sm font-medium">Processor Allocation</label>
                  <select
                    className="p-2 border rounded-md"
                    defaultValue={agent.metadata.processor}
                    disabled
                  >
                    <option value="standard">Standard (1 CPU Core)</option>
                    <option value="enhanced">Enhanced (2 CPU Cores)</option>
                    <option value="premium">Premium (4 CPU Cores)</option>
                  </select>
                </div>
                
                <div className="grid gap-2">
                  <label className="text-sm font-medium">Memory Allocation</label>
                  <select
                    className="p-2 border rounded-md"
                    defaultValue={agent.metadata.memory}
                    disabled
                  >
                    <option value="512MB">512 MB RAM</option>
                    <option value="1GB">1 GB RAM</option>
                    <option value="2GB">2 GB RAM</option>
                    <option value="4GB">4 GB RAM</option>
                  </select>
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => router.push(`/agents/${agentId}/edit`)}
              >
                <Edit className="mr-2 h-4 w-4" />
                Edit Agent Settings
              </Button>
            </CardFooter>
          </Card>
          
          <Card className="border-red-200">
            <CardHeader>
              <CardTitle className="text-red-600">Danger Zone</CardTitle>
              <CardDescription>
                Irreversible actions for this agent
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive" className="w-full">
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete Agent
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This will permanently delete the agent "{agent.name}" and all its associated data.
                      This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      className="bg-red-500 hover:bg-red-600"
                      onClick={() => deleteAgentMutation.mutate()}
                      disabled={deleteAgentMutation.isPending}
                    >
                      {deleteAgentMutation.isPending ? 'Deleting...' : 'Delete'}
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}