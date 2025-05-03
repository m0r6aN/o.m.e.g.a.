// src/app/agents/[id]/page.tsx
import { Metadata } from 'next';
import { AgentDetail } from '@/components/agents/agent-detail';

export const metadata: Metadata = {
  title: 'Agent Details | OMEGA Framework',
  description: 'View and manage agent details in the OMEGA Framework',
};

export default function AgentDetailPage({ params }: { params: { id: string } }) {
  return (
    <div className="container mx-auto py-6">
      <AgentDetail agentId={params.id} />
    </div>
  );
}