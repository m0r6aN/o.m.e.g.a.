// src/app/workflows/page.tsx
import { WorkflowList } from '@/components/workflows/workflow-list';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Workflows | OMEGA Framework',
  description: 'Create and manage workflows in the OMEGA Framework',
};

export default function WorkflowsPage() {
  return (
    <div className="container py-6">
      <WorkflowList />
    </div>
  );
}