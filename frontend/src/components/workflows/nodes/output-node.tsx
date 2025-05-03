// src/components/workflows/nodes/output-node.tsx
import React, { memo } from 'react';
import { NodeProps } from 'reactflow';
import { User, Database, Webhook } from 'lucide-react';
import { BaseNode } from './base-node';

interface OutputNodeData {
  label: string;
  entityId: string; // 'user_response', 'webhook', or 'database'
  params?: Record<string, any>;
  status?: 'pending' | 'running' | 'completed' | 'failed' | 'warning';
  message?: string;
}

export const OutputNode = memo(({ id, data, selected, type }: NodeProps<OutputNodeData>) => {
  // Choose icon based on output type
  let icon;
  switch (data.entityId) {
    case 'webhook':
      icon = <Webhook className="h-4 w-4" />;
      break;
    case 'database':
      icon = <Database className="h-4 w-4" />;
      break;
    case 'user_response':
    default:
      icon = <User className="h-4 w-4" />;
      break;
  }

  return (
    <BaseNode
      id={id}
      data={data}
      selected={selected}
      type={type}
      position={{ x: 0, y: 0 }}
      icon={icon}
      baseColor="amber"
      canHaveOutputs={false}
    />
  );
});

OutputNode.displayName = 'OutputNode';