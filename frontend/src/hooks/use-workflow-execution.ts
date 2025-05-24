// src/hooks/use-workflow-execution.ts
import { useState, useEffect, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Node as ReactFlowNode } from 'reactflow'; // Import ReactFlowNode
import { config } from '@/lib/env-config';
import { WorkflowNodeData, WorkflowExecutionUpdate } from '@/lib/workflow/types'; // Corrected import

/**
 * Hook to track real-time workflow execution via WebSockets
 * @param executionId The ID of the execution to track
 * @param setNodes Function to update nodes (from useNodesState)
 */
export function useWorkflowExecution(
  executionId: string | null,
  // The `nodes` parameter is not strictly used by this hook's internal logic for updates,
  // as updates are done via the functional form of `setNodes`.
  // If it were to be used (e.g., for reading current node state outside `setNodes`),
  // it should be typed as ReactFlowNode<WorkflowNodeData>[] and added to dependencies carefully.
  // nodes: ReactFlowNode<WorkflowNodeData>[], 
  setNodes: React.Dispatch<React.SetStateAction<ReactFlowNode<WorkflowNodeData>[]>> // Corrected type for setNodes
) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WorkflowExecutionUpdate | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const queryClient = useQueryClient();

  // Handle updating a node's status
  const updateNodeStatus = useCallback(
    (nodeId: string, newExecutionStatus: WorkflowExecutionUpdate['status'], message?: string) => {
      setNodes((prevNodes) =>
        prevNodes.map((node) => { // prevNodes are ReactFlowNode<WorkflowNodeData>[]
          if (node.id === nodeId) {
            let visualNodeStatus = node.data.status; // Keep current visual status by default

            // Map WorkflowExecutionUpdate status to WorkflowNodeData status
            // 'warning' from execution update might not have a direct visual equivalent in WorkflowNodeData['status']
            // Decide how to handle 'warning': ignore for visual status, or map if WorkflowNodeData.status is extended.
            if (newExecutionStatus === 'pending' || newExecutionStatus === 'running' || newExecutionStatus === 'completed' || newExecutionStatus === 'failed') {
              visualNodeStatus = newExecutionStatus;
            }
            // If newExecutionStatus is 'warning', visualNodeStatus remains unchanged from node.data.status,
            // but the message will be updated.

            return {
              ...node, // Spread existing node properties (id, position, type, etc.)
              data: {
                ...node.data, // Spread existing data properties
                status: visualNodeStatus,
                // If incoming message is undefined, keep the old one.
                // If you want undefined to clear the message, use `message: message`
                message: message !== undefined ? message : node.data.message, 
              },
            };
          }
          return node;
        })
      );
    },
    [setNodes] // Dependency on setNodes (which is stable)
  );

  // Connect to the WebSocket server
  useEffect(() => {
    if (!executionId) {
      // If there was a previous connection, ensure it's cleaned up or state is reset
      setIsConnected(false);
      setLastMessage(null);
      // setError(null); // Optionally reset error, or let it persist if it was from a previous attempt
      return;
    }

    const wsUrl = `${config.api.wsBaseUrl}/workflows/executions/${executionId}`;
    console.log(`Connecting to WebSocket at ${wsUrl}`);
    
    let socket: WebSocket | null = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const reconnectDelay = 2000; // 2 seconds
    let unmounted = false; // Flag to prevent actions on unmounted component
    
    const setupWebSocket = () => {
      if (unmounted) return; // Don't setup if component unmounted

      socket = new WebSocket(wsUrl);
      
      socket.onopen = () => {
        if (unmounted) return;
        console.log(`WebSocket connected for execution ${executionId}`);
        setIsConnected(true);
        setError(null);
        reconnectAttempts = 0;
      };

      socket.onmessage = (event) => {
        if (unmounted) return;
        try {
          const messageData = JSON.parse(event.data as string) as WorkflowExecutionUpdate;
          setLastMessage(messageData);

          if (messageData.nodeId) {
            updateNodeStatus(messageData.nodeId, messageData.status, messageData.message);
          }

          if (messageData.status === 'completed' || messageData.status === 'failed') {
            queryClient.invalidateQueries({ queryKey: ['workflow-execution', executionId] });
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
          // Optionally set an error state here if parsing fails consistently
        }
      };

      socket.onerror = (event) => {
        if (unmounted) return;
        console.error('WebSocket error:', event);
        // Don't setIsConnected(false) here directly, onclose will handle it.
        // Differentiate between connection error and runtime error if possible.
        setError(new Error('WebSocket connection encountered an error.'));
      };

      socket.onclose = (event) => {
        if (unmounted) return;
        console.log(`WebSocket connection closed: ${event.code} ${event.reason}`);
        setIsConnected(false); // Always set to false on close
        
        if (event.code !== 1000 && event.code !== 1005 /* Normal Closure / No Status Recvd */ && reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++;
          console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`);
          setTimeout(setupWebSocket, reconnectDelay);
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          setError(new Error(`Failed to connect to WebSocket after ${maxReconnectAttempts} attempts.`));
        }
        // If it's a normal closure (1000), or we've exceeded attempts, don't set a new error unless it's not already set.
      };
    };
    
    setupWebSocket();
    
    return () => {
      unmounted = true;
      if (socket) {
        // Ensure onclose and onerror handlers are cleared to prevent them from running after unmount
        // especially if they have logic tied to component state (like setTimeout for reconnect)
        socket.onopen = null;
        socket.onmessage = null;
        socket.onerror = null;
        socket.onclose = null;
        if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
          socket.close(1000, 'Component unmounted');
        }
      }
    };
  }, [executionId, queryClient, updateNodeStatus]); // updateNodeStatus is stable due to its own useCallback

  // Method to manually update node status (useful for testing or imperative updates)
  // The `status` type here should match `WorkflowExecutionUpdate['status']` for consistency with how `updateNodeStatus` handles it.
  const updateNode = useCallback(
    (nodeId: string, status: WorkflowExecutionUpdate['status'], message?: string) => {
      updateNodeStatus(nodeId, status, message);
    },
    [updateNodeStatus]
  );

  return {
    isConnected,
    lastMessage,
    error,
    updateNode,
  };
}