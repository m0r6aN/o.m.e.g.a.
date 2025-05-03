# omega/services/agent_registry/service.py

import os
import time
from typing import List, Optional, Literal
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.collection import Collection
from contextlib import asynccontextmanager
from omega.core.agent_discovery import CapabilityRegistry, AgentCapability

capability_registry = CapabilityRegistry(db_client=app.database)

# Data models
class EndpointUrls(BaseModel):
    base_url: str
    a2a_card: Optional[str] = None
    mcp_endpoint: Optional[str] = None


class AgentMetadata(BaseModel):
    description: str
    version: str
    tags: List[str] = []


class AgentInfo(BaseModel):
    id: str
    name: str
    type: Literal["agent", "tool"]
    protocol: Literal["a2a", "mcp", "dual"]
    capabilities: List[str] = []
    endpoints: EndpointUrls
    metadata: AgentMetadata
    last_heartbeat: float = Field(default_factory=time.time)


class HeartbeatRequest(BaseModel):
    id: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to MongoDB on startup
    app.mongodb_client = MongoClient(
        os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
    )
    app.database = app.mongodb_client[os.getenv("MONGODB_NAME", "agent_registry")]
    
    # Create indexes if they don't exist
    app.database.agents.create_index("id", unique=True)
    app.database.agents.create_index("type")
    app.database.agents.create_index("capabilities")
    
    print("🚀 Connected to MongoDB")
    
    yield
    
    # Close MongoDB connection on shutdown
    app.mongodb_client.close()
    print("👋 Closed MongoDB connection")


app = FastAPI(lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get the agents collection
def get_agent_collection() -> Collection:
    return app.database.agents

# A2A Agent Registry

@app.post("/registry/register", response_model=AgentInfo)
async def register_agent(agent: AgentInfo, collection: Collection = Depends(get_agent_collection)):
    """Register a new agent or update an existing one"""
    # Set the current time as last heartbeat
    agent.last_heartbeat = time.time()
    
    # Check if agent already exists
    existing = collection.find_one({"id": agent.id})
    
    if existing:
        # Update existing agent
        collection.update_one(
            {"id": agent.id},
            {"$set": agent.model_dump()}
        )
        return agent
    else:
        # Insert new agent
        collection.insert_one(agent.model_dump())
        return agent


@app.get("/registry/discover", response_model=List[AgentInfo])
async def discover_all_agents(collection: Collection = Depends(get_agent_collection)):
    """Get all registered agents and tools"""
    # Find all agents with heartbeat in the last 60 seconds
    cutoff_time = time.time() - 60
    agents = list(collection.find({"last_heartbeat": {"$gt": cutoff_time}}))
    return agents


@app.get("/registry/discover/{agent_id}", response_model=AgentInfo)
async def discover_agent_by_id(agent_id: str, collection: Collection = Depends(get_agent_collection)):
    """Get a specific agent by ID"""
    agent = collection.find_one({"id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
    return agent


@app.get("/registry/discover/type/{agent_type}", response_model=List[AgentInfo])
async def discover_agents_by_type(
    agent_type: Literal["agent", "tool"], 
    collection: Collection = Depends(get_agent_collection)
):
    """Get all agents or all tools"""
    # Find all agents/tools with heartbeat in the last 60 seconds
    cutoff_time = time.time() - 60
    agents = list(collection.find({
        "type": agent_type,
        "last_heartbeat": {"$gt": cutoff_time}
    }))
    return agents


@app.get("/registry/discover/capability", response_model=List[AgentInfo])
async def discover_agents_by_capability(request: dict, collection: Collection = Depends(get_agent_collection)):
    """Find agents that match a capability with enhanced scoring"""
    capability = request.get("capability")
    min_score = request.get("min_score", 0.5)
    
    if not capability:
        raise HTTPException(status_code=400, detail="Capability name is required")
    
    # Get all active agents
    cutoff_time = time.time() - 60
    all_agents = list(collection.find({"last_heartbeat": {"$gt": cutoff_time}}))
    
    # Initialize the capability matcher
    matcher = EnhancedCapabilityMatcher(None)  # We'll handle registry access directly
    
    # Score and filter agents
    scored_agents = []
    for agent_data in all_agents:
        agent = AgentInfo(**agent_data)
        score = matcher._score_agent_for_capability(agent, capability)
        
        if score >= min_score:
            scored_agents.append({
                "agent_id": agent.id,
                "name": agent.name,
                "score": score,
                "endpoints": agent.endpoints,
                "metadata": agent.metadata
            })
    
    # Sort by score (highest first)
    scored_agents.sort(key=lambda a: a["score"], reverse=True)
    return scored_agents
@app.post("/registry/capabilities/register")
async def register_agent_capabilities(request: dict):
    """Register an agent's capabilities"""
    agent_id = request.get("agent_id")
    capabilities_data = request.get("capabilities", [])
    
    if not agent_id:
        raise HTTPException(status_code=400, detail="Agent ID is required")
    
    # Convert to AgentCapability objects
    capabilities = [AgentCapability(**cap) for cap in capabilities_data]
    
    # Register with the capability registry
    result = await capability_registry.register_agent_capabilities(agent_id, capabilities)
    return result

@app.get("/registry/capabilities/get/{agent_id}")
async def get_agent_capabilities(agent_id: str):
    """Get an agent's registered capabilities"""
    capabilities = await capability_registry.get_agent_capabilities(agent_id)
    return [cap.model_dump() for cap in capabilities]

@app.post("/registry/capabilities/match")
async def match_capability(request: dict):
    """Find agents that match a capability query"""
    capability_query = request.get("text", "")
    min_score = request.get("min_score", 0.5)
    
    if not capability_query:
        raise HTTPException(status_code=400, detail="Capability query is required")
    
    # Use the capability registry to find matching agents
    matches = await capability_registry.match_capability(request, min_score)
    return matches

@app.post("/registry/heartbeat")
async def update_heartbeat(
    request: HeartbeatRequest,
    collection: Collection = Depends(get_agent_collection)
):
    """Update the last heartbeat time for an agent"""
    result = collection.update_one(
        {"id": request.id},
        {"$set": {"last_heartbeat": time.time()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Agent with ID {request.id} not found")
    
    return {"status": "ok"}


@app.delete("/registry/unregister/{agent_id}")
async def unregister_agent(agent_id: str, collection: Collection = Depends(get_agent_collection)):
    """Remove an agent from the registry"""
    result = collection.delete_one({"id": agent_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
    
    return {"status": "ok", "message": f"Agent {agent_id} unregistered successfully"}


