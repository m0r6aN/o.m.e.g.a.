# Model Context Protocol (MCP) Integration Guide for OMEGA UI

## Introduction

The OMEGA Framework uses the Model Context Protocol (MCP) for communication between agents, tools, and the UI. This document explains how to integrate MCP into the OMEGA UI for seamless communication with the backend services.

## What is MCP?

MCP (Model Context Protocol) is a standardized communication protocol that enables AI models, tools, and agents to interoperate. It provides a structured way for these components to discover each other's capabilities and exchange data.

Key features of MCP include:
- Tool discovery and execution
- Resource access and management
- Prompt template management
- Capability sharing

## Setting Up MCP Client in OMEGA UI

### 1. MCP Client Setup

Create a TypeScript MCP client for the OMEGA UI:

```typescript
// src/lib/mcp/client.ts
import axios, { AxiosInstance } from 'axios';

export interface McpTool {
  id: string;
  name: string;
  description: string;
  capabilities: McpCapability[];
  mcp_endpoint: string;
  host: string;
  port: number;
  tags: string[];
}

export interface McpCapability {
  name: string;
  description: string;
  parameters: Record<string, any>;
  returns?: Record<string, any>;
}

export class McpClient {
  private axiosInstance: AxiosInstance;
  private registryUrl: string;

  constructor(registryUrl: string) {
    this.registryUrl = registryUrl;
    this.axiosInstance = axios.create({
      baseURL: registryUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Discover all MCP tools registered in the system
  async discoverTools(): Promise<McpTool[]> {
    const response = await this.axiosInstance.get('/mcp/discover');
    return response.data;
  }

  // Get a specific tool by ID
  async getToolById(toolId: string): Promise<McpTool> {
    const response = await this.axiosInstance.get(`/mcp/discover/${toolId}`);
    return response.data;
  }

  // Discover tools by capability
  async discoverToolsByCapability(capability: string): Promise<McpTool[]> {
    const response = await this.axiosInstance.get(`/mcp/discover/capability/${capability}`);
    return response.data;
  }

  // Call a tool with parameters
  async callTool(toolEndpoint: string, toolName: string, params: Record<string, any>): Promise<any> {
    const response = await axios.post(toolEndpoint, {
      name: toolName,
      parameters: params
    });
    return response.data;
  }

  // Find and call a tool by ID
  async findAndCallTool(toolId: string, toolName: string, params: Record<string, any>): Promise<any> {
    const tool = await this.getToolById(toolId);
    if (!tool) {
      throw new Error(`Tool ${toolId} not found`);
    }

    return this.callTool(tool.mcp_endpoint, toolName, params);
  }

  // Register a new MCP tool
  async registerTool(toolData: Omit<McpTool, 'mcp_endpoint'>): Promise<McpTool> {
    const response = await this.axiosInstance.post('/mcp/register', toolData);
    return response.data;
  }

  // Send a heartbeat for a tool
  async sendHeartbeat(toolId: string): Promise<void> {
    await this.axiosInstance.post('/mcp/heartbeat', { id: toolId });
  }

  // Unregister a tool
  async unregisterTool(toolId: string): Promise<void> {
    await this.axiosInstance.delete(`/mcp/unregister/${toolId}`);
  }
}

// Create singleton instance
export const mcpClient = new McpClient(
  process.env.NEXT_PUBLIC_MCP_REGISTRY_URL || 'http://localhost:8080/registry'
);
```

### 2. React Hooks for MCP

Create React hooks to easily use MCP in UI components:

