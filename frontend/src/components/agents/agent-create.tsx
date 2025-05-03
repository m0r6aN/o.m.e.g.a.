// src/components/agents/agent-create.tsx
import React from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';
import { 
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger
} from '@/components/ui/accordion';
import { Checkbox } from '@/components/ui/checkbox';
import { ArrowLeft, Plus, Trash, Save } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

// Define the form schema using zod
const agentFormSchema = z.object({
  name: z.string().min(3, {
    message: 'Agent name must be at least 3 characters.',
  }),
  description: z.string().min(10, {
    message: 'Description must be at least 10 characters.',
  }),
  type: z.enum(['agent', 'tool', 'dual'], {
    required_error: 'Please select an agent type.',
  }),
  protocol: z.enum(['a2a', 'mcp', 'dual'], {
    required_error: 'Please select a protocol.',
  }),
  capabilities: z.array(z.string()).min(1, {
    message: 'Select at least one capability.',
  }),
  tags: z.string().optional(),
  processor: z.enum(['standard', 'enhanced', 'premium'], {
    required_error: 'Please select a processor allocation.',
  }),
  memory: z.enum(['512MB', '1GB', '2GB', '4GB'], {
    required_error: 'Please select a memory allocation.',
  }),
  autoStart: z.boolean().default(false),
});

// Type for form values
type AgentFormValues = z.infer<typeof agentFormSchema>;

// Available capabilities
const availableCapabilities = [
  { id: 'prompt_optimization', name: 'Prompt Optimization' },
  { id: 'research', name: 'Research' },
  { id: 'code_generation', name: 'Code Generation' },
  { id: 'math_solving', name: 'Math Solving' },
  { id: 'weather_forecast', name: 'Weather Forecast' },
  { id: 'natural_language_processing', name: 'Natural Language Processing' },
  { id: 'image_analysis', name: 'Image Analysis' },
  { id: 'data_analysis', name: 'Data Analysis' },
  { id: 'workflow_planning', name: 'Workflow Planning' },
  { id: 'translation', name: 'Translation' },
];

// Default form values
const defaultValues: Partial<AgentFormValues> = {
  type: 'agent',
  protocol: 'dual',
  capabilities: [],
  processor: 'standard',
  memory: '1GB',
  autoStart: true,
};

// Create agent function
async function createAgent(data: AgentFormValues) {
  const response = await fetch('/api/agents', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ...data,
      // Convert tags string to array
      tags: data.tags ? data.tags.split(',').map(tag => tag.trim()) : [],
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to create agent');
  }

  return response.json();
}

