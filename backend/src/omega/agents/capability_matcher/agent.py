#!/usr/bin/env python3
"""
OMEGA Capability Matcher Agent - Modern Self-Contained Version
Intelligently matches user requests to the best available agents based on capabilities.
"""

import os
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

# ============================================================================
# CONFIGURATION
# ============================================================================

AGENT_ID = "capability_matcher_001"
AGENT_NAME = "Capability Matcher Agent"
AGENT_DESCRIPTION = "Intelligent capability matching agent that finds the best agents for specific tasks"
AGENT_SKILLS = [
    "capability_matching",
    "agent_discovery",
    "skill_analysis", 
    "task_routing",
    "intelligent_scoring",
    "agent_recommendation",
    "workflow_routing"
]
AGENT_TAGS = ["matching", "discovery", "routing", "intelligence", "coordination"]

PORT = int(os.getenv("PORT", 9008))
MCP_PORT = int(os.getenv("MCP_PORT", 9009))
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://agent_registry:9401")
MCP_REGISTRY_URL = os.getenv("MCP_REGISTRY_URL", "http://mcp_registry:9402")

print(f"🚀 {AGENT_NAME} Configuration:")
print(f"   Agent ID: {AGENT_ID}")
print(f"   Port: {PORT}")
print(f"   Registry: {REGISTRY_URL}")
print(f"   MCP Registry: {MCP_REGISTRY_URL}")

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

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

class CapabilityRequest(BaseModel):
    query: str
    requirements: List[str] = []
    min_score: float = 0.5
    max_results: int = 5

class AgentMatch(BaseModel):
    agent_id: str
    name: str
    score: float
    matching_skills: List[str]
    matching_tags: List[str]
    description: str
    confidence: str  # high, medium, low
    endpoints: Dict[str, str]

class MatchResponse(BaseModel):
    matches: List[AgentMatch]
    query: str
    total_found: int
    best_match: Optional[AgentMatch] = None
    timestamp: str
    success: bool = True

class RouteRequest(BaseModel):
    task_description: str
    required_capabilities: List[str] = []
    context: Optional[str] = None

class RouteResponse(BaseModel):
    recommended_agent: Optional[AgentMatch] = None
    alternative_agents: List[AgentMatch] = []
    routing_confidence: float
    reasoning: str
    timestamp: str
    success: bool = True

# ============================================================================
# LIFESPAN HANDLERS
# ============================================================================

# Global variables
registered = False
heartbeat_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern FastAPI lifespan handler."""
    global heartbeat_task
    
    # Startup
    print(f"🚀 Starting {AGENT_NAME} on port {PORT}")
    print("⏳ Waiting for registry to be ready...")
    await asyncio.sleep(15)
    
    print("🔄 Attempting registry registration...")
    await register_with_registry()
    
    heartbeat_task = asyncio.create_task(send_heartbeat())
    print("💓 Heartbeat task started")
    print(f"✅ {AGENT_NAME} is fully operational!")
    
    yield  # App runs here
    
    # Shutdown
    print(f"👋 {AGENT_NAME} shutting down...")
    if heartbeat_task:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
    print(f"✅ {AGENT_NAME} shutdown complete")

app = FastAPI(
    title=f"OMEGA {AGENT_NAME}",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# REGISTRY INTEGRATION
# ============================================================================

async def register_with_registry():
    """Register this agent with the OMEGA registry."""
    global registered
    
    agent_info = AgentInfo(
        id=AGENT_ID,
        name=AGENT_NAME,
        description=AGENT_DESCRIPTION,
        skills=AGENT_SKILLS,
        tags=AGENT_TAGS,
        host="capability_matcher",  # Docker service name
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
                print(f"✅ Successfully registered {AGENT_NAME}")
                registered = True
                return True
            else:
                print(f"❌ Registration failed: {response.status_code}")
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
                        print(f"💓 Capability Matcher heartbeat sent")
                    else:
                        print(f"⚠️ Heartbeat failed: {response.status_code}")
                        
            except Exception as e:
                print(f"❌ Heartbeat error: {e}")
        
        await asyncio.sleep(30)

# ============================================================================
# AGENT DISCOVERY & ANALYSIS
# ============================================================================

async def get_all_agents():
    """Fetch all available agents from the registry."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{REGISTRY_URL}/agents", timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("agents", [])
            else:
                print(f"⚠️ Failed to fetch agents: {response.status_code}")
                return []
                
    except Exception as e:
        print(f"❌ Error fetching agents: {e}")
        return []

