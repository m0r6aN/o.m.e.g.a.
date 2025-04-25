
import os
from datetime import datetime, timezone
from backend.src.omega.agents.dual_mode_base import DualModeAgent
from omega.tools.nlp_to_sql import nlp_to_sql_tool
from omega.tools.execute_sql import execute_sql_tool

class ResearchAgent(DualModeAgent):
    def __init__(self):
        super().__init__(
            agent_id="ResearchAgent",
            redis_channel=os.getenv("REDIS_CHANNEL_RESEARCH", "agent:ResearchAgent"),
            result_channel=os.getenv("REDIS_CHANNEL_ORCHESTRATE", "orchestrator_dispatch_channel"),
            tool_name="research"
        )

    async def handle_task(self, task: dict) -> dict:
        task_id = task.get("id", "unknown")
        workflow_id = task.get("workflow_id")
        input_data = task.get("input", {})
        tools = task.get("assignments", {}).get("tools", [])

        result = None
        for tool in tools:
            if tool == "nlp_to_sql":
                result = nlp_to_sql_tool(input_data)
            elif tool == "execute_sql":
                result = execute_sql_tool(input_data)

        return {
            "task_id": task_id,
            "agent": self.agent_id,
            "workflow_id": workflow_id,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "output": result
        }

if __name__ == "__main__":
    print("🔬 ResearchAgent online (DualMode)")
    ResearchAgent().run()
