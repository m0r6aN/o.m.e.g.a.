// app/api/agents/route.ts
import { NextResponse } from 'next/server';

// GET /api/agents - Get all agents
export async function GET() {
  try {
    // In a real implementation, this would fetch from your backend service
    const response = await fetch(`${process.env.BACKEND_URL}/registry/discover`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const agents = await response.json();
    return NextResponse.json(agents);
  } catch (error) {
    console.error('Error fetching agents:', error);
    return NextResponse.json(
      { error: 'Failed to fetch agents' },
      { status: 500 }
    );
  }
}

// POST /api/agents - Create/register a new agent
export async function POST(request: Request) {
  try {
    const agentData = await request.json();
    
    const response = await fetch(`${process.env.BACKEND_URL}/registry/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(agentData),
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const result = await response.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error('Error registering agent:', error);
    return NextResponse.json(
      { error: 'Failed to register agent' },
      { status: 500 }
    );
  }
}