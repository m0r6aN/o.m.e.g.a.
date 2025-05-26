#!/usr/bin/env python3
"""
OMEGA Workflow Planner Agent - Modern Self-Contained Version
Creates optimized workflow plans with task dependencies and parallel execution paths.
"""

import os
import json
import uuid
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

AGENT_ID = "workflow_planner_001"
AGENT_NAME = "Workflow Planner Agent"
AGENT_DESCRIPTION = "Advanced workflow planning agent that breaks down complex tasks into structured, optimized execution plans"
AGENT_SKILLS = [
    "workflow_planning",
    "task_decomposition",
    "dependency_analysis", 
    "parallel_execution_optimization",
    "critical_path_analysis",
    "agent_orchestration",
    "process_optimization"
]
AGENT_TAGS = ["workflow", "planning", "orchestration", "optimization", "coordination"]

PORT = int(os.getenv("PORT", 9004))
MCP_PORT = int(os.getenv("MCP_PORT", 9005))
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://agent_registry:9401")
CAPABILITY_MATCHER_URL = os.getenv("CAPABILITY_MATCHER_URL", "http://capability_matcher:9008")

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print(f"🚀 {AGENT_NAME} Configuration:")
print(f"   Agent ID: {AGENT_ID}")
print(f"   Port: {PORT}")
print(f"   Registry: {REGISTRY_URL}")
print(f"   Capability Matcher: {CAPABILITY_MATCHER_URL}")
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

class WorkflowTask(BaseModel):
    id: str
    name: str
    description: str
    category: str
    required_capabilities: List[str]
    dependencies: List[str] = []
    parallelizable: bool = False
    estimated_duration: int = 1  # minutes
    priority: str = "medium"  # low, medium, high, critical
    assigned_agent: Optional[str] = None
    payload: Dict[str, Any] = {}

class WorkflowPlan(BaseModel):
    workflow_id: str
    name: str
    description: str
    tasks: List[WorkflowTask]
    parallel_groups: Dict[str, List[str]] = {}
    critical_path: List[str] = []
    total_estimated_duration: int = 0
    complexity_score: float = 0.0
    agent_assignments: Dict[str, str] = {}

class PlanRequest(BaseModel):
    prompt: str
    context: Optional[str] = None
    optimization_level: str = "balanced"  # simple, balanced, complex
    include_agent_assignment: bool = True

class PlanResponse(BaseModel):
    workflow_plan: WorkflowPlan
    optimization_notes: List[str]
    agent_id: str
    timestamp: str
    success: bool = True
    error: Optional[str] = None

class ExecuteRequest(BaseModel):
    workflow_plan: WorkflowPlan
    execution_mode: str = "sequential"  # sequential, parallel, optimized

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
        host="workflow_planner",  # Docker service name
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
                        print(f"💓 Workflow Planner heartbeat sent")
                    else:
                        print(f"⚠️ Heartbeat failed: {response.status_code}")
                        
            except Exception as e:
                print(f"❌ Heartbeat error: {e}")
        
        await asyncio.sleep(30)

# ============================================================================
# OPENAI INTEGRATION
# ============================================================================

async def call_openai_for_planning(prompt: str, context: str = None, optimization_level: str = "balanced") -> Dict[str, Any]:
    """Call OpenAI to create a structured workflow plan."""
    if not openai_client:
        raise ValueError("OpenAI client not initialized - check OPENAI_API_KEY")
    
    # Define the task schema for structured output
    task_schema = {
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "category": {"type": "string"},
                        "required_capabilities": {"type": "array", "items": {"type": "string"}},
                        "dependencies": {"type": "array", "items": {"type": "string"}},
                        "parallelizable": {"type": "boolean"},
                        "estimated_duration": {"type": "integer"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
                    },
                    "required": ["id", "name", "description", "category", "required_capabilities"]
                }
            }
        },
        "required": ["tasks"]
    }
    
    # Build system message based on optimization level
    optimization_instructions = {
        "simple": "Create a straightforward workflow with minimal complexity and clear sequential steps.",
        "balanced": "Balance efficiency with thoroughness, including some parallel tasks and dependencies where beneficial.",
        "complex": "Create a highly optimized workflow with maximum parallelization, detailed dependencies, and sophisticated task breakdown."
    }
    
    system_message = f"""You are an expert Process Optimization Engine. Your goal is to break down complex processes into well-structured, optimized tasks.

Optimization Level: {optimization_level}
Instructions: {optimization_instructions.get(optimization_level, optimization_instructions["balanced"])}

Guidelines:
1. Break down the process into logical, manageable tasks
2. Identify dependencies between tasks accurately
3. Mark tasks as parallelizable when they can run simultaneously
4. Assign appropriate categories (planning, research, development, testing, deployment, etc.)
5. Specify required capabilities for each task (be specific about skills needed)
6. Estimate realistic duration in minutes
7. Set appropriate priority levels
8. Ensure task IDs are unique and descriptive

Context: {context or "No additional context provided"}

Return a JSON object with a 'tasks' array containing the structured workflow."""

    try:
        # Add explicit JSON instruction to system message
        enhanced_system_message = system_message + "\n\nIMPORTANT: Respond with ONLY valid JSON in the exact format specified. No additional text or explanation."
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": enhanced_system_message},
                {"role": "user", "content": f"Create a workflow plan for: {prompt}"}
            ],
            temperature=0.3,
            max_tokens=2500
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up the response if it contains markdown or extra text
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()
        
        # Try to parse JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("No valid JSON found in response")
        
    except Exception as e:
        raise Exception(f"OpenAI workflow planning failed: {str(e)}")

