// app/api/agents/[id]/route.ts
import { NextResponse } from 'next/server';

// GET /api/agents/[id] - Get agent by ID
export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    
    const response = await fetch(`${process.env.BACKEND_URL}/registry/discover/${id}`, {
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

    const agent = await response.json();
    return NextResponse.json(agent);
  } catch (error) {
    console.error(`Error fetching agent ${params.id}:`, error);
    return NextResponse.json(
      { error: 'Failed to fetch agent details' },
      { status: 500 }
    );
  }
}

// DELETE /api/agents/[id] - Delete/unregister an agent
export async function DELETE(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    
    const response = await fetch(`${process.env.BACKEND_URL}/registry/unregister/${id}`, {
      method: 'DELETE',
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

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error(`Error unregistering agent ${params.id}:`, error);
    return NextResponse.json(
      { error: 'Failed to unregister agent' },
      { status: 500 }
    );
  }
}