```typescript
// src/hooks/use-mcp-tools.ts
import { useQuery, useMutation, Client } from '@tanstack/react-query';
import { mcpClient, McpTool } from '@/lib/mcp/client';

export function useMcpTools() {
  return useQuery({
    queryKey: ['mcp', 'tools'],
    queryFn: () => mcpClient.discoverTools(),
  });
}

export function useMcpToolById(toolId: string) {
  return useQuery({
    queryKey: ['mcp', 'tool', toolId],
    queryFn: () => mcpClient.getToolById(toolId),
    enabled: !!toolId,
  });
}

export function useMcpToolsByCapability(capability: string) {
  return useQuery({
    queryKey: ['mcp', 'capability', capability],
    queryFn: () => mcpClient.discoverToolsByCapability(capability),
    enabled: !!capability,
  });
}

export function useRegisterMcpTool() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (toolData: Omit<McpTool, 'mcp_endpoint'>) => 
      mcpClient.registerTool(toolData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp', 'tools'] });
    },
  });
}

export function useUnregisterMcpTool() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (toolId: string) => mcpClient.unregisterTool(toolId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp', 'tools'] });
    },
  });
}

export function useCallMcpTool() {
  return useMutation({
    mutationFn: ({ toolId, toolName, params }: { 
      toolId: string; 
      toolName: string; 
      params: Record<string, any> 
    }) => mcpClient.findAndCallTool(toolId, toolName, params),
  });
}
```

## Using MCP in OMEGA UI Components

### 1. Tool Explorer Component

```tsx
// src/components/tools/tool-explorer.tsx
import { useState } from 'react';
import { useMcpTools } from '@/hooks/use-mcp-tools';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export function ToolExplorer() {
  const { data: tools, isLoading, error } = useMcpTools();
  const [selectedTool, setSelectedTool] = useState<string | null>(null);

  if (isLoading) return <div>Loading tools...</div>;
  if (error) return <div>Error loading tools: {(error as Error).message}</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {tools?.map((tool) => (
        <Card 
          key={tool.id}
          className={`cursor-pointer transition-all ${selectedTool === tool.id ? 'ring-2 ring-primary' : ''}`}
          onClick={() => setSelectedTool(tool.id === selectedTool ? null : tool.id)}
        >
          <CardHeader className="pb-2">
            <CardTitle className="flex justify-between items-center">
              {tool.name}
              <div className="flex gap-1">
                {tool.tags.map((tag) => (
                  <Badge key={tag} variant="outline">{tag}</Badge>
                ))}
              </div>
            </CardTitle>
            <CardDescription>{tool.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <h4 className="text-sm font-semibold mb-2">Capabilities:</h4>
            <ul className="space-y-1">
              {tool.capabilities.map((cap) => (
                <li key={cap.name} className="text-sm">
                  {cap.name} - {cap.description}
                </li>
              ))}
            </ul>
            <div className="mt-4 text-xs text-muted-foreground">
              Endpoint: {tool.mcp_endpoint}
            </div>
            <div className="mt-4 flex justify-end">
              <Button size="sm">Call Tool</Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
```

### 2. Tool Registration Form

