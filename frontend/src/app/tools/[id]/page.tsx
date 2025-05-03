// src/app/tools/[id]/page.tsx
import { Metadata } from 'next';
import { ToolDetail } from '@/components/tools/tool-detail';

export const metadata: Metadata = {
  title: 'Tool Details | OMEGA Framework',
  description: 'View and manage tool details in the OMEGA Framework',
};

export default function ToolDetailPage({ params }: { params: { id: string } }) {
  return (
    <div className="container mx-auto py-6">
      <ToolDetail toolId={params.id} />
    </div>
  );
}