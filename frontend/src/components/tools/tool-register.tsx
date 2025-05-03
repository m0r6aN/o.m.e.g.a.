// src/components/tools/tool-register.tsx
import React, { useState } from 'react';
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
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Skeleton } from '@/components/ui/skeleton';
import {
  ArrowLeft,
  Plus,
  Trash2,
  Save,
  Copy,
  RefreshCw,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CodeBlock, atomOneDark } from 'react-code-blocks';
import { toast } from 'react-hot-toast';
import { Tool } from '@/types';
import { useMcp } from '@/hooks/use-mcp';

// Define the form schema using zod
const toolFormSchema = z.object({
  id: z
    .string()
    .min(3, {
      message: 'Tool ID must be at least 3 characters.',
    })
    .regex(/^[a-z0-9_-]+$/, {
      message: 'Tool ID can only contain lowercase letters, numbers, underscores, and hyphens.',
    }),
  name: z.string().min(3, {
    message: 'Tool name must be at least 3 characters.',
  }),
  description: z.string().min(10, {
    message: 'Description must be at least 10 characters.',
  }),
  host: z.string().min(1, {
    message: 'Host is required.',
  }),
  port: z.coerce.number().min(1, {
    message: 'Port must be at least 1.',
  }).max(65535, {
    message: 'Port must be at most 65535.',
  }),
  tags: z.string().optional(),
  capabilities: z.string().min(10, {
    message: 'Capabilities JSON is required.',
  }),
  version: z.string().optional(),
  metadata: z.string().optional(),
});

// Type for form values
type ToolFormValues = z.infer<typeof toolFormSchema>;

// Default capability template
const defaultCapability = {
  name: 'example_capability',
  description: 'An example capability',
  parameters: {
    input: {
      type: 'string',
      description: 'The input to process',
      required: true,
    },
  },
  returns: {
    type: 'string',
    description: 'The processed result',
  },
};

// Register tool function
async function registerTool(data: any) {
  const response = await fetch('/api/tools', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.message || 'Failed to register tool');
  }

  return response.json();
}

