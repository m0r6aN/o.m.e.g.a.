// app/api/tools/route.ts
import { NextResponse } from 'next/server';

// GET /api/tools - Get all tools
export async function GET() {
  try {
    // In a real implementation, this would fetch from your backend service
    const response = await fetch(`${process.env.BACKEND_URL}/registry/mcp/discover`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const tools = await response.json();
    return NextResponse.json(tools);
  } catch (error) {
    console.error('Error fetching tools:', error);
    return NextResponse.json(
      { error: 'Failed to fetch tools' },
      { status: 500 }
    );
  }
}

// POST /api/tools - Create/register a new tool
export async function POST(request: Request) {
  try {
    const toolData = await request.json();
    
    const response = await fetch(`${process.env.BACKEND_URL}/registry/mcp/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(toolData),
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error('Error registering tool:', error);
    return NextResponse.json(
      { error: 'Failed to register tool' },
      { status: 500 }
    );
  }
}