// src/components/tools/tool-list.tsx
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Skeleton } from '@/components/ui/skeleton';
import { Server, MoreHorizontal, Wrench, Plus, RefreshCw, Code, Terminal } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useDiscoverTools } from '@/hooks/use-mcp';
import { Tool } from '@/types';
import { error } from 'console';

export function ToolList() {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [filterTag, setFilterTag] = useState<string | null>(null);

  // Use useMcp to fetch tools
  const { data: tools, isLoading, error, refetch } = useDiscoverTools();

  // Filter tools based on search term and tag filter
  const filteredTools = React.useMemo(() => {
    if (!tools) return [];

    return tools.filter((tool: Tool) => {
      // Apply search term filter
      const matchesSearch =
        !searchTerm ||
        tool.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        tool.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        tool.capabilities.some((cap) =>
          cap.name.toLowerCase().includes(searchTerm.toLowerCase())
        );

      // Apply tag filter
      const matchesTag = !filterTag || tool.tags.includes(filterTag);

      return matchesSearch && matchesTag;
    });
  }, [tools, searchTerm, filterTag]);

  // Extract all unique tags from tools
  const allTags = React.useMemo(() => {
    if (!tools) return [];

    const tagSet = new Set<string>();
    tools.forEach((tool: Tool) => {
      tool.tags.forEach((tag) => tagSet.add(tag));
    });

    return Array.from(tagSet);
  }, [tools]);

  // Handle view tool details
  const handleViewTool = (toolId: string) => {
    router.push(`/tools/${toolId}`);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-3xl font-bold tracking-tight">Tools</h2>
          <Skeleton className="h-10 w-32" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, index) => (
            <Card key={index} className="shadow-md">
              <CardHeader className="pb-2">
                <Skeleton className="h-6 w-3/4 mb-2" />
                <Skeleton className="h-4 w-full" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-full mb-4" />
                <div className="flex flex-wrap gap-2 mt-2">
                  <Skeleton className="h-6 w-16" />
                  <Skeleton className="h-6 w-16" />
                  <Skeleton className="h-6 w-16" />
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Skeleton className="h-10 w-20" />
                <Skeleton className="h-10 w-20" />
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-3xl font-bold tracking-tight">Tools</h2>
          <Button onClick={() => router.push('/tools/create')}>
            <Plus className="mr-2 h-4 w-4" /> Register Tool
          </Button>
        </div>

        <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
          <h3 className="text-lg font-semibold text-red-800">Error loading tools</h3>
          <p className="text-red-600">{error instanceof Error ? error.message : 'Unknown error'}</p>
          <Button onClick={() => refetch()} variant="outline" className="mt-4">
            <RefreshCw className="mr-2 h-4 w-4" /> Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight">Tools</h2>
        <Button onClick={() => router.push('/tools/create')}>
          <Plus className="mr-2 h-4 w-4" /> Register Tool
        </Button>
      </div>

      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative w-full md:w-2/3">
          <Input
            placeholder="Search tools..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
          <div className="absolute left-3 top-2.5 text-gray-400">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="lucide lucide-search"
            >
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
          </div>
        </div>

        <div className="flex-1">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="w-full">
                {filterTag ? `Filter: ${filterTag}` : 'Filter by Tag'}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => setFilterTag(null)}>
                All Tags
              </DropdownMenuItem>
              {allTags.map((tag) => (
                <DropdownMenuItem key={tag} onClick={() => setFilterTag(tag)}>
                  {tag}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {filteredTools.length === 0 ? (
        <div className="text-center p-12 border border-dashed rounded-lg">
          <h3 className="font-medium text-lg mb-2">No tools found</h3>
          <p className="text-gray-500 mb-4">
            {searchTerm || filterTag
              ? "No tools match your search criteria"
              : "Get started by registering your first tool"}
          </p>
          <Button onClick={() => router.push('/tools/create')}>
            <Plus className="mr-2 h-4 w-4" /> Register Tool
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTools.map((tool: Tool) => (
            <Card
              key={tool.id}
              className={`shadow-md hover:shadow-lg transition-shadow ${
                tool.status === 'inactive' ? 'opacity-70' : ''
              }`}
            >
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <CardTitle className="flex items-center gap-2">
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
                  </CardTitle>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                      <DropdownMenuItem onClick={() => handleViewTool(tool.id)}>
                        View Details
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => router.push(`/tools/${tool.id}/call`)}>
                        Call Tool
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                <CardDescription>{tool.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-gray-500 mb-2">
                  <div className="flex items-center gap-1 mb-1">
                    <Server className="h-4 w-4" />
                    <span>
                      {tool.host}:{tool.port}
                    </span>
                  </div>
                  <div>Version: {tool.version}</div>
                  <div>Last heartbeat: {new Date(tool.lastHeartbeat).toLocaleString()}</div>
                </div>

                <div className="mt-3">
                  <h4 className="text-sm font-semibold mb-1">Capabilities:</h4>
                  <div className="flex flex-wrap gap-1">
                    {tool.capabilities.slice(0, 3).map((capability) => (
                      <TooltipProvider key={capability.name}>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Badge variant="secondary" className="cursor-help">
                              {capability.name}
                            </Badge>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>{capability.description}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    ))}
                    {tool.capabilities.length > 3 && (
                      <Badge variant="secondary">
                        +{tool.capabilities.length - 3} more
                      </Badge>
                    )}
                  </div>
                </div>

                <div className="flex flex-wrap gap-1 mt-2">
                  {tool.tags.map((tag) => (
                    <Badge key={tag} variant="outline">{tag}</Badge>
                  ))}
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button variant="outline" size="sm" onClick={() => handleViewTool(tool.id)}>
                  <Wrench className="mr-2 h-4 w-4" />
                  Details
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => router.push(`/tools/${tool.id}/call`)}
                >
                  <Terminal className="mr-2 h-4 w-4" /> Call
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}