#!/usr/bin/env python3
"""
OMEGA Prompt Optimizer Agent - Modern Self-Contained Version
Optimizes user prompts for clarity, specificity, and AI effectiveness.
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
from openai import OpenAI

# ============================================================================
# CONFIGURATION
# ============================================================================

AGENT_ID = "prompt_optimizer_001"
AGENT_NAME = "Prompt Optimizer Agent"
AGENT_DESCRIPTION = "AI prompt optimization specialist that enhances user requests for maximum clarity and effectiveness"
AGENT_SKILLS = [
    "prompt_optimization",
    "query_enhancement",
    "clarity_improvement",
    "ai_prompt_engineering",
    "request_structuring",
    "ambiguity_resolution"
]
AGENT_TAGS = ["optimization", "prompts", "ai", "enhancement", "clarity"]

PORT = int(os.getenv("PORT", 9006))
MCP_PORT = int(os.getenv("MCP_PORT", 9007))
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://agent_registry:9401")

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print(f"🚀 {AGENT_NAME} Configuration:")
print(f"   Agent ID: {AGENT_ID}")
print(f"   Port: {PORT}")
print(f"   Registry: {REGISTRY_URL}")
print(f"   OpenAI: {'✅' if OPENAI_API_KEY else '❌'}")

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

class OptimizeRequest(BaseModel):
    original_prompt: str
    target_ai: str = "general"  # general, coding, creative, analytical
    optimization_level: str = "balanced"  # light, balanced, heavy
    context: Optional[str] = None

class OptimizeResponse(BaseModel):
    original_prompt: str
    optimized_prompt: str
    improvement_score: float
    changes_made: List[str]
    suggestions: List[str]
    agent_id: str
    timestamp: str
    success: bool = True
    error: Optional[str] = None

class AnalyzeRequest(BaseModel):
    prompt: str

class AnalyzeResponse(BaseModel):
    clarity_score: float
    specificity_score: float
    completeness_score: float
    overall_score: float
    issues: List[str]
    strengths: List[str]
    agent_id: str
    timestamp: str

# ============================================================================
# OPENAI CLIENT SETUP
# ============================================================================

openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

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
        host="prompt_optimizer",  # Docker service name
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
                        print(f"💓 Prompt Optimizer heartbeat sent")
                    else:
                        print(f"⚠️ Heartbeat failed: {response.status_code}")
                        
            except Exception as e:
                print(f"❌ Heartbeat error: {e}")
        
        await asyncio.sleep(30)

# ============================================================================
# OPENAI INTEGRATION
# ============================================================================

async def call_openai_api(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Call OpenAI API with the given messages."""
    if not openai_client:
        raise ValueError("OpenAI client not initialized - check OPENAI_API_KEY")
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=1500,
            temperature=0.3  # Lower temperature for more consistent optimization
        )
        
        return {
            "choices": [{
                "message": {
                    "content": response.choices[0].message.content
                }
            }]
        }
        
    except Exception as e:
        raise Exception(f"OpenAI API call failed: {str(e)}")

# ============================================================================
# PROMPT OPTIMIZATION FUNCTIONS
# ============================================================================

async def optimize_prompt(original_prompt: str, target_ai: str = "general", 
                         optimization_level: str = "balanced", context: str = None) -> Dict[str, Any]:
    """Optimize a prompt for better AI interaction."""
    
    # Build system message based on target AI and optimization level
    system_messages = {
        "general": "You are an expert prompt engineer specializing in optimizing prompts for AI systems.",
        "coding": "You are an expert in optimizing prompts for code generation and technical AI assistance.",
        "creative": "You are an expert in optimizing prompts for creative AI applications like writing and design.",
        "analytical": "You are an expert in optimizing prompts for analytical and research-oriented AI tasks."
    }
    
    optimization_instructions = {
        "light": "Make minimal but impactful improvements to clarity and specificity.",
        "balanced": "Significantly improve clarity, specificity, and structure while maintaining the original intent.",
        "heavy": "Completely restructure and enhance the prompt for maximum effectiveness and clarity."
    }
    
    system_message = {
        "role": "system",
        "content": f"""
{system_messages.get(target_ai, system_messages["general"])}

Your task is to optimize user prompts to make them more effective for AI interaction. 
{optimization_instructions.get(optimization_level, optimization_instructions["balanced"])}

Guidelines for optimization:
1. Improve clarity and remove ambiguity
2. Add necessary context and specificity
3. Structure the request logically
4. Include relevant constraints or requirements
5. Use clear, direct language
6. Specify desired output format when helpful
7. Break down complex requests into clear components

Respond with a JSON object containing:
- "optimized_prompt": The improved version of the prompt
- "changes_made": List of specific improvements made
- "improvement_score": Float from 0-1 indicating how much improvement was possible
- "suggestions": Additional tips for the user

Context: {context or "No additional context provided"}
"""
    }
    
    user_message = {
        "role": "user",
        "content": f"Please optimize this prompt:\n\n{original_prompt}"
    }
    
    response = await call_openai_api([system_message, user_message])
    content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    try:
        # Try to parse JSON response
        import json
        result = json.loads(content)
        return result
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return {
            "optimized_prompt": content,
            "changes_made": ["General optimization applied"],
            "improvement_score": 0.7,
            "suggestions": ["Consider providing more specific requirements"]
        }

