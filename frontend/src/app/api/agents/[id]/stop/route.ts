// app/api/agents/[id]/stop/route.ts
import { NextResponse } from 'next/server';

// POST /api/agents/[id]/stop - Stop an agent
export async function POST(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    
    const response = await fetch(`${process.env.BACKEND_URL}/registry/agents/${id}/stop`, {
      method: 'POST',
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

    return NextResponse.json({ success: true, status: 'inactive' });
  } catch (error) {
    console.error(`Error stopping agent ${params.id}:`, error);
    return NextResponse.json(
      { error: 'Failed to stop agent' },
      { status: 500 }
    );
  }
}