export function ToolRegister() {
  const router = useRouter();
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState('form');

  // Initialize form
  const form = useForm<ToolFormValues>({
    resolver: zodResolver(toolFormSchema),
    defaultValues: {
      host: 'localhost',
      port: 9000,
      capabilities: JSON.stringify([defaultCapability], null, 2),
      version: '1.0.0',
      metadata: JSON.stringify(
        {
          author: '',
          documentation: '',
          repository: '',
        },
        null,
        2
      ),
    },
  });

  // Watch for form values to generate preview
  const formValues = form.watch();

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
    const newTags = tags.filter((tag) => tag !== tagToRemove);
    setTags(newTags);
    form.setValue('tags', newTags.join(','));
  };

  // Generate request preview
  const generateRequestPreview = () => {
    try {
      const formData = form.getValues();

      // Parse JSON fields
      const capabilities = JSON.parse(formData.capabilities);
      const metadata = formData.metadata ? JSON.parse(formData.metadata) : {};

      // Parse tags
      const parsedTags = formData.tags ? formData.tags.split(',').map((tag) => tag.trim()) : [];

      const requestData: Partial<Tool> = {
        id: formData.id,
        name: formData.name,
        description: formData.description,
        host: formData.host,
        port: formData.port,
        tags: parsedTags,
        capabilities,
        version: formData.version || '1.0.0',
        metadata,
      };

      return JSON.stringify(requestData, null, 2);
    } catch (error) {
      return `Error generating preview: ${error instanceof Error ? error.message : 'Invalid JSON'}`;
    }
  };

  // Create a curl command preview
  const generateCurlPreview = () => {
    try {
      const formData = form.getValues();

      // Parse JSON fields
      const capabilities = JSON.parse(formData.capabilities);
      const metadata = formData.metadata ? JSON.parse(formData.metadata) : {};

      // Parse tags
      const parsedTags = formData.tags ? formData.tags.split(',').map((tag) => tag.trim()) : [];

      const requestData: Partial<Tool> = {
        id: formData.id,
        name: formData.name,
        description: formData.description,
        host: formData.host,
        port: formData.port,
        tags: parsedTags,
        capabilities,
        version: formData.version || '1.0.0',
        metadata,
      };

      return `curl -X POST \\
  http://localhost:8080/api/tools \\
  -H 'Content-Type: application/json' \\
  -d '${JSON.stringify(requestData)}'`;
    } catch (error) {
      return `Error generating curl command: ${error instanceof Error ? error.message : 'Invalid JSON'}`;
    }
  };

  // Register tool mutation using useMcp
  const { callTool } = useMcp();
  const registerToolMutation = useMutation({
    mutationFn: async (data: ToolFormValues) => {
      try {
        // Parse JSON fields
        const capabilities = JSON.parse(data.capabilities);
        const metadata = data.metadata ? JSON.parse(data.metadata) : {};

        // Parse tags
        const parsedTags = data.tags ? data.tags.split(',').map((tag) => tag.trim()) : [];

        const requestData: Partial<Tool> = {
          id: data.id,
          name: data.name,
          description: data.description,
          host: data.host,
          port: data.port,
          tags: parsedTags,
          capabilities,
          version: data.version || '1.0.0',
          metadata,
        };

        return await registerTool(requestData);
      } catch (error) {
        throw new Error(`Failed to parse form data: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    },
    onSuccess: (data) => {
      toast.success('Tool registered successfully');
      router.push(`/tools/${data.id}`);
    },
    onError: (error) => {
      toast.error(`Failed to register tool: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  // Form submission handler
  const onSubmit = (values: ToolFormValues) => {
    registerToolMutation.mutate(values);
  };

  // Copy code to clipboard
  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    toast.success('Copied to clipboard');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <h1 className="text-3xl font-bold">Register New Tool</h1>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="form">Tool Form</TabsTrigger>
          <TabsTrigger value="preview">Request Preview</TabsTrigger>
        </TabsList>

        <TabsContent value="form">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Basic Information</CardTitle>
                  <CardDescription>Provide the essential details for your tool</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <FormField
                      control={form.control}
                      name="id"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Tool ID</FormLabel>
                          <FormControl>
                            <Input placeholder="my_awesome_tool" {...field} />
                          </FormControl>
                          <FormDescription>
                            A unique identifier for your tool (lowercase, no spaces)
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Tool Name</FormLabel>
                          <FormControl>
                            <Input placeholder="My Awesome Tool" {...field} />
                          </FormControl>
                          <FormDescription>A human-readable name for your tool</FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <FormField
                    control={form.control}
                    name="description"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Description</FormLabel>
                        <FormControl>
                          <Textarea placeholder="Describe what this tool does..." {...field} />
                        </FormControl>
                        <FormDescription>
                          A brief description of your tool's purpose and capabilities
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="version"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Version</FormLabel>
                        <FormControl>
                          <Input placeholder="1.0.0" {...field} />
                        </FormControl>
                        <FormDescription>The version of your tool (e.g., 1.0.0)</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

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
                          <Button type="button" variant="secondary" onClick={addTag}>
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
                                <Trash2 className="h-3 w-3" />
                              </button>
                            </Badge>
                          ))}
                        </div>
                        <input type="hidden" {...field} />
                        <FormDescription>Add tags to help categorize and search for your tool</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Connection Details</CardTitle>
                  <CardDescription>Specify how to connect to your tool</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <FormField
                      control={form.control}
                      name="host"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Host</FormLabel>
                          <FormControl>
                            <Input placeholder="localhost" {...field} />
                          </FormControl>
                          <FormDescription>The hostname or IP address where your tool is running</FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="port"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Port</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              placeholder="9000"
                              {...field}
                              onChange={(e) => field.onChange(parseInt(e.target.value) || '')}
                            />
                          </FormControl>
                          <FormDescription>The port number where your tool is listening</FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Capabilities</CardTitle>
                  <CardDescription>Define the capabilities your tool provides</CardDescription>
                </CardHeader>
                <CardContent>
                  <FormField
                    control={form.control}
                    name="capabilities"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Capabilities (JSON)</FormLabel>
                        <FormControl>
                          <Textarea className="h-96 font-mono text-sm" {...field} />
                        </FormControl>
                        <FormDescription>Define your tool's capabilities as a JSON array</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>

              <Accordion type="single" collapsible>
                <AccordionItem value="metadata">
                  <AccordionTrigger>Additional Metadata</AccordionTrigger>
                  <AccordionContent>
                    <Card>
                      <CardContent className="pt-6">
                        <FormField
                          control={form.control}
                          name="metadata"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Metadata (JSON)</FormLabel>
                              <FormControl>
                                <Textarea className="h-40 font-mono text-sm" {...field} />
                              </FormControl>
                              <FormDescription>
                                Optional metadata about your tool (author, documentation, etc.)
                              </FormDescription>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </CardContent>
                    </Card>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>

              <div className="flex justify-between">
                <Button type="button" variant="outline" onClick={() => router.back()}>
                  Cancel
                </Button>
                <Button type="submit" disabled={registerToolMutation.isPending}>
                  {registerToolMutation.isPending ? (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      Registering Tool...
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      Register Tool
                    </>
                  )}
                </Button>
              </div>
            </form>
          </Form>
        </TabsContent>

        <TabsContent value="preview">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Request Preview</CardTitle>
                <CardDescription>This is what will be sent to the registration API</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="relative">
                  <div className="bg-gray-900 rounded-md overflow-hidden">
                    <CodeBlock
                      text={generateRequestPreview()}
                      language="json"
                      showLineNumbers={true}
                      theme={atomOneDark}
                    />
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="absolute top-2 right-2 bg-black/20 hover:bg-black/40 text-white"
                    onClick={() => handleCopyCode(generateRequestPreview())}
                  >
                    <Copy className="h-4 w-4 mr-1" /> Copy
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>CURL Command</CardTitle>
                <CardDescription>Register your tool using curl from command line</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="relative">
                  <div className="bg-gray-900 rounded-md overflow-hidden">
                    <CodeBlock
                      text={generateCurlPreview()}
                      language="bash"
                      showLineNumbers={true}
                      theme={atomOneDark}
                    />
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="absolute top-2 right-2 bg-black/20 hover:bg-black/40 text-white"
                    onClick={() => handleCopyCode(generateCurlPreview())}
                  >
                    <Copy className="h-4 w-4 mr-1" /> Copy
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}