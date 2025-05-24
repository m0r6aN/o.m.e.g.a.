// src/app/api/workflows/route.ts
import { NextRequest, NextResponse } from 'next/server';
import {
  Workflow,
  WorkflowNode,
  WorkflowEdge,
  WorkflowExecution as ClientWorkflowExecution, // Renaming to avoid conflict with local var
  StepResult,
  WorkflowNodeData,
  //WorkflowTemplate as ClientWorkflowTemplate, // Using the one from types.ts
} from '@/lib/workflow/types'; // Centralized types
import { MarkerType, Position } from 'reactflow';  // For default edge properties

// Define a specific type for the nodes within a BackendWorkflowTemplate
interface BackendWorkflowTemplateNode {
  type: WorkflowNode['type']; // 'agentNode' | 'toolNode' | 'triggerNode' | 'outputNode'
  data: Partial<WorkflowNodeData> & { label: string; entityId?: string }; // label is required, entityId often too
  positionHint?: { x: number; y: number };
  // Add any other properties from WorkflowNode (except id, position) that you want to allow in a template node.
  // For example, if you want to specify default width/height:
  // width?: number;
  // height?: number;
}

// Define a more specific template type for backend use
interface BackendWorkflowTemplate {
  id: string;
  name: string;
  description: string;
  nodes: BackendWorkflowTemplateNode[]; // Use the new specific type here
  edges: Omit<WorkflowEdge, 'id' | 'source' | 'target'> & {
    sourceIndex: number; // Changed to required for clarity
    targetIndex: number; // Changed to required for clarity
  }[];
  tags: string[];
}

// Sample data for testing - conforming to Workflow interface
const sampleWorkflows: Workflow[] = [
  {
    id: 'wf-123',
    name: 'Research and Reporting Workflow',
    description: 'Automates research, analysis, and report generation.',
    nodes: [
      {
        id: 'trigger-1', type: 'triggerNode', position: { x: 50, y: 50 },
        data: { label: 'User Query', entityId: 'user_input', status: 'pending' }
      },
      {
        id: 'agent-1', type: 'agentNode', position: { x: 250, y: 50 },
        data: { label: 'Research Agent', entityId: 'research_agent_id', capability: 'web_search', params: { query: 'placeholder' }, status: 'pending' }
      },
      {
        id: 'agent-2', type: 'agentNode', position: { x: 500, y: 50 },
        data: { label: 'Analyzer Agent', entityId: 'analyzer_agent_id', status: 'pending' }
      },
      {
        id: 'output-1', type: 'outputNode', position: { x: 750, y: 50 },
        data: { label: 'Generate Report', entityId: 'user_response', status: 'pending' }
      },
    ],
    edges: [
      { id: 'e-trigger-1-agent-1', source: 'trigger-1', target: 'agent-1', type: 'smoothstep', markerEnd: { type: MarkerType.ArrowClosed }, animated: true },
      { id: 'e-agent-1-agent-2', source: 'agent-1', target: 'agent-2', type: 'smoothstep', markerEnd: { type: MarkerType.ArrowClosed }, animated: true },
      { id: 'e-agent-2-output-1', source: 'agent-2', target: 'output-1', type: 'smoothstep', markerEnd: { type: MarkerType.ArrowClosed }, animated: true },
    ],
    createdAt: '2025-04-15T10:30:00Z',
    updatedAt: '2025-04-15T14:45:00Z',
    status: 'active',
  },
  {
    id: 'wf-456',
    name: 'Code Review Workflow',
    description: 'Automates static analysis and code review.',
    nodes: [
      {
        id: 'trigger-code-1', type: 'triggerNode', position: { x: 50, y: 150 },
        data: { label: 'Code Commit', entityId: 'webhook', status: 'pending' }
      },
      {
        id: 'tool-code-1', type: 'toolNode', position: { x: 250, y: 150 },
        data: { label: 'Static Analyzer', entityId: 'static_analyzer_tool_id', capability: 'analyze_code', status: 'pending' }
      },
      {
        id: 'agent-code-1', type: 'agentNode', position: { x: 500, y: 150 },
        data: { label: 'Code Review Agent', entityId: 'code_review_agent_id', status: 'pending' }
      },
      {
        id: 'output-code-1', type: 'outputNode', position: { x: 750, y: 150 },
        data: { label: 'Review Result', entityId: 'webhook', status: 'pending' }
      },
    ],
    edges: [
      { id: 'ec-trigger-1-tool-1', source: 'trigger-code-1', target: 'tool-code-1', type: 'smoothstep', markerEnd: { type: MarkerType.ArrowClosed }, animated: true },
      { id: 'ec-tool-1-agent-1', source: 'tool-code-1', target: 'agent-code-1', type: 'smoothstep', markerEnd: { type: MarkerType.ArrowClosed }, animated: true },
      { id: 'ec-agent-1-output-1', source: 'agent-code-1', target: 'output-code-1', type: 'smoothstep', markerEnd: { type: MarkerType.ArrowClosed }, animated: true },
    ],
    createdAt: '2025-04-10T09:15:00Z',
    updatedAt: '2025-04-12T16:20:00Z',
    status: 'draft',
  }
];

