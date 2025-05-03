// src/components/workflows/workflow-detail.tsx
import { useState } from 'react';
import Link from 'next/link';
import { useWorkflowById, useExecuteWorkflow, useWorkflowExecution } from '@/hooks/use-workflows';
import { Workflow, WorkflowStep } from '@/lib/workflow/client';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  AlertCircleIcon, 
  ArrowLeftIcon, 
  CheckCircleIcon, 
  ClockIcon, 
  LoaderIcon, 
  PencilIcon, 
  PlayIcon, 
  StopCircleIcon 
} from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

interface WorkflowDetailProps {
  workflowId: string;
}

export function WorkflowDetail({ workflowId }: WorkflowDetailProps) {
  const { data: workflow, isLoading, error } = useWorkflowById(workflowId);
  const [activeTab, setActiveTab] = useState('overview');
  const [executionId, setExecutionId] = useState<string | null>(null);
  
  const executeWorkflow = useExecuteWorkflow();
  const { data: execution } = useWorkflowExecution(executionId || '');
  
  const handleExecute = async () => {
    try {
      const result = await executeWorkflow.mutateAsync({ workflowId });
      setExecutionId(result.id);
      toast({
        title: 'Workflow execution started',
        description: 'You can track the progress in the Execution tab.',
      });
      setActiveTab('execution');
    } catch (err) {
      toast({
        title: 'Failed to execute workflow',
        description: (err as Error).message,
        variant: 'destructive',
      });
    }
  };
  
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" disabled>
            <ArrowLeftIcon className="h-4 w-4" />
          </Button>
          <Skeleton className="h-8 w-64" />
        </div>
        
        <div className="grid gap-6">
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }
  
  if (error || !workflow) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/workflows">
              <ArrowLeftIcon className="h-4 w-4" />
            </Link>
          </Button>
          <h1 className="text-2xl font-bold">Error</h1>
        </div>
        
        <div className="p-6 border border-red-300 bg-red-50 rounded-md text-red-800">
          <h3 className="font-bold mb-2">Failed to load workflow</h3>
          <p>{(error as Error)?.message || 'Workflow not found'}</p>
        </div>
        
        <Button asChild>
          <Link href="/workflows">Back to Workflows</Link>
        </Button>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/workflows">
              <ArrowLeftIcon className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{workflow.name}</h1>
            <p className="text-muted-foreground">{workflow.description}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge 
            variant={
              workflow.status === 'active' ? 'default' :
              workflow.status === 'draft' ? 'secondary' :
              workflow.status === 'completed' ? 'success' :
              'destructive'
            }
          >
            {workflow.status}
          </Badge>
          
          <Button asChild variant="outline">
            <Link href={`/workflows/${workflowId}/edit`}>
              <PencilIcon className="h-4 w-4 mr-2" />
              Edit
            </Link>
          </Button>
          
          <Button 
            disabled={workflow.status !== 'active' || executeWorkflow.isPending} 
            onClick={handleExecute}
          >
            {executeWorkflow.isPending ? (
              <>
                <LoaderIcon className="h-4 w-4 mr-2 animate-spin" />
                Starting...
              </>
            ) : (
              <>
                <PlayIcon className="h-4 w-4 mr-2" />
                Execute
              </>
            )}
          </Button>
        </div>
      </div>
      
      <div className="flex flex-wrap gap-1 mb-2">
        {workflow.tags.map((tag) => (
          <Badge key={tag} variant="outline">
            {tag}
          </Badge>
        ))}
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="steps">Steps</TabsTrigger>
          <TabsTrigger value="execution">
            Execution
            {execution && (
              <Badge 
                variant={
                  execution.status === 'in_progress' ? 'default' :
                  execution.status === 'pending' ? 'secondary' :
                  execution.status === 'completed' ? 'success' :
                  'destructive'
                }
                className="ml-2"
              >
                {execution.status}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Workflow Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-semibold mb-1">Status</h4>
                  <Badge 
                    variant={
                      workflow.status === 'active' ? 'default' :
                      workflow.status === 'draft' ? 'secondary' :
                      workflow.status === 'completed' ? 'success' :
                      'destructive'
                    }
                  >
                    {workflow.status}
                  </Badge>
                </div>
                
                <div>
                  <h4 className="text-sm font-semibold mb-1">Steps</h4>
                  <p>{workflow.steps.length}</p>
                </div>
                
                <div>
                  <h4 className="text-sm font-semibold mb-1">Created</h4>
                  <p>{new Date(workflow.created_at).toLocaleString()}</p>
                </div>
                
                <div>
                  <h4 className="text-sm font-semibold mb-1">Last Updated</h4>
                  <p>{new Date(workflow.updated_at).toLocaleString()}</p>
                </div>
              </div>
              
              {workflow.metadata && (
                <div>
                  <h4 className="text-sm font-semibold mb-1">Metadata</h4>
                  <pre className="bg-muted p-4 rounded-md text-xs overflow-auto">
                    {JSON.stringify(workflow.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="steps" className="space-y-4">
          <WorkflowSteps steps={workflow.steps} />
        </TabsContent>
        
        <TabsContent value="execution" className="space-y-4">
          {execution ? (
            <WorkflowExecution execution={execution} steps={workflow.steps} />
          ) : (
            <div className="text-center p-12 border border-dashed rounded-lg">
              <p className="text-muted-foreground mb-4">
                No active execution. Start the workflow to see execution details.
              </p>
              <Button 
                onClick={handleExecute}
                disabled={workflow.status !== 'active' || executeWorkflow.isPending}
              >
                {executeWorkflow.isPending ? (
                  <>
                    <LoaderIcon className="h-4 w-4 mr-2 animate-spin" />
                    Starting...
                  </>
                ) : (
                  <>
                    <PlayIcon className="h-4 w-4 mr-2" />
                    Execute Workflow
                  </>
                )}
              </Button>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface WorkflowStepsProps {
  steps: WorkflowStep[];
}

function WorkflowSteps({ steps }: WorkflowStepsProps) {
  if (steps.length === 0) {
    return (
      <div className="text-center p-12 border border-dashed rounded-lg">
        <p className="text-muted-foreground">
          This workflow has no steps defined.
        </p>
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      {steps.map((step, index) => (
        <Card key={step.id}>
          <CardHeader className="pb-2">
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="flex items-center">
                  <span className="bg-primary text-primary-foreground w-6 h-6 rounded-full flex items-center justify-center text-sm mr-2">
                    {index + 1}
                  </span>
                  {step.name}
                </CardTitle>
                <CardDescription>{step.description}</CardDescription>
              </div>
              <Badge>
                {step.type}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="text-sm font-semibold mb-1">Target</h4>
                <p className="text-sm truncate">{step.target_id}</p>
              </div>
              
              {step.dependencies.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold mb-1">Dependencies</h4>
                  <div className="flex flex-wrap gap-1">
                    {step.dependencies.map((depId) => (
                      <Badge key={depId} variant="outline" className="text-xs">
                        {depId}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              
              {step.parameters && Object.keys(step.parameters).length > 0 && (
                <div className="col-span-2">
                  <h4 className="text-sm font-semibold mb-1">Parameters</h4>
                  <pre className="bg-muted p-2 rounded-md text-xs overflow-auto">
                    {JSON.stringify(step.parameters, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

interface WorkflowExecutionProps {
  execution: WorkflowExecution;
  steps: WorkflowStep[];
}

function WorkflowExecution({ execution, steps }: WorkflowExecutionProps) {
  const isPending = execution.status === 'pending';
  const isInProgress = execution.status === 'in_progress';
  const isCompleted = execution.status === 'completed';
  const isFailed = execution.status === 'failed';
  
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Execution Status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="text-sm font-semibold mb-1">Status</h4>
              <Badge 
                variant={
                  isInProgress ? 'default' :
                  isPending ? 'secondary' :
                  isCompleted ? 'success' :
                  'destructive'
                }
              >
                {execution.status}
              </Badge>
            </div>
            
            <div>
              <h4 className="text-sm font-semibold mb-1">Started</h4>
              <p>{new Date(execution.started_at).toLocaleString()}</p>
            </div>
            
            {execution.completed_at && (
              <div>
                <h4 className="text-sm font-semibold mb-1">Completed</h4>
                <p>{new Date(execution.completed_at).toLocaleString()}</p>
              </div>
            )}
            
            {isFailed && execution.metadata?.error && (
              <div className="col-span-2">
                <h4 className="text-sm font-semibold mb-1">Error</h4>
                <div className="bg-red-50 border border-red-200 p-2 rounded-md text-red-700 text-sm">
                  {execution.metadata.error}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
      
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Step Results</h3>
        
        {steps.map((step, index) => {
          const stepResult = execution.step_results[step.id];
          const stepStatus = stepResult?.status || 'pending';
          
          return (
            <Card key={step.id}>
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="flex items-center">
                      <span className="bg-primary text-primary-foreground w-6 h-6 rounded-full flex items-center justify-center text-sm mr-2">
                        {index + 1}
                      </span>
                      {step.name}
                    </CardTitle>
                    <CardDescription>{step.description}</CardDescription>
                  </div>
                  <div className="flex items-center">
                    {stepStatus === 'pending' && <ClockIcon className="h-4 w-4 text-muted-foreground mr-2" />}
                    {stepStatus === 'in_progress' && <LoaderIcon className="h-4 w-4 text-blue-500 animate-spin mr-2" />}
                    {stepStatus === 'completed' && <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2" />}
                    {stepStatus === 'failed' && <AlertCircleIcon className="h-4 w-4 text-red-500 mr-2" />}
                    <Badge 
                      variant={
                        stepStatus === 'in_progress' ? 'default' :
                        stepStatus === 'pending' ? 'secondary' :
                        stepStatus === 'completed' ? 'success' :
                        'destructive'
                      }
                    >
                      {stepStatus}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {stepResult ? (
                  <div className="space-y-2">
                    {stepResult.started_at && (
                      <div className="text-xs text-muted-foreground">
                        Started: {new Date(stepResult.started_at).toLocaleString()}
                        {stepResult.completed_at && (
                          <> • Completed: {new Date(stepResult.completed_at).toLocaleString()}</>
                        )}
                        {stepResult.duration && (
                          <> • Duration: {stepResult.duration}s</>
                        )}
                      </div>
                    )}
                    
                    {stepResult.output && (
                      <div>
                        <h4 className="text-sm font-semibold mb-1">Output</h4>
                        <pre className="bg-muted p-2 rounded-md text-xs overflow-auto max-h-64">
                          {typeof stepResult.output === 'object' 
                            ? JSON.stringify(stepResult.output, null, 2) 
                            : stepResult.output}
                        </pre>
                      </div>
                    )}
                    
                    {stepResult.error && (
                      <div>
                        <h4 className="text-sm font-semibold mb-1">Error</h4>
                        <div className="bg-red-50 border border-red-200 p-2 rounded-md text-red-700 text-sm">
                          {stepResult.error}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center p-4 text-muted-foreground">
                    {isPending || isInProgress ? "Waiting to start..." : "No result data available"}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}