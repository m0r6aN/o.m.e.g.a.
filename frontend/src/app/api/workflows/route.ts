// src/app/api/workflows/route.ts
import { WorkflowExecution } from '@/lib/workflow/client';
import { WorkflowNode } from '@/lib/workflow/types';
import { NextRequest, NextResponse } from 'next/server';

// Sample data for testing
const sampleWorkflows: WorkflowNode[] = [
  {
    id: 'wf-123',
    name: 'Research and Analysis',
    description: 'A workflow for collecting and analyzing information on a topic',
    status: 'active',
    steps: [
      {
        id: 'step-1',
        name: 'Research Task',
        description: 'Gather information from external sources',
        type: 'agent',
        target_id: 'research_agent',
        dependencies: [],
        parameters: { query: 'Query parameter will be provided at runtime' }
      },
      {
        id: 'step-2',
        name: 'Analyze Results',
        description: 'Analyze the gathered information',
        type: 'agent',
        target_id: 'analyzer_agent',
        dependencies: ['step-1'],
        parameters: {}
      },
      {
        id: 'step-3',
        name: 'Generate Report',
        description: 'Create a summary report',
        type: 'agent',
        target_id: 'report_generator_agent',
        dependencies: ['step-2'],
        parameters: { format: 'markdown' }
      }
    ],
    created_at: '2025-04-15T10:30:00Z',
    updated_at: '2025-04-15T14:45:00Z',
    tags: ['research', 'analysis', 'automation'],
  },
  {
    id: 'wf-456',
    name: 'Code Review Pipeline',
    description: 'Automated workflow for reviewing and improving code submissions',
    status: 'draft',
    steps: [
      {
        id: 'step-1',
        name: 'Static Analysis',
        description: 'Perform static code analysis on submitted code',
        type: 'tool',
        target_id: 'static_analyzer_tool',
        dependencies: [],
        parameters: {}
      },
      {
        id: 'step-2',
        name: 'AI Code Review',
        description: 'Review code with AI assistance',
        type: 'agent',
        target_id: 'code_review_agent',
        dependencies: ['step-1'],
        parameters: {}
      },
      {
        id: 'step-3',
        name: 'Generate Improvement Suggestions',
        description: 'Provide concrete improvement suggestions',
        type: 'agent',
        target_id: 'code_improvement_agent',
        dependencies: ['step-2'],
        parameters: {}
      }
    ],
    created_at: '2025-04-10T09:15:00Z',
    updated_at: '2025-04-12T16:20:00Z',
    tags: ['code', 'review', 'development'],
  }
];

// Sample templates for testing
const sampleTemplates = [
  {
    id: 'template-1',
    name: 'Simple Research Workflow',
    description: 'A basic template for research-oriented workflows',
    steps: [
      {
        name: 'Research',
        description: 'Gather information on the topic',
        type: 'agent',
        target_id: 'research_agent',
        dependencies: [],
        parameters: { depth: 'medium' }
      },
      {
        name: 'Summarize',
        description: 'Create a summary of findings',
        type: 'agent',
        target_id: 'summarizer_agent',
        dependencies: ['0'],
        parameters: {}
      }
    ],
    tags: ['research', 'template', 'basic'],
  },
  {
    id: 'template-2',
    name: 'Development Workflow',
    description: 'Template for software development tasks',
    steps: [
      {
        name: 'Plan Architecture',
        description: 'Design system architecture',
        type: 'agent',
        target_id: 'architect_agent',
        dependencies: [],
        parameters: {}
      },
      {
        name: 'Generate Code',
        description: 'Create initial code implementation',
        type: 'agent',
        target_id: 'code_generator_agent',
        dependencies: ['0'],
        parameters: {}
      },
      {
        name: 'Test Code',
        description: 'Perform automated testing',
        type: 'tool',
        target_id: 'testing_tool',
        dependencies: ['1'],
        parameters: { coverage: 'high' }
      }
    ],
    tags: ['development', 'coding', 'template'],
  }
];

// In-memory storage for testing
let workflows = [...sampleWorkflows];
let workflowExecutions: WorkflowExecution[] = [];
let nextWorkflowId = 789; // Just for demo purposes

