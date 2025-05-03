// src/app/dashboard/page.tsx
'use client';

import React, { useCallback, Suspense, ComponentType } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Bot, Cpu, GitBranch, PanelTop, RefreshCw, Wrench } from 'lucide-react';
import dynamic from 'next/dynamic';
import { AgentNetworkGraphProps } from '@/components/visualizations/agent-network-graph';

// Explicitly type the dynamic import, using default export
const AgentNetworkGraph = dynamic<AgentNetworkGraphProps>( 
  () => import('@/components/visualizations/agent-network-graph').then((mod) => mod.default),
  {
    ssr: false,
    loading: () => <Skeleton className="h-[600px] w-full" />,
  }
);

// Interfaces for stats and workflows
interface DashboardStat {
  name: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: React.ComponentType<{ className?: string }>;
}

interface RecentWorkflow {
  id: string;
  name: string;
  status: 'completed' | 'in-progress' | 'failed';
  type: string;
  startedAt: string;
  duration: string;
}

// Fetch dashboard stats
async function fetchDashboardStats(): Promise<DashboardStat[]> {
  const response = await fetch('/api/dashboard/stats');
  if (!response.ok) {
    throw new Error('Failed to fetch dashboard stats');
  }
  const data = await response.json();
  return [
    {
      name: 'Active Agents',
      value: data.activeAgents.toString(),
      change: data.activeAgentsChange > 0 ? `+${data.activeAgentsChange}` : data.activeAgentsChange.toString(),
      changeType: data.activeAgentsChange > 0 ? 'positive' : data.activeAgentsChange < 0 ? 'negative' : 'neutral',
      icon: Bot,
    },
    {
      name: 'Active Tools',
      value: data.activeTools.toString(),
      change: data.activeToolsChange > 0 ? `+${data.activeToolsChange}` : data.activeToolsChange.toString(),
      changeType: data.activeToolsChange > 0 ? 'positive' : data.activeAgentsChange < 0 ? 'negative' : 'neutral',
      icon: Wrench,
    },
    {
      name: 'Active Workflows',
      value: data.activeWorkflows.toString(),
      change: data.activeWorkflowsChange > 0 ? `+${data.activeWorkflowsChange}` : data.activeWorkflowsChange.toString(),
      changeType: data.activeWorkflowsChange > 0 ? 'positive' : data.activeWorkflowsChange < 0 ? 'negative' : 'neutral',
      icon: GitBranch,
    },
    {
      name: 'System Load',
      value: `${data.systemLoad}%`,
      change: data.systemLoadChange > 0 ? `+${data.systemLoadChange}%` : `${data.systemLoadChange}%`,
      changeType: data.systemLoadChange > 0 ? 'negative' : data.systemLoadChange < 0 ? 'positive' : 'neutral',
      icon: Cpu,
    },
  ];
}

// Fetch recent workflows
async function fetchRecentWorkflows(): Promise<RecentWorkflow[]> {
  const response = await fetch('/api/workflows/recent');
  if (!response.ok) {
    throw new Error('Failed to fetch recent workflows');
  }
  return response.json();
}

