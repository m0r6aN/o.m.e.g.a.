// app/api/agents/[id]/start/route.ts
import { NextResponse } from 'next/server';

// POST /api/agents/[id]/start - Start an agent
export async function POST(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    
    const response = await fetch(`${process.env.BACKEND_URL}/registry/agents/${id}/start`, {
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

    return NextResponse.json({ success: true, status: 'active' });
  } catch (error) {
    console.error(`Error starting agent ${params.id}:`, error);
    return NextResponse.json(
      { error: 'Failed to start agent' },
      { status: 500 }
    );
  }
}