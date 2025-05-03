# omega/services/mcp_registry/service.py
# MCP Tool Registry

# Enhanced models to support MCP tool details
class ToolCapability(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any] = {}
    returns: Dict[str, Any] = {}

class MCPToolInfo(BaseModel):
    id: str
    name: str
    description: str
    version: str
    capabilities: List[ToolCapability]
    mcp_endpoint: str
    host: str
    port: int
    tags: List[str] = []
    last_heartbeat: float = Field(default_factory=time.time)

class MCPToolRegistration(BaseModel):
    id: str
    name: str
    description: str
    version: str
    capabilities: List[ToolCapability]
    host: str
    port: int
    tags: List[str] = []

class MCPToolHeartbeat(BaseModel):
    id: str

def setup_mcp_tool_routes(app: FastAPI):
    """Add MCP tool registry routes to the existing FastAPI app"""
    
    # Dependency to get the MCP tools collection
    def get_mcp_tools_collection() -> Collection:
        return app.database.mcp_tools
    
@app.post("/registry/mcp/register", response_model=MCPToolInfo)
async def register_mcp_tool(
    tool: MCPToolRegistration, 
    collection: Collection = Depends(get_mcp_tools_collection)
):
    """Register a new MCP tool or update an existing one"""
    # Set the current time as last heartbeat
    tool_dict = tool.model_dump()
    tool_dict["last_heartbeat"] = time.time()
    
    # Construct the MCP endpoint URL
    tool_dict["mcp_endpoint"] = f"http://{tool.host}:{tool.port}/mcp"
    
    # Check if tool already exists
    existing = collection.find_one({"id": tool.id})
    
    if existing:
        # Update existing tool
        collection.update_one(
            {"id": tool.id},
            {"$set": tool_dict}
        )
    else:
        # Insert new tool
        collection.insert_one(tool_dict)
    
    return MCPToolInfo(**tool_dict)

@app.post("/registry/mcp/heartbeat")
async def update_mcp_tool_heartbeat(
    request: MCPToolHeartbeat,
    collection: Collection = Depends(get_mcp_tools_collection)
):
    """Update the last heartbeat time for an MCP tool"""
    result = collection.update_one(
        {"id": request.id},
        {"$set": {"last_heartbeat": time.time()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"MCP tool with ID {request.id} not found")
    
    return {"status": "ok"}


@app.get("/registry/mcp/discover", response_model=List[MCPToolInfo])
async def discover_all_mcp_tools(
    collection: Collection = Depends(get_mcp_tools_collection)
):
    """Get all registered MCP tools"""
    # Find all tools with heartbeat in the last 60 seconds
    cutoff_time = time.time() - 60
    tools = list(collection.find({"last_heartbeat": {"$gt": cutoff_time}}))
    return tools


@app.get("/registry/mcp/discover/{tool_id}", response_model=MCPToolInfo)
async def discover_mcp_tool_by_id(
    tool_id: str,
    collection: Collection = Depends(get_mcp_tools_collection)
):
    """Get a specific MCP tool by ID"""
    tool = collection.find_one({"id": tool_id})
    if not tool:
        raise HTTPException(status_code=404, detail=f"MCP tool with ID {tool_id} not found")
    return tool


@app.get("/registry/mcp/discover/capability/{capability_name}", response_model=List[MCPToolInfo])
async def discover_mcp_tools_by_capability(
    capability_name: str,
    collection: Collection = Depends(get_mcp_tools_collection)
):
    """Get all MCP tools that offer a specific capability"""
    # Find all tools with the specified capability and recent heartbeat
    cutoff_time = time.time() - 60
    pipeline = [
        {"$match": {"last_heartbeat": {"$gt": cutoff_time}}},
        {"$match": {"capabilities.name": capability_name}}
    ]
    
    tools = list(collection.aggregate(pipeline))
    return tools


@app.delete("/registry/mcp/unregister/{tool_id}")
async def unregister_mcp_tool(
    tool_id: str,
    collection: Collection = Depends(get_mcp_tools_collection)
):
    """Remove an MCP tool from the registry"""
    result = collection.delete_one({"id": tool_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"MCP tool with ID {tool_id} not found")
    
    return {"status": "ok", "message": f"MCP tool {tool_id} unregistered successfully"}

# External tool registration endpoints
@app.post("/registry/mcp/register/external")
async def register_external_tool(tool: ToolInfo):
    """
    Register an external MCP tool with the registry.
    Unlike regular tool registration, this doesn't require heartbeats.
    """
    tool.last_heartbeat = float('inf')  # Set to infinity to prevent expiry
    self.mcp_tools[tool.id] = tool
    print(f"🔌 Registered external MCP tool: {tool.id}")
    return {"status": "registered", "tool_id": tool.id}

@app.get("/registry/mcp/list/external")
async def list_external_tools():
    """Get all registered external MCP tools"""
    external_tools = [tool for tool in self.mcp_tools.values() 
                    if tool.last_heartbeat == float('inf')]
    return external_tools

@app.put("/registry/mcp/update/{tool_id}")
async def update_mcp_tool(tool_id: str, tool: ToolInfo):
    """Update an existing MCP tool configuration"""
    if tool_id in self.mcp_tools:
        # Preserve the heartbeat status
        heartbeat = self.mcp_tools[tool_id].last_heartbeat
        tool.last_heartbeat = heartbeat
        self.mcp_tools[tool_id] = tool
        print(f"✏️ Updated MCP tool: {tool_id}")
        return {"status": "updated", "tool_id": tool_id}
    else:
        raise HTTPException(status_code=404, detail=f"Tool {tool_id} not found")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# This function should be called inside the app startup in the registry service
def setup_mcp_registry(app: FastAPI):
    """Set up the MCP registry"""
    # Create indexes if they don't exist
    app.database.mcp_tools.create_index("id", unique=True)
    app.database.mcp_tools.create_index("capabilities.name")
    
    # Add the MCP tool routes
    setup_mcp_tool_routes(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 9401)))