```tsx
// src/components/tools/tool-registration-form.tsx
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useRegisterMcpTool } from '@/hooks/use-mcp-tools';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Textarea } from '@/components/ui/textarea';
import { toast } from '@/components/ui/use-toast';

const formSchema = z.object({
  id: z.string().min(1, 'Tool ID is required'),
  name: z.string().min(1, 'Tool name is required'),
  description: z.string().min(1, 'Description is required'),
  host: z.string().min(1, 'Host is required'),
  port: z.number().min(1, 'Port is required'),
  tags: z.string(),
  capabilities: z.string(),
});

export function ToolRegistrationForm() {
  const { mutate, isPending } = useRegisterMcpTool();
  
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      id: '',
      name: '',
      description: '',
      host: 'localhost',
      port: 9000,
      tags: '',
      capabilities: JSON.stringify([
        {
          name: 'example_capability',
          description: 'Example capability description',
          parameters: {
            param1: { type: 'string', description: 'Parameter 1' }
          }
        }
      ], null, 2),
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    try {
      const parsedCapabilities = JSON.parse(values.capabilities);
      const parsedTags = values.tags.split(',').map(tag => tag.trim()).filter(Boolean);
      
      mutate({
        id: values.id,
        name: values.name,
        description: values.description,
        host: values.host,
        port: Number(values.port),
        tags: parsedTags,
        capabilities: parsedCapabilities,
      }, {
        onSuccess: () => {
          toast({
            title: 'Tool registered successfully',
            description: `${values.name} has been registered with the MCP registry.`,
          });
          form.reset();
        },
        onError: (error) => {
          toast({
            title: 'Failed to register tool',
            description: (error as Error).message,
            variant: 'destructive',
          });
        }
      });
    } catch (e) {
      toast({
        title: 'Invalid JSON',
        description: 'Please check your capabilities JSON format.',
        variant: 'destructive',
      });
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="id"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Tool ID</FormLabel>
                <FormControl>
                  <Input placeholder="calculator_tool" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Tool Name</FormLabel>
                <FormControl>
                  <Input placeholder="Calculator Tool" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
        
        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description</FormLabel>
              <FormControl>
                <Textarea placeholder="A tool for performing calculations" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="host"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Host</FormLabel>
                <FormControl>
                  <Input placeholder="localhost" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          
          <FormField
            control={form.control}
            name="port"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Port</FormLabel>
                <FormControl>
                  <Input type="number" placeholder="9000" {...field} onChange={e => field.onChange(parseInt(e.target.value))} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
        
        <FormField
          control={form.control}
          name="tags"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Tags (comma-separated)</FormLabel>
              <FormControl>
                <Input placeholder="math,calculator,arithmetic" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={form.control}
          name="capabilities"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Capabilities JSON</FormLabel>
              <FormControl>
                <Textarea className="font-mono h-64" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Registering...' : 'Register Tool'}
        </Button>
      </form>
    </Form>
  );
}
```

### 3. Tool Caller Component

```tsx
// src/components/tools/tool-caller.tsx
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMcpToolById, useCallMcpTool } from '@/hooks/use-mcp-tools';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { toast } from '@/components/ui/use-toast';

interface ToolCallerProps {
  toolId: string;
  capabilityName: string;
}

export function ToolCaller({ toolId, capabilityName }: ToolCallerProps) {
  const { data: tool, isLoading } = useMcpToolById(toolId);
  const { mutate, isPending, data: result } = useCallMcpTool();
  const [paramsSchema, setParamsSchema] = useState<any>(null);
  
  // Find the capability and its parameters
  const capability = tool?.capabilities.find(c => c.name === capabilityName);
  
  // Dynamically create a zod schema based on the tool parameters
  const createDynamicSchema = (params: Record<string, any>) => {
    const schemaObj: Record<string, any> = {};
    
    Object.entries(params).forEach(([key, value]) => {
      if (value.type === 'string') {
        schemaObj[key] = value.required ? z.string() : z.string().optional();
      } else if (value.type === 'number') {
        schemaObj[key] = value.required ? z.number() : z.number().optional();
      } else if (value.type === 'boolean') {
        schemaObj[key] = value.required ? z.boolean() : z.boolean().optional();
      } else {
        // Default to string for unknown types
        schemaObj[key] = value.required ? z.string() : z.string().optional();
      }
    });
    
    return z.object(schemaObj);
  };
  
  // Initialize the form when the tool data loads
  useState(() => {
    if (capability && capability.parameters) {
      const schema = createDynamicSchema(capability.parameters);
      setParamsSchema(schema);
    }
  });
  
  if (isLoading || !tool || !capability) {
    return <div>Loading tool...</div>;
  }
  
  // Create an empty form if parameters schema hasn't been set
  if (!paramsSchema) {
    return <div>No parameters required for this tool</div>;
  }
  
  const form = useForm({
    resolver: zodResolver(paramsSchema),
    defaultValues: Object.fromEntries(
      Object.entries(capability.parameters).map(([key, value]) => [key, ''])
    ),
  });
  
  function onSubmit(values: any) {
    mutate({
      toolId,
      toolName: capabilityName,
      params: values
    }, {
      onSuccess: (data) => {
        toast({
          title: 'Tool executed successfully',
          description: 'The tool returned a result.',
        });
      },
      onError: (error) => {
        toast({
          title: 'Failed to execute tool',
          description: (error as Error).message,
          variant: 'destructive',
        });
      }
    });
  }
  
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{tool.name}: {capabilityName}</CardTitle>
          <CardDescription>{capability.description}</CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              {Object.entries(capability.parameters).map(([key, value]: [string, any]) => (
                <FormField
                  key={key}
                  control={form.control}
                  name={key}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{key}</FormLabel>
                      <FormControl>
                        {value.type === 'string' && value.description?.includes('multiline') ? (
                          <Textarea placeholder={value.description} {...field} />
                        ) : (
                          <Input 
                            type={value.type === 'number' ? 'number' : 'text'} 
                            placeholder={value.description} 
                            {...field} 
                            onChange={e => {
                              if (value.type === 'number') {
                                field.onChange(Number(e.target.value));
                              } else {
                                field.onChange(e.target.value);
                              }
                            }}
                          />
                        )}
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              ))}
              
              <Button type="submit" disabled={isPending}>
                {isPending ? 'Executing...' : 'Execute Tool'}
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
      
      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Result</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-muted p-4 rounded-md overflow-auto">
              {typeof result === 'object' ? JSON.stringify(result, null, 2) : result.toString()}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
```