// Sample templates for testing - adapted to include nodes and edges
const sampleTemplates: BackendWorkflowTemplate[] = [
  {
    id: 'template-research-basic',
    name: 'Basic Research Template',
    description: 'A simple template for research and summarization.',
    nodes: [
      { type: 'triggerNode', data: { label: 'Topic Input', entityId: 'user_input' }, positionHint: {x: 50, y: 50}},
      { type: 'agentNode', data: { label: 'Research Agent', entityId: 'research_agent_id', capability: 'web_search', params: { depth: 'medium' } }, positionHint: {x: 250, y: 50} },
      { type: 'agentNode', data: { label: 'Summarizer Agent', entityId: 'summarizer_agent_id' }, positionHint: {x: 500, y: 50} },
      { type: 'outputNode', data: { label: 'Summary Output', entityId: 'user_response' }, positionHint: {x: 750, y: 50} },
    ],
    edges: [
      { sourceIndex: 0, targetIndex: 1 },
      { sourceIndex: 1, targetIndex: 2 },
      { sourceIndex: 2, targetIndex: 3 },
    ],
    tags: ['research', 'template', 'basic'],
  },
];

// In-memory storage for testing
let workflowsStore: Workflow[] = [...sampleWorkflows]; // Renamed to avoid conflict
let workflowExecutionsStore: ClientWorkflowExecution[] = [];
let nextWorkflowIdCounter = 789;

export async function GET(req: NextRequest) {
  const requestUrl = new URL(req.url); // Use a different variable name
  const pathParts = requestUrl.pathname.split('/');
  const lastSegment = pathParts[pathParts.length - 1];

  // Check if the last segment is 'workflows', implying a list request
  // or if it's part of a specific workflow ID like /api/workflows/wf-123
  if (lastSegment === 'workflows' && pathParts[pathParts.length - 2] === 'api') {
    return NextResponse.json(workflowsStore);
  }

  // If the last segment is 'templates'
  if (lastSegment === 'templates' && pathParts[pathParts.length - 2] === 'workflows') {
    return NextResponse.json(sampleTemplates);
  }

  // Otherwise, assume lastSegment is a workflowId
  const workflowId = lastSegment;
  const workflow = workflowsStore.find(wf => wf.id === workflowId);
  if (workflow) {
    return NextResponse.json(workflow);
  }
  
  return NextResponse.json({ error: 'Resource not found or invalid path' }, { status: 404 });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const requestUrl = new URL(req.url); // Use a different variable name

    if (requestUrl.pathname.endsWith('/from-template')) {
      const { template_id, name, description } = body as { template_id: string, name?: string, description?: string };
      const template = sampleTemplates.find(t => t.id === template_id);
      
      if (!template) {
        return NextResponse.json({ error: 'Template not found' }, { status: 404 });
      }
      
      const newWorkflowId = `wf-${nextWorkflowIdCounter++}`;
      const instantiatedNodes: WorkflowNode[] = template.nodes.map((tn, index) => ({
        id: `${newWorkflowId}-node-${index}`,
        type: tn.type,
        position: tn.positionHint || { x: 50 + index * 200, y: 100 }, // Basic layout
        data: {
          ...tn.data, // Spread template data
          status: 'pending', // Default status
        } as WorkflowNodeData, // Ensure data conforms to WorkflowNodeData
      }));

      const instantiatedEdges: WorkflowEdge[] = template.edges.map((te, index) => ({
        id: `${newWorkflowId}-edge-${index}`,
        source: instantiatedNodes[te.sourceIndex!].id,
        target: instantiatedNodes[te.targetIndex!].id,
        type: 'smoothstep',
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed },
      }));
      
      const newWorkflow: Workflow = {
        id: newWorkflowId,
        name: name || template.name || `Workflow from ${template.id}`,
        description: description || template.description || `Description for ${template.id}`,
        nodes: instantiatedNodes,
        edges: instantiatedEdges,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        status: 'draft', // New workflows from template are drafts
        // tags: template.tags, // Removed as 'tags' is not in Workflow interface
      };
      
      workflowsStore.push(newWorkflow);
      return NextResponse.json(newWorkflow, { status: 201 });
    }
    
    if (requestUrl.pathname.includes('/execute')) {
      const pathParts = requestUrl.pathname.split('/');
      const workflowId = pathParts[pathParts.length - 2]; // ID is before "execute"
      
      const workflow = workflowsStore.find(wf => wf.id === workflowId);
      if (!workflow) {
        return NextResponse.json({ error: 'Workflow not found for execution' }, { status: 404 });
      }
      
      const execution: ClientWorkflowExecution = {
        id: `exec-${Date.now()}`,
        workflow_id: workflowId,
        status: 'in_progress',
        started_at: new Date().toISOString(),
        step_results: {}, // Changed from array to Record<string, StepResult>
        // metadata: {}, // If you use metadata
      };
      
      workflowExecutionsStore.push(execution);
      
      // Simulate execution
      setTimeout(() => {
        const execIndex = workflowExecutionsStore.findIndex(e => e.id === execution.id);
        if (execIndex !== -1) {
          const updatedStepResults: Record<string, StepResult> = {};
          workflow.nodes.forEach(node => { // Iterate over nodes
            if (node.type !== 'triggerNode' && node.type !== 'outputNode') { // Simulate results for processing nodes
              updatedStepResults[node.id] = {
                status: 'completed',
                started_at: new Date(Date.now() - Math.random() * 3000).toISOString(),
                completed_at: new Date().toISOString(),
                duration: Math.floor(Math.random() * 3000) + 500,
                output: { result: `Simulated result for node ${node.data.label}` },
              };
            }
          });
          
          workflowExecutionsStore[execIndex] = {
            ...workflowExecutionsStore[execIndex],
            status: 'completed',
            completed_at: new Date().toISOString(),
            step_results: updatedStepResults,
          };
          console.log(`Simulated execution completed for ${execution.id}`);
        }
      }, 3000); // Simulate a 3-second execution
      
      return NextResponse.json({ executionId: execution.id }, { status: 202 });
    }
    
    // Regular workflow creation
    // The body should be a Partial<Workflow> but must include name, nodes, edges.
    const { name, description, nodes, edges, status } = body as Partial<Workflow> & { name: string, nodes: WorkflowNode[], edges: WorkflowEdge[] };

    if (!name || !nodes || !edges) {
        return NextResponse.json({ error: 'Missing required fields: name, nodes, edges' }, { status: 400 });
    }
    
    const newWorkflow: Workflow = {
      id: `wf-${nextWorkflowIdCounter++}`,
      name,
      description: description || '',
      nodes,
      edges,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      status: status || 'draft',
    };
    
    workflowsStore.push(newWorkflow);
    return NextResponse.json(newWorkflow, { status: 201 });

  } catch (error) {
    console.error("POST Error:", error);
    return NextResponse.json(
      { error: 'Invalid request', details: (error as Error).message },
      { status: 400 }
    );
  }
}