def calculate_capability_score(agent: dict, query: str, requirements: List[str]) -> tuple[float, List[str], List[str]]:
    """
    Calculate how well an agent matches the capability requirements.
    Returns (score, matching_skills, matching_tags)
    """
    score = 0.0
    matching_skills = []
    matching_tags = []
    
    # Get agent data
    skills = agent.get("skills", [])
    tags = agent.get("tags", [])
    description = agent.get("description", "").lower()
    name = agent.get("name", "").lower()
    
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    # Score based on exact skill matches (highest weight)
    for skill in skills:
        skill_lower = skill.lower()
        skill_words = set(skill_lower.replace("_", " ").split())
        
        if skill_lower in query_lower:
            score += 1.0  # Exact skill match
            matching_skills.append(skill)
        elif query_words.intersection(skill_words):
            score += 0.7  # Partial skill match
            matching_skills.append(skill)
    
    # Score based on tag matches (medium weight)
    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower in query_lower:
            score += 0.6  # Direct tag match
            matching_tags.append(tag)
        elif any(word in tag_lower for word in query_words):
            score += 0.4  # Partial tag match
            matching_tags.append(tag)
    
    # Score based on description and name matches (lower weight)
    description_matches = sum(1 for word in query_words if word in description)
    name_matches = sum(1 for word in query_words if word in name)
    
    score += description_matches * 0.3
    score += name_matches * 0.5
    
    # Score based on specific requirements
    for req in requirements:
        req_lower = req.lower()
        req_words = set(req_lower.split())
        
        # Check skills
        for skill in skills:
            skill_lower = skill.lower()
            if req_lower in skill_lower or skill_lower in req_lower:
                score += 0.8
                if skill not in matching_skills:
                    matching_skills.append(skill)
        
        # Check tags
        for tag in tags:
            tag_lower = tag.lower()
            if req_lower in tag_lower or tag_lower in req_lower:
                score += 0.6
                if tag not in matching_tags:
                    matching_tags.append(tag)
    
    # Normalize score based on query complexity
    max_possible_score = len(query_words) + len(requirements) + 1
    normalized_score = min(score / max_possible_score, 1.0)
    
    return normalized_score, matching_skills, matching_tags

def determine_confidence(score: float) -> str:
    """Determine confidence level based on score."""
    if score >= 0.8:
        return "high"
    elif score >= 0.5:
        return "medium"
    else:
        return "low"

# ============================================================================
# CORE MATCHING FUNCTIONS
# ============================================================================

async def match_capabilities(query: str, requirements: List[str] = None, 
                           min_score: float = 0.5, max_results: int = 5) -> List[AgentMatch]:
    """Find the best agents for a given capability request."""
    print(f"🔍 Matching capabilities for: '{query}'")
    
    requirements = requirements or []
    agents = await get_all_agents()
    
    if not agents:
        print("⚠️ No agents available for matching")
        return []
    
    # Score and filter agents
    scored_agents = []
    for agent in agents:
        # Skip self
        if agent.get("id") == AGENT_ID:
            continue
            
        score, matching_skills, matching_tags = calculate_capability_score(
            agent, query, requirements
        )
        
        if score >= min_score:
            confidence = determine_confidence(score)
            
            scored_agents.append(AgentMatch(
                agent_id=agent.get("id", ""),
                name=agent.get("name", "Unknown"),
                score=round(score, 3),
                matching_skills=matching_skills,
                matching_tags=matching_tags,
                description=agent.get("description", ""),
                confidence=confidence,
                endpoints={
                    "api": f"http://{agent.get('host', 'localhost')}:{agent.get('port', 8000)}",
                    "mcp": f"http://{agent.get('host', 'localhost')}:{agent.get('mcp_port', 9000)}" 
                        if agent.get('mcp_port') else None
                }
            ))
    
    # Sort by score (highest first) and limit results
    scored_agents.sort(key=lambda x: x.score, reverse=True)
    return scored_agents[:max_results]

