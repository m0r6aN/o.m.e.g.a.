// src/components/tools/tool-detail.tsx
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Card, 
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle 
} from '@/components/ui/card';
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from '@/components/ui/tabs';
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  ArrowLeft,
  RefreshCw,
  Trash2,
  Edit,
  Terminal,
  Server,
  Heart,
  Clock,
  Shield
} from 'lucide-react';

import { Tool } from '@/types';

import { ToolOverviewTab } from './tool-tabs/overview-tab';

import { ToolUsageTab } from './tool-tabs/usage-tab';
import { ToolCapabilitiesTab, ToolSettingsTab } from './tool-tabs';

// Fetch a single tool by ID
async function fetchTool(id: string): Promise<Tool> {
  const response = await fetch(`/api/tools/${id}`);
  if (!response.ok) {
    throw new Error('Failed to fetch tool details');
  }
  return response.json();
}

// Send a heartbeat ping to a tool
async function sendHeartbeat(id: string): Promise<{ success: boolean }> {
  const response = await fetch(`/api/tools/${id}/heartbeat`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to send heartbeat');
  }
  return response.json();
}

interface ToolDetailProps {
  toolId: string;
}

export function ToolDetail({ toolId }: ToolDetailProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('overview');
  
  // Fetch tool details
  const { 
    data: tool, 
    isLoading, 
    isError,
    error,
    refetch 
  } = useQuery({
    queryKey: ['tool', toolId],
    queryFn: () => fetchTool(toolId),
  });

  // Heartbeat mutation
  const heartbeatMutation = useMutation({
    mutationFn: () => sendHeartbeat(toolId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tool', toolId] });
    },
  });

  // Unregister tool mutation
  const unregisterMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`/api/tools/${toolId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to unregister tool');
      }
      return response.json();
    },
    onSuccess: () => {
      router.push('/tools');
    },
  });

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <Skeleton className="h-8 w-1/3" />
        </div>
        
        <Card>
          <CardHeader>
            <Skeleton className="h-8 w-1/4 mb-2" />
            <Skeleton className="h-4 w-3/4" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
          <h3 className="text-lg font-semibold text-red-800">Error loading tool details</h3>
          <p className="text-red-600">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
          <Button 
            onClick={() => refetch()} 
            variant="outline" 
            className="mt-4"
          >
            <RefreshCw className="mr-2 h-4 w-4" /> Try Again
          </Button>
        </div>
      </div>
    );
  }

  if (!tool) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        
        <div className="p-6 bg-amber-50 border border-amber-200 rounded-lg">
          <h3 className="text-lg font-semibold text-amber-800">Tool not found</h3>
          <p className="text-amber-600">
            The tool you're looking for doesn't exist or has been unregistered.
          </p>
          <Button 
            onClick={() => router.push('/tools')} 
            variant="outline" 
            className="mt-4"
          >
            View All Tools
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-center">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              {tool.name}
              <Badge 
                className={
                  tool.status === 'active' 
                    ? 'bg-green-500 text-white' 
                    : 'bg-red-500 text-white'
                }
              >
                {tool.status}
              </Badge>
            </h1>
            <p className="text-gray-500">{tool.description}</p>
          </div>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => heartbeatMutation.mutate()}
            disabled={heartbeatMutation.isPending}
          >
            {heartbeatMutation.isPending ? (
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Heart className="mr-2 h-4 w-4" />
            )}
            Send Heartbeat
          </Button>

          <Button
            variant="outline"
            onClick={() => router.push(`/tools/${toolId}/edit`)}
          >
            <Edit className="mr-2 h-4 w-4" />
            Edit
          </Button>
          
          <Button
            variant="default"
            onClick={() => router.push(`/tools/${toolId}/call`)}
          >
            <Terminal className="mr-2 h-4 w-4" />
            Call Tool
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-4 w-full md:w-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="capabilities">Capabilities</TabsTrigger>
          <TabsTrigger value="usage">Usage</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>
        
        {/* Overview Tab */}
        <TabsContent value="overview">
          <ToolOverviewTab tool={tool} />
        </TabsContent>
        
        {/* Capabilities Tab */}
        <TabsContent value="capabilities">
          <ToolCapabilitiesTab 
            tool={tool} 
            toolId={toolId} 
            router={router} 
          />
        </TabsContent>
        
        {/* Usage Tab */}
        <TabsContent value="usage">
          <ToolUsageTab tool={tool} />
        </TabsContent>
        
        {/* Settings Tab */}
        <TabsContent value="settings">
          <ToolSettingsTab 
            tool={tool} 
            toolId={toolId} 
            router={router} 
            onUnregister={() => unregisterMutation.mutate()}
            isUnregistering={unregisterMutation.isPending}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}