# ============================================================================
# WORKFLOW ANALYSIS FUNCTIONS
# ============================================================================

def identify_parallel_groups(tasks: List[WorkflowTask]) -> Dict[str, List[str]]:
    """Identify groups of tasks that can run in parallel."""
    parallel_groups = {}
    group_counter = 1
    
    # Find tasks with no dependencies or same dependencies
    for task in tasks:
        if task.parallelizable:
            # Group by dependency pattern
            dep_signature = "|".join(sorted(task.dependencies))
            
            # Find existing group with same dependencies
            group_found = False
            for group_id, task_ids in parallel_groups.items():
                # Check if any task in this group has the same dependencies
                for existing_task_id in task_ids:
                    existing_task = next((t for t in tasks if t.id == existing_task_id), None)
                    if existing_task and "|".join(sorted(existing_task.dependencies)) == dep_signature:
                        parallel_groups[group_id].append(task.id)
                        group_found = True
                        break
                if group_found:
                    break
            
            if not group_found:
                group_id = f"parallel_group_{group_counter}"
                parallel_groups[group_id] = [task.id]
                group_counter += 1
    
    return parallel_groups

def calculate_critical_path(tasks: List[WorkflowTask]) -> List[str]:
    """Calculate the critical path through the workflow."""
    # Build dependency graph
    task_dict = {task.id: task for task in tasks}
    
    # Simple critical path: longest path through dependencies
    def get_path_duration(task_id: str, visited: set = None) -> tuple[int, List[str]]:
        if visited is None:
            visited = set()
        
        if task_id in visited:
            return 0, []  # Avoid cycles
        
        visited.add(task_id)
        task = task_dict.get(task_id)
        if not task:
            return 0, []
        
        if not task.dependencies:
            return task.estimated_duration, [task_id]
        
        max_duration = 0
        best_path = []
        
        for dep in task.dependencies:
            dep_duration, dep_path = get_path_duration(dep, visited.copy())
            if dep_duration > max_duration:
                max_duration = dep_duration
                best_path = dep_path
        
        return max_duration + task.estimated_duration, best_path + [task_id]
    
    # Find the longest path
    max_duration = 0
    critical_path = []
    
    for task in tasks:
        duration, path = get_path_duration(task.id)
        if duration > max_duration:
            max_duration = duration
            critical_path = path
    
    return critical_path

def calculate_complexity_score(tasks: List[WorkflowTask]) -> float:
    """Calculate workflow complexity score (0-1)."""
    if not tasks:
        return 0.0
    
    num_tasks = len(tasks)
    num_dependencies = sum(len(task.dependencies) for task in tasks)
    num_parallel = sum(1 for task in tasks if task.parallelizable)
    
    # Normalize components
    task_complexity = min(num_tasks / 20, 1.0)  # 20+ tasks = max complexity
    dependency_complexity = min(num_dependencies / (num_tasks * 3), 1.0)  # Avg 3 deps per task = max
    parallel_factor = num_parallel / num_tasks if num_tasks > 0 else 0
    
    # Weighted average
    complexity = (task_complexity * 0.4 + dependency_complexity * 0.4 + parallel_factor * 0.2)
    return round(complexity, 3)

# ============================================================================
# AGENT ASSIGNMENT INTEGRATION
# ============================================================================

