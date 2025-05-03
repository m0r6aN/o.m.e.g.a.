// src/app/workflows/create/page.tsx
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { WorkflowCreateForm } from '@/components/workflows/workflow-create-form';
import { ArrowLeftIcon } from 'lucide-react';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Create Workflow | OMEGA Framework',
  description: 'Create a new workflow in the OMEGA Framework',
};

export default function CreateWorkflowPage() {
  return (
    <div className="container py-6">
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/workflows">
            <ArrowLeftIcon className="h-4 w-4" />
          </Link>
        </Button>
        <h1 className="text-2xl font-bold">Create New Workflow</h1>
      </div>
      
      <div className="max-w-4xl mx-auto">
        <WorkflowCreateForm />
      </div>
    </div>
  );
}