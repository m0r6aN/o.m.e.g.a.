// src/components/workflows/workflow-builder.tsx
'use client';

import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import ReactFlow, {
  ReactFlowProvider,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Panel,
  MarkerType,
  NodeTypes,
  ReactFlowInstance,
  Edge as ReactFlowEdge,
  Node as ReactFlowNode
} from 'reactflow';
import 'reactflow/dist/style.css';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { toast } from 'react-hot-toast';
import {
  ArrowLeft,
  Save,
  Play,
  Trash2,
  Settings,
  FileDown,
  FileUp,
  User,
  MessageSquare,
  RefreshCw,
  Wrench,
  Bot,
  Code,
  CheckCircle,
  AlertCircle,
  Circle,
} from 'lucide-react';
import { useMcp } from '@/hooks/use-mcp';
import { AgentNode, ToolNode, TriggerNode, OutputNode } from './nodes';
import { useWorkflowExecution } from '@/hooks/use-workflow-execution';
import { config } from '@/lib/env-config';

// Configuration constants
const CONFIG = {
  colors: {
    agent: '#3B82F6',
    tool: '#10B981',
    trigger: '#8B5CF6',
    output: '#F59E0B',
    default: '#9CA3AF',
  },
  nodeTypes: {
    agentNode: AgentNode,
    toolNode: ToolNode,
    triggerNode: TriggerNode,
    outputNode: OutputNode,
  } as NodeTypes,
  edge: {
    type: 'smoothstep',
    markerEnd: { type: MarkerType.ArrowClosed },
    animated: true,
  },
};

// Define interfaces
interface Agent {
  id: string;
  name: string;
  description: string;
  type: string;
  capabilities: string[];
  status: 'active' | 'inactive';
}

interface ToolCapability {
  name: string;
  description: string;
  parameters: Record<string, { type: string; description: string; required?: boolean }>;
}

interface Tool {
  id: string;
  name: string;
  description: string;
  capabilities: ToolCapability[];
  status: 'active' | 'inactive';
}

interface WorkflowNodeData {
  label: string;
  entityId: string;
  capability?: string;
  params?: Record<string, any>;
  status?: 'pending' | 'running' | 'completed' | 'failed';
}

interface WorkflowNode extends ReactFlowNode<WorkflowNodeData> {
  type: 'agentNode' | 'toolNode' | 'triggerNode' | 'outputNode';
}

type WorkflowEdge = ReactFlowEdge & {
  // You can specify or override properties here
  type: 'smoothstep'; // Ensure the type is 'smoothstep'
  markerEnd: { type: MarkerType }; // Specify the markerEnd structure
  animated: boolean; // Ensure animated is boolean (or maybe always true?)
  // Add any other custom properties specific to your workflow edges, if any
};

interface Workflow {
  id: string;
  name: string;
  description: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  createdAt: string;
  updatedAt: string;
  status: 'draft' | 'active' | 'inactive';
}

// Workflow form schema
const workflowFormSchema = z.object({
  name: z.string().min(3, 'Workflow name must be at least 3 characters.'),
  description: z.string().min(10, 'Description must be at least 10 characters.'),
});

type WorkflowFormValues = z.infer<typeof workflowFormSchema>;

// Node form schema
const nodeFormSchema = z.object({
  id: z.string().optional(),
  type: z.enum(['agentNode', 'toolNode', 'triggerNode', 'outputNode']),
  label: z.string().min(3, 'Node label must be at least 3 characters.'),
  entityId: z.string().min(1, 'You must select an entity.'),
  capability: z.string().optional(),
  params: z.record(z.string(), z.any()).optional(),
  position: z.object({ x: z.number(), y: z.number() }).optional(),
});

type NodeFormValues = z.infer<typeof nodeFormSchema>;

// API functions
async function fetchWorkflow(id: string): Promise<Workflow> {
  const response = await fetch(`/api/workflows/${id}`);
  if (!response.ok) {
    throw new Error('Failed to fetch workflow');
  }
  return response.json();
}

async function saveWorkflow(workflow: Partial<Workflow>): Promise<Workflow> {
  const method = workflow.id ? 'PUT' : 'POST';
  const url = workflow.id ? `/api/workflows/${workflow.id}` : '/api/workflows';
  const response = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(workflow),
  });
  if (!response.ok) {
    throw new Error('Failed to save workflow');
  }
  return response.json();
}