async def analyze_prompt(prompt: str) -> Dict[str, Any]:
    """Analyze a prompt for clarity, specificity, and completeness."""
    
    system_message = {
        "role": "system",
        "content": """
You are an expert prompt analyzer. Evaluate prompts on multiple dimensions and provide detailed feedback.

Analyze the given prompt and respond with a JSON object containing:
- "clarity_score": Float 0-1 (how clear and unambiguous the prompt is)
- "specificity_score": Float 0-1 (how specific and detailed the requirements are)
- "completeness_score": Float 0-1 (how complete the request is)
- "overall_score": Float 0-1 (overall quality assessment)
- "issues": List of problems or areas for improvement
- "strengths": List of what works well in the prompt

Be thorough but constructive in your analysis.
"""
    }
    
    user_message = {
        "role": "user",
        "content": f"Please analyze this prompt:\n\n{prompt}"
    }
    
    response = await call_openai_api([system_message, user_message])
    content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    try:
        import json
        result = json.loads(content)
        return result
    except json.JSONDecodeError:
        # Fallback analysis
        return {
            "clarity_score": 0.6,
            "specificity_score": 0.5,
            "completeness_score": 0.6,
            "overall_score": 0.57,
            "issues": ["Unable to perform detailed analysis"],
            "strengths": ["Prompt provided for analysis"]
        }

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
        "capabilities": {
            "openai": bool(OPENAI_API_KEY)
        },
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
        "ports": {"api": PORT, "mcp": MCP_PORT},
        "capabilities": {
            "openai": bool(OPENAI_API_KEY)
        }
    }

@app.post("/optimize", response_model=OptimizeResponse)
async def optimize_prompt_endpoint(request: OptimizeRequest):
    """Optimize a user prompt for better AI interaction."""
    print(f"✨ Prompt optimization request: {request.original_prompt[:100]}...")
    
    try:
        if not OPENAI_API_KEY:
            return OptimizeResponse(
                original_prompt=request.original_prompt,
                optimized_prompt=request.original_prompt,
                improvement_score=0.0,
                changes_made=["OpenAI API key not configured"],
                suggestions=["Configure OPENAI_API_KEY to enable optimization"],
                agent_id=AGENT_ID,
                timestamp=datetime.now(timezone.utc).isoformat(),
                success=False,
                error="OPENAI_API_KEY not set"
            )
        
        result = await optimize_prompt(
            original_prompt=request.original_prompt,
            target_ai=request.target_ai,
            optimization_level=request.optimization_level,
            context=request.context
        )
        
        return OptimizeResponse(
            original_prompt=request.original_prompt,
            optimized_prompt=result.get("optimized_prompt", request.original_prompt),
            improvement_score=result.get("improvement_score", 0.5),
            changes_made=result.get("changes_made", []),
            suggestions=result.get("suggestions", []),
            agent_id=AGENT_ID,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=True
        )
        
    except Exception as e:
        print(f"❌ Prompt optimization error: {e}")
        return OptimizeResponse(
            original_prompt=request.original_prompt,
            optimized_prompt=request.original_prompt,
            improvement_score=0.0,
            changes_made=[],
            suggestions=["Error occurred during optimization"],
            agent_id=AGENT_ID,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=False,
            error=str(e)
        )

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_prompt_endpoint(request: AnalyzeRequest):
    """Analyze a prompt for quality and completeness."""
    print(f"🔍 Prompt analysis request: {request.prompt[:100]}...")
    
    try:
        if not OPENAI_API_KEY:
            return AnalyzeResponse(
                clarity_score=0.0,
                specificity_score=0.0,
                completeness_score=0.0,
                overall_score=0.0,
                issues=["OpenAI API key not configured"],
                strengths=[],
                agent_id=AGENT_ID,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
        
        result = await analyze_prompt(request.prompt)
        
        return AnalyzeResponse(
            clarity_score=result.get("clarity_score", 0.5),
            specificity_score=result.get("specificity_score", 0.5),
            completeness_score=result.get("completeness_score", 0.5),
            overall_score=result.get("overall_score", 0.5),
            issues=result.get("issues", []),
            strengths=result.get("strengths", []),
            agent_id=AGENT_ID,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        print(f"❌ Prompt analysis error: {e}")
        return AnalyzeResponse(
            clarity_score=0.0,
            specificity_score=0.0,
            completeness_score=0.0,
            overall_score=0.0,
            issues=[f"Analysis error: {str(e)}"],
            strengths=[],
            agent_id=AGENT_ID,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

@app.post("/ping")
async def ping():
    """Simple ping endpoint."""
    return {
        "message": "pong",
        "agent_id": AGENT_ID,
        "service": "prompt_optimizer",
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