export async function GET(req: NextRequest) {
  // Check for specific workflow ID in the URL
  const url = new URL(req.url);
  const pathParts = url.pathname.split('/');
  const workflowId = pathParts[pathParts.length - 1];
  
  // If the URL ends with 'workflows', return all workflows
  if (workflowId === 'workflows') {
    return NextResponse.json(workflows);
  }
  
  // If we have an ID, find that specific workflow
  const workflow = workflows.find(wf => wf.id === workflowId);
  if (workflow) {
    return NextResponse.json(workflow);
  }
  
  // Special endpoints
  if (workflowId === 'templates') {
    return NextResponse.json(sampleTemplates);
  }
  
  // If we couldn't find the workflow, return 404
  return NextResponse.json({ error: 'Workflow not found' }, { status: 404 });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    
    // Check if this is a template-based creation
    if (req.url.endsWith('from-template')) {
      const { template_id, parameters } = body;
      const template = sampleTemplates.find(t => t.id === template_id);
      
      if (!template) {
        return NextResponse.json({ error: 'Template not found' }, { status: 404 });
      }
      
      // Create workflow from template
      const newWorkflow: WorkflowNode = {
        id: `wf-${nextWorkflowId++}`,
        name: template.name,
        description: template.description,
        status: 'draft',
        steps: template.steps.map((step, index) => ({
          ...step,
          id: `step-${Date.now()}-${index}`,
          // Update dependencies to use actual step IDs if needed
        })),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        tags: template.tags,
      };
      
      workflows.push(newWorkflow);
      return NextResponse.json(newWorkflow);
    }
    
    // Handle workflow execution
    if (req.url.includes('/execute')) {
      const pathParts = url.pathname.split('/');
      const workflowId = pathParts[pathParts.length - 2]; // ID is before "execute"
      
      const workflow = workflows.find(wf => wf.id === workflowId);
      if (!workflow) {
        return NextResponse.json({ error: 'Workflow not found' }, { status: 404 });
      }
      
      // Create a new execution record
      const execution: WorkflowExecution = {
        id: `exec-${Date.now()}`,
        workflow_id: workflowId,
        status: 'in_progress' as const,
        started_at: new Date().toISOString(),
        step_results: [] as StepResult[],
      };
      
      workflowExecutions.push(execution);
      
      // In a real implementation, we would start the actual workflow execution here
      // For demo purposes, we'll simulate this with a timeout that completes the execution
      setTimeout(() => {
        // Find the execution and update it
        const idx = workflowExecutions.findIndex(e => e.id === execution.id);
        if (idx !== -1) {
          // Simulate step results
          const stepResults: StepResult[] = [];
          workflow.steps.forEach(step => {
            stepResults.push({
              status: 'completed',
              started_at: new Date(Date.now() - 5000).toISOString(),
              completed_at: new Date().toISOString(),
              duration: Math.floor(Math.random() * 5) + 1,
              output: { result: `Simulated result for step ${step.name}` }
            });
          });
          
          workflowExecutions[idx] = {
            ...execution,
            status: 'completed',
            completed_at: new Date().toISOString(),
            step_results: stepResults
          };
        }
      }, 5000); // Simulate a 5-second execution
      
      return NextResponse.json(execution);
    }
    
    // Regular workflow creation
    const newWorkflow: WorkflowNode = {
      id: `wf-${nextWorkflowId++}`,
      ...body,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    
    workflows.push(newWorkflow);
    return NextResponse.json(newWorkflow);
  } catch (error) {
    return NextResponse.json(
      { error: 'Invalid request', details: (error as Error).message },
      { status: 400 }
    );
  }
}

export async function PUT(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const pathParts = url.pathname.split('/');
    const workflowId = pathParts[pathParts.length - 1];
    
    const workflowIndex = workflows.findIndex(wf => wf.id === workflowId);
    if (workflowIndex === -1) {
      return NextResponse.json({ error: 'Workflow not found' }, { status: 404 });
    }
    
    const updates = await req.json();
    
    workflows[workflowIndex] = {
      ...workflows[workflowIndex],
      ...updates,
      updated_at: new Date().toISOString()
    } as WorkflowNode;
    
    return NextResponse.json(workflows[workflowIndex]);
  } catch (error) {
    return NextResponse.json(
      { error: 'Invalid request', details: (error as Error).message },
      { status: 400 }
    );
  }
}

export async function DELETE(req: NextRequest) {
  const url = new URL(req.url);
  const pathParts = url.pathname.split('/');
  const workflowId = pathParts[pathParts.length - 1];
  
  const initialLength = workflows.length;
  workflows = workflows.filter(wf => wf.id !== workflowId);
  
  if (workflows.length === initialLength) {
    return NextResponse.json({ error: 'Workflow not found' }, { status: 404 });
  }
  
  return NextResponse.json({ success: true });
}