export function AgentCreate() {
  const router = useRouter();
  const [tagInput, setTagInput] = React.useState('');
  const [tags, setTags] = React.useState<string[]>([]);

  // Initialize form
  const form = useForm<AgentFormValues>({
    resolver: zodResolver(agentFormSchema),
    defaultValues,
  });

  // Handle tag input
  const handleTagInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag();
    }
  };

  const addTag = () => {
    const tag = tagInput.trim();
    if (tag && !tags.includes(tag)) {
      const newTags = [...tags, tag];
      setTags(newTags);
      form.setValue('tags', newTags.join(','));
      setTagInput('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    const newTags = tags.filter(tag => tag !== tagToRemove);
    setTags(newTags);
    form.setValue('tags', newTags.join(','));
  };

  // Create agent mutation
  const createAgentMutation = useMutation({
    mutationFn: createAgent,
    onSuccess: (data) => {
      router.push(`/agents/${data.id}`);
    },
  });

  // Form submission handler
  const onSubmit = (values: AgentFormValues) => {
    createAgentMutation.mutate(values);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <h1 className="text-3xl font-bold">Create New Agent</h1>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
              <CardDescription>
                Provide the essential details for your new agent
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Agent Name</FormLabel>
                    <FormControl>
                      <Input placeholder="My Awesome Agent" {...field} />
                    </FormControl>
                    <FormDescription>
                      A unique name for your agent
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea 
                        placeholder="Describe what this agent does..." 
                        {...field} 
                      />
                    </FormControl>
                    <FormDescription>
                      A brief description of your agent's purpose and capabilities
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <FormField
                  control={form.control}
                  name="type"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Agent Type</FormLabel>
                      <Select 
                        onValueChange={field.onChange} 
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select agent type" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="agent">Agent (Reasoner)</SelectItem>
                          <SelectItem value="tool">Tool (Function)</SelectItem>
                          <SelectItem value="dual">Dual (Agent & Tool)</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        Determines how this agent functions
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="protocol"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Protocol</FormLabel>
                      <Select 
                        onValueChange={field.onChange} 
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select protocol" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="a2a">A2A (Agent-to-Agent)</SelectItem>
                          <SelectItem value="mcp">MCP (Model Context Protocol)</SelectItem>
                          <SelectItem value="dual">Dual (A2A & MCP)</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        The communication protocol used by this agent
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="tags"
                render={({ field }) => (
                  <FormItem className="flex flex-col">
                    <FormLabel>Tags</FormLabel>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Add tags..."
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        onKeyDown={handleTagInputKeyDown}
                        onBlur={addTag}
                      />
                      <Button 
                        type="button"
                        variant="secondary"
                        onClick={addTag}
                      >
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="flex items-center gap-1">
                          {tag}
                          <button 
                            type="button" 
                            onClick={() => removeTag(tag)}
                            className="rounded-full hover:bg-gray-200 p-1"
                          >
                            <Trash className="h-3 w-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                    <input type="hidden" {...field} />
                    <FormDescription>
                      Add tags to help categorize and search for your agent
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Capabilities</CardTitle>
              <CardDescription>
                Select the capabilities this agent will provide
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FormField
                control={form.control}
                name="capabilities"
                render={() => (
                  <FormItem>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {availableCapabilities.map((capability) => (
                        <FormField
                          key={capability.id}
                          control={form.control}
                          name="capabilities"
                          render={({ field }) => {
                            return (
                              <FormItem
                                key={capability.id}
                                className="flex flex-row items-start space-x-3 space-y-0"
                              >
                                <FormControl>
                                  <Checkbox
                                    checked={field.value?.includes(capability.id)}
                                    onCheckedChange={(checked) => {
                                      return checked
                                        ? field.onChange([...field.value, capability.id])
                                        : field.onChange(
                                            field.value?.filter(
                                              (value) => value !== capability.id
                                            )
                                          )
                                    }}
                                  />
                                </FormControl>
                                <FormLabel className="font-normal">
                                  {capability.name}
                                </FormLabel>
                              </FormItem>
                            )
                          }}
                        />
                      ))}
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Advanced Settings</CardTitle>
              <CardDescription>
                Configure additional settings for your agent
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible>
                <AccordionItem value="resource-allocation">
                  <AccordionTrigger>Resource Allocation</AccordionTrigger>
                  <AccordionContent className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <FormField
                        control={form.control}
                        name="processor"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Processor Allocation</FormLabel>
                            <Select 
                              onValueChange={field.onChange} 
                              defaultValue={field.value}
                            >
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select processor allocation" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                <SelectItem value="standard">Standard (1 CPU Core)</SelectItem>
                                <SelectItem value="enhanced">Enhanced (2 CPU Cores)</SelectItem>
                                <SelectItem value="premium">Premium (4 CPU Cores)</SelectItem>
                              </SelectContent>
                            </Select>
                            <FormDescription>
                              The amount of processing power allocated to the agent
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="memory"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Memory Allocation</FormLabel>
                            <Select 
                              onValueChange={field.onChange} 
                              defaultValue={field.value}
                            >
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select memory allocation" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                <SelectItem value="512MB">512 MB RAM</SelectItem>
                                <SelectItem value="1GB">1 GB RAM</SelectItem>
                                <SelectItem value="2GB">2 GB RAM</SelectItem>
                                <SelectItem value="4GB">4 GB RAM</SelectItem>
                              </SelectContent>
                            </Select>
                            <FormDescription>
                              The amount of memory allocated to the agent
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>
                  </AccordionContent>
                </AccordionItem>

                <AccordionItem value="startup-options">
                  <AccordionTrigger>Startup Options</AccordionTrigger>
                  <AccordionContent>
                    <FormField
                      control={form.control}
                      name="autoStart"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                          <FormControl>
                            <Checkbox
                              checked={field.value}
                              onCheckedChange={field.onChange}
                            />
                          </FormControl>
                          <div className="space-y-1 leading-none">
                            <FormLabel>
                              Auto-start agent after creation
                            </FormLabel>
                            <FormDescription>
                              Automatically start the agent once it's created
                            </FormDescription>
                          </div>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>

          <div className="flex justify-between">
            <Button
              type="button"
              variant="outline"
              onClick={() => router.back()}
            >
              Cancel
            </Button>
            <Button 
              type="submit"
              disabled={createAgentMutation.isPending}
            >
              {createAgentMutation.isPending ? (
                <>Creating Agent...</>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Create Agent
                </>
              )}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}