export default function DashboardPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  // Fetch dashboard stats
  const { data: stats, isLoading: isStatsLoading, error: statsError } = useQuery<DashboardStat[], Error>({
    queryKey: ['dashboard-stats'],
    queryFn: fetchDashboardStats,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Fetch recent workflows
  const { data: recentWorkflows, isLoading: isWorkflowsLoading, error: workflowsError } = useQuery<RecentWorkflow[], Error>({
    queryKey: ['recent-workflows'],
    queryFn: fetchRecentWorkflows,
    staleTime: 5 * 60 * 1000,
  });

  // Handle refresh
  const handleRefresh = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    queryClient.invalidateQueries({ queryKey: ['recent-workflows'] });
  }, [queryClient]);

  // Loading state
  if (isStatsLoading || isWorkflowsLoading) {
    return (
      <div className="flex flex-col space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Overview</h2>
          <Button variant="ghost" disabled aria-label="Refresh dashboard">
            <RefreshCw className="h-3 w-3 animate-spin" />
            <span>Refreshing...</span>
          </Button>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, index) => (
            <Skeleton key={index} className="h-[120px] w-full" />
          ))}
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          <Skeleton className="md:col-span-4 h-[400px]" />
          <Skeleton className="md:col-span-3 h-[400px]" />
        </div>
      </div>
    );
  }

  // Error state
  if (statsError || workflowsError) {
    return (
      <div className="flex flex-col space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Overview</h2>
          <Button variant="ghost" onClick={handleRefresh} aria-label="Refresh dashboard">
            <RefreshCw className="h-3 w-3 mr-1" />
            <span>Refresh</span>
          </Button>
        </div>
        <Card>
          <CardContent className="p-6">
            <h3 className="text-lg font-semibold text-red-800">Error loading dashboard</h3>
            <p className="text-red-600">
              {statsError instanceof Error
                ? statsError.message
                : workflowsError instanceof Error
                ? workflowsError.message
                : 'Unknown error'}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Overview</h2>
        <Button variant="ghost" onClick={handleRefresh} aria-label="Refresh dashboard">
          <RefreshCw className="h-3 w-3 mr-1" />
          <span>Refresh</span>
        </Button>
      </div>

      {/* Stats cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats?.map((stat) => (
          <Card key={stat.name}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">{stat.name}</p>
                  <h3 className="text-2xl font-bold">{stat.value}</h3>
                </div>
                <div
                  className={`rounded-full p-2 ${
                    stat.name === 'Active Agents'
                      ? 'bg-blue-100 text-blue-600 dark:bg-blue-950 dark:text-blue-400'
                      : stat.name === 'Active Tools'
                      ? 'bg-purple-100 text-purple-600 dark:bg-purple-950 dark:text-purple-400'
                      : stat.name === 'Active Workflows'
                      ? 'bg-green-100 text-green-600 dark:bg-green-950 dark:text-green-400'
                      : 'bg-orange-100 text-orange-600 dark:bg-orange-950 dark:text-orange-400'
                  }`}
                >
                  <stat.icon className="h-4 w-4" />
                </div>
              </div>
              <div className="mt-4">
                <span
                  className={`text-xs font-medium ${
                    stat.changeType === 'positive'
                      ? 'text-green-600 dark:text-green-400'
                      : stat.changeType === 'negative'
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-gray-600 dark:text-gray-400'
                  }`}
                >
                  {stat.change !== '0' ? stat.change : 'No change'}
                </span>
                <span className="text-xs text-muted-foreground"> from last week</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Tabs for different dashboard views */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="workflows" onClick={() => router.push('/workflows')}>
            Workflows
          </TabsTrigger>
          <TabsTrigger value="agents" onClick={() => router.push('/agents')}>
            Agents
          </TabsTrigger>
          <TabsTrigger value="tools" onClick={() => router.push('/tools')}>
            Tools
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            {/* Agent Network Visualization - Takes 4 out of 7 columns */}
            <Card className="md:col-span-4">
              <CardHeader>
                <CardTitle>Agent Network</CardTitle>
                <CardDescription>Live visualization of connected agents and tools</CardDescription>
              </CardHeader>
              <CardContent className="pl-2">
                <Suspense fallback={<Skeleton className="h-[600px] w-full" />}>
                  <AgentNetworkGraph width={800} height={600} router={router} />
                </Suspense>
              </CardContent>
            </Card>

            {/* Recent Activity - Takes 3 out of 7 columns */}
            <Card className="md:col-span-3">
              <CardHeader>
                <CardTitle>Recent Workflows</CardTitle>
                <CardDescription>Latest workflow executions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-8">
                  {recentWorkflows?.map((workflow) => (
                    <div key={workflow.id} className="flex items-center">
                      <div
                        className={`mr-4 rounded p-2 ${
                          workflow.status === 'completed'
                            ? 'bg-green-100 text-green-600 dark:bg-green-950 dark:text-green-400'
                            : workflow.status === 'failed'
                            ? 'bg-red-100 text-red-600 dark:bg-red-950 dark:text-red-400'
                            : 'bg-blue-100 text-blue-600 dark:bg-blue-950 dark:text-blue-400'
                        }`}
                      >
                        <PanelTop className="h-4 w-4" />
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm font-medium leading-none">{workflow.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {workflow.id} • {workflow.startedAt}
                        </p>
                      </div>
                      <div className="ml-auto flex items-center gap-2">
                        <div
                          className={`rounded-full px-2 py-1 text-xs ${
                            workflow.status === 'completed'
                              ? 'bg-green-100 text-green-600 dark:bg-green-950 dark:text-green-400'
                              : workflow.status === 'failed'
                              ? 'bg-red-100 text-red-600 dark:bg-red-950 dark:text-red-400'
                              : 'bg-blue-100 text-blue-600 dark:bg-blue-950 dark:text-blue-400'
                          }`}
                        >
                          {workflow.status === 'completed'
                            ? 'Completed'
                            : workflow.status === 'failed'
                            ? 'Failed'
                            : 'Running'}
                        </div>
                        <span className="text-xs text-muted-foreground">{workflow.duration}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="workflows" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Workflow Management</CardTitle>
              <CardDescription>Create, monitor, and manage workflows</CardDescription>
            </CardHeader>
            <CardContent>
              <p>Redirecting to Workflow Management...</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="agents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agent Management</CardTitle>
              <CardDescription>Manage and monitor your OMEGA agents</CardDescription>
            </CardHeader>
            <CardContent>
              <p>Redirecting to Agent Management...</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tools" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Tool Management</CardTitle>
              <CardDescription>Register and manage your MCP tools</CardDescription>
            </CardHeader>
            <CardContent>
              <p>Redirecting to Tool Management...</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}