# omega/core/agent_discovery.py

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
import time

class AgentCapability(BaseModel):
    """Model for agent capabilities with examples"""
    name: str = Field(..., description="Name of the capability")
    description: str = Field(..., description="Description of what the agent can do")
    examples: List[str] = Field(default_factory=list, description="Example prompts that demonstrate this capability")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parameters this capability accepts")
    tags: List[str] = Field(default_factory=list, description="Tags related to this capability")

class CapabilityRegistry:
    """
    Registry for tracking agent capabilities with sophisticated matching
    """
    
    def __init__(self, db_client=None):
        self.db_client = db_client
        # Fallback to in-memory storage if no DB client
        self.in_memory_registry = {}
    
    async def register_agent_capabilities(self, agent_id: str, capabilities: List[AgentCapability]):
        """Register an agent's capabilities in the registry"""
        if self.db_client:
            # Store in database
            await self.db_client.capabilities.update_one(
                {"agent_id": agent_id},
                {"$set": {
                    "agent_id": agent_id,
                    "capabilities": [cap.model_dump() for cap in capabilities],
                    "last_updated": time.time()
                }},
                upsert=True
            )
        else:
            # Store in memory
            self.in_memory_registry[agent_id] = {
                "capabilities": capabilities,
                "last_updated": time.time()
            }
        
        return {"status": "registered", "agent_id": agent_id, "capability_count": len(capabilities)}
    
    async def get_agent_capabilities(self, agent_id: str) -> List[AgentCapability]:
        """Get an agent's registered capabilities"""
        if self.db_client:
            # Retrieve from database
            agent_data = await self.db_client.capabilities.find_one({"agent_id": agent_id})
            if agent_data:
                return [AgentCapability(**cap) for cap in agent_data.get("capabilities", [])]
            return []
        else:
            # Retrieve from memory
            agent_data = self.in_memory_registry.get(agent_id, {})
            return agent_data.get("capabilities", [])
    
    async def match_capability(self, capability_query: Union[str, Dict], min_score: float = 0.5) -> List[Dict[str, Any]]:
        """
        Find agents that match a capability query with sophisticated scoring
        
        Args:
            capability_query: Either a capability name string or a dict with detailed query parameters
            min_score: Minimum score threshold (0.0 to 1.0)
            
        Returns:
            List of matching agents with scores, sorted by score (highest first)
        """
        # Handle string or dict query
        query_text = capability_query if isinstance(capability_query, str) else capability_query.get("text", "")
        query_tags = capability_query.get("tags", []) if isinstance(capability_query, dict) else []
        
        # Get all agents
        all_agents = []
        if self.db_client:
            # Get from database
            cursor = self.db_client.capabilities.find()
            async for agent in cursor:
                all_agents.append(agent)
        else:
            # Get from memory
            for agent_id, data in self.in_memory_registry.items():
                all_agents.append({"agent_id": agent_id, **data})
        
        # Score each agent
        scored_agents = []
        for agent in all_agents:
            agent_id = agent.get("agent_id")
            capabilities = [
                AgentCapability(**cap) if isinstance(cap, dict) else cap 
                for cap in agent.get("capabilities", [])
            ]
            
            # Find best matching capability for this agent
            best_score = 0.0
            best_capability = None
            
            for capability in capabilities:
                score = self._score_capability_match(capability, query_text, query_tags)
                if score > best_score:
                    best_score = score
                    best_capability = capability
            
            # Add agent if it meets threshold
            if best_score >= min_score:
                scored_agents.append({
                    "agent_id": agent_id,
                    "score": best_score,
                    "matched_capability": best_capability.model_dump() if best_capability else None
                })
        
        # Sort by score (highest first)
        scored_agents.sort(key=lambda a: a["score"], reverse=True)
        return scored_agents
    
    def _score_capability_match(self, capability: AgentCapability, query_text: str, query_tags: List[str] = None) -> float:
        """
        Score how well a capability matches a query (0.0 to 1.0)
        
        This implements a sophisticated matching algorithm that considers:
        - Exact name matches
        - Partial name matches
        - Description content
        - Tag overlap
        - Example prompt similarity
        """
        score = 0.0
        query_text = query_text.lower().strip()
        query_tags = [tag.lower() for tag in (query_tags or [])]
        
        # Exact name match (highest priority)
        if capability.name.lower() == query_text:
            return 1.0
        
        # Partial name match
        if query_text in capability.name.lower():
            score = max(score, 0.8)
        
        # Description match
        if query_text in capability.description.lower():
            score = max(score, 0.6)
        
        # Example similarity
        for example in capability.examples:
            if query_text in example.lower():
                score = max(score, 0.7)
        
        # Tag matching
        if query_tags and capability.tags:
            matching_tags = set(query_tags) & set(tag.lower() for tag in capability.tags)
            if matching_tags:
                tag_score = 0.5 + (len(matching_tags) / len(query_tags)) * 0.4
                score = max(score, tag_score)
        
        return score