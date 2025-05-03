import os
import json
import uuid
import asyncio
import openai
from typing import Dict, Any, List
from fastmcp.decorators import tool
from omega.core.models.task_models import TaskCore, TaskHeader, TaskStatus, TaskEnvelope, TaskEvent
from omega.core.utils.task_utils import identify_parallel_groups, calculate_critical_path

# Import the RegisterableDualModeAgent base class instead of DualModeAgent
from registerable_dual_mode_agent import RegisterableDualModeAgent

@tool
def plan_workflow(prompt: str) -> dict:
    """
    Create a structured workflow plan from a natural language prompt.
    
    Args:
        prompt: A natural language description of the task to be accomplished
        
    Returns:
        A dictionary containing structured tasks with dependencies and execution hints
    """
    return asyncio.run(WorkflowPlannerAgent._plan_static(prompt))

class WorkflowPlannerAgent(RegisterableDualModeAgent):
    """
    Agent that breaks down complex tasks into structured workflows.
    Identifies task dependencies, parallelization opportunities, and
    required capabilities for each subtask.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="workflow_planner",
            tool_name="plan_workflow",
            description="Creates optimized workflow plans with task dependencies and parallel execution paths",
            version="1.0.0",
            skills=["plan_workflow", "identify_dependencies", "optimize_execution"],
            agent_type="agent",
            tags=["workflow", "planning", "orchestration"]
        )
        self.client = openai.OpenAI()
        
        # Register the MCP tool
        self.mcp.add_tool(plan_workflow)

    @staticmethod
    async def _plan_static(prompt: str) -> Dict[str, Any]:
        """
        Static method to create a workflow plan using OpenAI's Responses API.
        
        Args:
            prompt: Natural language description of the task
            
        Returns:
            Dictionary containing structured tasks with dependencies
        """
        client = openai.OpenAI()
        schema_block = TaskCore.model_json_schema(indent=2)
        planning_prompt = (
            "You are a Process Optimization Engine. Your goal is to break down complex processes "
            "into well-structured, optimized tasks that conform exactly to the provided Task schema.\n\n"
            "Return the tasks as a JSON object with a single field called 'tasks'.\n\n"
            f"Here is the Task schema definition (Pydantic-compliant):\n{json.dumps(schema_block, indent=2)}\n\n"
            f"Process to optimize: {prompt}"
        )

        response = await client.responses.create(
            model="gpt-o3",
            input=planning_prompt,
            response_format=schema_block,
            temperature=0.3,
            max_tokens=2000
        )

        return json.loads(response.output_text)

    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        """
        Process a task envelope containing a request to create a workflow plan.
        
        Args:
            env: Task envelope with the request
            
        Returns:
            Updated task envelope with workflow plan results
        """
        try:
            # Extract the optimized prompt from the task envelope
            optimized_prompt = env.task.payload.get("optimized_prompt", env.task.description)
            workflow_id = env.task.id or str(uuid.uuid4())

            # Create the workflow plan
            tasks = (await self._plan_static(optimized_prompt))["tasks"]
            
            # Analyze the tasks for parallelization and critical path
            parallel_groups = identify_parallel_groups(tasks)
            critical_path = calculate_critical_path(tasks)

            # Create task envelopes for each subtask and publish them
            for task_dict in tasks:
                new_task = TaskCore(
                    id=task_dict["id"],
                    name=task_dict["name"],
                    description=task_dict["description"],
                    category=task_dict["category"],
                    required_capabilities=task_dict["required_capabilities"],
                    dependencies=task_dict.get("dependencies", []),
                    parallelizable=task_dict.get("parallelizable", False),
                    payload={
                        **task_dict.get("payload", {}),
                        "group_id": parallel_groups.get(task_dict["id"], None),
                        "critical_path": critical_path,
                    }
                )

                child_env = TaskEnvelope(
                    header=TaskHeader(
                        conversation_id=workflow_id,
                        sender=self.agent_id,
                        status=TaskStatus.NEW,
                        confidence=0.9,
                        last_event=TaskEvent.PLAN,
                        history=[],
                    ),
                    task=new_task
                )

                # Send the subtask to the matcher for agent assignment
                await self.redis.xadd("task.to_match", {"payload": child_env.model_dump_json()})

            # Update and return the original task envelope
            env.header.last_event = TaskEvent.COMPLETE
            env.header.status = TaskStatus.COMPLETED
            
            # Add the workflow structure to the payload for reference
            env.task.payload["workflow"] = {
                "tasks": tasks,
                "parallel_groups": parallel_groups,
                "critical_path": critical_path
            }
            
            return env

        except Exception as e:
            # Handle errors
            print(f"❌ Error in WorkflowPlannerAgent: {e}")
            env.header.status = TaskStatus.FAILED
            env.header.last_event = TaskEvent.FAIL
            env.task.payload["error"] = str(e)
            return env

    def _register_a2a_capabilities(self):
        """Register A2A capabilities"""
        # For now, we'll just implement the basic required method
        # Later we can add A2A skills if needed
        pass

    async def discover_available_agents(self) -> List[Dict[str, Any]]:
        """
        Helper method to discover available agents in the registry.
        This helps the planner assign appropriate agents to tasks.
        
        Returns:
            List of available agents with their capabilities
        """
        try:
            return await self.discover_agents()
        except Exception as e:
            print(f"❌ Error discovering agents: {str(e)}")
            return []

if __name__ == "__main__":
    print("🧩 WorkflowPlannerAgent online (RegisterableDualMode + MCPServer + Responses API)")
    agent = WorkflowPlannerAgent()
    agent.run()