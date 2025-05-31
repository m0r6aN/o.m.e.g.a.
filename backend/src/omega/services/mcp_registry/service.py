# D:/Repos/o.m.e.g.a/backend/src/omega/services/mcp_registry/service.py

"""
OMEGA MCP Registry Service
Manages registration, discovery, and health monitoring of MCP tools
"""

from __future__ import annotations
import os
import time
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

# ============================================================================
# CONFIGURATION
# ============================================================================

SERVICE_NAME = "MCP Registry Service"
SERVICE_ID = "mcp_registry"
PORT = int(os.getenv("PORT", 9402))
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://omega:omegapass@mongo:27017/omega?authSource=admin")
MONGODB_NAME = os.getenv("MONGODB_NAME", "omega")
HEARTBEAT_TIMEOUT = int(os.getenv("HEARTBEAT_TIMEOUT", "60"))  # seconds

print(f"🔧 {SERVICE_NAME} Configuration:")
print(f"   Port: {PORT}")
print(f"   MongoDB: {MONGODB_URL}")
print(f"   Database: {MONGODB_NAME}")
print(f"   Heartbeat Timeout: {HEARTBEAT_TIMEOUT}s")

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ToolCapability(BaseModel):
    """Represents a single capability/function of an MCP tool"""
    name: str = Field(..., description="Name of the capability/function")
    description: str = Field(..., description="Description of what this capability does")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters schema")
    returns: Dict[str, Any] = Field(default_factory=dict, description="Return value schema")

class MCPToolInfo(BaseModel):
    """Complete information about a registered MCP tool"""
    id: str = Field(..., description="Unique identifier for the tool")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Description of the tool's purpose")
    version: str = Field(default="1.0.0", description="Tool version")
    capabilities: List[ToolCapability] = Field(default_factory=list, description="List of tool capabilities")
    host: str = Field(..., description="Host where the tool is running")
    port: int = Field(..., description="Port where the tool is accessible")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    endpoints: Dict[str, str] = Field(default_factory=dict, description="Tool endpoints")
    last_heartbeat: float = Field(default_factory=time.time, description="Last heartbeat timestamp")
    status: str = Field(default="active", description="Tool status")
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MCPToolRegistration(BaseModel):
    """Request model for registering an MCP tool"""
    id: str = Field(..., description="Unique identifier for the tool")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Description of the tool's purpose")
    version: str = Field(default="1.0.0", description="Tool version")
    capabilities: List[ToolCapability] = Field(default_factory=list, description="List of tool capabilities")
    host: str = Field(..., description="Host where the tool is running")
    port: int = Field(..., description="Port where the tool is accessible")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    endpoints: Dict[str, str] = Field(default_factory=dict, description="Tool endpoints")

class MCPToolHeartbeat(BaseModel):
    """Request model for tool heartbeat updates"""
    id: str = Field(..., description="Tool ID sending the heartbeat")
    
