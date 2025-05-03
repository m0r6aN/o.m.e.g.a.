# OMEGA Workflow Integration

This document provides an overview of the workflow management system we've integrated into the OMEGA Framework UI.

## Components Created

### Client Libraries
- **Workflow Client** (`src/lib/workflow/client.ts`): API client for workflow operations
- **Environment Config** (`src/lib/env-config.ts`): Utility for managing environment variables

### React Hooks
- **Workflow Hooks** (`src/hooks/use-workflows.ts`): Custom React hooks for managing workflow state

### UI Components
- **Workflow List** (`src/components/workflows/workflow-list.tsx`): Component for displaying and filtering workflows
- **Workflow Detail** (`src/components/workflows/workflow-detail.tsx`): Component for viewing workflow details and execution
- **Workflow Create Form** (`src/components/workflows/workflow-create-form.tsx`): Form for creating new workflows

### Next.js Pages
- **Workflows Page** (`src/app/workflows/page.tsx`): Main workflows listing page
- **Workflow Details Page** (`src/app/workflows/[id]/page.tsx`): Page for viewing workflow details
- **Create Workflow Page** (`src/app/workflows/create/page.tsx`): Page for creating new workflows

### API Routes
- **Workflows API** (`src/app/api/workflows/route.ts`): API endpoints for workflow CRUD operations
- **Workflow Executions API** (`src/app/api/workflow-executions/[id]/route.ts`): API for workflow execution operations

### Configuration
- **Environment Variables** (`.env.local`): Configuration for Docker container ports and service URLs

## Features Implemented

- **Workflow Management**: Create, read, update, delete workflows
- **Workflow Execution**: Execute workflows and monitor their progress
- **Step Configuration**: Define and configure workflow steps
- **Dependency Management**: Set up dependencies between workflow steps
- **Templates**: Apply pre-defined templates to quickly create workflows
- **Filtering**: Filter workflows by tags
- **Status Tracking**: View current workflow status and execution details

## Integration with OMEGA Framework

The workflow system integrates with the broader OMEGA Framework through:

1. **MCP Protocol**: Workflows can target both agents (via A2A protocol) and tools (via MCP protocol)
2. **Registry Services**: Discovers available agents and tools dynamically
3. **Environment Configuration**: Uses centralized configuration for service discovery

## Docker Integration

All workflow components are Docker-ready with appropriate port mappings:

- **Workflow Template Registry**: Port 9403
- **Collaborative Workflow Generator**: Port 9404
- **Template Discovery Service**: Port 9405

## Next Steps

1. **Workflow Visualization**: Implement a drag-and-drop workflow builder interface
2. **Advanced Execution**: Add real-time monitoring with WebSocket updates
3. **Agent Integration**: Enhance integration with OMEGA agents ecosystem
4. **DAG Support**: Add support for non-linear workflow execution with branching
5. **Error Handling**: Implement robust error recovery for workflow steps
6. **Runtime Parameters**: Support providing parameters at execution time
7. **Persistence**: Connect to a database for persistent workflow storage

## Usage Examples

### Creating a Workflow

```tsx
// In a component
const { mutate, isPending } = useCreateWorkflow();

// Later, when submitting the form
mutate({
  name: "My Workflow",
  description: "A workflow that does something awesome",
  status: "active",
  steps: [...],
  tags: ["example", "documentation"]
});
```

### Executing a Workflow

```tsx
// In a component
const { mutate } = useExecuteWorkflow();
const [executionId, setExecutionId] = useState(null);

// Later, when triggering execution
const handleExecute = async () => {
  const result = await mutate({ workflowId });
  setExecutionId(result.id);
};
```

### Monitoring Execution

```tsx
// In a component
const { data: execution, isLoading } = useWorkflowExecution(executionId);

// In the render function
if (isLoading) {
  return <LoadingIndicator />;
}

return (
  <div>
    <div>Status: {execution.status}</div>
    <div>Steps: {Object.keys(execution.step_results).length}</div>
  </div>
);
```