export async function PUT(req: NextRequest) {
  try {
    const requestUrl = new URL(req.url); // Use a different variable name
    const pathParts = requestUrl.pathname.split('/');
    const workflowId = pathParts[pathParts.length - 1];
    
    const workflowIndex = workflowsStore.findIndex(wf => wf.id === workflowId);
    if (workflowIndex === -1) {
      return NextResponse.json({ error: 'Workflow not found to update' }, { status: 404 });
    }
    
    const updates = (await req.json()) as Partial<Workflow>;
    
    // Ensure nodes and edges are fully replaced if provided, or keep existing
    // Prevent partial updates of nodes/edges arrays themselves, they should be sent complete.
    const updatedWorkflow: Workflow = {
      ...workflowsStore[workflowIndex],
      ...updates, // Apply all updates
      nodes: updates.nodes || workflowsStore[workflowIndex].nodes, // Replace nodes array if provided
      edges: updates.edges || workflowsStore[workflowIndex].edges, // Replace edges array if provided
      updatedAt: new Date().toISOString(),
    };
    
    workflowsStore[workflowIndex] = updatedWorkflow;
    
    return NextResponse.json(updatedWorkflow);
  } catch (error) {
    console.error("PUT Error:", error);
    return NextResponse.json(
      { error: 'Invalid request', details: (error as Error).message },
      { status: 400 }
    );
  }
}

export async function DELETE(req: NextRequest) {
  const requestUrl = new URL(req.url); // Use a different variable name
  const pathParts = requestUrl.pathname.split('/');
  const workflowId = pathParts[pathParts.length - 1];
  
  const initialLength = workflowsStore.length;
  workflowsStore = workflowsStore.filter(wf => wf.id !== workflowId);
  
  if (workflowsStore.length === initialLength) {
    return NextResponse.json({ error: 'Workflow not found to delete' }, { status: 404 });
  }
  
  return NextResponse.json({ message: `Workflow ${workflowId} deleted successfully.` });
}