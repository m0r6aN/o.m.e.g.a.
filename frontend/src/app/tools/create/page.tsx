// src/app/tools/create/page.tsx
import { Metadata } from 'next';
import { ToolRegister } from '@/components/tools/tool-register';

export const metadata: Metadata = {
  title: 'Register Tool | OMEGA Framework',
  description: 'Register a new MCP tool with the OMEGA Framework',
};

export default function RegisterToolPage() {
  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">Register New Tool</h1>
      <ToolRegister />
    </div>
  );
}