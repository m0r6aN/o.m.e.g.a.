#!/usr/bin/env python3
"""
Minimal OMEGA Agent Registry Service
Handles agent registration, discovery, and heartbeats.
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import redis.asyncio as redis
from pymongo import MongoClient
import uvicorn

# Configuration
PORT = int(os.getenv("PORT", 9401))
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://omega:omegapass@localhost:27017/agent_registry?authSource=admin")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

# Setup logging
logging.basicConfig(level=LOG_LEVEL.upper())
logger = logging.getLogger("agent_registry")

# Pydantic Models
class AgentInfo(BaseModel):
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    skills: List[str] = []
    agent_type: str = "agent"
    host: str = "localhost"
    port: int = 8000
    mcp_port: Optional[int] = None
    tags: List[str] = []
    status: str = "registered"
    last_heartbeat: Optional[datetime] = None
    registered_at: datetime = Field(default_factory=datetime.utcnow)

class HeartbeatRequest(BaseModel):
    agent_id: str
    status: str = "active"

# Global connections
redis_client: Optional[redis.Redis] = None
mongo_client: Optional[MongoClient] = None
agents_collection = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global redis_client, mongo_client, agents_collection
    
    # Startup
    logger.info("🚀 Starting OMEGA Agent Registry Service")
    
    try:
        # Connect to Redis
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        await redis_client.ping()
        logger.info("✅ Connected to Redis")
        
        # Connect to MongoDB
        mongo_client = MongoClient(MONGODB_URL)
        db = mongo_client.get_default_database()
        agents_collection = db.agents
        
        # Test MongoDB connection
        mongo_client.admin.command('ping')
        logger.info("✅ Connected to MongoDB")
        
        # Create indexes
        agents_collection.create_index("id", unique=True)
        agents_collection.create_index("last_heartbeat")
        
        logger.info("🌟 Agent Registry Service is READY!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize connections: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Agent Registry Service")
    if redis_client:
        await redis_client.close()
    if mongo_client:
        mongo_client.close()

# Create FastAPI app
app = FastAPI(
    title="OMEGA Agent Registry",
    description="Central registry for OMEGA framework agents",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis
        await redis_client.ping()
        
        # Check MongoDB
        mongo_client.admin.command('ping')
        
        return {
            "status": "healthy",
            "service": "agent_registry",
            "timestamp": datetime.utcnow().isoformat(),
            "connections": {
                "redis": "connected",
                "mongodb": "connected"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/agents/register")
async def register_agent(agent: AgentInfo, background_tasks: BackgroundTasks):
    """Register a new agent"""
    try:
        # Store in MongoDB
        agent_dict = agent.model_dump()
        agents_collection.replace_one(
            {"id": agent.id},
            agent_dict,
            upsert=True
        )
        
        # Store in Redis for fast access
        await redis_client.hset(
            f"agent:{agent.id}",
            mapping={
                "name": agent.name,
                "status": agent.status,
                "last_heartbeat": datetime.utcnow().isoformat(),
                "host": agent.host,
                "port": str(agent.port)
            }
        )
        
        # Set TTL for Redis entry (agents must send heartbeats)
        await redis_client.expire(f"agent:{agent.id}", 300)  # 5 minutes
        
        logger.info(f"✅ Registered agent: {agent.id} ({agent.name})")
        
        return {
            "status": "registered",
            "agent_id": agent.id,
            "message": f"Agent {agent.name} registered successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to register agent {agent.id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agents/heartbeat")
async def agent_heartbeat(heartbeat: HeartbeatRequest):
    """Receive agent heartbeat"""
    try:
        current_time = datetime.utcnow()
        
        # Update MongoDB
        result = agents_collection.update_one(
            {"id": heartbeat.agent_id},
            {
                "$set": {
                    "last_heartbeat": current_time,
                    "status": heartbeat.status
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update Redis
        await redis_client.hset(
            f"agent:{heartbeat.agent_id}",
            mapping={
                "status": heartbeat.status,
                "last_heartbeat": current_time.isoformat()
            }
        )
        await redis_client.expire(f"agent:{heartbeat.agent_id}", 300)
        
        return {
            "status": "acknowledged",
            "agent_id": heartbeat.agent_id,
            "timestamp": current_time.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Heartbeat failed for {heartbeat.agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
async def list_agents():
    """List all registered agents"""
    try:
        agents = list(agents_collection.find({}, {"_id": 0}))
        
        # Convert datetime objects to ISO strings
        for agent in agents:
            if "registered_at" in agent and agent["registered_at"]:
                agent["registered_at"] = agent["registered_at"].isoformat()
            if "last_heartbeat" in agent and agent["last_heartbeat"]:
                agent["last_heartbeat"] = agent["last_heartbeat"].isoformat()
        
        return {
            "agents": agents,
            "count": len(agents),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent information"""
    try:
        agent = agents_collection.find_one({"id": agent_id}, {"_id": 0})
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Convert datetime objects
        if "registered_at" in agent and agent["registered_at"]:
            agent["registered_at"] = agent["registered_at"].isoformat()
        if "last_heartbeat" in agent and agent["last_heartbeat"]:
            agent["last_heartbeat"] = agent["last_heartbeat"].isoformat()
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/agents/{agent_id}")
async def unregister_agent(agent_id: str):
    """Unregister an agent"""
    try:
        # Remove from MongoDB
        result = agents_collection.delete_one({"id": agent_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Remove from Redis
        await redis_client.delete(f"agent:{agent_id}")
        
        logger.info(f"✅ Unregistered agent: {agent_id}")
        
        return {
            "status": "unregistered",
            "agent_id": agent_id,
            "message": "Agent unregistered successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to unregister agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get registry statistics"""
    try:
        total_agents = agents_collection.count_documents({})
        active_agents = agents_collection.count_documents({
            "last_heartbeat": {"$gte": datetime.utcnow() - timedelta(minutes=5)}
        })
        
        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "inactive_agents": total_agents - active_agents,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info(f"🚀 Starting OMEGA Agent Registry on port {PORT}")
    uvicorn.run(
        "service:app",
        host="0.0.0.0",
        port=PORT,
        log_level=LOG_LEVEL.lower(),
        reload=False
    )