async function executeWorkflow(id: string): Promise<{ executionId: string }> {
  const response = await fetch(`/api/workflows/${id}/execute`, { method: 'POST' });
  if (!response.ok) {
    throw new Error('Failed to execute workflow');
  }
  return response.json();
}

// Utility to detect cycles in the workflow graph
function hasCycle(nodes: WorkflowNode[], edges: WorkflowEdge[]): boolean {
  const graph = new Map<string, string[]>();
  nodes.forEach((node) => graph.set(node.id, []));
  edges.forEach((edge) => graph.get(edge.source)?.push(edge.target));

  const visited = new Set<string>();
  const recStack = new Set<string>();

  function dfs(nodeId: string): boolean {
    visited.add(nodeId);
    recStack.add(nodeId);

    const neighbors = graph.get(nodeId) || [];
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor) && dfs(neighbor)) {
        return true;
      } else if (recStack.has(neighbor)) {
        return true;
      }
    }

    recStack.delete(nodeId);
    return false;
  }

  for (const nodeId of graph.keys()) {
    if (!visited.has(nodeId) && dfs(nodeId)) {
      return true;
    }
  }
  return false;
}

// Validate workflow
function validateWorkflow(nodes: WorkflowNode[], edges: WorkflowEdge[]): string[] {
  const errors: string[] = [];
  if (!nodes.some((node) => node.type === 'triggerNode')) {
    errors.push('Workflow must have at least one trigger node.');
  }
  if (hasCycle(nodes, edges)) {
    errors.push('Workflow contains cycles, which are not allowed.');
  }
  if (!nodes.some((node) => node.type === 'outputNode')) {
    errors.push('Workflow must have at least one output node.');
  }
  return errors;
}

interface WorkflowBuilderProps {
  workflowId?: string;
}

// Wrap the WorkflowBuilderContent in ReactFlowProvider
export function WorkflowBuilder({ workflowId }: WorkflowBuilderProps) {
  return (
    <ReactFlowProvider>
      <WorkflowBuilderContent workflowId={workflowId} />
    </ReactFlowProvider>
  );
}

