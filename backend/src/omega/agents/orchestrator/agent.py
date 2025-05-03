import os
import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from fastmcp.decorators import tool
from omega.core.models.task_models import TaskCore, TaskHeader, TaskStatus, TaskEnvelope, TaskEvent

# Import the RegisterableDualModeAgent base class
from registerable_dual_mode_agent import RegisterableDualModeAgent

@tool
def execute_workflow(workflow_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a multi-step workflow based on a high-level request.
    
    Args:
        workflow_request: Dictionary containing the workflow request details
            {
                "request": "The natural language request to process",
                "options": {
                    "max_parallel_tasks": 5,
                    "priority": "speed|quality",
                    "max_confidence_threshold": 0.7
                }
            }
            
    Returns:
        Dictionary containing workflow execution results
    """
    # This is just a stub - the real implementation happens in the agent
    return {"status": "accepted", "workflow_id": str(uuid.uuid4())}

@tool
def get_workflow_status(workflow_id: str) -> Dict[str, Any]:
    """
    Get the current status of a workflow execution.
    
    Args:
        workflow_id: The ID of the workflow to check
        
    Returns:
        Dictionary containing the current workflow status
    """
    # This is just a stub - the real implementation happens in the agent
    return {"status": "unknown", "workflow_id": workflow_id}

class OrchestratorAgent(RegisterableDualModeAgent):
    """
    Master orchestrator agent that coordinates the entire OMEGA framework.
    
    This agent:
    1. Receives user requests
    2. Sends them to the PromptOptimizer
    3. Forwards optimized prompts to the WorkflowPlanner
    4. Tracks execution of all subtasks
    5. Aggregates results and provides status updates
    """
    
    def __init__(self):
        super().__init__(
            agent_id="orchestrator",
            tool_name="orchestrator",
            description="Main orchestrator that coordinates all agents and tools in the OMEGA framework",
            version="1.0.0",
            skills=["execute_workflow", "get_workflow_status", "orchestrate_agents"],
            agent_type="agent",
            tags=["orchestration", "workflow", "coordination"]
        )
        
        # Register the MCP tools
        self.mcp.add_tool(execute_workflow)
        self.mcp.add_tool(get_workflow_status)
        
        # Workflow tracking
        self.active_workflows = {}
        self.completed_subtasks = {}

    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        """
        Process a task envelope containing a request or status update.
        
        Args:
            env: Task envelope with the request or update
            
        Returns:
            Updated task envelope with results
        """
        try:
            # Check if this is a new workflow request or a subtask update
            if env.header.conversation_id in self.active_workflows:
                # This is a subtask update for an existing workflow
                return await self._handle_subtask_update(env)
            else:
                # This is a new workflow request
                return await self._handle_new_workflow(env)
                
        except Exception as e:
            # Handle errors
            print(f"❌ Error in OrchestratorAgent: {e}")
            env.header.status = TaskStatus.FAILED
            env.header.last_event = TaskEvent.FAIL
            env.task.payload["error"] = str(e)
            return env

    async def _handle_new_workflow(self, env: TaskEnvelope) -> TaskEnvelope:
        """
        Handle a new workflow request by sending it through the optimization
        and planning pipeline.
        
        Args:
            env: Task envelope with the new workflow request
            
        Returns:
            Updated task envelope with initial workflow status
        """
        # Generate a workflow ID if not already present
        workflow_id = env.header.conversation_id or str(uuid.uuid4())
        env.header.conversation_id = workflow_id
        
        # Initialize workflow tracking
        self.active_workflows[workflow_id] = {
            "status": "INITIALIZING",
            "request": env.task.description,
            "start_time": asyncio.get_event_loop().time(),
            "subtasks": {},
            "results": {}
        }
        
        # Step 1: Find the PromptOptimizer agent
        prompt_optimizer = await self._find_agent_by_id("prompt_optimizer")
        if not prompt_optimizer:
            raise Exception("PromptOptimizer agent not found")
            
        # Step 2: Create a new task for the PromptOptimizer
        optimizer_env = TaskEnvelope(
            header=TaskHeader(
                conversation_id=workflow_id,
                sender=self.agent_id,
                assigned_agent="prompt_optimizer",
                status=TaskStatus.NEW,
                confidence=1.0,
                last_event=TaskEvent.SUBMIT,
                history=[],
            ),
            task=TaskCore(
                id=f"{workflow_id}-optimize",
                name="Optimize user request",
                description=env.task.description,
                category="prompt_optimization",
                required_capabilities=["optimize_prompt"],
                dependencies=[],
                parallelizable=False,
                payload=env.task.payload or {}
            )
        )
        
        # Step 3: Send the task to the PromptOptimizer's inbox
        await self.redis.xadd(
            "prompt_optimizer.inbox",
            {"payload": optimizer_env.model_dump_json()}
        )
        
        # Update the original task envelope with workflow info
        env.header.last_event = TaskEvent.ACCEPT
        env.header.status = TaskStatus.IN_PROGRESS
        env.task.payload = env.task.payload or {}
        env.task.payload["workflow_id"] = workflow_id
        env.task.payload["status"] = "Optimization in progress"
        
        # Return the updated envelope
        return env

    async def _handle_subtask_update(self, env: TaskEnvelope) -> TaskEnvelope:
        """
        Handle updates from subtasks in an active workflow.
        
        Args:
            env: Task envelope with the subtask update
            
        Returns:
            Updated task envelope with workflow status
        """
        workflow_id = env.header.conversation_id
        task_id = env.task.id
        
        # Update workflow tracking
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            
            # Check if this is from the PromptOptimizer
            if env.header.sender == "prompt_optimizer" and env.header.last_event == TaskEvent.COMPLETE:
                # The prompt has been optimized, now send it to the WorkflowPlanner
                return await self._forward_to_workflow_planner(env)
            
            # Check if this is from the WorkflowPlanner
            elif env.header.sender == "workflow_planner" and env.header.last_event == TaskEvent.COMPLETE:
                # The workflow has been planned, update status
                workflow["status"] = "EXECUTING"
                workflow["plan"] = env.task.payload.get("workflow", {})
                
                # Return updated status
                env.task.payload["status"] = "Workflow execution in progress"
                return env
            
            # This is a regular subtask update
            elif task_id in workflow["subtasks"]:
                # Update the subtask status
                workflow["subtasks"][task_id] = {
                    "status": env.header.status,
                    "last_event": env.header.last_event,
                    "result": env.task.payload
                }
                
                # Check if this completed a subtask
                if env.header.status == TaskStatus.COMPLETED:
                    self.completed_subtasks[task_id] = True
                    
                    # Check if all subtasks are complete
                    if self._check_workflow_completion(workflow_id):
                        # All subtasks are complete, mark workflow as complete
                        workflow["status"] = "COMPLETED"
                        workflow["end_time"] = asyncio.get_event_loop().time()
                        
                        # Aggregate results
                        aggregated_results = self._aggregate_workflow_results(workflow_id)
                        
                        # Update the envelope with final results
                        env.header.last_event = TaskEvent.COMPLETE
                        env.header.status = TaskStatus.COMPLETED
                        env.task.payload["status"] = "Workflow completed"
                        env.task.payload["results"] = aggregated_results
                
                return env
        
        # If we get here, something went wrong
        env.header.last_event = TaskEvent.FAIL
        env.header.status = TaskStatus.FAILED
        env.task.payload["error"] = f"Workflow {workflow_id} not found or invalid update"
        return env

    async def _forward_to_workflow_planner(self, env: TaskEnvelope) -> TaskEnvelope:
        """
        Forward an optimized prompt to the WorkflowPlanner agent.
        
        Args:
            env: Task envelope with the optimized prompt
            
        Returns:
            Updated task envelope with workflow status
        """
        workflow_id = env.header.conversation_id
        
        # Find the WorkflowPlanner agent
        workflow_planner = await self._find_agent_by_id("workflow_planner")
        if not workflow_planner:
            raise Exception("WorkflowPlanner agent not found")
            
        # Create a new task for the WorkflowPlanner
        planner_env = TaskEnvelope(
            header=TaskHeader(
                conversation_id=workflow_id,
                sender=self.agent_id,
                assigned_agent="workflow_planner",
                status=TaskStatus.NEW,
                confidence=1.0,
                last_event=TaskEvent.SUBMIT,
                history=[],
            ),
            task=TaskCore(
                id=f"{workflow_id}-plan",
                name="Plan workflow execution",
                description=env.task.description,
                category="workflow_planning",
                required_capabilities=["plan_workflow"],
                dependencies=[],
                parallelizable=False,
                payload={
                    "optimized_prompt": env.task.payload.get("optimized_prompt", {})
                }
            )
        )
        
        # Send the task to the WorkflowPlanner's inbox
        await self.redis.xadd(
            "workflow_planner.inbox",
            {"payload": planner_env.model_dump_json()}
        )
        
        # Update the workflow status
        workflow = self.active_workflows[workflow_id]
        workflow["status"] = "PLANNING"
        workflow["optimized_prompt"] = env.task.payload.get("optimized_prompt", {})
        
        # Update the original task envelope
        env.header.last_event = TaskEvent.FORWARD
        env.task.payload["status"] = "Workflow planning in progress"
        
        return env

    def _check_workflow_completion(self, workflow_id: str) -> bool:
        """
        Check if all subtasks in a workflow have been completed.
        
        Args:
            workflow_id: The ID of the workflow to check
            
        Returns:
            True if all subtasks are complete, False otherwise
        """
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return False
            
        # Get all subtasks from the workflow plan
        all_tasks = set(workflow.get("plan", {}).get("tasks", {}).keys())
        if not all_tasks:
            return False
            
        # Check if all tasks are in the completed list
        return all(task_id in self.completed_subtasks for task_id in all_tasks)

    def _aggregate_workflow_results(self, workflow_id: str) -> Dict[str, Any]:
        """
        Aggregate results from all subtasks in a completed workflow.
        
        Args:
            workflow_id: The ID of the completed workflow
            
        Returns:
            Dictionary containing aggregated results
        """
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return {"error": "Workflow not found"}
            
        # Collect all subtask results
        results = {}
        for task_id, task_info in workflow["subtasks"].items():
            results[task_id] = task_info.get("result", {})
            
        # Calculate execution time
        execution_time = workflow.get("end_time", 0) - workflow.get("start_time", 0)
            
        return {
            "workflow_id": workflow_id,
            "execution_time": execution_time,
            "status": workflow["status"],
            "optimized_prompt": workflow.get("optimized_prompt", {}),
            "plan": workflow.get("plan", {}),
            "subtask_results": results
        }

    async def _find_agent_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Find an agent in the registry by its ID.
        
        Args:
            agent_id: The ID of the agent to find
            
        Returns:
            Agent information or None if not found
        """
        try:
            agents = await self.discover_agents()
            for agent in agents:
                if agent.get("id") == agent_id:
                    return agent
            return None
        except Exception as e:
            print(f"❌ Error finding agent {agent_id}: {str(e)}")
            return None

    def _register_a2a_capabilities(self):
        """Register A2A capabilities"""
        # For now, we'll just implement the basic required method
        # Later we can add A2A skills if needed
        pass

if __name__ == "__main__":
    print("🎯 OrchestratorAgent online (RegisterableDualMode + MCPServer)")
    agent = OrchestratorAgent()
    agent.run()