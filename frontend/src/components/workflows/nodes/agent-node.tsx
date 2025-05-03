// src/components/workflows/nodes/agent-node.tsx
import React, { memo } from 'react';
import { NodeProps } from 'reactflow';
import { Bot } from 'lucide-react';
import { BaseNode } from './base-node';

interface AgentNodeData {
  label: string;
  entityId: string;
  capability?: string;
  params?: Record<string, any>;
  status?: 'pending' | 'running' | 'completed' | 'failed' | 'warning';
  message?: string;
}

export const AgentNode = memo(({ id, data, selected, type }: NodeProps<AgentNodeData>) => {
  return (
    <BaseNode
      id={id}
      data={data}
      selected={selected}
      type={type}
      position={{ x: 0, y: 0 }}
      icon={<Bot className="h-4 w-4" />}
      baseColor="blue"
    />
  );
});

AgentNode.displayName = 'AgentNode';