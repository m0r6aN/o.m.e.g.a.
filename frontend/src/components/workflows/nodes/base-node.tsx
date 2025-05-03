// src/components/workflows/nodes/base-node.tsx
import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  AlertCircle
} from 'lucide-react';

interface BaseNodeData {
  label: string;
  entityId: string;
  capability?: string;
  params?: Record<string, any>;
  status?: 'pending' | 'running' | 'completed' | 'failed' | 'warning';
  message?: string;
}

export interface BaseNodeProps extends NodeProps<BaseNodeData> {
  icon: React.ReactNode;
  baseColor: string;
  canHaveInputs?: boolean;
  canHaveOutputs?: boolean;
}

const statusColors = {
  pending: 'bg-gray-100 text-gray-700 border-gray-300',
  running: 'bg-blue-100 text-blue-700 border-blue-300',
  completed: 'bg-green-100 text-green-700 border-green-300',
  failed: 'bg-red-100 text-red-700 border-red-300',
  warning: 'bg-amber-100 text-amber-700 border-amber-300',
};

const statusIcons = {
  pending: <Clock className="h-4 w-4 mr-1" />,
  running: <RefreshCw className="h-4 w-4 mr-1 animate-spin" />,
  completed: <CheckCircle className="h-4 w-4 mr-1" />,
  failed: <XCircle className="h-4 w-4 mr-1" />,
  warning: <AlertTriangle className="h-4 w-4 mr-1" />,
};

export const BaseNode = memo(
  ({ data, selected, icon, baseColor, canHaveInputs = true, canHaveOutputs = true }: BaseNodeProps) => {
    const status = data.status || 'pending';
    const statusColor = statusColors[status] || statusColors.pending;
    const statusIcon = statusIcons[status] || statusIcons.pending;

    return (
      <div className="group">
        {canHaveInputs && (
          <Handle
            type="target"
            position={Position.Top}
            className={cn(
              "w-3 h-3 border-2 transition-all",
              selected ? `border-${baseColor}-500` : "border-gray-400",
              "group-hover:border-current"
            )}
          />
        )}
        <Card
          className={cn(
            "min-w-[180px] transition-all duration-300 shadow-md", 
            `border-${baseColor}-200`,
            selected ? `ring-2 ring-${baseColor}-500` : "ring-transparent",
            statusColor
          )}
        >
          <CardHeader className="px-3 py-2 flex flex-row items-start space-y-0 gap-2">
            <div className={`p-1.5 rounded-md bg-${baseColor}-100 text-${baseColor}-700`}>
              {icon}
            </div>
            <div className="flex-1">
              <CardTitle className="text-sm font-medium">{data.label}</CardTitle>
              {data.capability && (
                <div className="text-xs text-gray-500">{data.capability}</div>
              )}
            </div>
            <Badge 
              variant="outline" 
              className={cn(
                "ml-auto text-xs transition-all",
                status === 'running' && "animate-pulse"
              )}
            >
              <div className="flex items-center">
                {statusIcon}
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </div>
            </Badge>
          </CardHeader>
          <CardContent className="px-3 py-2 text-xs">
            {data.entityId && <div className="truncate text-gray-500">ID: {data.entityId}</div>}
            {data.message && (
              <div className={cn(
                "mt-1 p-1 rounded text-xs overflow-hidden text-ellipsis",
                status === 'failed' ? "bg-red-50 text-red-700" : 
                status === 'warning' ? "bg-amber-50 text-amber-700" : 
                "bg-gray-50 text-gray-700"
              )}>
                {data.message}
              </div>
            )}
            {data.params && Object.keys(data.params).length > 0 && (
              <div className="mt-1 border-t pt-1">
                <div className="font-medium text-xs text-gray-700">Params:</div>
                <div className="grid grid-cols-1 gap-1 mt-1">
                  {Object.entries(data.params).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="font-medium">{key}:</span>
                      <span className="truncate max-w-[100px]">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        {canHaveOutputs && (
          <Handle
            type="source"
            position={Position.Bottom}
            className={cn(
              "w-3 h-3 border-2 transition-all",
              selected ? `border-${baseColor}-500` : "border-gray-400",
              "group-hover:border-current"
            )}
          />
        )}
      </div>
    );
  }
);

BaseNode.displayName = 'BaseNode';