// app/api/tools/call/route.ts
import { NextResponse } from 'next/server';

// POST /api/tools/call - Call a tool
export async function POST(request: Request) {
  try {
    const { toolId, capability, parameters } = await request.json();
    
    // First, get the tool to find its endpoint
    const toolResponse = await fetch(`${process.env.BACKEND_URL}/registry/mcp/discover/${toolId}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!toolResponse.ok) {
      if (toolResponse.status === 404) {
        return NextResponse.json(
          { error: 'Tool not found' },
          { status: 404 }
        );
      }
      throw new Error(`Backend returned ${toolResponse.status}`);
    }

    const tool = await toolResponse.json();
    
    // Now call the tool endpoint
    const callResponse = await fetch(tool.mcp_endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: capability,
        parameters: parameters
      }),
    });

    if (!callResponse.ok) {
      throw new Error(`Tool call failed with status ${callResponse.status}`);
    }

    const result = await callResponse.json();
    return NextResponse.json(result);
  } catch (error) {
    console.error('Error calling tool:', error);
    return NextResponse.json(
      { error: 'Failed to call tool' },
      { status: 500 }
    );
  }
}