function WorkflowBuilderContent({ workflowId }: WorkflowBuilderProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<WorkflowNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isWorkflowDialogOpen, setIsWorkflowDialogOpen] = useState(false);
  const [isNodeDialogOpen, setIsNodeDialogOpen] = useState(false);
  const [selectedNodeType, setSelectedNodeType] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [workflowName, setWorkflowName] = useState('Untitled Workflow');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [workflowStatus, setWorkflowStatus] = useState<'draft' | 'active' | 'inactive'>('draft');
  const [executionId, setExecutionId] = useState<string | null>(null);

  const { discoverAgents, discoverTools } = useMcp();

  // Fetch workflow data
  const {
    data: workflow,
    isLoading: isWorkflowLoading,
    error: workflowError,
  } = useQuery({
    queryKey: ['workflow', workflowId],
    queryFn: () => fetchWorkflow(workflowId!),
    enabled: !!workflowId,
  });

  // Workflow form
  const workflowForm = useForm<WorkflowFormValues>({
    resolver: zodResolver(workflowFormSchema),
    defaultValues: { name: workflowName, description: workflowDescription },
  });

  // Node form
  const nodeForm = useForm<NodeFormValues>({
    resolver: zodResolver(nodeFormSchema),
    defaultValues: {
      type: 'agentNode',
      label: '',
      entityId: '',
      position: { x: 100, y: 100 },
    },
  });

  // Mutations
  const saveWorkflowMutation = useMutation({
    mutationFn: saveWorkflow,
    onSuccess: (data) => {
      toast.success(`Workflow "${data.name}" saved successfully.`);
      if (!workflowId) {
        router.push(`/workflows/${data.id}`);
      } else {
        queryClient.invalidateQueries({ queryKey: ['workflow', workflowId] });
      }
    },
    onError: (error) => {
      toast.error(`Failed to save workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const executeWorkflowMutation = useMutation({
    mutationFn: () => executeWorkflow(workflowId!),
    onSuccess: (data) => {
      toast.success(`Workflow execution started: ${data.executionId}`);
      router.push(`/workflows/${workflowId}/executions/${data.executionId}`);
    },
    onError: (error) => {
      toast.error(`Failed to execute workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const {
    isConnected: wsConnected,
    lastMessage: wsLastMessage,
    error: wsError,
  } = useWorkflowExecution(executionId, nodes as WorkflowNode[], setNodes);

  // Initialize workflow data
  useEffect(() => {
    if (workflow) {
      setWorkflowName(workflow.name);
      setWorkflowDescription(workflow.description);
      setWorkflowStatus(workflow.status);
      setNodes(workflow.nodes || []);
      setEdges(workflow.edges || []);
      workflowForm.reset({ name: workflow.name, description: workflow.description });
    }
  }, [workflow, workflowForm, setNodes, setEdges]);

  // Handle node connection
  const onConnect = useCallback(
    (params: Connection) =>
      setEdges((eds) => addEdge({ ...params, ...CONFIG.edge }, eds)),
    [setEdges]
  );

  // Handle node click
  const onNodeClick = useCallback(
    (event: React.MouseEvent, node: ReactFlowNode) => {
      setSelectedNode(node as WorkflowNode);
    },
    [setSelectedNode] // Add setSelectedNode dependency
  );

  // Handle drag start
  const onDragStart = useCallback((event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
    setIsDragging(true);
  }, []);

  // Handle drag over
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle drop
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      setIsDragging(false);
      if (!reactFlowInstance || !reactFlowWrapper.current) return;

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const type = event.dataTransfer.getData('application/reactflow');
      if (!type) return;

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      setSelectedNodeType(type);
      nodeForm.reset({ type: undefined, label: '', entityId: '', capability: '' });
      setIsNodeDialogOpen(true);
    },
    [reactFlowInstance, nodeForm]
  );

  // Handle adding node
  const handleAddNode = useCallback(
    (data: NodeFormValues) => {
      const position = data.position || { x: 100, y: 100 };
      const newNode: WorkflowNode = {
        id: data.id || `${data.type}_${Date.now()}`,
        type: data.type,
        position,
        data: {
          label: data.label,
          entityId: data.entityId,
          capability: data.capability,
          params: data.params,
          status: 'pending',
        },
      };
      setNodes((nds) => [...nds, newNode]);
      setIsNodeDialogOpen(false);
    },
    [setNodes]
  );

  // Handle updating node
  const handleUpdateNode = useCallback(
    (data: NodeFormValues) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === data.id
            ? {
              ...node,
              data: {
                ...node.data,
                label: data.label,
                entityId: data.entityId,
                capability: data.capability,
                params: data.params,
              },
            }
            : node
        )
      );
      setSelectedNode(null);
      setIsNodeDialogOpen(false);
    },
    [setNodes]
  );

  // Handle deleting node
  const handleDeleteNode = useCallback(
    (nodeId: string) => {
      setNodes((nds) => nds.filter((node) => node.id !== nodeId));
      setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
      setSelectedNode(null);
    },
    [setNodes, setEdges]
  );

  // Handle saving workflow
  const handleSaveWorkflow = useCallback(
    (data: WorkflowFormValues) => {
      // Use type assertion when calling validateWorkflow
      const errors = validateWorkflow(
        nodes as WorkflowNode[], // Assert nodes type
        edges as WorkflowEdge[]  // Assert edges type
      );
      if (errors.length > 0) {
        errors.forEach((error) => toast.error(error));
        return;
      }
      saveWorkflowMutation.mutate({
        id: workflowId,
        name: data.name,
        description: data.description,
        // Use type assertion when passing to the mutation
        nodes: nodes as WorkflowNode[], // Assert nodes type
        edges: edges as WorkflowEdge[], // Assert edges type
        status: workflowStatus,
      });
      setIsWorkflowDialogOpen(false);
      setWorkflowName(data.name);
      setWorkflowDescription(data.description);
    },
    [workflowId, nodes, edges, workflowStatus, saveWorkflowMutation]
  );

  // Handle executing workflow
  const handleExecuteWorkflow = useCallback(() => {
    if (!workflowId) {
      toast.error('Please save the workflow before executing.');
      return;
    }

    const errors = validateWorkflow(nodes as WorkflowNode[], edges as WorkflowEdge[]);
    if (errors.length > 0) {
      errors.forEach((error) => toast.error(error));
      return;
    }

    executeWorkflowMutation.mutate(undefined, {
      onSuccess: (data) => {
        toast.success(`Workflow execution started: ${data.executionId}`);
        setExecutionId(data.executionId);

        // Set all nodes to pending status
        setNodes((nds) =>
          nds.map((node) => ({
            ...node,
            data: {
              ...node.data,
              status: 'pending',
              message: undefined,
            },
          }))
        );
      },
    });
  }, [workflowId, nodes, edges, executeWorkflowMutation, setNodes]);

  // Handle importing workflow
  const handleImportWorkflow = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const content = e.target?.result as string;
          const importedWorkflow = JSON.parse(content);
          setWorkflowName(importedWorkflow.name || 'Imported Workflow');
          setWorkflowDescription(importedWorkflow.description || '');
          setWorkflowStatus(importedWorkflow.status || 'draft');
          setNodes(importedWorkflow.nodes || []);
          setEdges(importedWorkflow.edges || []);
          toast.success(`Workflow imported: ${importedWorkflow.name}`);
        } catch (error) {
          toast.error(`Failed to import workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      };
      reader.readAsText(file);
      event.target.value = '';
    },
    [setNodes, setEdges]
  );

  // Handle validating workflow
  const handleValidateWorkflow = useCallback(() => {
    const errors = validateWorkflow(nodes as WorkflowNode[], edges as WorkflowEdge[]);
    if (errors.length === 0) {
      toast.success('Workflow is valid!');
    } else {
      errors.forEach((error) => toast.error(error));
    }
  }, [nodes, edges]);

  // Loading state
  if (isWorkflowLoading || discoverAgents.isLoading || discoverTools.isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => router.back()} aria-label="Go back">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <Skeleton className="h-8 w-1/3" />
          </div>
          <Skeleton className="h-10 w-24" />
        </div>
        <div className="h-[600px] border rounded-lg">
          <div className="flex h-full items-center justify-center">
            <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (workflowError || discoverAgents.error || discoverTools.error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.back()} aria-label="Go back">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <h1 className="text-3xl font-bold">Workflow Builder</h1>
        </div>
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
          <h3 className="text-lg font-semibold text-red-800">Error loading data</h3>
          <p className="text-red-600">
            {workflowError instanceof Error
              ? workflowError.message
              : discoverAgents.error instanceof Error
                ? discoverAgents.error.message
                : discoverTools.error instanceof Error
                  ? discoverTools.error.message
                  : 'Unknown error'}
          </p>
          <Button
            onClick={() => window.location.reload()}
            variant="outline"
            className="mt-4"
            aria-label="Try again"
          >
            <RefreshCw className="mr-2 h-4 w-4" /> Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.back()} aria-label="Go back">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold">{workflowName}</h1>
            {workflowDescription && <p className="text-gray-500">{workflowDescription}</p>}
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleValidateWorkflow}
            aria-label="Validate workflow"
          >
            <CheckCircle className="mr-2 h-4 w-4" />
            Validate
          </Button>
          <Button
            variant="outline"
            onClick={() => setIsWorkflowDialogOpen(true)}
            aria-label="Workflow settings"
          >
            <Settings className="mr-2 h-4 w-4" />
            Settings
          </Button>
          <Button
            variant="default"
            onClick={handleExecuteWorkflow}
            disabled={!workflowId || executeWorkflowMutation.isPending}
            aria-label="Execute workflow"
          >
            {executeWorkflowMutation.isPending ? (
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Play className="mr-2 h-4 w-4" />
            )}
            Execute
          </Button>
          <Button
            variant="default"
            onClick={() => {
              workflowForm.reset({ name: workflowName, description: workflowDescription });
              setIsWorkflowDialogOpen(true);
            }}
            aria-label="Save workflow"
          >
            <Save className="mr-2 h-4 w-4" />
            Save
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Components</CardTitle>
              <CardDescription>Drag and drop components to the canvas</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px] pr-4">
                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-medium mb-2">Agents</h3>
                    <div className="space-y-2">
                      {!discoverAgents.data || discoverAgents.data.length === 0 ? (
                        <p className="text-sm text-gray-500">No agents available</p>
                      ) : (
                        discoverAgents.data
                          .filter((agent) => agent.status === 'active')
                          .map((agent) => (
                            <div
                              key={agent.id}
                              className="p-2 border rounded-md cursor-pointer bg-blue-50 hover:bg-blue-100 transition-colors"
                              draggable
                              onDragStart={(event) => onDragStart(event, 'agentNode')}
                              role="button"
                              aria-label={`Add ${agent.name} agent`}
                            >
                              <div className="flex items-center">
                                <Bot className="h-4 w-4 mr-2 text-blue-600" />
                                <span className="font-medium">{agent.name}</span>
                              </div>
                              <p className="text-xs text-gray-500 mt-1 truncate">{agent.description}</p>
                            </div>
                          ))
                      )}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium mb-2">Tools</h3>
                    <div className="space-y-2">
                      {!discoverTools.data || discoverTools.data.length === 0 ? (
                        <p className="text-sm text-gray-500">No tools available</p>
                      ) : (
                        discoverTools.data
                          .filter((tool) => tool.status === 'active')
                          .map((tool) => (
                            <div
                              key={tool.id}
                              className="p-2 border rounded-md cursor-pointer bg-green-50 hover:bg-green-100 transition-colors"
                              draggable
                              onDragStart={(event) => onDragStart(event, 'toolNode')}
                              role="button"
                              aria-label={`Add ${tool.name} tool`}
                            >
                              <div className="flex items-center">
                                <Wrench className="h-4 w-4 mr-2 text-green-600" />
                                <span className="font-medium">{tool.name}</span>
                              </div>
                              <p className="text-xs text-gray-500 mt-1 truncate">{tool.description}</p>
                            </div>
                          ))
                      )}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium mb-2">Triggers</h3>
                    <div className="space-y-2">
                      <div
                        className="p-2 border rounded-md cursor-pointer bg-purple-50 hover:bg-purple-100 transition-colors"
                        draggable
                        onDragStart={(event) => onDragStart(event, 'triggerNode')}
                        role="button"
                        aria-label="Add user input trigger"
                      >
                        <div className="flex items-center">
                          <MessageSquare className="h-4 w-4 mr-2 text-purple-600" />
                          <span className="font-medium">User Input</span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">Start workflow with user input</p>
                      </div>
                      <div
                        className="p-2 border rounded-md cursor-pointer bg-purple-50 hover:bg-purple-100 transition-colors"
                        draggable
                        onDragStart={(event) => onDragStart(event, 'triggerNode')}
                        role="button"
                        aria-label="Add webhook trigger"
                      >
                        <div className="flex items-center">
                          <Code className="h-4 w-4 mr-2 text-purple-600" />
                          <span className="font-medium">Webhook</span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">Trigger from external webhook</p>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium mb-2">Outputs</h3>
                    <div className="space-y-2">
                      <div
                        className="p-2 border rounded-md cursor-pointer bg-amber-50 hover:bg-amber-100 transition-colors"
                        draggable
                        onDragStart={(event) => onDragStart(event, 'outputNode')}
                        role="button"
                        aria-label="Add user response output"
                      >
                        <div className="flex items-center">
                          <User className="h-4 w-4 mr-2 text-amber-600" />
                          <span className="font-medium">User Response</span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">Return output to the user</p>
                      </div>
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="outline" size="sm" onClick={handleExportWorkflow} aria-label="Export workflow">
                <FileDown className="mr-2 h-4 w-4" />
                Export
              </Button>
              <label htmlFor="import-file">
                <Button variant="outline" size="sm" asChild aria-label="Import workflow">
                  <div className="cursor-pointer">
                    <FileUp className="mr-2 h-4 w-4" />
                    Import
                  </div>
                </Button>
              </label>
              <input
                type="file"
                id="import-file"
                className="hidden"
                accept=".json"
                onChange={handleImportWorkflow}
              />
            </CardFooter>
          </Card>
        </div>
        <div className="lg:col-span-4">
          {wsError && (
            <div className="mb-4 p-2 bg-red-50 border border-red-200 rounded-md text-red-700 text-xs">
              <AlertCircle className="h-4 w-4 inline mr-1" />
              Failed to connect to execution WebSocket: {wsError.message}
            </div>
          )}
          {executionId && !wsError && (
            <div className="mb-4 p-2 bg-green-50 border border-green-200 rounded-md text-green-700 text-xs flex items-center">
              {wsConnected ? (
                <>
                  <span className="relative flex h-3 w-3 mr-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                  </span>
                  Connected to execution {executionId}
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin mr-1" />
                  Connecting to execution {executionId}...
                </>
              )}
            </div>
          )}
          <div className="h-[800px] border rounded-lg" ref={reactFlowWrapper}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onInit={setReactFlowInstance}
              onDrop={onDrop}
              onDragOver={onDragOver}
              nodeTypes={CONFIG.nodeTypes}
              fitView
              tabIndex={0}
              aria-label="Workflow builder canvas"
            >
              <Controls />
              <MiniMap />
              <Background gap={12} size={1} />
              <Panel position="top-right" className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => selectedNode && handleDeleteNode(selectedNode.id)}
                  disabled={!selectedNode}
                  aria-label="Delete selected node"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    if (selectedNode) {
                      nodeForm.reset({
                        id: selectedNode.id,
                        type: selectedNode.type,
                        label: selectedNode.data.label,
                        entityId: selectedNode.data.entityId,
                        capability: selectedNode.data.capability,
                        params: selectedNode.data.params,
                      });
                      setIsNodeDialogOpen(true);
                    }
                  }}
                  disabled={!selectedNode}
                  aria-label="Edit selected node"
                >
                  <Settings className="mr-2 h-4 w-4" />
                  Edit
                </Button>
              </Panel>
              // Add a completion panel that shows when execution is done
              // Add this as a conditional panel in ReactFlow
              {wsLastMessage && (wsLastMessage.status === 'completed' || wsLastMessage.status === 'failed') && (
                <Panel position="top-center" className="bg-white p-3 rounded-md shadow-lg border">
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-2">
                      {wsLastMessage.status === 'completed' ? (
                        <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                      ) : (
                        <Circle className="h-5 w-5 text-red-500 mr-2" />
                      )}
                      <span className="font-medium">
                        Workflow execution {wsLastMessage.status === 'completed' ? 'completed' : 'failed'}
                      </span>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push(`/workflows/${workflowId}/executions/${executionId}`)}
                    >
                      View Execution Details
                    </Button>
                  </div>
                </Panel>
              )}
            </ReactFlow>
          </div>
        </div>
      </div>

      {/* Workflow Settings Dialog */}
      <Dialog open={isWorkflowDialogOpen} onOpenChange={setIsWorkflowDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Workflow Settings</DialogTitle>
            <DialogDescription>Configure your workflow properties</DialogDescription>
          </DialogHeader>
          <Form {...workflowForm}>
            <form onSubmit={workflowForm.handleSubmit(handleSaveWorkflow)}>
              <div className="space-y-4 py-4">
                <FormField
                  control={workflowForm.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Workflow Name</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="Enter workflow name" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={workflowForm.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description</FormLabel>
                      <FormControl>
                        <Textarea
                          {...field}
                          placeholder="Enter workflow description"
                          rows={3}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <div>
                  <FormLabel>Status</FormLabel>
                  <Select
                    value={workflowStatus}
                    onValueChange={(value: 'draft' | 'active' | 'inactive') =>
                      setWorkflowStatus(value)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="draft">Draft</SelectItem>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="inactive">Inactive</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <DialogClose asChild>
                  <Button type="button" variant="outline" aria-label="Cancel">
                    Cancel
                  </Button>
                </DialogClose>
                <Button
                  type="submit"
                  disabled={saveWorkflowMutation.isPending}
                  aria-label="Save workflow"
                >
                  {saveWorkflowMutation.isPending ? (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    'Save Workflow'
                  )}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      {/* Node Settings Dialog */}
      <Dialog open={isNodeDialogOpen} onOpenChange={setIsNodeDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>{selectedNode ? 'Edit Node' : 'Add New Node'}</DialogTitle>
            <DialogDescription>Configure the node properties</DialogDescription>
          </DialogHeader>
          <Form {...nodeForm}>
            <form onSubmit={nodeForm.handleSubmit(selectedNode ? handleUpdateNode : handleAddNode)}>
              <div className="space-y-4 py-4">
                <FormField
                  control={nodeForm.control}
                  name="label"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Node Label</FormLabel>
                      <FormControl>
                        <Input {...field} placeholder="Enter node label" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={nodeForm.control}
                  name="type"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Node Type</FormLabel>
                      <FormControl>
                        <Select
                          value={field.value}
                          onValueChange={field.onChange}
                          disabled={!!selectedNode}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select node type" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="agentNode">Agent</SelectItem>
                            <SelectItem value="toolNode">Tool</SelectItem>
                            <SelectItem value="triggerNode">Trigger</SelectItem>
                            <SelectItem value="outputNode">Output</SelectItem>
                          </SelectContent>
                        </Select>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                {(nodeForm.watch('type') === 'agentNode' || selectedNodeType === 'agentNode') && (
                  <FormField
                    control={nodeForm.control}
                    name="entityId"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Agent</FormLabel>
                        <FormControl>
                          <Select value={field.value} onValueChange={field.onChange}>
                            <SelectTrigger>
                              <SelectValue placeholder="Select agent" />
                            </SelectTrigger>
                            <SelectContent>
                              {discoverAgents.data?.map((agent) => (
                                <SelectItem key={agent.id} value={agent.id}>
                                  {agent.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                )}
                {(nodeForm.watch('type') === 'toolNode' || selectedNodeType === 'toolNode') && (
                  <>
                    <FormField
                      control={nodeForm.control}
                      name="entityId"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Tool</FormLabel>
                          <FormControl>
                            <Select
                              value={field.value}
                              onValueChange={(value) => {
                                field.onChange(value);
                                nodeForm.setValue('capability', '');
                              }}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Select tool" />
                              </SelectTrigger>
                              <SelectContent>
                                {discoverTools.data?.map((tool) => (
                                  <SelectItem key={tool.id} value={tool.id}>
                                    {tool.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    {nodeForm.watch('entityId') && (
                      <FormField
                        control={nodeForm.control}
                        name="capability"
                        render={({ field }) => {
                          const selectedTool = discoverTools.data?.find((t) => t.id === nodeForm.watch('entityId'));
                          return (
                            <FormItem>
                              <FormLabel>Capability</FormLabel>
                              <FormControl>
                                <Select value={field.value} onValueChange={field.onChange}>
                                  <SelectTrigger>
                                    <SelectValue placeholder="Select capability" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {selectedTool?.capabilities.map((cap) => (
                                      <SelectItem key={cap.name} value={cap.name}>
                                        {cap.name}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          );
                        }}
                      />
                    )}
                    {nodeForm.watch('capability') && (
                      <FormField
                        control={nodeForm.control}
                        name="params"
                        render={({ field }) => {
                          const selectedTool = discoverTools.data?.find((t) => t.id === nodeForm.watch('entityId'));
                          const capability = selectedTool?.capabilities.find(
                            (cap) => cap.name === nodeForm.watch('capability')
                          );
                          return (
                            <FormItem>
                              <FormLabel>Parameters</FormLabel>
                              <FormControl>
                                <div className="space-y-2">
                                  {capability?.parameters &&
                                    Object.entries(capability.parameters).map(([key, param]) => (
                                      <div key={key}>
                                        <label className="text-sm font-medium">{key}</label>
                                        <Input
                                          placeholder={param.description}
                                          value={field.value?.[key] || ''}
                                          onChange={(e) =>
                                            field.onChange({
                                              ...field.value,
                                              [key]: e.target.value,
                                            })
                                          }
                                          required={param.required}
                                        />
                                      </div>
                                    ))}
                                </div>
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          );
                        }}
                      />
                    )}
                  </>
                )}
                {(nodeForm.watch('type') === 'triggerNode' || selectedNodeType === 'triggerNode') && (
                  <FormField
                    control={nodeForm.control}
                    name="entityId"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Trigger Type</FormLabel>
                        <FormControl>
                          <Select value={field.value} onValueChange={field.onChange}>
                            <SelectTrigger>
                              <SelectValue placeholder="Select trigger type" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="user_input">User Input</SelectItem>
                              <SelectItem value="webhook">Webhook</SelectItem>
                              <SelectItem value="schedule">Schedule</SelectItem>
                            </SelectContent>
                          </Select>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                )}
                {(nodeForm.watch('type') === 'outputNode' || selectedNodeType === 'outputNode') && (
                  <FormField
                    control={nodeForm.control}
                    name="entityId"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Output Type</FormLabel>
                        <FormControl>
                          <Select value={field.value} onValueChange={field.onChange}>
                            <SelectTrigger>
                              <SelectValue placeholder="Select output type" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="user_response">User Response</SelectItem>
                              <SelectItem value="webhook">Webhook</SelectItem>
                              <SelectItem value="database">Database</SelectItem>
                            </SelectContent>
                          </Select>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                )}
              </div>
              <DialogFooter>
                <DialogClose asChild>
                  <Button type="button" variant="outline" aria-label="Cancel">
                    Cancel
                  </Button>
                </DialogClose>
                <Button type="submit" aria-label={selectedNode ? 'Update node' : 'Add node'}>
                  {selectedNode ? 'Update Node' : 'Add Node'}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </div>
  );
}