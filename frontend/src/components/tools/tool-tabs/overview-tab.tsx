// src/components/tools/tool-tabs/overview-tab.tsx
import React from 'react';
import { 
  Card, 
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle 
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Server } from 'lucide-react';

import { Tool } from '../tool-detail';

interface ToolOverviewTabProps {
  tool: Tool;
}

export function ToolOverviewTab({ tool }: ToolOverviewTabProps) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Tool Information</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium text-gray-500">Host</h3>
              <p className="mt-1">{tool.host}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Port</h3>
              <p className="mt-1">{tool.port}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Version</h3>
              <p className="mt-1">{tool.version}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Last Heartbeat</h3>
              <p className="mt-1">{new Date(tool.lastHeartbeat).toLocaleString()}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Registered At</h3>
              <p className="mt-1">{new Date(tool.registeredAt).toLocaleString()}</p>
            </div>
          </div>
          
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-2">Tags</h3>
            <div className="flex flex-wrap gap-2">
              {tool.tags.map((tag) => (
                <Badge key={tag} variant="secondary">{tag}</Badge>
              ))}
            </div>
          </div>
          
          {tool.metadata && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Metadata</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {tool.metadata.author && (
                  <div>
                    <span className="text-xs text-gray-500">Author</span>
                    <p className="text-sm">{tool.metadata.author}</p>
                  </div>
                )}
                {tool.metadata.documentation && (
                  <div>
                    <span className="text-xs text-gray-500">Documentation</span>
                    <p className="text-sm">
                      <a 
                        href={tool.metadata.documentation} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-500 hover:underline"
                      >
                        View Documentation
                      </a>
                    </p>
                  </div>
                )}
                {tool.metadata.repository && (
                  <div>
                    <span className="text-xs text-gray-500">Repository</span>
                    <p className="text-sm">
                      <a 
                        href={tool.metadata.repository} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-500 hover:underline"
                      >
                        View Repository
                      </a>
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Endpoint Information</CardTitle>
          <CardDescription>Connection details for this tool</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
            <div className="flex items-center">
              <Server className="h-4 w-4 mr-2 text-gray-500" />
              <span className="text-sm font-medium">MCP Endpoint</span>
            </div>
            <code className="bg-gray-100 px-2 py-1 rounded text-sm">
              {tool.mcp_endpoint}
            </code>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}