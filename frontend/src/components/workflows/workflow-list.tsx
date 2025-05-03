// src/components/workflows/workflow-list.tsx
import { useState } from 'react';
import Link from 'next/link';
import { useWorkflows } from '@/hooks/use-workflows';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';
import { 
  ChevronDownIcon, 
  PencilIcon, 
  PlayIcon, 
  PlusIcon, 
  TagIcon, 
  TrashIcon 
} from 'lucide-react';

export function WorkflowList() {
  const { data: workflows, isLoading, error } = useWorkflows();
  const [filterTag, setFilterTag] = useState<string | null>(null);
  
  // Extract all unique tags from workflows
  const allTags = workflows 
    ? [...new Set(workflows.flatMap(workflow => workflow.tags))]
    : [];
  
  // Filter workflows by tag if a filter is set
  const filteredWorkflows = filterTag
    ? workflows?.filter(workflow => workflow.tags.includes(filterTag))
    : workflows;
  
  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold">Workflows</h2>
          <Button disabled>
            <PlusIcon className="h-4 w-4 mr-2" />
            New Workflow
          </Button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="overflow-hidden">
              <CardHeader className="pb-2">
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-full" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-2/3" />
              </CardContent>
              <CardFooter>
                <Skeleton className="h-9 w-full" />
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="p-4 border border-red-300 bg-red-50 rounded-md text-red-800">
        <h3 className="font-bold">Error loading workflows</h3>
        <p>{(error as Error).message}</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Workflows</h2>
        <Link href="/workflows/create">
          <Button>
            <PlusIcon className="h-4 w-4 mr-2" />
            New Workflow
          </Button>
        </Link>
      </div>
      
      {allTags.length > 0 && (
        <div className="flex items-center gap-2">
          <TagIcon className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Filter by tag:</span>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="h-8">
                {filterTag || 'All workflows'}
                <ChevronDownIcon className="h-4 w-4 ml-2" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => setFilterTag(null)}>
                All workflows
              </DropdownMenuItem>
              {allTags.map((tag) => (
                <DropdownMenuItem key={tag} onClick={() => setFilterTag(tag)}>
                  {tag}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      )}
      
      {filteredWorkflows?.length === 0 ? (
        <div className="text-center p-12 border border-dashed rounded-lg">
          <p className="text-muted-foreground mb-4">
            {filterTag 
              ? `No workflows found with tag "${filterTag}"`
              : "No workflows found"
            }
          </p>
          <Link href="/workflows/create">
            <Button>
              <PlusIcon className="h-4 w-4 mr-2" />
              Create your first workflow
            </Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredWorkflows?.map((workflow) => (
            <Card key={workflow.id}>
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg">
                    {workflow.name}
                  </CardTitle>
                  <Badge 
                    variant={
                      workflow.status === 'active' ? 'default' :
                      workflow.status === 'draft' ? 'secondary' :
                      workflow.status === 'completed' ? 'success' :
                      'destructive'
                    }
                  >
                    {workflow.status}
                  </Badge>
                </div>
                <CardDescription className="line-clamp-2">
                  {workflow.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1 mb-2">
                  {workflow.tags.map((tag) => (
                    <Badge key={tag} variant="outline" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
                <div className="text-xs text-muted-foreground">
                  {workflow.steps.length} step{workflow.steps.length !== 1 ? 's' : ''}
                  • Updated {new Date(workflow.updated_at).toLocaleDateString()}
                </div>
              </CardContent>
              <CardFooter className="flex justify-between pt-2">
                <Button variant="outline" size="sm" asChild>
                  <Link href={`/workflows/${workflow.id}`}>
                    View Details
                  </Link>
                </Button>
                <div className="flex gap-2">
                  <Button 
                    size="icon" 
                    variant="ghost" 
                    className="h-8 w-8"
                    disabled={workflow.status !== 'active'}
                    title="Run workflow"
                  >
                    <PlayIcon className="h-4 w-4" />
                  </Button>
                  <Button 
                    size="icon" 
                    variant="ghost" 
                    className="h-8 w-8"
                    asChild
                  >
                    <Link href={`/workflows/${workflow.id}/edit`} title="Edit workflow">
                      <PencilIcon className="h-4 w-4" />
                    </Link>
                  </Button>
                  <Button 
                    size="icon" 
                    variant="ghost" 
                    className="h-8 w-8 text-destructive"
                    title="Delete workflow"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </Button>
                </div>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}