## MCP Integration Patterns

### 1. Dashboard Integration

The OMEGA UI dashboard can display real-time agent and tool status by integrating MCP discovery:

```tsx
// In your dashboard component:
import { useMcpTools } from '@/hooks/use-mcp-tools';

// Count active tools
const { data: tools } = useMcpTools();
const activeToolsCount = tools?.length || 0;

// Display in dashboard metrics
<MetricCard
  title="Active Tools"
  value={activeToolsCount}
  icon={<Wrench className="h-5 w-5" />}
/>
```

### 2. Workflow Builder Integration

When building workflows, use MCP to discover available agents and tools:

```tsx
// In your workflow builder component:
import { useMcpTools, useMcpToolsByCapability } from '@/hooks/use-mcp-tools';

// Get all tools for the toolbox panel
const { data: allTools } = useMcpTools();

// Get tools with a specific capability for a workflow step
const { data: calculationTools } = useMcpToolsByCapability('calculate');

// Display available tools in the workflow builder toolbox
<ToolboxPanel tools={allTools} onDragTool={handleDragTool} />
```

### 3. Agent Network Visualization

Use MCP discovery to visualize the agent network:

```tsx
// In your network visualization component:
import { useMcpTools } from '@/hooks/use-mcp-tools';

// Transform MCP data to network graph format
const { data: tools } = useMcpTools();

const networkData = React.useMemo(() => {
  if (!tools) return { nodes: [], links: [] };
  
  // Create nodes from tools
  const nodes = tools.map(tool => ({
    id: tool.id,
    type: tool.tags.includes('agent') ? 'agent' : 'tool',
    name: tool.name,
    status: 'active'
  }));
  
  // Create links based on tool capabilities and dependencies
  // This is a simplified example - in reality, you'd need more data
  const links = [];
  
  // Return the network data
  return { nodes, links };
}, [tools]);

// Render with the network graph component
<AgentNetworkGraph data={networkData} />
```

## Best Practices

1. **Error Handling**: Always implement proper error handling for MCP API calls. Servers may be unavailable or tool execution could fail.

2. **Caching**: Use React Query's caching capabilities to minimize API calls to the MCP registry.

3. **Validation**: Validate parameters before calling MCP tools to prevent errors.

4. **Progress Indicators**: Show loading states during MCP operations, as they may take time.

5. **Heartbeats**: For tools registered from the UI, implement a heartbeat mechanism to keep them active in the registry.

6. **Security**: Implement proper authentication and authorization for MCP registry access.

7. **Log Handling**: Create a unified logging view for MCP tool execution results and errors.

## Conclusion

By following this guide, you can effectively integrate the Model Context Protocol into the OMEGA UI, enabling seamless communication with agents and tools in the OMEGA Framework. This integration allows for dynamic discovery, execution, and management of capabilities across the system.
