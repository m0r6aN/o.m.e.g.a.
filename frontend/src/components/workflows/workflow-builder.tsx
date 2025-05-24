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
  Node as ReactFlowNode,
  NodeProps, // For custom node components if needed for explicit typing
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
import { simulateExecution } from '@/lib/workflow/execution';
import { config } from '@/lib/env-config';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { WorkflowNode, WorkflowEdge, Workflow, WorkflowNodeData } from '@/lib/workflow/types';

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
  } as NodeTypes, // NodeTypes is Record<string, ComponentType<NodeProps<any>>> which is fine.
  // Custom nodes (AgentNode, etc.) should internally use NodeProps<WorkflowNodeData>.
  edge: {
    type: 'smoothstep' as const, // Use 'as const' for precise typing
    markerEnd: { type: MarkerType.ArrowClosed },
    animated: true,
  },
};

// Utility to coerce any node array into WorkflowNode[] type-safely
// Only use this when loading from untyped/external sources (API, import)
function safeWorkflowNodes(nodes: any[] | undefined): WorkflowNode[] {
  if (!Array.isArray(nodes)) return [];
  return nodes
    .filter(node => node && typeof node === 'object' && node.data && typeof node.data === 'object' && node.id && node.position)
    .map(node => ({
      id: String(node.id),
      position: node.position, // Assuming position is { x: number, y: number }
      type: (node.type ?? 'agentNode') as WorkflowNode['type'],
      data: {
        label: node.data.label ?? 'Untitled Node',
        entityId: node.data.entityId ?? '',
        capability: node.data.capability,
        params: node.data.params ?? {},
        status: (node.data.status ?? 'pending') as WorkflowNodeData['status'],
        message: node.data.message,
      },
      // Spread other valid ReactFlowNode properties if necessary (e.g., width, height, draggable)
      ...node // Spreading the original node can be risky if it has incompatible props.
      // Be more selective or ensure the source 'node' structure is compatible.
      // For now, let's assume basic properties (id, position, type, data) are primary.
      // To be safer:
      // ...(typeof node.width === 'number' && { width: node.width }),
      // ...(typeof node.height === 'number' && { height: node.height }),
    }) as WorkflowNode); // Cast to WorkflowNode at the end
}

// Utility to coerce any edge array into WorkflowEdge[] type-safely
function safeWorkflowEdges(edges: any[] | undefined): WorkflowEdge[] {
  if (!Array.isArray(edges)) return [];
  return edges
    .filter(edge => edge && typeof edge === 'object' && edge.id && edge.source && edge.target)
    .map(edge => ({
      id: String(edge.id),
      source: String(edge.source),
      target: String(edge.target),
      ...CONFIG.edge, // Apply default/required edge properties
      // Spread other valid ReactFlowEdge properties if necessary
      ...(edge.data && { data: edge.data }), // If edges can have data
      // Override with specific properties from imported edge if they are valid
      ...(edge.type && { type: edge.type as 'smoothstep' }), // Be careful with types
      ...(edge.animated !== undefined && { animated: edge.animated }),
      ...(edge.markerEnd && { markerEnd: edge.markerEnd }),
    }));
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
  position: z.object({ x: z.number(), y: z.number() }).optional(), // Made optional as it might not always be in form
});

type NodeFormValues = z.infer<typeof nodeFormSchema>;

// API functions
async function fetchWorkflow(id: string): Promise<Workflow> {
  const response = await fetch(`/api/workflows/${id}`);
  if (!response.ok) {
    throw new Error('Failed to fetch workflow');
  }
  // The response.json() is 'any'. It should be cast or validated against Workflow.
  // For now, we assume it returns something compatible with Workflow structure.
  return response.json() as Promise<Workflow>;
}

async function saveWorkflow(workflow: Partial<Workflow> & { nodes: WorkflowNode[], edges: WorkflowEdge[] }): Promise<Workflow> {
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
  return response.json() as Promise<Workflow>;
}

async function executeWorkflow(id: string): Promise<{ executionId: string }> {
  const response = await fetch(`/api/workflows/${id}/execute`, { method: 'POST' });
  if (!response.ok) {
    throw new Error('Failed to execute workflow');
  }
  return response.json();
}

