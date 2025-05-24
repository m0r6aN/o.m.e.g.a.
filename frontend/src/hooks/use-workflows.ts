// src/hooks/use-workflows.ts
import { useQuery, useMutation, useQueryClient, Query } from '@tanstack/react-query';
import { workflowClient, Workflow, WorkflowExecution, WorkflowTemplate } from '@/lib/workflow/client';

// Workflows
export function useWorkflows() {
  return useQuery({
    queryKey: ['workflows'],
    queryFn: () => workflowClient.getWorkflows(),
  });
}

export function useWorkflowById(workflowId: string) {
  return useQuery({
    queryKey: ['workflow', workflowId],
    queryFn: () => workflowClient.getWorkflowById(workflowId),
    enabled: !!workflowId,
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (workflow: Omit<Workflow, 'id' | 'created_at' | 'updated_at'>) => 
      workflowClient.createWorkflow(workflow),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });
}

export function useUpdateWorkflow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ workflowId, updates }: { 
      workflowId: string; 
      updates: Partial<Workflow>;
    }) => workflowClient.updateWorkflow(workflowId, updates),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      queryClient.invalidateQueries({ queryKey: ['workflow', data.id] });
    },
  });
}

export function useDeleteWorkflow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (workflowId: string) => workflowClient.deleteWorkflow(workflowId),
    onSuccess: (_data, workflowId) => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      queryClient.removeQueries({ queryKey: ['workflow', workflowId] });
    },
  });
}

// Workflow Execution
export function useExecuteWorkflow() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ workflowId, parameters }: { 
      workflowId: string; 
      parameters?: Record<string, any>; 
    }) => workflowClient.executeWorkflow(workflowId, parameters),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['workflow-execution', data.id] });
      queryClient.invalidateQueries({ queryKey: ['workflow', data.workflow_id] });
    },
  });
}

export function useWorkflowExecution(executionId: string) {
  return useQuery<WorkflowExecution, Error>({ // Explicitly type query data and error
    queryKey: ['workflow-execution', executionId],
    queryFn: () => workflowClient.getWorkflowExecution(executionId),
    enabled: !!executionId,

    // Poll for updates while execution is in progress (v5 Syntax)
    refetchInterval: (query: Query<WorkflowExecution, Error>) => { // Parameter is the Query object
      // Check if the query was successful AND if the data exists
      if (query.state.status === 'success' && query.state.data) {
        // Access the workflow status from the fetched data within the query state
        const workflowStatus = query.state.data.status;
        return workflowStatus === 'in_progress' || workflowStatus === 'pending'
          ? 2000 // Poll every 2 seconds if workflow is running
          : false; // Stop polling if workflow is completed or failed
      }
      // If query is not successful (e.g., initial load, error) or data is missing,
      // don't start polling based on workflow status yet.
      return false;
    },
    // Optional: You might want staleTime to be 0 if polling frequently
    // staleTime: 0,
  });
}

export function useCancelWorkflowExecution() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (executionId: string) => workflowClient.cancelWorkflowExecution(executionId),
    onSuccess: (_data, executionId) => {
      queryClient.invalidateQueries({ queryKey: ['workflow-execution', executionId] });
    },
  });
}

// Workflow Templates
export function useWorkflowTemplates() {
  return useQuery({
    queryKey: ['workflow-templates'],
    queryFn: () => workflowClient.getWorkflowTemplates(),
  });
}

export function useWorkflowTemplateById(templateId: string) {
  return useQuery({
    queryKey: ['workflow-template', templateId],
    queryFn: () => workflowClient.getWorkflowTemplateById(templateId),
    enabled: !!templateId,
  });
}

export function useCreateWorkflowFromTemplate() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ templateId, parameters }: { 
      templateId: string; 
      parameters?: Record<string, any>; 
    }) => workflowClient.createWorkflowFromTemplate(templateId, parameters),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      queryClient.setQueryData(['workflow', data.id], data);
    },
  });
}