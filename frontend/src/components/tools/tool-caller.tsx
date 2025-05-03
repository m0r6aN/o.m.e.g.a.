// src/components/tools/tool-caller.tsx
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import {
  ArrowLeft,
  Code,
  RefreshCw,
  Terminal,
  Send,
  Copy,
  Check,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CodeBlock, atomOneDark } from 'react-code-blocks';
import { useMcp } from '@/hooks/use-mcp';
import { Tool, ToolCapability as Capability } from '@/types';
import { toast } from 'react-hot-toast';

interface ToolCallerProps {
  toolId: string;
  capability?: string;
}

export function ToolCaller({ toolId, capability: initialCapability }: ToolCallerProps) {
  const router = useRouter();
  const [selectedCapability, setSelectedCapability] = useState<string | null>(initialCapability || null);
  const [formSchema, setFormSchema] = useState<z.ZodObject<any> | null>(null);
  const [activeResultTab, setActiveResultTab] = useState('result');
  const [copySuccess, setCopySuccess] = useState(false);

  // Fetch tool details using useMcp
  const { discoverTools, callTool } = useMcp();
  const tool = discoverTools.find((t: Tool) => t.id === toolId);
  const { isLoading, isError, error, refetch } = useQuery({
    queryKey: ['tools'],
    queryFn: () => discoverTools,
  });

  // Create dynamic form based on selected capability
  React.useEffect(() => {
    if (!tool || !selectedCapability) return;

    const capability = tool.capabilities.find((c: Capability) => c.name === selectedCapability);
    if (!capability) return;

    const schema: Record<string, any> = {};

    // Create zod schema based on capability parameters
    Object.entries(capability.parameters).forEach(([key, param]: [string, any]) => {
      let fieldSchema;

      if (param.type === 'string') {
        fieldSchema = z.string();
        if (param.required) {
          fieldSchema = fieldSchema.min(1, `${key} is required`);
        } else {
          fieldSchema = fieldSchema.optional();
        }
      } else if (param.type === 'number') {
        fieldSchema = z.coerce.number();
        if (param.required) {
          fieldSchema = fieldSchema.min(-Infinity, `${key} is required`);
        } else {
          fieldSchema = fieldSchema.optional();
        }
      } else if (param.type === 'boolean') {
        fieldSchema = z.boolean().optional();
      } else if (param.type === 'array') {
        fieldSchema = z.string().transform((val) => {
          try {
            return JSON.parse(val);
          } catch (e) {
            return [];
          }
        });
        if (param.required) {
          fieldSchema = fieldSchema.array();
        } else {
          fieldSchema = fieldSchema.optional();
        }
      } else if (param.type === 'object') {
        fieldSchema = z.string().transform((val) => {
          try {
            return JSON.parse(val);
          } catch (e) {
            return {};
          }
        });
        if (param.required) {
          fieldSchema = fieldSchema.array();
        } else {
          fieldSchema = fieldSchema.optional();
        }
      } else {
        fieldSchema = z.any();
      }

      schema[key] = fieldSchema;
    });

    setFormSchema(z.object(schema));
  }, [tool, selectedCapability]);

  // Create form with dynamic schema
  const form = useForm<any>({
    resolver: formSchema ? zodResolver(formSchema) : undefined,
    defaultValues: {},
  });

  // Call tool mutation using useMcp
  const callToolMutation = useMutation({
    mutationFn: (data: Record<string, any>) => {
      if (!selectedCapability) {
        throw new Error('No capability selected');
      }

      // Process form data
      const processedData: Record<string, any> = {};

      const capability = tool?.capabilities.find((c: Capability) => c.name === selectedCapability);
      if (!capability) throw new Error('Capability not found');

      Object.entries(data).forEach(([key, value]) => {
        const paramType = capability.parameters[key]?.type;

        if (paramType === 'string') {
          processedData[key] = value;
        } else if (paramType === 'number') {
          processedData[key] = Number(value);
        } else if (paramType === 'boolean') {
          processedData[key] = Boolean(value);
        } else if (paramType === 'array' || paramType === 'object') {
          // Already transformed by zod
          processedData[key] = value;
        } else {
          processedData[key] = value;
        }
      });

      return new Promise((resolve, reject) => {
        callTool(
          { toolId, capability: selectedCapability, parameters: processedData },
          {
            onSuccess: (result) => resolve(result),
            onError: (error) => reject(error),
          }
        );
      });
    },
    onSuccess: () => {
      toast.success('Tool called successfully');
    },
    onError: (error) => {
      toast.error(`Failed to call tool: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  // Handle form submission
  const onSubmit = (data: Record<string, any>) => {
    callToolMutation.mutate(data);
  };

  // Handle copying result to clipboard
  const handleCopyResult = () => {
    if (callToolMutation.data) {
      navigator.clipboard.writeText(
        typeof callToolMutation.data === 'object'
          ? JSON.stringify(callToolMutation.data, null, 2)
          : String(callToolMutation.data)
      );
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  // Generate example code for the selected capability
  const generateExampleCode = () => {
    if (!tool || !selectedCapability) return '';

    const capability = tool.capabilities.find((c: Capability) => c.name === selectedCapability);
    if (!capability) return '';

    const paramValues: Record<string, any> = {};

    // Generate example values for parameters
    Object.entries(capability.parameters).forEach(([key, param]: [string, any]) => {
      if (param.type === 'string') {
        paramValues[key] = param.example || 'example_string';
      } else if (param.type === 'number') {
        paramValues[key] = param.example || 42;
      } else if (param.type === 'boolean') {
        paramValues[key] = param.example || true;
      } else if (param.type === 'array') {
        paramValues[key] = param.example || [1, 2, 3];
      } else if (param.type === 'object') {
        paramValues[key] = param.example || { key: 'value' };
      }
    });

    const code = `// Example: Calling the ${capability.name} capability
import { callMcpTool } from '@/lib/mcp/client';

// Call the tool
const result = await callMcpTool(
  '${tool?.mcp_endpoint || '[MCP_ENDPOINT]'}',
  '${capability.name}',
  ${JSON.stringify(paramValues, null, 2)}
);

// Process the result
console.log(result);`;

    return code;
  };

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
          <CardContent>
            <Skeleton className="h-32 w-full" />
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
          <Button onClick={() => refetch()} variant="outline" className="mt-4">
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
          <Button onClick={() => router.push('/tools')} variant="outline" className="mt-4">
            View All Tools
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Call Tool: {tool.name}</h1>
          <p className="text-gray-500">{tool.description}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Select Capability</CardTitle>
              <CardDescription>Choose a capability to call</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {tool.capabilities.map((capability: Capability) => (
                  <div
                    key={capability.name}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedCapability === capability.name
                        ? 'border-primary bg-primary/5'
                        : 'hover:border-gray-300 hover:bg-gray-50'
                    }`}
                    onClick={() => setSelectedCapability(capability.name)}
                  >
                    <div className="flex flex-col">
                      <div className="flex items-center justify-between">
                        <h3 className="font-medium">{capability.name}</h3>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">{capability.description}</p>
                      {selectedCapability === capability.name && (
                        <Badge className="mt-2 self-start">Selected</Badge>
                      )}
                    </div>
                  </div>
                ))}

                {tool.capabilities.length === 0 && (
                  <div className="text-center p-6 border border-dashed rounded-lg">
                    <h3 className="font-medium text-lg mb-2">No capabilities available</h3>
                    <p className="text-gray-500">This tool doesn't have any capabilities defined.</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2">
          {selectedCapability ? (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Call {selectedCapability}</CardTitle>
                  <CardDescription>Provide the parameters for this capability</CardDescription>
                </CardHeader>
                <CardContent>
                  {formSchema ? (
                    <Form {...form}>
                      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                        {tool.capabilities
                          .find((c: Capability) => c.name === selectedCapability)
                          ?.parameters &&
                          Object.entries(
                            tool.capabilities.find((c: Capability) => c.name === selectedCapability)!.parameters
                          ).map(([key, param]: [string, any]) => {
                            return (
                              <FormField
                                key={key}
                                control={form.control}
                                name={key}
                                render={({ field }) => (
                                  <FormItem>
                                    <FormLabel>{key}</FormLabel>
                                    {param.type === 'string' && (
                                      param.description?.toLowerCase().includes('multiline') ? (
                                        <FormControl>
                                          <Textarea
                                            placeholder={param.description || `Enter ${key}`}
                                            {...field}
                                          />
                                        </FormControl>
                                      ) : (
                                        <FormControl>
                                          <Input
                                            placeholder={param.description || `Enter ${key}`}
                                            {...field}
                                          />
                                        </FormControl>
                                      )
                                    )}

                                    {param.type === 'number' && (
                                      <FormControl>
                                        <Input
                                          type="number"
                                          placeholder={param.description || `Enter ${key}`}
                                          {...field}
                                        />
                                      </FormControl>
                                    )}

                                    {param.type === 'boolean' && (
                                      <FormControl>
                                        <Select
                                          onValueChange={(value) => field.onChange(value === 'true')}
                                          defaultValue={field.value?.toString()}
                                        >
                                          <SelectTrigger>
                                            <SelectValue placeholder="Select a value" />
                                          </SelectTrigger>
                                          <SelectContent>
                                            <SelectItem value="true">True</SelectItem>
                                            <SelectItem value="false">False</SelectItem>
                                          </SelectContent>
                                        </Select>
                                      </FormControl>
                                    )}

                                    {(param.type === 'array' || param.type === 'object') && (
                                      <FormControl>
                                        <Textarea
                                          placeholder={`Enter JSON ${param.type === 'array' ? 'array' : 'object'}`}
                                          {...field}
                                        />
                                      </FormControl>
                                    )}

                                    <FormDescription>
                                      {param.description || `Enter ${key}`}
                                      {param.required && ' (Required)'}
                                    </FormDescription>
                                    <FormMessage />
                                  </FormItem>
                                )}
                              />
                            );
                          })}

                        <Button type="submit" disabled={callToolMutation.isPending} className="w-full">
                          {callToolMutation.isPending ? (
                            <>
                              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                              Calling Tool...
                            </>
                          ) : (
                            <>
                              <Send className="mr-2 h-4 w-4" />
                              Call Tool
                            </>
                          )}
                        </Button>
                      </form>
                    </Form>
                  ) : (
                    <div className="text-center p-8">
                      <RefreshCw className="h-8 w-8 mx-auto mb-4 animate-spin text-gray-400" />
                      <p>Loading form...</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {callToolMutation.isSuccess && (
                <Card>
                  <CardHeader>
                    <CardTitle>Result</CardTitle>
                    <CardDescription>The response from the tool</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Tabs value={activeResultTab} onValueChange={setActiveResultTab}>
                      <TabsList className="grid w-full grid-cols-2">
                        <TabsTrigger value="result">Result</TabsTrigger>
                        <TabsTrigger value="raw">Raw JSON</TabsTrigger>
                      </TabsList>
                      <TabsContent value="result" className="pt-4">
                        {typeof callToolMutation.data === 'object' ? (
                          <div className="relative overflow-x-auto border rounded-lg">
                            <table className="w-full text-sm text-left">
                              <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                                <tr>
                                  <th scope="col" className="px-6 py-3">Key</th>
                                  <th scope="col" className="px-6 py-3">Value</th>
                                </tr>
                              </thead>
                              <tbody>
                                {Object.entries(callToolMutation.data || {}).map(([key, value]) => (
                                  <tr key={key} className="bg-white border-b">
                                    <th scope="row" className="px-6 py-4 font-medium whitespace-nowrap">
                                      {key}
                                    </th>
                                    <td className="px-6 py-4">
                                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <div className="p-4 border rounded-lg">{String(callToolMutation.data)}</div>
                        )}
                      </TabsContent>
                      <TabsContent value="raw" className="pt-4">
                        <div className="relative">
                          <div className="bg-gray-900 rounded-md overflow-hidden">
                            <CodeBlock
                              text={JSON.stringify(callToolMutation.data, null, 2)}
                              language="json"
                              showLineNumbers={true}
                              theme={atomOneDark}
                            />
                          </div>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="absolute top-2 right-2 bg-black/20 hover:bg-black/40"
                            onClick={handleCopyResult}
                          >
                            {copySuccess ? (
                              <span className="text-green-400 flex items-center">
                                <Check className="h-4 w-4 mr-1" /> Copied!
                              </span>
                            ) : (
                              <span className="text-white flex items-center">
                                <Copy className="h-4 w-4 mr-1" /> Copy
                              </span>
                            )}
                          </Button>
                        </div>
                      </TabsContent>
                    </Tabs>
                  </CardContent>
                </Card>
              )}

              {callToolMutation.isError && (
                <Card className="border-red-200">
                  <CardHeader>
                    <CardTitle className="text-red-600">Error</CardTitle>
                    <CardDescription>An error occurred while calling the tool</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-red-600">
                        {callToolMutation.error instanceof Error
                          ? callToolMutation.error.message
                          : 'An unknown error occurred'}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}

              <Card>
                <CardHeader>
                  <CardTitle>Code Example</CardTitle>
                  <CardDescription>Example code to call this capability programmatically</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="bg-gray-900 rounded-md overflow-hidden">
                    <CodeBlock
                      text={generateExampleCode()}
                      language="javascript"
                      showLineNumbers={true}
                      theme={atomOneDark}
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Select a Capability</CardTitle>
                <CardDescription>Please select a capability from the list to continue</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex justify-center items-center p-12 border border-dashed rounded-lg">
                  <div className="text-center">
                    <Terminal className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                    <h3 className="font-medium text-lg mb-2">No capability selected</h3>
                    <p className="text-gray-500 mb-4">
                      Select a capability from the list on the left to get started
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}