// src/components/agents/agent-list.tsx
'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

// Assuming we have an agent provider or hook
import { useDiscoverAgents } from '@/hooks/use-mcp';

export function AgentList() {
  const [filter, setFilter] = useState('all');
  const { data: agents, isLoading, error } = useDiscoverAgents();

  const filteredAgents = agents?.filter(agent => {
    if (filter === 'all') return true;
    return agent.tags.includes(filter);
  });

  if (error) {
    return (
      <div className="rounded-md bg-destructive/15 p-4">
        <div className="flex items-start space-x-4">
          <div>
            <h3 className="font-medium text-destructive">Error Loading Agents</h3>
            <div className="text-sm text-destructive">
              {error instanceof Error ? error.message : 'An unknown error occurred'}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Tabs defaultValue="all" className="w-full" onValueChange={setFilter}>
        <TabsList className="mb-4">
          <TabsTrigger value="all">All Agents</TabsTrigger>
          <TabsTrigger value="orchestrator">Orchestrator</TabsTrigger>
          <TabsTrigger value="workflow">Workflow</TabsTrigger>
          <TabsTrigger value="capability">Capability</TabsTrigger>
        </TabsList>
        
        <TabsContent value={filter} className="mt-0">
          {isLoading ? (
            // Loading skeletons
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array(6).fill(0).map((_, i) => (
                <Card key={i} className="overflow-hidden">
                  <CardHeader className="pb-2">
                    <Skeleton className="h-6 w-1/2" />
                    <Skeleton className="h-4 w-3/4" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-20 w-full" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredAgents?.map((agent) => (
                <Link href={`/agents/${agent.id}`} key={agent.id}>
                  <Card className="h-full hover:bg-muted/50 transition-colors cursor-pointer">
                    <CardHeader className="pb-2">
                      <div className="flex justify-between items-start">
                        <CardTitle className="text-lg">{agent.name}</CardTitle>
                        <div className="flex gap-1">
                          {agent.tags.map((tag) => (
                            <Badge key={tag} variant="outline">{tag}</Badge>
                          ))}
                        </div>
                      </div>
                      <CardDescription>{agent.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm">
                        <p className="font-medium">Capabilities:</p>
                        <ul className="list-disc list-inside pl-2 mt-1">
                          {agent.capabilities.slice(0, 3).map((cap) => (
                            <li key={cap}>{cap}</li>
                          ))}
                          {agent.capabilities.length > 3 && (
                            <li>+{agent.capabilities.length - 3} more</li>
                          )}
                        </ul>
                      </div>
                      <div className="flex justify-end mt-4">
                        <Button size="sm" variant="outline">Details</Button>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}