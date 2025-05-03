// src/components/tools/tool-tabs/usage-tab.tsx
import React from 'react';
import { 
  Card, 
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle 
} from '@/components/ui/card';
import {
  Terminal,
  Shield,
  Clock
} from 'lucide-react';

import { Tool } from '../tool-detail';

interface ToolUsageTabProps {
  tool: Tool;
}

export function ToolUsageTab({ tool }: ToolUsageTabProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Usage Statistics</CardTitle>
        <CardDescription>Tool usage metrics and statistics</CardDescription>
      </CardHeader>
      <CardContent>
        {!tool.usage ? (
          <div className="text-center p-12 border border-dashed rounded-lg">
            <h3 className="font-medium text-lg mb-2">No usage data available</h3>
            <p className="text-gray-500 mb-4">
              This tool hasn't been used yet or usage tracking is not enabled.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex flex-col p-4 border rounded-lg">
              <div className="flex items-center mb-2">
                <Terminal className="h-5 w-5 mr-2 text-blue-500" />
                <span className="text-lg font-medium">Total Calls</span>
              </div>
              <span className="text-3xl font-bold">{tool.usage.totalCalls.toLocaleString()}</span>
            </div>
            
            <div className="flex flex-col p-4 border rounded-lg">
              <div className="flex items-center mb-2">
                <Shield className="h-5 w-5 mr-2 text-green-500" />
                <span className="text-lg font-medium">Success Rate</span>
              </div>
              <span className="text-3xl font-bold">{(tool.usage.successRate * 100).toFixed(1)}%</span>
            </div>
            
            <div className="flex flex-col p-4 border rounded-lg">
              <div className="flex items-center mb-2">
                <Clock className="h-5 w-5 mr-2 text-amber-500" />
                <span className="text-lg font-medium">Avg. Response Time</span>
              </div>
              <span className="text-3xl font-bold">{tool.usage.averageResponseTime.toFixed(2)} ms</span>
            </div>
            
            <div className="flex flex-col p-4 border rounded-lg">
              <div className="flex items-center mb-2">
                <Clock className="h-5 w-5 mr-2 text-purple-500" />
                <span className="text-lg font-medium">Last Used</span>
              </div>
              <span className="text-2xl font-bold">
                {new Date(tool.usage.lastUsed).toLocaleString()}
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}