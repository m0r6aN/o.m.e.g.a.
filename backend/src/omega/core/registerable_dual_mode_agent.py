# omega/agents/registerable_dual_mode_agent.py - updated version

import os
import asyncio
import time
import threading
import uuid
import json
import aiohttp
from typing import List, Dict, Any, Optional, Literal

from dual_mode_agent import DualModeAgent  # This extends A2AServer
from omega.core.agent_discovery import AgentCapability

class RegisterableDualModeAgent(DualModeAgent):
    """
    Extended DualModeAgent that automatically registers with a central registry service,
    sends periodic heartbeats to maintain its registered status, and provides
    helper methods for discovering and using MCP tools.
    
    Includes support for sophisticated capability description and discovery.
    """
    
    def __init__(
        self, 
        agent_id: str, 
        tool_name: str, 
        description: str = "A dual-mode agent",
        version: str = "1.0.0",
        capabilities: List[AgentCapability] = None,  # Detailed capabilities
        skills: List[str] = None,  # For backward compatibility
        agent_type: Literal["agent", "tool", "dual"] = "dual",
        registry_url: Optional[str] = None,
        tags: List[str] = None
    ):
        # Store detailed capabilities
        self.detailed_capabilities = capabilities or []
        
        # Transform capabilities to skills list for backward compatibility
        if skills is None:
            skills = [cap.name for cap in self.detailed_capabilities]
        
        super().__init__(
            agent_id=agent_id,
            tool_name=tool_name,
            description=description,
            version=version,
            skills=skills
        )
        
        self.agent_type = "agent" if agent_type == "agent" else "tool" if agent_type == "tool" else "agent"
        self.protocol = "dual"  # This agent supports both A2A and MCP
        self.tags = tags or []
        
        # Registry service configuration
        self.registry_url = registry_url or os.getenv("REGISTRY_URL", "http://registry:9401")
        self.heartbeat_interval = int(os.getenv("HEARTBEAT_INTERVAL", "30"))  # seconds
        
        # Flag to control the heartbeat thread
        self.running = False
        self.heartbeat_thread = None
    
    def _get_registration_payload(self):
        """Enhanced registration payload with detailed capabilities"""
        host = os.getenv("HOST", "localhost")
        port = os.getenv("PORT", "8000")
        base_url = f"http://{host}:{port}"
        
        # Start with basic payload
        payload = {
            "id": self.agent_id,
            "name": self.agent_id,
            "type": self.agent_type,
            "protocol": self.protocol,
            "capabilities": self.skills_list,
            "endpoints": {
                "base_url": base_url,
                "a2a_card": "/.well-known/a2a/agent-card",
                "mcp_endpoint": f"/tools/{self.tool_name}"
            },
            "metadata": {
                "description": self.description,
                "version": self.version,
                "tags": self.tags
            }
        }
        
        # Add detailed capability information
        if self.detailed_capabilities:
            payload["detailed_capabilities"] = [
                cap.model_dump() for cap in self.detailed_capabilities
            ]
        
        return payload
    
    def register_with_registry(self):
        """Register this agent with the registry service"""
        try:
            payload = self._get_registration_payload()
            response = requests.post(
                f"{self.registry_url}/registry/register",
                json=payload
            )
            
            if response.status_code == 200:
                print(f"✅ {self.agent_id} registered successfully with registry")
                
                # Also register detailed capabilities if available
                if self.detailed_capabilities:
                    asyncio.create_task(self.register_capabilities())
                
                return True
            else:
                print(f"❌ Failed to register {self.agent_id} with registry: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        
        except Exception as e:
            print(f"❌ Error registering {self.agent_id} with registry: {str(e)}")
            return False
    
    async def register_capabilities(self):
        """Register detailed capabilities with the capability registry"""
        if not self.detailed_capabilities:
            return {"status": "skipped", "reason": "No detailed capabilities defined"}
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "agent_id": self.agent_id,
                    "capabilities": [cap.model_dump() for cap in self.detailed_capabilities]
                }
                
                async with session.post(
                    f"{self.registry_url}/registry/capabilities/register",
                    json=payload
                ) as response:
                    if response.status == 200:
                        print(f"✅ {self.agent_id} capabilities registered successfully")
                        return await response.json()
                    else:
                        print(f"❌ Failed to register capabilities: {response.status}")
                        return {"error": f"Failed with status {response.status}"}
        
        except Exception as e:
            print(f"❌ Error registering capabilities: {str(e)}")
            return {"error": str(e)}
    
    async def discover_agents_by_capability(self, capability_query, min_score: float = 0.5):
        """
        Discover agents that can fulfill a capability with minimum match score
        
        Args:
            capability_query: String capability name or dict with query parameters
            min_score: Minimum score threshold (0.0 to 1.0)
            
        Returns:
            List of matching agents with scores
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Prepare query
                if isinstance(capability_query, str):
                    query = {"text": capability_query}
                else:
                    query = capability_query
                
                query["min_score"] = min_score
                
                # Make request
                async with session.post(
                    f"{self.registry_url}/registry/capabilities/match",
                    json=query
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"❌ Failed to discover agents: {response.status}")
                        return []
        except Exception as e:
            print(f"❌ Error discovering agents: {str(e)}")
            return []
    
    async def find_and_use_capability(self, capability_name: str, **params):
        """
        Find the best agent for a capability and use it
        
        Args:
            capability_name: The capability to use
            **params: Parameters to pass to the capability
            
        Returns:
            Result from the capability
        """
        # Find agents with this capability
        matches = await self.discover_agents_by_capability(capability_name, min_score=0.7)
        
        if not matches:
            return {"error": f"No agents found with capability '{capability_name}'"}
        
        # Use the best agent
        best_agent = matches[0]
        agent_id = best_agent["agent_id"]
        
        # Get agent info to find its endpoints
        agent_info = await self.discover_agent_by_id(agent_id)
        
        if not agent_info:
            return {"error": f"Could not find endpoint information for agent {agent_id}"}
        
        # Call the agent with the capability
        try:
            async with aiohttp.ClientSession() as session:
                # Try MCP endpoint first
                if "mcp_endpoint" in agent_info.get("endpoints", {}):
                    mcp_url = agent_info["endpoints"]["mcp_endpoint"]
                    payload = {
                        "name": capability_name,
                        "parameters": params
                    }
                    
                    async with session.post(mcp_url, json=payload) as response:
                        if response.status == 200:
                            return await response.json()
                
                # Fall back to A2A endpoint
                if "a2a_card" in agent_info.get("endpoints", {}):
                    # Get A2A agent card first
                    base_url = agent_info["endpoints"]["base_url"]
                    card_url = f"{base_url}{agent_info['endpoints']['a2a_card']}"
                    
                    async with session.get(card_url) as response:
                        if response.status == 200:
                            agent_card = await response.json()
                            
                            # Use A2A task send endpoint
                            if "tasks_send" in agent_card.get("endpoints", {}):
                                task_url = f"{base_url}{agent_card['endpoints']['tasks_send']}"
                                
                                # Create A2A message
                                payload = {
                                    "task_id": str(uuid.uuid4()),
                                    "message": {
                                        "role": "user",
                                        "content": {
                                            "type": "text",
                                            "text": f"Use capability '{capability_name}' with parameters: {json.dumps(params)}"
                                        }
                                    }
                                }
                                
                                async with session.post(task_url, json=payload) as response:
                                    if response.status == 200:
                                        return await response.json()
                
                return {"error": f"Could not find a way to call agent {agent_id}"}
                
        except Exception as e:
            print(f"❌ Error calling agent capability: {str(e)}")
            return {"error": f"Exception: {str(e)}"}
    
    # Original methods from RegisterableDualModeAgent follow here...
    def send_heartbeat(self):
        """Send a heartbeat to the registry service"""
        try:
            response = requests.post(
                f"{self.registry_url}/registry/heartbeat",
                json={"id": self.agent_id}
            )
            
            if response.status_code != 200:
                print(f"⚠️ Heartbeat failed for {self.agent_id}: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Heartbeat error for {self.agent_id}: {str(e)}")
    
    def heartbeat_loop(self):
        """Background thread function to send periodic heartbeats"""
        while self.running:
            self.send_heartbeat()
            time.sleep(self.heartbeat_interval)
    
    def unregister(self):
        """Unregister this agent from the registry service"""
        try:
            response = requests.delete(
                f"{self.registry_url}/registry/unregister/{self.agent_id}"
            )
            
            if response.status_code == 200:
                print(f"👋 {self.agent_id} unregistered from registry")
            else:
                print(f"⚠️ Failed to unregister {self.agent_id}: {response.status_code}")
        
        except Exception as e:
            print(f"⚠️ Error unregistering {self.agent_id}: {str(e)}")
    
    def start_heartbeat_thread(self):
        """Start the background thread for sending heartbeats"""
        if not self.heartbeat_thread:
            self.running = True
            self.heartbeat_thread = threading.Thread(
                target=self.heartbeat_loop,
                daemon=True
            )
            self.heartbeat_thread.start()
            print(f"💓 Started heartbeat thread for {self.agent_id}")
    
    def stop_heartbeat_thread(self):
        """Stop the heartbeat thread"""
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=1)
            self.heartbeat_thread = None
            print(f"🛑 Stopped heartbeat thread for {self.agent_id}")

    async def discover_mcp_tools_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """
        Discover MCP tools by capability
        
        Args:
            capability: The capability to search for
            
        Returns:
            List of tools with the specified capability
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.registry_url}/registry/mcp/discover/capability/{capability}") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"❌ Failed to discover MCP tools with capability {capability}: {response.status}")
                        return []
        except Exception as e:
            print(f"❌ Error discovering MCP tools by capability: {str(e)}")
            return []
    
    async def discover_mcp_tools_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Discover MCP tools by tag
        
        Args:
            tag: The tag to search for
            
        Returns:
            List of tools with the specified tag
        """
        try:
            # Get all tools and filter by tag
            all_tools = await self.discover_mcp_tools()
            return [tool for tool in all_tools if tag in tool.get("tags", [])]
        except Exception as e:
            print(f"❌ Error discovering MCP tools by tag: {str(e)}")
            return []
    
    async def call_mcp_tool(self, tool_endpoint: str, tool_name: str, **params):
        """
        Call an MCP tool with the given parameters
        
        Args:
            tool_endpoint: The MCP endpoint URL of the tool
            tool_name: The name of the tool function to call
            **params: Parameters to pass to the tool
            
        Returns:
            The tool's response
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "name": tool_name,
                    "parameters": params
                }
                
                async with session.post(f"{tool_endpoint}", json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"❌ Tool call failed: {response.status}")
                        error_text = await response.text()
                        print(f"Error: {error_text}")
                        return {"error": f"Tool call failed: {response.status}"}
        except Exception as e:
            print(f"❌ Error calling tool: {str(e)}")
            return {"error": f"Exception: {str(e)}"}
    
    async def find_and_call_tool(self, tool_id: str, tool_name: str, **params):
        """
        Find a tool by ID and call one of its functions
        
        Args:
            tool_id: The ID of the tool to use
            tool_name: The name of the tool function to call
            **params: Parameters to pass to the tool
            
        Returns:
            The tool's response or error message
        """
        # Find the tool
        tool = await self.discover_mcp_tool_by_id(tool_id)
        
        if not tool:
            return {"error": f"Tool {tool_id} not found"}
        
        # Get the MCP endpoint
        mcp_endpoint = tool.get("mcp_endpoint")
        
        if not mcp_endpoint:
            return {"error": f"Tool {tool_id} has no MCP endpoint"}
        
        # Call the tool
        return await self.call_mcp_tool(mcp_endpoint, tool_name, **params)
    
    async def find_tool_by_capability_and_call(self, capability: str, **params):
        """
        Find tools with a specific capability and call the first one
        
        Args:
            capability: The capability to search for
            **params: Parameters to pass to the tool
            
        Returns:
            The tool's response or error message
        """
        # Find tools with the capability
        tools = await self.discover_mcp_tools_by_capability(capability)
        
        if not tools:
            return {"error": f"No tools found with capability {capability}"}
        
        # Use the first tool
        tool = tools[0]
        mcp_endpoint = tool.get("mcp_endpoint")
        
        if not mcp_endpoint:
            return {"error": f"Tool {tool['id']} has no MCP endpoint"}
        
        # Call the tool
        return await self.call_mcp_tool(mcp_endpoint, capability, **params)
    
    @asynccontextmanager
    async def _lifespan(self, _app):
        """
        Extend the base lifespan context manager to register with the registry 
        and start the heartbeat thread.
        """
        # First call the parent's lifespan context manager
        async with super()._lifespan(_app):
            # Register with the registry service
            if self.register_with_registry():
                # Start sending heartbeats
                self.start_heartbeat_thread()
            
            yield
            
            # Stop the heartbeat thread and unregister
            self.stop_heartbeat_thread()
            self.unregister()
    
    def run(self):
        """Override the run method to ensure clean shutdown"""
        try:
            super().run()
        finally:
            # Ensure we stop the heartbeat thread and unregister
            self.stop_heartbeat_thread()
            self.unregister()