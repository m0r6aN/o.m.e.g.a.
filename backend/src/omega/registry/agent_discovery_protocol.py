# ===============================
# Agent Discovery Protocol Models
# ===============================

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AgentCapability(BaseModel):
    """Model for agent capabilities"""
    name: str = Field(..., description="Name of the capability")
    description: str = Field(..., description="Description of what the agent can do")
    examples: List[str] = Field(default_factory=list, description="Example prompts that demonstrate this capability")

class AgentDescription(BaseModel):
    """Model for describing an agent's capabilities and interface"""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Human-readable name of the agent")
    version: str = Field(..., description="Version of the agent")
    description: str = Field(..., description="Description of the agent's purpose and functionality")
    capabilities: List[AgentCapability] = Field(..., description="List of the agent's capabilities")
    mcp_url: str = Field(..., description="URL to the agent's MCP interface")
    api_version: str = Field("1.0", description="Version of the A2A protocol this agent supports")
    schema_url: Optional[str] = Field(None, description="URL to the agent's OpenAPI schema (if available)")
    pricing: Optional[Dict[str, Any]] = Field(None, description="Pricing information for using this agent (if applicable)")
    provider: Optional[str] = Field(None, description="Provider or organization that created this agent")
    rate_limits: Optional[Dict[str, Any]] = Field(None, description="Rate limiting information for this agent")

class AgentRegistryEntry(BaseModel):
    """Model for an agent entry in the registry"""
    agent_description: AgentDescription = Field(..., description="Description of the agent")
    last_heartbeat: float = Field(..., description="Timestamp of the last heartbeat")
    status: str = Field("active", description="Current status of the agent")

class AgentDiscoveryRequest(BaseModel):
    """Model for agent discovery requests"""
    capability_keywords: Optional[List[str]] = Field(None, description="Keywords to search for in capabilities")
    min_version: Optional[str] = Field(None, description="Minimum agent version")
    provider: Optional[str] = Field(None, description="Filter by provider")
    limit: Optional[int] = Field(None, description="Maximum number of results to return")

class AgentDiscoveryResponse(BaseModel):
    """Model for agent discovery responses"""
    agents: List[AgentDescription] = Field(..., description="List of agents matching the query")
    total: int = Field(..., description="Total number of matching agents")