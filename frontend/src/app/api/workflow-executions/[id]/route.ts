// src/app/api/workflow-executions/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { WorkflowExecution } from '@/lib/workflow/types';

// Sample execution data for testing
const sampleExecutions: WorkflowExecution[] = [
  {
    id: 'exec-123',
    workflow_id: 'wf-123',
    status: 'completed',
    started_at: '2025-05-01T09:30:00Z',
    completed_at: '2025-05-01T09:35:00Z',
    step_results: {
      'step-1': {
        status: 'completed',
        started_at: '2025-05-01T09:30:00Z',
        completed_at: '2025-05-01T09:32:00Z',
        duration: 2,
        output: { 
          result: 'Gathered research information on AI developments',
          sources: ['MIT Technology Review', 'AI Research Journal']
        }
      },
      'step-2': {
        status: 'completed',
        started_at: '2025-05-01T09:32:00Z',
        completed_at: '2025-05-01T09:34:00Z',
        duration: 2,
        output: { 
          analysis: 'Trends indicate increased adoption of multimodal AI systems',
          confidence: 0.85
        }
      },
      'step-3': {
        status: 'completed',
        started_at: '2025-05-01T09:34:00Z',
        completed_at: '2025-05-01T09:35:00Z',
        duration: 1,
        output: { 
          report_url: '/reports/ai-trends-2025.md',
          summary: 'Report on multimodal AI adoption trends in 2025'
        }
      }
    }
  },
  {
    id: 'exec-456',
    workflow_id: 'wf-456',
    status: 'failed',
    started_at: '2025-05-01T10:15:00Z',
    completed_at: '2025-05-01T10:16:30Z',
    step_results: {
      'step-1': {
        status: 'completed',
        started_at: '2025-05-01T10:15:00Z',
        completed_at: '2025-05-01T10:15:30Z',
        duration: 0.5,
        output: { 
          issues_found: 12,
          severity: { high: 2, medium: 5, low: 5 }
        }
      },
      'step-2': {
        status: 'failed',
        started_at: '2025-05-01T10:15:30Z',
        completed_at: '2025-05-01T10:16:30Z',
        duration: 1,
        error: 'Failed to connect to code repository'
      }
    },
    metadata: {
      error: 'Workflow failed at step "AI Code Review"'
    }
  }
];

// In-memory storage for testing
let executions: WorkflowExecution[] = [...sampleExecutions];

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const executionId = params.id;
  
  // Find the requested execution
  const execution = executions.find(exec => exec.id === executionId);
  
  if (!execution) {
    return NextResponse.json(
      { error: 'Execution not found' }, 
      { status: 404 }
    );
  }
  
  return NextResponse.json(execution);
}

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const executionId = params.id;
  const urlPath = req.nextUrl.pathname;
  
  // Check if this is a cancel request
  if (urlPath.endsWith('/cancel')) {
    const executionIndex = executions.findIndex(exec => exec.id === executionId);
    
    if (executionIndex === -1) {
      return NextResponse.json(
        { error: 'Execution not found' }, 
        { status: 404 }
      );
    }
    
    // Only allow cancellation of pending or in-progress executions
    const execution = executions[executionIndex];
    if (execution.status !== 'pending' && execution.status !== 'in_progress') {
      return NextResponse.json(
        { error: 'Cannot cancel execution with status: ' + execution.status }, 
        { status: 400 }
      );
    }
    
    // Update the execution status
    executions[executionIndex] = {
      ...execution,
      status: 'canceled',
      completed_at: new Date().toISOString(),
      metadata: {
        ...execution.metadata,
        canceled_reason: 'Canceled by user request'
      }
    };
    
    return NextResponse.json(executions[executionIndex]);
  }
  
  // For any other POST requests, return an error
  return NextResponse.json(
    { error: 'Unsupported operation' }, 
    { status: 400 }
  );
}