class HealthCheck(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Health status of the service")
    service: str = Field(..., description="Name of the service")
    timestamp: str = Field(..., description="Timestamp of the health check")
    database_connected: bool = Field(..., description="Whether the database connection is active")

class ToolQuery(BaseModel):
    """Request model for querying tools by capabilities"""
    capability: Optional[str] = Field(None, description="Required capability name")
    tags: List[str] = Field(default_factory=list, description="Required tags")
    status: str = Field(default="active", description="Tool status filter")

# ============================================================================
# DATABASE SETUP
# ============================================================================

class DatabaseManager:
    """Manages MongoDB connections and operations"""
    
    def __init__(self):
        self.client: Optional[MongoClient[Dict[str, Any]]] = None
        self.db: Optional[Database[Dict[str, Any]]] = None
        self.mcp_tools: Optional[Collection[Dict[str, Any]]] = None
        
    async def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.client = MongoClient(MONGODB_URL)
            self.db = self.client[MONGODB_NAME]
            self.mcp_tools = self.db.mcp_tools
            
            # Create indexes for better performance
            self.mcp_tools.create_index("id", unique=True)
            self.mcp_tools.create_index("capabilities.name")
            self.mcp_tools.create_index("tags")
            self.mcp_tools.create_index("last_heartbeat")
            self.mcp_tools.create_index("status")
            
            # Test the connection
            self.client.admin.command('ping')
            print(f"✅ Connected to MongoDB: {MONGODB_NAME}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Close database connection"""
        if self.client:
            self.client.close()
            print("👋 Disconnected from MongoDB")

# Global database manager
db_manager = DatabaseManager()

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_mcp_tools_collection() -> Collection[Dict[str, Any]]:
    """Dependency to get the MCP tools collection"""
    if db_manager.mcp_tools is None:
        print("❌ Database not connected - cannot access MCP tools collection")
        raise HTTPException(status_code=500, detail="Database not connected")
    return db_manager.mcp_tools

# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    # Startup
    print(f"🚀 Starting {SERVICE_NAME}")
    
    # Connect to database
    if not await db_manager.connect():
        print("❌ Failed to connect to database - exiting")
        return
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_stale_tools())
    
    print(f"✅ {SERVICE_NAME} is ready!")
    
    yield  # Application runs here
    
    # Shutdown
    print(f"🛑 Shutting down {SERVICE_NAME}")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    
    await db_manager.disconnect()
    print(f"👋 {SERVICE_NAME} shutdown complete")

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def cleanup_stale_tools() -> None:
    """Background task to clean up stale tools"""
    while True:
        try:
            if db_manager.mcp_tools is not None:
                cutoff_time = time.time() - HEARTBEAT_TIMEOUT
                
                # Mark stale tools as inactive
                result = db_manager.mcp_tools.update_many(
                    {
                        "last_heartbeat": {"$lt": cutoff_time},
                        "status": "active"
                    },
                    {"$set": {"status": "inactive"}}
                )
                
                if result.modified_count > 0:
                    print(f"⚠️ Marked {result.modified_count} tools as inactive due to missed heartbeat")
                
                # Remove very old inactive tools (older than 5 minutes)
                very_old_cutoff = time.time() - (5 * 60)
                result = db_manager.mcp_tools.delete_many(
                    {
                        "last_heartbeat": {"$lt": very_old_cutoff},
                        "status": "inactive"
                    }
                )
                
                if result.deleted_count > 0:
                    print(f"🗑️ Removed {result.deleted_count} very old inactive tools")
            else:
                print("❌ Database not connected - cannot perform cleanup")
            
        except Exception as e:
            print(f"❌ Error in cleanup task: {e}")
        
        # Run cleanup every 30 seconds
        await asyncio.sleep(30)

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="OMEGA MCP Registry Service",
    description="Central registry for MCP tools in the OMEGA framework",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        if db_manager.client is None or db_manager.db is None:
            print("❌ Database not connected")
            raise HTTPException(status_code=500, detail="Database not connected")
        
        # Test the connection
        db_manager.client.admin.command('ping')
        
        return HealthCheck(
            status="ok",
            service=SERVICE_NAME,
            timestamp=datetime.now(timezone.utc).isoformat(),
            database_connected=True
        )
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/registry/mcp/register", response_model=MCPToolInfo)
async def register_mcp_tool(
    tool: MCPToolRegistration, 
    collection: Collection[Dict[str, Any]] = Depends(get_mcp_tools_collection)
):
    """Register a new MCP tool or update an existing one"""
    try:
        # Prepare tool document
        tool_dict = tool.model_dump()
        tool_dict["last_heartbeat"] = time.time()
        tool_dict["status"] = "active"
        tool_dict["registered_at"] = datetime.now(timezone.utc)
        
        # Add default endpoints if not provided
        if not tool_dict.get("endpoints"):
            tool_dict["endpoints"] = {
                "health": f"http://{tool.host}:{tool.port}/health",
                "capabilities": f"http://{tool.host}:{tool.port}/capabilities"
            }
        
        # Upsert the tool (update if exists, insert if not)
        collection.replace_one(
            {"id": tool.id},
            tool_dict,
            upsert=True
        )
        
        print(f"✅ Registered MCP tool: {tool.id} ({tool.name})")
        return MCPToolInfo(**tool_dict)
        
    except Exception as e:
        print(f"❌ Error registering tool {tool.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to register tool: {str(e)}")

@app.post("/registry/mcp/heartbeat")
async def update_mcp_tool_heartbeat(
    request: MCPToolHeartbeat,
    collection: Collection[Dict[str, Any]] = Depends(get_mcp_tools_collection)
):
    """Update the last heartbeat time for an MCP tool"""
    try:
        result = collection.update_one(
            {"id": request.id},
            {
                "$set": {
                    "last_heartbeat": time.time(),
                    "status": "active"
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"MCP tool with ID {request.id} not found")
        
        return {"status": "ok", "timestamp": time.time()}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating heartbeat for {request.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update heartbeat: {str(e)}")

@app.get("/registry/mcp/discover", response_model=List[MCPToolInfo])
async def discover_all_mcp_tools(
    active_only: bool = True,
    collection: Collection[Dict[str, Any]] = Depends(get_mcp_tools_collection)
):
    """Get all registered MCP tools"""
    try:
        query: Dict[str, Any] = {}
        if active_only:
            cutoff_time = time.time() - HEARTBEAT_TIMEOUT
            query = {
                "last_heartbeat": {"$gt": cutoff_time},
                "status": "active"
            }
        
        tools = list(collection.find(query, {"_id": 0}))
        return [MCPToolInfo(**tool) for tool in tools]
        
    except Exception as e:
        print(f"❌ Error discovering tools: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to discover tools: {str(e)}")

@app.get("/registry/mcp/discover/{tool_id}", response_model=MCPToolInfo)
async def discover_mcp_tool_by_id(
    tool_id: str,
    collection: Collection[Dict[str, Any]] = Depends(get_mcp_tools_collection)
):
    """Get a specific MCP tool by ID"""
    try:
        tool = collection.find_one({"id": tool_id}, {"_id": 0})
        if not tool:
            raise HTTPException(status_code=404, detail=f"MCP tool with ID {tool_id} not found")
        
        return MCPToolInfo(**tool)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error finding tool {tool_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find tool: {str(e)}")

@app.get("/registry/mcp/discover/capability/{capability_name}", response_model=List[MCPToolInfo])
async def discover_mcp_tools_by_capability(
    capability_name: str,
    active_only: bool = True,
    collection: Collection[Dict[str, Any]] = Depends(get_mcp_tools_collection)
):
    """Get all MCP tools that offer a specific capability"""
    try:
        query: Dict[str, Any] = {"capabilities.name": capability_name}
        
        if active_only:
            cutoff_time = time.time() - HEARTBEAT_TIMEOUT
            query.update({
                "last_heartbeat": {"$gt": cutoff_time},
                "status": "active"
            })
        
        tools = list(collection.find(query, {"_id": 0}))
        return [MCPToolInfo(**tool) for tool in tools]
        
    except Exception as e:
        print(f"❌ Error finding tools with capability {capability_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find tools: {str(e)}")

@app.get("/registry/mcp/discover/tag/{tag}", response_model=List[MCPToolInfo])
async def discover_mcp_tools_by_tag(
    tag: str,
    active_only: bool = True,
    collection: Collection[Dict[str, Any]] = Depends(get_mcp_tools_collection)
):
    """Get all MCP tools that have a specific tag"""
    try:
        query: Dict[str, Any] = {"tags": tag}
        
        if active_only:
            cutoff_time = time.time() - HEARTBEAT_TIMEOUT
            query.update({
                "last_heartbeat": {"$gt": cutoff_time},
                "status": "active"
            })
        
        tools = list(collection.find(query, {"_id": 0}))
        return [MCPToolInfo(**tool) for tool in tools]
        
    except Exception as e:
        print(f"❌ Error finding tools with tag {tag}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find tools: {str(e)}")

@app.post("/registry/mcp/query", response_model=List[MCPToolInfo])
async def query_mcp_tools(
    query: ToolQuery,
    collection: Collection[Dict[str, Any]] = Depends(get_mcp_tools_collection)
):
    """Query MCP tools based on multiple criteria"""
    try:
        mongo_query: Dict[str, Any] = {}
        
        # Filter by capability if specified
        if query.capability:
            mongo_query["capabilities.name"] = query.capability
        
        # Filter by tags if specified
        if query.tags:
            mongo_query["tags"] = {"$in": query.tags}
        
        # Filter by status
        mongo_query["status"] = query.status
        
        # Only active tools with recent heartbeat
        if query.status == "active":
            cutoff_time = time.time() - HEARTBEAT_TIMEOUT
            mongo_query["last_heartbeat"] = {"$gt": cutoff_time}
        
        tools = list(collection.find(mongo_query, {"_id": 0}))
        return [MCPToolInfo(**tool) for tool in tools]
        
    except Exception as e:
        print(f"❌ Error querying tools: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to query tools: {str(e)}")

@app.delete("/registry/mcp/unregister/{tool_id}")
async def unregister_mcp_tool(
    tool_id: str,
    collection: Collection[Dict[str, Any]] = Depends(get_mcp_tools_collection)
):
    """Remove an MCP tool from the registry"""
    try:
        result = collection.delete_one({"id": tool_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"MCP tool with ID {tool_id} not found")
        
        print(f"🗑️ Unregistered MCP tool: {tool_id}")
        return {"status": "ok", "message": f"MCP tool {tool_id} unregistered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error unregistering tool {tool_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unregister tool: {str(e)}")

@app.get("/registry/mcp/stats")
async def get_registry_stats(
    collection: Collection[Dict[str, Any]] = Depends(get_mcp_tools_collection)
):
    """Get statistics about the MCP registry"""
    try:
        total_tools = collection.count_documents({})
        
        cutoff_time = time.time() - HEARTBEAT_TIMEOUT
        active_tools = collection.count_documents({
            "last_heartbeat": {"$gt": cutoff_time},
            "status": "active"
        })
        
        inactive_tools = total_tools - active_tools
        
        # Get capability distribution
        pipeline = [
            {"$unwind": "$capabilities"},
            {"$group": {"_id": "$capabilities.name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        capabilities = list(collection.aggregate(pipeline))
        
        # Get tag distribution
        pipeline = [
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        tags = list(collection.aggregate(pipeline))
        
        return {
            "total_tools": total_tools,
            "active_tools": active_tools,
            "inactive_tools": inactive_tools,
            "top_capabilities": capabilities,
            "top_tags": tags,
            "heartbeat_timeout": HEARTBEAT_TIMEOUT,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error getting registry stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print(f"🌟 Starting {SERVICE_NAME} on port {PORT}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )