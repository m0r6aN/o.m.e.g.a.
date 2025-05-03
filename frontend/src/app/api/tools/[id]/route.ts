// app/api/tools/[id]/route.ts
import { NextResponse } from 'next/server';

// GET /api/tools/[id] - Get tool by ID
export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    
    const response = await fetch(`${process.env.BACKEND_URL}/registry/mcp/discover/${id}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json(
          { error: 'Tool not found' },
          { status: 404 }
        );
      }
      throw new Error(`Backend returned ${response.status}`);
    }

    const tool = await response.json();
    return NextResponse.json(tool);
  } catch (error) {
    console.error(`Error fetching tool ${params.id}:`, error);
    return NextResponse.json(
      { error: 'Failed to fetch tool details' },
      { status: 500 }
    );
  }
}

// DELETE /api/tools/[id] - Delete/unregister a tool
export async function DELETE(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    
    const response = await fetch(`${process.env.BACKEND_URL}/registry/mcp/unregister/${id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json(
          { error: 'Tool not found' },
          { status: 404 }
        );
      }
      throw new Error(`Backend returned ${response.status}`);
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error(`Error unregistering tool ${params.id}:`, error);
    return NextResponse.json(
      { error: 'Failed to unregister tool' },
      { status: 500 }
    );
  }
}