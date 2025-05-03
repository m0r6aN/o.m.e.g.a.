// app/api/agents/[id]/tasks/route.ts
import { NextResponse } from 'next/server';

// GET /api/agents/[id]/tasks - Get tasks for an agent
export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    
    const response = await fetch(`${process.env.BACKEND_URL}/registry/agents/${id}/tasks`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json(
          { error: 'Agent not found' },
          { status: 404 }
        );
      }
      throw new Error(`Backend returned ${response.status}`);
    }

    const tasks = await response.json();
    return NextResponse.json(tasks);
  } catch (error) {
    console.error(`Error fetching tasks for agent ${params.id}:`, error);
    return NextResponse.json(
      { error: 'Failed to fetch agent tasks' },
      { status: 500 }
    );
  }
}