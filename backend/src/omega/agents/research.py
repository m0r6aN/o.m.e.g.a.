import os
from datetime import datetime, timezone
from fastmcp.decorators import tool
from omega.agents.dual_mode_base_mcpserver import DualModeAgent
from backend.src.omega.tools.nlp_to_sql_tool.nlp_to_sql import nlp_to_sql_tool
from backend.src.omega.tools.execute_sql_tool.execute_sql import execute_sql_tool

@tool
def nlp_to_sql(input_data: dict) -> dict:
    return nlp_to_sql_tool(input_data)

@tool
def execute_sql(input_data: dict) -> dict:
    return execute_sql_tool(input_data)

class ResearchAgent(DualModeAgent):
    def __init__(self):
        super().__init__(
            agent_id="ResearchAgent",
            tool_name="research",
            mcp_tools=[nlp_to_sql, execute_sql]
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
    print("🔬 ResearchAgent online (DualMode + MCPServer)")
    ResearchAgent().run()