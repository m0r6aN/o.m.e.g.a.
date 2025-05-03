// src/components/workflows/nodes/tool-node.tsx
import React, { memo } from 'react';
import { NodeProps } from 'reactflow';
import { Wrench } from 'lucide-react';
import { BaseNode } from './base-node';

interface ToolNodeData {
  label: string;
  entityId: string;
  capability?: string;
  params?: Record<string, any>;
  status?: 'pending' | 'running' | 'completed' | 'failed' | 'warning';
  message?: string;
}

export const ToolNode = memo(({ id, data, selected, type }: NodeProps<ToolNodeData>) => {
  return (
    <BaseNode
      id={id}
      data={data}
      selected={selected}
      type={type}
      position={{ x: 0, y: 0 }}
      icon={<Wrench className="h-4 w-4" />}
      baseColor="green"
    />
  );
});

ToolNode.displayName = 'ToolNode';