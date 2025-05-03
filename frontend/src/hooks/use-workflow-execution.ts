// src/hooks/use-workflow-execution.ts
import { useState, useEffect, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { config } from '@/lib/env-config';
import { WorkflowNode, WorkflowExecutionUpdate } from '@/lib/workflow/types';

/**
 * Hook to track real-time workflow execution via WebSockets
 * @param executionId The ID of the execution to track
 * @param nodes The workflow nodes to update
 * @param setNodes Function to update nodes
 */
export function useWorkflowExecution(
  executionId: string | null,
  nodes: WorkflowNode[],
  setNodes: React.Dispatch<React.SetStateAction<WorkflowNode[]>>
) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WorkflowExecutionUpdate | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const queryClient = useQueryClient();

  // Handle updating a node's status
  const updateNodeStatus = useCallback(
    (nodeId: string, status: string, message?: string) => {
      setNodes((prevNodes) =>
        prevNodes.map((node) => {
          if (node.id === nodeId) {
            return {
              ...node,
              data: {
                ...node.data,
                status: status as 'pending' | 'running' | 'completed' | 'failed' | 'warning',
                message: message || node.data.message,
              },
            };
          }
          return node;
        })
      );
    },
    [setNodes]
  );

  // Set up WebSocket connection for real-time updates
  useEffect(() => {
    if (!executionId) return;

    const wsUrl = `${config.api.wsBaseUrl}/workflows/executions/${executionId}`;
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log(`WebSocket connected for execution ${executionId}`);
      setIsConnected(true);
      setError(null);
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WorkflowExecutionUpdate;
        setLastMessage(message);

        // Update node status
        if (message.nodeId) {
          updateNodeStatus(message.nodeId, message.status, message.message);
        }

        // If we get a completion message, invalidate the execution query
        if (message.status === 'completed' || message.status === 'failed') {
          queryClient.invalidateQueries(['workflow-execution', executionId]);
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    socket.onerror = (event) => {
      console.error('WebSocket error:', event);
      setIsConnected(false);
      setError(new Error('Failed to connect to execution WebSocket'));
    };

    socket.onclose = () => {
      console.log('WebSocket connection closed');
      setIsConnected(false);
    };

    // Clean up WebSocket on unmount
    return () => {
      socket.close();
    };
  }, [executionId, queryClient, updateNodeStatus]);

  // Method to manually update node status (useful for testing)
  const updateNode = useCallback(
    (nodeId: string, status: 'pending' | 'running' | 'completed' | 'failed' | 'warning', message?: string) => {
      updateNodeStatus(nodeId, status, message);
    },
    [updateNodeStatus]
  );

  return {
    isConnected,
    lastMessage,
    error,
    updateNode, // Expose this for manual updates/testing
  };
}