// Utility to detect cycles in the workflow graph
function hasCycle(nodes: ReactFlowNode<WorkflowNodeData>[], edges: ReactFlowEdge[]): boolean { // Use general ReactFlow types
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
function validateWorkflow(nodes: ReactFlowNode<WorkflowNodeData>[], edges: ReactFlowEdge[]): string[] { // Use general ReactFlow types
  const errors: string[] = [];
  // Access node.type, which is string | undefined for ReactFlowNode. Cast if needed.
  if (!nodes.some((node) => (node.type as WorkflowNode['type']) === 'triggerNode')) {
    errors.push('Workflow must have at least one trigger node.');
  }
  if (hasCycle(nodes, edges)) {
    errors.push('Workflow contains cycles, which are not allowed.');
  }
  if (!nodes.some((node) => (node.type as WorkflowNode['type']) === 'outputNode')) {
    errors.push('Workflow must have at least one output node.');
  }
  return errors;
}

interface WorkflowBuilderProps {
  workflowId?: string;
}

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

  // Nodes state uses WorkflowNodeData for the data property
  const [nodes, setNodes, onNodesChange] = useNodesState<WorkflowNodeData>([]);
  // Edges state can be generic ReactFlowEdge if no specific edge data, or WorkflowEdge if structure is guaranteed
  const [edges, setEdges, onEdgesChange] = useEdgesState<WorkflowEdge>([]); // Using WorkflowEdge if all edges conform to it

  const [isWorkflowDialogOpen, setIsWorkflowDialogOpen] = useState(false);
  const [isNodeDialogOpen, setIsNodeDialogOpen] = useState(false);
  const [selectedNodeType, setSelectedNodeType] = useState<WorkflowNode['type'] | null>(null); // Use specific type
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null); // This is ReactFlowNode<WorkflowNodeData> with specific type
  const [isDragging, setIsDragging] = useState(false);
  const [workflowName, setWorkflowName] = useState('Untitled Workflow');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [workflowStatus, setWorkflowStatus] = useState<'draft' | 'active' | 'inactive'>('draft');
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [nodeCreationPosition, setNodeCreationPosition] = useState<{ x: number; y: number } | null>(null);


  const { discoverAgents, discoverTools } = useMcp();

  const {
    data: workflow,
    isLoading: isWorkflowLoading,
    error: workflowError,
  } = useQuery({
    queryKey: ['workflow', workflowId],
    queryFn: () => fetchWorkflow(workflowId!),
    enabled: !!workflowId,
  });

  const workflowForm = useForm<WorkflowFormValues>({
    resolver: zodResolver(workflowFormSchema),
    defaultValues: { name: workflowName, description: workflowDescription },
  });

  const nodeForm = useForm<NodeFormValues>({
    resolver: zodResolver(nodeFormSchema),
    defaultValues: {
      type: 'agentNode', // Default type
      label: '',
      entityId: '',
      // position is determined on drop or defaults in handleAddNode
    },
  });

  const saveWorkflowMutation = useMutation({
    mutationFn: (wfData: Partial<Workflow> & { nodes: WorkflowNode[], edges: WorkflowEdge[] }) => saveWorkflow(wfData),
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
      // router.push(`/workflows/${workflowId}/executions/${data.executionId}`); // Navigation moved to panel button
      setExecutionId(data.executionId);
    },
    onError: (error) => {
      toast.error(`Failed to execute workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const {
    isConnected: wsConnected,
    lastMessage: wsLastMessage,
    error: wsError,
  } = useWorkflowExecution(executionId, setNodes); 

  useEffect(() => {
    if (workflow) {
      setWorkflowName(workflow.name);
      setWorkflowDescription(workflow.description);
      setWorkflowStatus(workflow.status);
      setNodes(safeWorkflowNodes(workflow.nodes));
      setEdges(safeWorkflowEdges(workflow.edges));
      workflowForm.reset({ name: workflow.name, description: workflow.description });
    }
  }, [workflow, workflowForm, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) =>
      setEdges((eds) => addEdge({ ...params, ...CONFIG.edge } as WorkflowEdge, eds)), // Ensure added edge is WorkflowEdge
    [setEdges]
  );

  const onNodeClick = useCallback(
    (event: React.MouseEvent, node: ReactFlowNode<WorkflowNodeData>) => { // node is ReactFlowNode<WorkflowNodeData>
      setSelectedNode(node as WorkflowNode); // Cast to our more specific WorkflowNode
    },
    [] // Removed setSelectedNode dependency as it's a state setter
  );

  const onDragStart = useCallback((event: React.DragEvent, nodeType: WorkflowNode['type']) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
    setIsDragging(true);
  }, []);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      setIsDragging(false);
      if (!reactFlowInstance || !reactFlowWrapper.current) return;

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const type = event.dataTransfer.getData('application/reactflow') as WorkflowNode['type'];
      if (!type || !CONFIG.nodeTypes[type]) return; // Validate type

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      setNodeCreationPosition(position); // Store position for handleAddNode
      setSelectedNodeType(type);
      nodeForm.reset({
        type: type,
        label: '',
        entityId: '',
        capability: '',
        // position will be taken from nodeCreationPosition in handleAddNode
      });
      setIsNodeDialogOpen(true);
    },
    [reactFlowInstance, nodeForm, setSelectedNodeType, setNodeCreationPosition] // Added dependencies
  );

  const handleAddNode = useCallback(
    (data: NodeFormValues) => {
      const position = nodeCreationPosition || data.position || { x: Math.random() * 400, y: Math.random() * 400 };
      const newNode: WorkflowNode = {
        id: data.id || `${data.type}_${Date.now()}`,
        type: data.type,
        position,
        data: {
          label: data.label,
          entityId: data.entityId,
          capability: data.capability,
          params: data.params,
          status: 'pending', // Ensure status is initialized
          message: undefined,
        },
      };
      setNodes((nds) => [...nds, newNode]);
      setIsNodeDialogOpen(false);
      setNodeCreationPosition(null); // Reset position
    },
    [setNodes, nodeCreationPosition] // Added nodeCreationPosition
  );

  const handleUpdateNode = useCallback(
    (data: NodeFormValues) => {
      setNodes((nds) =>
        nds.map((node) => // node is ReactFlowNode<WorkflowNodeData>
          node.id === data.id
            ? {
              ...node,
              type: data.type, // Update type if it can change (usually not for existing nodes)
              data: {
                ...node.data,
                label: data.label,
                entityId: data.entityId,
                capability: data.capability,
                params: data.params,
              },
            } as WorkflowNode // Cast the updated node to WorkflowNode
            : node
        )
      );
      setSelectedNode(null);
      setIsNodeDialogOpen(false);
    },
    [setNodes]
  );

  const handleDeleteNode = useCallback(
    (nodeId: string) => {
      setNodes((nds) => nds.filter((node) => node.id !== nodeId));
      setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
      setSelectedNode(null);
    },
    [setNodes, setEdges]
  );

  const handleExportWorkflow = () => {
    const workflowData = {
      name: workflowName,
      description: workflowDescription,
      status: workflowStatus,
      nodes: nodes as WorkflowNode[], // nodes are ReactFlowNode<WorkflowNodeData>[], cast to specific type for export
      edges: edges as WorkflowEdge[],   // edges are ReactFlowEdge[], cast for export
    };
    const blob = new Blob([JSON.stringify(workflowData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${workflowName.toLowerCase().replace(/\s+/g, '-') || 'workflow'}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleSaveWorkflow = useCallback(
    (formData: WorkflowFormValues) => {
      const currentNodes = nodes as WorkflowNode[]; // Use consistent view of nodes
      const currentEdges = edges as WorkflowEdge[];
      const errors = validateWorkflow(currentNodes, currentEdges);
      if (errors.length > 0) {
        errors.forEach((error) => toast.error(error));
        return;
      }
      saveWorkflowMutation.mutate({
        id: workflowId,
        name: formData.name,
        description: formData.description,
        nodes: currentNodes,
        edges: currentEdges,
        status: workflowStatus,
      });
      setIsWorkflowDialogOpen(false);
      setWorkflowName(formData.name); // Update local state after successful save dialog submission
      setWorkflowDescription(formData.description);
    },
    [workflowId, nodes, edges, workflowStatus, saveWorkflowMutation]
  );

  const handleExecuteWorkflow = useCallback(() => {
    if (!workflowId) {
      toast.error('Please save the workflow before executing.');
      return;
    }
    const currentNodes = nodes as WorkflowNode[]; // Use consistent view of nodes
    const currentEdges = edges as WorkflowEdge[];

    const errors = validateWorkflow(currentNodes, currentEdges);
    if (errors.length > 0) {
      errors.forEach((error) => toast.error(error));
      return;
    }

    // Set all nodes to pending status before execution
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

    if (config.features.enableWorkflowVisualization) {
      executeWorkflowMutation.mutate(undefined, {
        // onSuccess handled by mutation definition, setExecutionId triggers WS connection
      });
    } else {
      toast.success('Workflow execution started (simulation mode)');
      // simulateExecution expects WorkflowNode[], nodes is ReactFlowNode<WorkflowNodeData>[]
      simulateExecution(`sim-${Date.now()}`, currentNodes, setNodes as any); // Adjust simulateExecution if needed
    }
  }, [workflowId, nodes, edges, executeWorkflowMutation, setNodes]);

  const handleImportWorkflow = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const content = e.target?.result as string;
          const importedWorkflow = JSON.parse(content); // importedWorkflow is any

          // Validate imported structure a bit more if needed
          setWorkflowName(importedWorkflow.name || 'Imported Workflow');
          setWorkflowDescription(importedWorkflow.description || '');
          setWorkflowStatus(importedWorkflow.status || 'draft');
          setNodes(safeWorkflowNodes(importedWorkflow.nodes));
          setEdges(safeWorkflowEdges(importedWorkflow.edges));
          toast.success(`Workflow imported: ${importedWorkflow.name || 'Untitled'}`);

          // Reset form with imported name/description
          workflowForm.reset({
            name: importedWorkflow.name || 'Imported Workflow',
            description: importedWorkflow.description || ''
          });

        } catch (error) {
          toast.error(`Failed to import workflow: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      };
      reader.readAsText(file);
      event.target.value = ''; // Reset file input
    },
    [setNodes, setEdges, workflowForm] // Added workflowForm
  );

  const handleValidateWorkflow = useCallback(() => {
    const errors = validateWorkflow(nodes, edges); // Pass ReactFlowNode<WorkflowNodeData>[] and ReactFlowEdge[]
    if (errors.length === 0) {
      toast.success('Workflow is valid!');
    } else {
      errors.forEach((error) => toast.error(error));
    }
  }, [nodes, edges]);

  // ... (loading and error states remain similar)
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
            onClick={() => queryClient.invalidateQueries({ queryKey: ['workflow', workflowId] })} // More specific refetch
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


  // JSX rendering part remains largely the same, ensure node data access is correct (e.g. selectedNode.data.label)
  // For example, in Panel for Edit button:
  // label: selectedNode.data.label (this is correct as selectedNode is WorkflowNode, data is WorkflowNodeData)

  return (
    <div className="space-y-6">
      {/* Header */}
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
            onClick={() => {
              workflowForm.reset({ name: workflowName, description: workflowDescription }); // Ensure form has current values
              setIsWorkflowDialogOpen(true);
            }}
            aria-label="Workflow settings"
          >
            <Settings className="mr-2 h-4 w-4" />
            Settings
          </Button>
          <Button
            variant="default" // Changed from "default" to "primary" or keep as "default" if that's your style
            onClick={handleExecuteWorkflow}
            disabled={!workflowId || executeWorkflowMutation.isPending || saveWorkflowMutation.isPending}
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
            variant="default" // Changed from "default" to "primary" or keep as "default"
            onClick={() => { // This button's purpose seems to be "Save" by opening dialog
              workflowForm.reset({ name: workflowName, description: workflowDescription });
              setIsWorkflowDialogOpen(true); // This will trigger the save dialog
            }}
            disabled={saveWorkflowMutation.isPending}
            aria-label="Save workflow"
          >
            {saveWorkflowMutation.isPending ? (
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-2 h-4 w-4" />
            )}
            Save
          </Button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Components Panel */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Components</CardTitle>
              <CardDescription>Drag and drop components to the canvas</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[calc(800px-120px)] pr-4"> {/* Adjusted height */}
                <div className="space-y-6">
                  {/* Agents */}
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
                  {/* Tools */}
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
                  {/* Triggers */}
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
                  {/* Outputs */}
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
              <label htmlFor="import-file" className="inline-flex items-center">
                <Button variant="outline" size="sm" asChild aria-label="Import workflow">
                  <span className="cursor-pointer flex items-center"> {/* Ensure span behaves like button */}
                    <FileUp className="mr-2 h-4 w-4" />
                    Import
                  </span>
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

        {/* React Flow Canvas */}
        <div className="lg:col-span-4">
          {/* Execution Status Info */}
          {executionId && (
            <div className="mb-4">
              {wsError ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>WebSocket Connection Error</AlertTitle>
                  <AlertDescription>
                    {wsError.message} - Execution status updates may be unavailable.
                  </AlertDescription>
                </Alert>
              ) : wsConnected ? (
                <Alert variant="default" className="bg-green-50 text-green-800 border-green-200">
                  <CheckCircle className="h-4 w-4" />
                  <AlertTitle className="flex items-center">
                    <span className="relative flex h-3 w-3 mr-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                    </span>
                    Connected to Execution {executionId.substring(0, 8)}...
                  </AlertTitle>
                  <AlertDescription>
                    Receiving real-time updates for workflow execution.
                  </AlertDescription>
                </Alert>
              ) : (
                <Alert>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <AlertTitle>Connecting to Execution {executionId.substring(0, 8)}...</AlertTitle>
                  <AlertDescription>
                    Attempting to establish WebSocket connection...
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}
          <div className="h-[800px] border rounded-lg" ref={reactFlowWrapper}>
            <ReactFlow
              nodes={nodes} // These are ReactFlowNode<WorkflowNodeData>[]
              edges={edges} // These are WorkflowEdge[] (or ReactFlowEdge[] if useEdgesState is generic)
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onInit={setReactFlowInstance}
              onDrop={onDrop}
              onDragOver={onDragOver}
              nodeTypes={CONFIG.nodeTypes}
              fitView
              tabIndex={0} // For keyboard accessibility
              aria-label="Workflow builder canvas"
            >
              <Controls />
              <MiniMap />
              <Background gap={12} size={1} />
              <Panel position="top-right" className="flex gap-2 p-2 bg-background/80 rounded-md">
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
                    if (selectedNode) { // selectedNode is WorkflowNode
                      nodeForm.reset({
                        id: selectedNode.id,
                        type: selectedNode.type, // This is 'agentNode' etc.
                        label: selectedNode.data.label,
                        entityId: selectedNode.data.entityId,
                        capability: selectedNode.data.capability,
                        params: selectedNode.data.params,
                        position: selectedNode.position, // Include position if it can be edited
                      });
                      setSelectedNodeType(selectedNode.type); // Ensure selectedNodeType is also updated
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
              {wsLastMessage && (wsLastMessage.status === 'completed' || wsLastMessage.status === 'failed') && executionId && (
                <Panel position="top-center" className="bg-background p-3 rounded-md shadow-lg border">
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-2">
                      {wsLastMessage.status === 'completed' ? (
                        <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                      ) : (
                        <AlertCircle className="h-5 w-5 text-red-500 mr-2" /> // Changed from Circle to AlertCircle for failed
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
            <form onSubmit={workflowForm.handleSubmit(handleSaveWorkflow)} className="space-y-4">
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
      <Dialog open={isNodeDialogOpen} onOpenChange={(open) => {
        setIsNodeDialogOpen(open);
        if (!open) {
          setSelectedNode(null); // Clear selected node when dialog closes
          setSelectedNodeType(null);
        }
      }}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>{selectedNode ? 'Edit Node' : 'Add New Node'}</DialogTitle>
            <DialogDescription>Configure the node properties</DialogDescription>
          </DialogHeader>
          <Form {...nodeForm}>
            {/* Use selectedNode for edit, selectedNodeType for new node type determination */}
            <form onSubmit={nodeForm.handleSubmit(selectedNode ? handleUpdateNode : handleAddNode)} className="space-y-4">
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
                    <Select
                      value={field.value}
                      onValueChange={(value: WorkflowNode['type']) => {
                        field.onChange(value);
                        setSelectedNodeType(value); // Sync selectedNodeType if type changes
                        // Reset entityId and capability when type changes, as they are type-dependent
                        nodeForm.setValue('entityId', '');
                        nodeForm.setValue('capability', undefined);
                        nodeForm.setValue('params', undefined);
                      }}
                      disabled={!!selectedNode} // Usually type is not changed for existing nodes
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
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Conditional fields based on node type (watched from form or from selectedNodeType for new nodes) */}
              {(nodeForm.watch('type') === 'agentNode') && (
                <FormField
                  control={nodeForm.control}
                  name="entityId"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Agent</FormLabel>
                      <Select value={field.value} onValueChange={field.onChange}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select agent" />
                        </SelectTrigger>
                        <SelectContent>
                          {discoverAgents.data?.filter(a => a.status === 'active').map((agent) => (
                            <SelectItem key={agent.id} value={agent.id}>
                              {agent.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}
              {(nodeForm.watch('type') === 'toolNode') && (
                <>
                  <FormField
                    control={nodeForm.control}
                    name="entityId" // This is the Tool ID
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Tool</FormLabel>
                        <Select
                          value={field.value}
                          onValueChange={(value) => {
                            field.onChange(value);
                            nodeForm.setValue('capability', ''); // Reset capability
                            nodeForm.setValue('params', {}); // Reset params
                          }}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select tool" />
                          </SelectTrigger>
                          <SelectContent>
                            {discoverTools.data?.filter(t => t.status === 'active').map((tool) => (
                              <SelectItem key={tool.id} value={tool.id}>
                                {tool.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  {nodeForm.watch('entityId') && ( // Only show capability if a tool is selected
                    <FormField
                      control={nodeForm.control}
                      name="capability"
                      render={({ field }) => {
                        const selectedTool = discoverTools.data?.find((t) => t.id === nodeForm.watch('entityId'));
                        return (
                          <FormItem>
                            <FormLabel>Capability</FormLabel>
                            <Select value={field.value || ''} onValueChange={field.onChange}>
                              <SelectTrigger>
                                <SelectValue placeholder="Select capability" />
                              </SelectTrigger>
                              <SelectContent>
                                {selectedTool?.capabilities.map((cap) => (
                                  <SelectItem key={cap.name} value={cap.name}>
                                    {cap.name} ({cap.description.substring(0, 30)}...)
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <FormMessage />
                          </FormItem>
                        );
                      }}
                    />
                  )}
                  {nodeForm.watch('capability') && ( // Only show params if a capability is selected
                     <FormField
                     control={nodeForm.control}
                     name="params"
                     render={({ field }) => {
                       const selectedTool = discoverTools.data?.find((t) => t.id === nodeForm.watch('entityId'));
                       const capability = selectedTool?.capabilities.find(
                         (cap) => cap.name === nodeForm.watch('capability')
                       );
                       if (!capability || !capability.parameters || Object.keys(capability.parameters).length === 0) {
                           return <></>; // No parameters to show - FIXED: return empty fragment
                       }
                       return (
                         <FormItem>
                           <FormLabel>Parameters</FormLabel>
                           <div className="space-y-3 p-3 border rounded-md">
                             {Object.entries(capability.parameters).map(([key, param]) => (
                               <div key={key}>
                                 <label htmlFor={`param-${key}`} className="text-sm font-medium capitalize">
                                   {key}
                                   {param.required && <span className="text-destructive">*</span>}
                                 </label>
                                 {/* FormControl should ideally wrap the direct input for RHF context, 
                                     but here, the structure with multiple inputs is common.
                                     The 'field' object is for the 'params' object as a whole.
                                     Individual inputs update parts of 'field.value'.
                                     This part is complex but not the direct cause of *this specific* error.
                                     The immediate error is the 'null' return.
                                 */}
                                 <FormControl> {/* This FormControl is a bit unusual here if field is for the whole params object.
                                                Usually FormControl wraps a single input tied to 'field'. 
                                                However, for a group of inputs updating a record, this structure is often used.
                                                The main thing is that the render prop itself returns a ReactElement. */}
                                   <Input
                                     id={`param-${key}`}
                                     placeholder={param.description}
                                     value={field.value?.[key] || ''}
                                     onChange={(e) =>
                                       field.onChange({
                                         ...(field.value || {}), // Ensure field.value is an object
                                         [key]: e.target.value,
                                       })
                                     }
                                     required={param.required}
                                     className="mt-1"
                                   />
                                 </FormControl> 
                                  <p className="text-xs text-muted-foreground mt-1">{param.description}</p>
                               </div>
                             ))}
                           </div>
                           <FormMessage /> {/* This FormMessage is for the 'params' field as a whole */}
                         </FormItem>
                       );
                     }}
                   />
                 )}
                </>
              )}
              {(nodeForm.watch('type') === 'triggerNode') && (
                <FormField
                  control={nodeForm.control}
                  name="entityId" // For triggers, entityId represents the trigger type (e.g., "user_input")
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Trigger Type</FormLabel>
                      <Select value={field.value} onValueChange={field.onChange}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select trigger type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="user_input">User Input</SelectItem>
                          <SelectItem value="webhook">Webhook</SelectItem>
                          <SelectItem value="schedule">Schedule (Cron)</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}
              {(nodeForm.watch('type') === 'outputNode') && (
                <FormField
                  control={nodeForm.control}
                  name="entityId" // For outputs, entityId represents the output type (e.g., "user_response")
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Output Type</FormLabel>
                      <Select value={field.value} onValueChange={field.onChange}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select output type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="user_response">User Response</SelectItem>
                          <SelectItem value="webhook_call">Webhook Call</SelectItem>
                          <SelectItem value="database_write">Database Write</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}
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