async def route_task(task_description: str, required_capabilities: List[str] = None, 
                    context: str = None) -> tuple[Optional[AgentMatch], List[AgentMatch], str]:
    """Route a task to the best agent with reasoning."""
    
    # Combine task description and context for matching
    full_query = task_description
    if context:
        full_query += f" {context}"
    
    matches = await match_capabilities(
        query=full_query,
        requirements=required_capabilities or [],
        min_score=0.3,
        max_results=10
    )
    
    if not matches:
        return None, [], "No suitable agents found for this task"
    
    best_match = matches[0]
    alternatives = matches[1:5]  # Top 4 alternatives
    
    # Generate reasoning
    reasoning = f"Selected '{best_match.name}' (score: {best_match.score}) because it matches "
    
    if best_match.matching_skills:
        reasoning += f"skills: {', '.join(best_match.matching_skills[:3])}"
    
    if best_match.matching_tags:
        if best_match.matching_skills:
            reasoning += " and "
        reasoning += f"tags: {', '.join(best_match.matching_tags[:3])}"
    
    reasoning += f". Confidence: {best_match.confidence}"
    
    return best_match, alternatives, reasoning

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_id": AGENT_ID,
        "name": AGENT_NAME,
        "registered": registered,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/info")
async def agent_info():
    """Get agent information."""
    return {
        "id": AGENT_ID,
        "name": AGENT_NAME,
        "description": AGENT_DESCRIPTION,
        "version": "1.0.0",
        "skills": AGENT_SKILLS,
        "tags": AGENT_TAGS,
        "status": "active",
        "registered": registered,
        "ports": {"api": PORT, "mcp": MCP_PORT}
    }

@app.post("/match", response_model=MatchResponse)
async def match_capabilities_endpoint(request: CapabilityRequest):
    """Find the best agents for a given capability request."""
    print(f"🔍 Capability matching request: '{request.query}'")
    
    try:
        matches = await match_capabilities(
            query=request.query,
            requirements=request.requirements,
            min_score=request.min_score,
            max_results=request.max_results
        )
        
        best_match = matches[0] if matches else None
        
        return MatchResponse(
            matches=matches,
            query=request.query,
            total_found=len(matches),
            best_match=best_match,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=True
        )
        
    except Exception as e:
        print(f"❌ Capability matching error: {e}")
        return MatchResponse(
            matches=[],
            query=request.query,
            total_found=0,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=False
        )

@app.post("/route", response_model=RouteResponse)
async def route_task_endpoint(request: RouteRequest):
    """Route a task to the best available agent."""
    print(f"🎯 Task routing request: '{request.task_description[:100]}...'")
    
    try:
        recommended, alternatives, reasoning = await route_task(
            task_description=request.task_description,
            required_capabilities=request.required_capabilities,
            context=request.context
        )
        
        routing_confidence = recommended.score if recommended else 0.0
        
        return RouteResponse(
            recommended_agent=recommended,
            alternative_agents=alternatives,
            routing_confidence=routing_confidence,
            reasoning=reasoning,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=True
        )
        
    except Exception as e:
        print(f"❌ Task routing error: {e}")
        return RouteResponse(
            routing_confidence=0.0,
            reasoning=f"Error occurred during routing: {str(e)}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=False
        )

@app.get("/agents")
async def list_all_agents():
    """List all available agents in the registry."""
    agents = await get_all_agents()
    return {
        "agents": agents,
        "count": len(agents),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/ping")
async def ping():
    """Simple ping endpoint."""
    return {
        "message": "pong",
        "agent_id": AGENT_ID,
        "service": "capability_matcher",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    print(f"🌟 OMEGA {AGENT_NAME} starting on port {PORT}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )