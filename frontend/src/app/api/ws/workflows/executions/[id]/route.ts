// src/app/api/ws/workflows/executions/[id]/route.ts
import { NextResponse } from 'next/server';
import { WebSocketServer } from 'ws';
import { Server } from 'http';
import { Redis } from 'ioredis';

// This is a placeholder for a Next.js API route that would set up WebSockets
// In a real implementation, you would likely use a separate server or service

// Redis client for pub/sub
let redis: Redis | null = null;

// Map of execution IDs to connected clients
const executionClients = new Map<string, Set<WebSocket>>();

// Initialize WebSocket server
let wss: WebSocketServer | null = null;

function initializeWebSocketServer(server: Server) {
  if (wss) return;
  
  wss = new WebSocketServer({ server });
  
  wss.on('connection', (ws, req) => {
    // Parse the execution ID from the URL
    const match = req.url?.match(/\/ws\/workflows\/executions\/([^/]+)/);
    if (!match) {
      ws.close(1003, 'Invalid WebSocket URL');
      return;
    }
    
    const executionId = match[1];
    console.log(`WebSocket connected for execution ${executionId}`);
    
    // Add this client to the execution's set of clients
    if (!executionClients.has(executionId)) {
      executionClients.set(executionId, new Set());
    }
    executionClients.get(executionId)?.add(ws);
    
    // Listen for client disconnection
    ws.on('close', () => {
      console.log(`WebSocket disconnected for execution ${executionId}`);
      executionClients.get(executionId)?.delete(ws);
      if (executionClients.get(executionId)?.size === 0) {
        executionClients.delete(executionId);
      }
    });
  });
  
  // Initialize Redis for pub/sub
  redis = new Redis({
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379'),
  });
  
  // Subscribe to workflow execution updates
  redis.subscribe('workflow:execution:updates');
  
  redis.on('message', (channel, message) => {
    if (channel === 'workflow:execution:updates') {
      try {
        const update = JSON.parse(message);
        const { executionId } = update;
        
        // Send the update to all clients subscribed to this execution
        const clients = executionClients.get(executionId);
        if (clients) {
          clients.forEach((client) => {
            if (client.readyState === WebSocket.OPEN) {
              client.send(JSON.stringify(update));
            }
          });
        }
      } catch (error) {
        console.error('Error processing Redis message:', error);
      }
    }
  });
  
  // Handle server shutdown
  process.on('SIGINT', closeWebSocketServer);
  process.on('SIGTERM', closeWebSocketServer);
}

function closeWebSocketServer() {
  if (wss) {
    console.log('Closing WebSocket server...');
    wss.close(() => {
      console.log('WebSocket server closed.');
    });
    wss = null;
  }
  
  if (redis) {
    console.log('Closing Redis connection...');
    redis.quit();
    redis = null;
  }
}

// Function to publish an update to Redis
export async function publishExecutionUpdate(update: {
  executionId: string;
  workflowId: string;
  nodeId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'warning';
  timestamp: string;
  message?: string;
  data?: any;
}) {
  // Create a Redis client if we haven't already
  const publisher = new Redis({
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379'),
  });
  
  try {
    // Publish the update to Redis
    await publisher.publish('workflow:execution:updates', JSON.stringify(update));
    console.log(`Published update for execution ${update.executionId}, node ${update.nodeId}`);
  } catch (error) {
    console.error('Error publishing execution update:', error);
  } finally {
    // Always close the Redis connection
    publisher.quit();
  }
}

// Next.js API route handler - not actually used for WebSocket connections
// but required for the file to be a valid API route
export async function GET(
  req: Request,
  { params }: { params: { id: string } }
) {
  // WebSocket connections are handled by the WebSocketServer directly
  // This is just here to satisfy Next.js API route requirements
  return NextResponse.json({ message: 'WebSocket endpoint - should not be called directly' });
}