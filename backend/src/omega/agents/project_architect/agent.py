#!/usr/bin/env python3
"""
Minimal OMEGA Test Agent
Registers with the agent registry and sends heartbeats.
"""

import os
import asyncio
import json
import time
from datetime import datetime
from typing import List

import httpx
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

# Configuration
AGENT_ID = "test_agent_001"
AGENT_NAME = "Test Agent"
PORT = int(os.getenv("PORT", 9016))
MCP_PORT = int(os.getenv("MCP_PORT", 9017))
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:9401")

# Pydantic Models
class AgentInfo(BaseModel):
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    skills: List[str] = []
    agent_type: str = "agent"
    host: str = "localhost"
    port: int = PORT
    mcp_port: int = MCP_PORT
    tags: List[str] = []
    status: str = "active"

# FastAPI app
app = FastAPI(title="OMEGA Test Agent", version="1.0.0")

# Global variables
registered = False
heartbeat_task = None

async def register_with_registry():
    """Register this agent with the OMEGA registry."""
    global registered
    
    agent_info = AgentInfo(
        id=AGENT_ID,
        name=AGENT_NAME,
        description="A minimal test agent for OMEGA framework",
        skills=["test", "ping", "echo"],
        tags=["test", "minimal"],
        host="project_architect",  # Docker service name
        port=PORT,
        mcp_port=MCP_PORT
    )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{REGISTRY_URL}/agents/register",
                json=agent_info.model_dump(),
                timeout=10.0
            )
            
            if response.status_code == 200:
                print(f"✅ Successfully registered {AGENT_NAME} with registry")
                registered = True
                return True
            else:
                print(f"❌ Failed to register: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Registry connection failed: {e}")
        return False

async def send_heartbeat():
    """Send periodic heartbeats to the registry."""
    while True:
        if registered:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{REGISTRY_URL}/agents/heartbeat",
                        json={"agent_id": AGENT_ID},
                        timeout=5.0
                    )
                    
                    if response.status_code == 200:
                        print(f"💓 Heartbeat sent successfully at {datetime.now()}")
                    else:
                        print(f"⚠️ Heartbeat failed: {response.status_code}")
                        
            except Exception as e:
                print(f"❌ Heartbeat error: {e}")
        
        # Wait 30 seconds before next heartbeat
        await asyncio.sleep(30)

@app.on_event("startup")
async def startup_event():
    """Startup tasks."""
    global heartbeat_task
    
    print(f"🚀 Starting {AGENT_NAME} on port {PORT}")
    
    # Wait a bit for registry to be ready
    await asyncio.sleep(5)
    
    # Register with the registry
    await register_with_registry()
    
    # Start heartbeat task
    heartbeat_task = asyncio.create_task(send_heartbeat())

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global heartbeat_task
    
    if heartbeat_task:
        heartbeat_task.cancel()
    
    print(f"👋 {AGENT_NAME} shutting down")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_id": AGENT_ID,
        "name": AGENT_NAME,
        "registered": registered,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/info")
async def agent_info():
    """Get agent information."""
    return {
        "id": AGENT_ID,
        "name": AGENT_NAME,
        "description": "A minimal test agent for OMEGA framework",
        "version": "1.0.0",
        "skills": ["test", "ping", "echo"],
        "tags": ["test", "minimal"],
        "status": "active",
        "registered": registered,
        "ports": {"api": PORT, "mcp": MCP_PORT}
    }

@app.post("/ping")
async def ping():
    """Simple ping endpoint."""
    return {
        "message": "pong",
        "agent_id": AGENT_ID,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/echo")
async def echo(data: dict):
    """Echo back the received data."""
    return {
        "agent_id": AGENT_ID,
        "echo": data,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    print(f"🌟 OMEGA Test Agent starting on port {PORT}")
    uvicorn.run(
        "agent:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )