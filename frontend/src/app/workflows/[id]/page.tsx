// src/app/workflows/[id]/page.tsx
import { WorkflowDetail } from '@/components/workflows/workflow-detail';
import { Metadata } from 'next';

interface WorkflowDetailsPageProps {
  params: {
    id: string;
  };
}

export const generateMetadata = async (
  { params }: WorkflowDetailsPageProps
): Promise<Metadata> {
  // You could fetch the workflow here to get its actual name for the title
  // For simplicity, we'll use a generic title
  return {
    title: `Workflow Details | OMEGA Framework`,
    description: 'View and manage a workflow in the OMEGA Framework',
  };
};

export default function WorkflowDetailsPage({ params }: WorkflowDetailsPageProps) {
  return (
    <div className="container py-6">
      <WorkflowDetail workflowId={params.id} />
    </div>
  );
}