// src/app/agents/create/page.tsx
import { Metadata } from 'next';
import { AgentCreate } from '@/components/agents/agent-create';

export const metadata: Metadata = {
  title: 'Create Agent | OMEGA Framework',
  description: 'Create a new agent in the OMEGA Framework',
};

export default function CreateAgentPage() {
  return (
    <div className="container mx-auto py-6">
      <AgentCreate />
    </div>
  );
}