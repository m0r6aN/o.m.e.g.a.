# /omega/services/agent_registry/service.py
"""
Minimal OMEGA Agent Registry Service
A lightweight service to get the constellation operational
"""

import os
import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis.asyncio import Redis

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent_registry")

# Models
class AgentInfo(BaseModel):
    id: str
    name: str
    type: str
    description: str
    version: str
    host: str
    port: int
    mcp_port: int
    capabilities: List[Dict[str, Any]] = []
    skills: List[str] = []
    tags: List[str] = []
    status: str = "active"
    registered_at: datetime = None
    last_heartbeat: datetime = None

class HeartbeatRequest(BaseModel):
    agent_id: str

class RegistryService:
    def __init__(self):
        self.app = FastAPI(
            title="OMEGA Agent Registry",
            version="1.0.0",
            description="Central registry for OMEGA AI agents"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # In-memory storage (for now)
        self.agents: Dict[str, AgentInfo] = {}
        self.redis: Redis = None
        
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.on_event("startup")
        async def startup():
            logger.info("🚀 Starting OMEGA Agent Registry Service")
            try:
                # Connect to Redis
                self.redis = Redis(
                    host=os.getenv("REDIS_HOST", "redis"),
                    port=int(os.getenv("REDIS_PORT", "6379")),
                    decode_responses=True
                )
                await self.redis.ping()
                logger.info("✅ Connected to Redis")
            except Exception as e:
                logger.warning(f"⚠️ Redis connection failed: {e}")
                logger.info("📝 Using in-memory storage only")
                self.redis = None
            
            logger.info("🌟 Agent Registry is ready for business!")
        
        @self.app.on_event("shutdown")
        async def shutdown():
            if self.redis:
                await self.redis.close()
            logger.info("👋 Agent Registry shutting down")
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            redis_status = "connected" if self.redis else "disconnected"
            return {
                "status": "healthy",
                "service": "agent_registry",
                "version": "1.0.0",
                "redis": redis_status,
                "registered_agents": len(self.agents),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.post("/agents/register")
        async def register_agent(agent_info: AgentInfo):
            """Register a new agent"""
            try:
                agent_info.registered_at = datetime.utcnow()
                agent_info.last_heartbeat = datetime.utcnow()
                
                self.agents[agent_info.id] = agent_info
                
                # Store in Redis if available
                if self.redis:
                    await self.redis.hset(
                        "agents", 
                        agent_info.id, 
                        agent_info.model_dump_json()
                    )
                
                logger.info(f"✅ Registered agent: {agent_info.name} ({agent_info.id})")
                return {"status": "registered", "agent_id": agent_info.id}
                
            except Exception as e:
                logger.error(f"❌ Registration failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/agents/heartbeat")
        async def agent_heartbeat(heartbeat: HeartbeatRequest):
            """Process agent heartbeat"""
            agent_id = heartbeat.agent_id
            
            if agent_id not in self.agents:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            # Update heartbeat timestamp
            self.agents[agent_id].last_heartbeat = datetime.utcnow()
            
            # Update in Redis if available
            if self.redis:
                await self.redis.hset(
                    "agents",
                    agent_id,
                    self.agents[agent_id].model_dump_json()
                )
            
            return {"status": "acknowledged", "agent_id": agent_id}
        
        @self.app.get("/agents")
        async def list_agents():
            """List all registered agents"""
            # Clean up stale agents (no heartbeat in 5 minutes)
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            active_agents = {}
            
            for agent_id, agent_info in self.agents.items():
                if agent_info.last_heartbeat and agent_info.last_heartbeat > cutoff_time:
                    active_agents[agent_id] = agent_info
                else:
                    logger.info(f"🧹 Removing stale agent: {agent_info.name}")
            
            self.agents = active_agents
            
            return {
                "agents": list(self.agents.values()),
                "count": len(self.agents),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.get("/agents/{agent_id}")
        async def get_agent(agent_id: str):
            """Get specific agent information"""
            if agent_id not in self.agents:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            return self.agents[agent_id]
        
        @self.app.delete("/agents/{agent_id}")
        async def unregister_agent(agent_id: str):
            """Unregister an agent"""
            if agent_id not in self.agents:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            agent_name = self.agents[agent_id].name
            del self.agents[agent_id]
            
            # Remove from Redis if available
            if self.redis:
                await self.redis.hdel("agents", agent_id)
            
            logger.info(f"👋 Unregistered agent: {agent_name} ({agent_id})")
            return {"status": "unregistered", "agent_id": agent_id}
        
        @self.app.get("/status")
        async def system_status():
            """Get system status"""
            return {
                "service": "OMEGA Agent Registry",
                "version": "1.0.0",
                "status": "operational",
                "registered_agents": len(self.agents),
                "redis_connected": self.redis is not None,
                "uptime": "running",
                "timestamp": datetime.utcnow().isoformat()
            }

# Create service instance
service = RegistryService()
app = service.app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "9401"))
    logger.info(f"🚀 Starting OMEGA Agent Registry on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )