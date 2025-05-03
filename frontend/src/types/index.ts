// src/types/index.ts
import { Node, Edge } from 'reactflow';

export interface Agent {
  id: string;
  name: string;
  description: string;
  type: string;
  capabilities: string[];
  status: 'active' | 'inactive';
  host?: string;
  port?: number;
  tags?: string[];
  version?: string;
  registeredAt?: string;
  lastHeartbeat?: string;
  metadata?: {
    author?: string;
    documentation?: string;
    repository?: string;
  };
  usage?: {
    totalCalls: number;
    successRate: number;
    averageResponseTime: number;
    lastUsed: string;
  };
  mcp_endpoint?: string;
}

// Tool Capability interface (combined from all tool files)
export interface ToolCapability {
  name: string;
  description: string;
  parameters: Record<string, {
    type: string;
    description?: string;
    required?: boolean;
    example?: any;
  }>;
  returns?: Record<string, {
    type: string;
    description?: string;
  }>;
}

// Tool interface (combined from tool-detail.tsx, tool-caller.tsx, tool-list.tsx, tool-register.tsx)
export interface Tool {
  id: string;
  name: string;
  description: string;
  host: string;
  port: number;
  capabilities: ToolCapability[];
  tags: string[];
  version: string;
  registeredAt: string;
  lastHeartbeat: string;
  status: 'active' | 'inactive';
  metadata?: {
    author?: string;
    documentation?: string;
    repository?: string;
  };
  usage?: {
    totalCalls: number;
    successRate: number;
    averageResponseTime: number;
    lastUsed: string;
  };
  mcp_endpoint: string;
}

export type WorkflowNodeData = {
  label: string;
  entityId: string;
  capability?: string;
  params?: Record<string, any>;
  status?: 'pending' | 'running' | 'completed' | 'failed';
}

export type WorkflowNode = Node<WorkflowNodeData> & {
  type: 'agentNode' | 'toolNode' | 'triggerNode' | 'outputNode';
}

export type WorkflowEdge = Edge & {
  type: 'smoothstep';
  markerEnd: { type: string };
  animated: boolean;
};

export type Workflow = {
  id: string;
  name: string;
  description: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  createdAt: string;
  updatedAt: string;
  status: 'draft' | 'active' | 'inactive';
}
