// src/components/workflows/workflow-create-form.tsx
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateWorkflow, useWorkflowTemplates } from '@/hooks/use-workflows';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'react-hot-toast';
import { WorkflowStep } from '@/lib/workflow/client';
import { PlusIcon } from 'lucide-react';

const workflowFormSchema = z.object({
  name: z.string().min(3, {
    message: "Workflow name must be at least 3 characters.",
  }),
  description: z.string().min(10, {
    message: "Description must be at least 10 characters.",
  }),
  status: z.enum(['draft', 'active']),
  tags: z.string().optional(),
});

type WorkflowFormValues = z.infer<typeof workflowFormSchema>;

const defaultValues: Partial<WorkflowFormValues> = {
  name: "",
  description: "",
  status: "draft",
  tags: "",
};

export function WorkflowCreateForm() {
  const router = useRouter();
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [activeTab, setActiveTab] = useState<string>("basic");
  const { data: templates } = useWorkflowTemplates();
  
  const createWorkflow = useCreateWorkflow();
  
  const form = useForm<WorkflowFormValues>({
    resolver: zodResolver(workflowFormSchema),
    defaultValues,
  });
  
  async function onSubmit(data: WorkflowFormValues) {
    try {
      if (steps.length === 0) {
        toast("Please add at least one step to your workflow before creating it.");
        setActiveTab("steps");
        return;
      }
      
      // Process tags string into array
      const tags = data.tags ? data.tags.split(',').map(tag => tag.trim()) : [];
      
      const result = await createWorkflow.mutateAsync({
        name: data.name,
        description: data.description,
        status: data.status,
        steps,
        tags,
      });
      
      toast("Your workflow has been created successfully.");
      
      router.push(`/workflows/${result.id}`);
    } catch (error) {
      toast((error as Error).message);
    }
  }
  
  const addEmptyStep = () => {
    const newStep: WorkflowStep = {
      id: `step-${Date.now()}`,
      name: `Step ${steps.length + 1}`,
      description: "",
      type: "agent",
      target_id: "",
      dependencies: [],
    };
    
    setSteps([...steps, newStep]);
  };
  
  const updateStep = (index: number, updates: Partial<WorkflowStep>) => {
    const updatedSteps = [...steps];
    updatedSteps[index] = { ...updatedSteps[index], ...updates };
    setSteps(updatedSteps);
  };
  
  const removeStep = (index: number) => {
    const stepId = steps[index].id;
    
    // First, remove this step from dependencies of other steps
    const updatedSteps = steps.map(step => ({
      ...step,
      dependencies: step.dependencies.filter(dep => dep !== stepId)
    }));
    
    // Then remove the step itself
    updatedSteps.splice(index, 1);
    
    setSteps(updatedSteps);
  };
  
  const applyTemplate = (templateId: string) => {
    const template = templates?.find(t => t.id === templateId);
    
    if (!template) {
      toast("Template not found");
      return;
    }
    
    // Generate IDs for the template steps
    const templateSteps = template.steps.map(step => ({
      ...step,
      id: `step-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
    }));
    
    setSteps(templateSteps);
    
    form.setValue("name", template.name);
    form.setValue("description", template.description);
    
    if (template.tags.length > 0) {
      form.setValue("tags", template.tags.join(', '));
    }
    
    toast("Template applied successfully.");
    setActiveTab("steps");
  };
  
  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="basic">Basic Info</TabsTrigger>
          <TabsTrigger value="steps">Steps</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
        </TabsList>
        
        <TabsContent value="basic" className="space-y-4 pt-4">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Workflow Name</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter workflow name" {...field} />
                    </FormControl>
                    <FormDescription>
                      A descriptive name for your workflow.
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
                        placeholder="Describe what this workflow does"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      A detailed description of the workflow's purpose and behavior.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="status"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Status</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select status" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="draft">Draft</SelectItem>
                          <SelectItem value="active">Active</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        Draft workflows can be edited but not executed.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="tags"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Tags</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Enter comma-separated tags"
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Optional tags to categorize this workflow.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              
              <Button 
                type="button" 
                variant="outline"
                onClick={() => setActiveTab("steps")}
              >
                Continue to Steps
              </Button>
            </form>
          </Form>
        </TabsContent>
        
        <TabsContent value="steps" className="space-y-4 pt-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium">Workflow Steps</h3>
            <Button onClick={addEmptyStep} size="sm">
              <PlusIcon className="h-4 w-4 mr-2" />
              Add Step
            </Button>
          </div>
          
          {steps.length === 0 ? (
            <div className="text-center p-12 border border-dashed rounded-lg">
              <p className="text-muted-foreground mb-4">
                No steps defined yet. Add steps to your workflow or use a template.
              </p>
              <div className="flex justify-center gap-4">
                <Button onClick={addEmptyStep}>
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Add Step
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => setActiveTab("templates")}
                >
                  Use Template
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {steps.map((step, index) => (
                <StepEditor
                  key={step.id}
                  step={step}
                  index={index}
                  updateStep={(updates) => updateStep(index, updates)}
                  removeStep={() => removeStep(index)}
                  availableStepIds={steps.map(s => s.id).filter(id => id !== step.id)}
                />
              ))}
            </div>
          )}
          
          <div className="flex justify-between pt-4">
            <Button 
              variant="outline" 
              onClick={() => setActiveTab("basic")}
            >
              Back to Basic Info
            </Button>
            
            <Button 
              onClick={form.handleSubmit(onSubmit)}
              disabled={createWorkflow.isPending}
            >
              Create Workflow
            </Button>
          </div>
        </TabsContent>
        
        <TabsContent value="templates" className="space-y-4 pt-4">
          <h3 className="text-lg font-medium mb-4">Workflow Templates</h3>
          
          {!templates || templates.length === 0 ? (
            <div className="text-center p-12 border border-dashed rounded-lg">
              <p className="text-muted-foreground mb-4">
                No templates available. Create a workflow from scratch.
              </p>
              <Button onClick={() => setActiveTab("basic")}>
                Create Custom Workflow
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {templates.map((template) => (
                <Card 
                  key={template.id} 
                  className="cursor-pointer hover:border-primary transition-colors"
                  onClick={() => applyTemplate(template.id)}
                >
                  <CardHeader>
                    <CardTitle>{template.name}</CardTitle>
                    <CardDescription>{template.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-sm text-muted-foreground mb-2">
                      {template.steps.length} step{template.steps.length !== 1 ? 's' : ''}
                    </div>
                    <Button variant="secondary" size="sm" className="w-full">
                      Use Template
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface StepEditorProps {
  step: WorkflowStep;
  index: number;
  updateStep: (updates: Partial<WorkflowStep>) => void;
  removeStep: () => void;
  availableStepIds: string[];
}

function StepEditor({ step, index, updateStep, removeStep, availableStepIds }: StepEditorProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <CardTitle className="text-lg flex items-center">
            <span className="bg-primary text-primary-foreground w-6 h-6 rounded-full flex items-center justify-center text-sm mr-2">
              {index + 1}
            </span>
            <Input
              value={step.name}
              onChange={(e) => updateStep({ name: e.target.value })}
              className="border-none text-lg font-semibold p-0 h-7"
              placeholder="Step Name"
            />
          </CardTitle>
          <Button variant="destructive" size="sm" onClick={removeStep}>
            Remove
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <FormLabel>Description</FormLabel>
          <Textarea
            value={step.description}
            onChange={(e) => updateStep({ description: e.target.value })}
            placeholder="Describe what this step does"
            className="mt-1"
          />
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormLabel>Step Type</FormLabel>
            <Select
              value={step.type}
              onValueChange={(value) => updateStep({ type: value as any })}
            >
              <SelectTrigger className="mt-1">
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="agent">Agent</SelectItem>
                <SelectItem value="tool">Tool</SelectItem>
                <SelectItem value="condition">Condition</SelectItem>
                <SelectItem value="trigger">Trigger</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <FormLabel>Target ID</FormLabel>
            <Input
              value={step.target_id}
              onChange={(e) => updateStep({ target_id: e.target.value })}
              placeholder="Enter target ID"
              className="mt-1"
            />
          </div>
        </div>
        
        <div>
          <FormLabel>Dependencies</FormLabel>
          <div className="mt-1">
            {availableStepIds.length === 0 ? (
              <div className="text-sm text-muted-foreground">
                No other steps available to depend on.
              </div>
            ) : (
              <div className="space-y-2">
                {availableStepIds.map((stepId) => (
                  <div key={stepId} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id={`dep-${stepId}`}
                      checked={step.dependencies.includes(stepId)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          updateStep({
                            dependencies: [...step.dependencies, stepId]
                          });
                        } else {
                          updateStep({
                            dependencies: step.dependencies.filter(id => id !== stepId)
                          });
                        }
                      }}
                      className="rounded border-gray-300"
                    />
                    <label htmlFor={`dep-${stepId}`} className="text-sm">
                      {stepId}
                    </label>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        
        <div>
          <FormLabel>Parameters (JSON)</FormLabel>
          <Textarea
            value={step.parameters ? JSON.stringify(step.parameters, null, 2) : ''}
            onChange={(e) => {
              try {
                const params = e.target.value ? JSON.parse(e.target.value) : undefined;
                updateStep({ parameters: params });
              } catch (err) {
                // Don't update if JSON is invalid
              }
            }}
            placeholder="{}"
            className="mt-1 font-mono text-sm"
          />
        </div>
      </CardContent>
    </Card>
  );
}