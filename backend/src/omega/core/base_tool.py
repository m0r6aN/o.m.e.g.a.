# /omega/core/base_tool.py
import os
import time
import threading
import requests
import uvicorn
from typing import List, Dict, Any, Callable
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from omega.core.base_entity import OmegaEntity

class ToolCapability(BaseModel):
    """Model for MCP tool capability"""
    name: str
    description: str
    parameters: Dict[str, Any] = {}
    returns: Dict[str, Any] = {}


class BaseTool(OmegaEntity):
    """
    A wrapper class for MCP tools that automatically registers with a central registry
    and sends periodic heartbeats to maintain its registered status.
    """
    def __init__(self, tool_id: str, name: str, description: str, port: int, mcp_port: int, tags: list = None):
        super().__init__(entity_id=tool_id, entity_type="tool", port=port, mcp_port=mcp_port)
        self.name = name
        self.description = description
        self.tags = tags or []
        self.capabilities = []  
        self.tool_id = tool_id      
        self.version = version
        
        # MCP server setup
        self.mcp = MCPServer(
            agent_name=name,
            tools=[]  # We'll add tools programmatically
        )
        
        # FastAPI setup
        self.app = FastAPI()
        self.app.router.lifespan_context = self._lifespan
        
        # Enable CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Registry service configuration
        self.registry_url = os.getenv("REGISTRY_URL", "http://registry:9080")
        self.heartbeat_interval = int(os.getenv("HEARTBEAT_INTERVAL", "30"))  # seconds
        
        # Flag to control the heartbeat thread
        self.running = False
        self.heartbeat_thread = None
        
        # Store capabilities
        self.capabilities = []
        
        # Set up routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up FastAPI routes"""
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy"}
        
        @self.app.get("/capabilities")
        async def get_capabilities():
            """Return this tool's capabilities"""
            return {"capabilities": self.capabilities}
    
    @asynccontextmanager
    async def _lifespan(self, _app):
        """
        Lifespan context manager to handle startup and shutdown events.
        """
        # Start MCP server
        import asyncio
        mcp_task = asyncio.create_task(self._run_mcp_server())
        
        # Register with the registry service
        if self.register_with_registry():
            # Start sending heartbeats
            self.start_heartbeat_thread()
        
        yield
        
        # Stop the heartbeat thread and unregister
        self.stop_heartbeat_thread()
        self.unregister()
        
        # Cancel MCP server task
        mcp_task.cancel()
    
    async def _run_mcp_server(self):
        """Run the MCP server"""
        try:
            mcp_port = int(os.getenv("MCP_PORT", 9000))
            print(f"🔌 Starting MCPServer on port {mcp_port} for {self.name}")
            await self.mcp.serve("0.0.0.0", mcp_port)
        except Exception as e:
            print(f"❌ MCP server failed for {self.name}: {e}")
    
    def add_tool(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Dict[str, Any] = None
    ):
        """
        Add a tool to the MCP server and update capabilities.
        
        Args:
            name: The name of the tool
            description: A description of what the tool does
            func: The function that implements the tool
            parameters: Parameter definitions for the tool
        """
        # Add the tool to the MCP server
        self.mcp.add_tool(
            Tool(
                name=name,
                description=description,
                function=func,
                parameters=parameters or {}
            )
        )
        
        # Update capabilities
        capability = ToolCapability(
            name=name,
            description=description,
            parameters=parameters or {},
            returns={"type": "text"}  # Default return type
        )
        
        self.capabilities.append(capability)
        
        print(f"🔧 Added tool '{name}' to {self.name}")
        
        # If we're already registered, update the registration
        if self.heartbeat_thread:
            self.register_with_registry()
    
    def _get_registration_payload(self):
        """Create the registration payload for the registry service"""
        host = os.getenv("HOST", "localhost")
        port = int(os.getenv("MCP_PORT", "9000"))
        
        return {
            "id": self.id, 
            "name": self.name, 
            "description": self.description,
            "tags": self.tags, 
            "host": self.host, 
            "port": self.port,
            "mcp_port": self.mcp_port, 
            "capabilities": self.capabilities
        }
    
    def register_with_registry(self):
        """Register this tool with the registry service"""
        try:
            payload = self._get_registration_payload()
            response = requests.post(
                f"{self.registry_url}/registry/mcp/register",
                json=payload
            )
            
            if response.status_code == 200:
                print(f"✅ {self.name} registered successfully with registry")
                return True
            else:
                print(f"❌ Failed to register {self.name} with registry: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        
        except Exception as e:
            print(f"❌ Error registering {self.name} with registry: {str(e)}")
            return False
    
    def send_heartbeat(self):
        """Send a heartbeat to the registry service"""
        try:
            response = requests.post(
                f"{self.registry_url}/registry/mcp/heartbeat",
                json={"id": self.tool_id}
            )
            
            if response.status_code != 200:
                print(f"⚠️ Heartbeat failed for {self.name}: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Heartbeat error for {self.name}: {str(e)}")
    
    def heartbeat_loop(self):
        """Background thread function to send periodic heartbeats"""
        while self.running:
            self.send_heartbeat()
            time.sleep(self.heartbeat_interval)
    
    def unregister(self):
        """Unregister this tool from the registry service"""
        try:
            response = requests.delete(
                f"{self.registry_url}/registry/mcp/unregister/{self.tool_id}"
            )
            
            if response.status_code == 200:
                print(f"👋 {self.name} unregistered from registry")
            else:
                print(f"⚠️ Failed to unregister {self.name}: {response.status_code}")
        
        except Exception as e:
            print(f"⚠️ Error unregistering {self.name}: {str(e)}")
    
    def start_heartbeat_thread(self):
        """Start the background thread for sending heartbeats"""
        if not self.heartbeat_thread:
            self.running = True
            self.heartbeat_thread = threading.Thread(
                target=self.heartbeat_loop,
                daemon=True
            )
            self.heartbeat_thread.start()
            print(f"💓 Started heartbeat thread for {self.name}")
    
    def stop_heartbeat_thread(self):
        """Stop the heartbeat thread"""
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=1)
            self.heartbeat_thread = None
            print(f"🛑 Stopped heartbeat thread for {self.name}")
    
    def run(self):
        """Run the FastAPI server"""
        try:
            port = int(os.getenv("PORT", "8000"))
            uvicorn.run(self.app, host="0.0.0.0", port=port)
        finally:
            # Ensure we stop the heartbeat thread and unregister
            self.stop_heartbeat_thread()
            self.unregister()