async def assign_agents_to_tasks(tasks: List[WorkflowTask]) -> Dict[str, str]:
    """Use the Capability Matcher to assign agents to tasks."""
    assignments = {}
    
    try:
        async with httpx.AsyncClient() as client:
            for task in tasks:
                # Create capability query
                capabilities_query = f"{task.description} {' '.join(task.required_capabilities)}"
                
                try:
                    response = await client.post(
                        f"{CAPABILITY_MATCHER_URL}/match",
                        json={
                            "query": capabilities_query,
                            "requirements": task.required_capabilities,
                            "min_score": 0.4,
                            "max_results": 1
                        },
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("matches"):
                            best_match = data["matches"][0]
                            assignments[task.id] = best_match["agent_id"]
                            task.assigned_agent = best_match["agent_id"]
                        else:
                            assignments[task.id] = "no_agent_found"
                    
                except Exception as e:
                    print(f"⚠️ Failed to assign agent for task {task.id}: {e}")
                    assignments[task.id] = "assignment_failed"
                    
    except Exception as e:
        print(f"❌ Error in agent assignment: {e}")
    
    return assignments

# ============================================================================
# CORE WORKFLOW PLANNING FUNCTIONS
# ============================================================================

async def create_workflow_plan(prompt: str, context: str = None, 
                              optimization_level: str = "balanced",
                              include_agent_assignment: bool = True) -> tuple[WorkflowPlan, List[str]]:
    """Create a complete workflow plan with optimization analysis."""
    
    # Get structured tasks from OpenAI
    planning_result = await call_openai_for_planning(prompt, context, optimization_level)
    
    # Convert to WorkflowTask objects
    tasks = []
    for task_data in planning_result.get("tasks", []):
        task = WorkflowTask(**task_data)
        tasks.append(task)
    
    if not tasks:
        raise ValueError("No tasks generated from prompt")
    
    # Analyze workflow structure
    parallel_groups = identify_parallel_groups(tasks)
    critical_path = calculate_critical_path(tasks)
    complexity_score = calculate_complexity_score(tasks)
    
    # Calculate total duration (considering parallelization)
    total_duration = sum(task.estimated_duration for task in tasks if task.id in critical_path)
    
    # Assign agents if requested
    agent_assignments = {}
    if include_agent_assignment:
        agent_assignments = await assign_agents_to_tasks(tasks)
    
    # Create workflow plan
    workflow_plan = WorkflowPlan(
        workflow_id=str(uuid.uuid4()),
        name=f"Workflow: {prompt[:50]}...",
        description=f"Generated workflow plan for: {prompt}",
        tasks=tasks,
        parallel_groups=parallel_groups,
        critical_path=critical_path,
        total_estimated_duration=total_duration,
        complexity_score=complexity_score,
        agent_assignments=agent_assignments
    )
    
    # Generate optimization notes
    optimization_notes = []
    optimization_notes.append(f"Workflow contains {len(tasks)} tasks")
    optimization_notes.append(f"Critical path duration: {total_duration} minutes")
    optimization_notes.append(f"Parallelizable tasks: {len([t for t in tasks if t.parallelizable])}")
    optimization_notes.append(f"Complexity score: {complexity_score}/1.0")
    
    if parallel_groups:
        optimization_notes.append(f"Identified {len(parallel_groups)} parallel execution groups")
    
    if agent_assignments:
        assigned_count = len([a for a in agent_assignments.values() if a not in ["no_agent_found", "assignment_failed"]])
        optimization_notes.append(f"Successfully assigned agents to {assigned_count}/{len(tasks)} tasks")
    
    return workflow_plan, optimization_notes

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
            "openai": bool(OPENAI_API_KEY),
            "capability_matcher": True
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
            "openai": bool(OPENAI_API_KEY),
            "capability_matcher": True
        }
    }

@app.post("/plan", response_model=PlanResponse)
async def create_plan_endpoint(request: PlanRequest):
    """Create a structured workflow plan from a natural language prompt."""
    print(f"🧩 Workflow planning request: {request.prompt[:100]}...")
    
    try:
        if not OPENAI_API_KEY:
            return PlanResponse(
                workflow_plan=WorkflowPlan(
                    workflow_id="",
                    name="Error",
                    description="OpenAI API key not configured",
                    tasks=[]
                ),
                optimization_notes=["OpenAI API key not configured"],
                agent_id=AGENT_ID,
                timestamp=datetime.now(timezone.utc).isoformat(),
                success=False,
                error="OPENAI_API_KEY not set"
            )
        
        workflow_plan, optimization_notes = await create_workflow_plan(
            prompt=request.prompt,
            context=request.context,
            optimization_level=request.optimization_level,
            include_agent_assignment=request.include_agent_assignment
        )
        
        return PlanResponse(
            workflow_plan=workflow_plan,
            optimization_notes=optimization_notes,
            agent_id=AGENT_ID,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=True
        )
        
    except Exception as e:
        print(f"❌ Workflow planning error: {e}")
        return PlanResponse(
            workflow_plan=WorkflowPlan(
                workflow_id="",
                name="Error",
                description=f"Planning failed: {str(e)}",
                tasks=[]
            ),
            optimization_notes=[f"Error: {str(e)}"],
            agent_id=AGENT_ID,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=False,
            error=str(e)
        )

@app.post("/ping")
async def ping():
    """Simple ping endpoint."""
    return {
        "message": "pong",
        "agent_id": AGENT_ID,
        "service": "workflow_planner",
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