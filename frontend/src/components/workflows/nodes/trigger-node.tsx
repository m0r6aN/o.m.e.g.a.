// src/components/workflows/nodes/trigger-node.tsx
import React, { memo } from 'react';
import { NodeProps } from 'reactflow';
import { MessageSquare, Code, Calendar } from 'lucide-react';
import { BaseNode } from './base-node';

interface TriggerNodeData {
  label: string;
  entityId: string; // 'user_input', 'webhook', or 'schedule'
  params?: Record<string, any>;
  status?: 'pending' | 'running' | 'completed' | 'failed' | 'warning';
  message?: string;
}

export const TriggerNode = memo(({ id, data, selected, type }: NodeProps<TriggerNodeData>) => {
  // Choose icon based on trigger type
  let icon;
  switch (data.entityId) {
    case 'webhook':
      icon = <Code className="h-4 w-4" />;
      break;
    case 'schedule':
      icon = <Calendar className="h-4 w-4" />;
      break;
    case 'user_input':
    default:
      icon = <MessageSquare className="h-4 w-4" />;
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
      baseColor="purple"
      canHaveInputs={false}
    />
  );
});

TriggerNode.displayName = 'TriggerNode';