// src/app/tools/page.tsx
import { Metadata } from 'next';
import { ToolList } from '@/components/tools/tool-list';

export const metadata: Metadata = {
  title: 'Tools | OMEGA Framework',
  description: 'Manage your MCP tools in the OMEGA Framework',
};

export default function ToolsPage() {
  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Tools</h1>
        <a
          href="/tools/create"
          className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90"
        >
          Register Tool
        </a>
      </div>
      <ToolList />
    </div>
  );
}