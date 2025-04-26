import os
import json
import uuid
import asyncio
import openai
from datetime import datetime, timezone
from fastmcp.decorators import tool
from omega.core.models.task_models import TaskCore, TaskHeader, TaskStatus, TaskEnvelope, TaskEvent
from omega.agents.dual_mode_base_mcpserver import DualModeAgent
from omega.core.utils.task_utils import identify_parallel_groups, calculate_critical_path

@tool
def plan_workflow(prompt: str) -> dict:
    return asyncio.run(WorkflowPlannerAgent._plan_static(prompt))

class WorkflowPlannerAgent(DualModeAgent):
    def __init__(self):
        super().__init__(
            agent_id="workflow_planner",
            tool_name="plan_workflow",
            mcp_tools=[plan_workflow]
        )
        self.client = openai.OpenAI()

    @staticmethod
    async def _plan_static(prompt: str) -> dict:
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
            model="gpt-4o",
            input=planning_prompt,
            response_format=schema_block,
            temperature=0.3,
            max_tokens=2000
        )

        return json.loads(response.output_text)

    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        optimized_prompt = env.task.payload.get("optimized_prompt", env.task.description)
        workflow_id = env.task.id or str(uuid.uuid4())

        try:
            tasks = (await self._plan_static(optimized_prompt))["tasks"]
            parallel_groups = identify_parallel_groups(tasks)
            critical_path = calculate_critical_path(tasks)

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

                await self.redis.xadd("task.to_match", {"payload": child_env.model_dump_json()})

            env.header.last_event = TaskEvent.COMPLETE
            env.header.status = TaskStatus.COMPLETED
            return env

        except Exception as e:
            print(f"❌ Error in WorkflowPlannerAgent: {e}")
            env.header.status = TaskStatus.FAILED
            env.header.last_event = TaskEvent.FAIL
            env.task.payload["error"] = str(e)
            return env

if __name__ == "__main__":
    print("🧩 WorkflowPlannerAgent online (DualMode + MCPServer + Responses API)")
    WorkflowPlannerAgent().run()