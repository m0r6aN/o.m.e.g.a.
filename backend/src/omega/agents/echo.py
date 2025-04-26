import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from fastmcp.decorators import tool
from omega.agents.dual_mode_base_mcpserver import DualModeAgent
from omega.core.models.task_models import TaskEnvelope, TaskEvent, TaskStatus

load_dotenv()

@tool
def summarize_text(text: str) -> str:
    return asyncio.run(EchoAgent._summarize_static(text))

class EchoAgent(DualModeAgent):
    def __init__(self):
        super().__init__(
            agent_id="echo",
            tool_name="echo_summary",
            mcp_tools=[summarize_text]
        )
        self.llm = AsyncOpenAI()

    @staticmethod
    async def _summarize_static(text: str) -> str:
        llm = AsyncOpenAI()
        try:
            response = await llm.responses.create(
                model="gpt-4o",
                input=f"Summarize this: {text[:4000]}"
            )
            return response.output_text.strip()
        except Exception as e:
            return f"Error: {e}"

    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        content = env.task.payload.get("content", env.task.description)
        summary = await self._summarize_static(content)
        env.task.payload["result"] = summary
        env.header.last_event = TaskEvent.COMPLETE
        env.header.status = TaskStatus.COMPLETED
        env.header.sender = self.agent_id
        return env

if __name__ == "__main__":
    print("🪞 EchoAgent online (DualMode + MCPServer + Responses API)")
    EchoAgent().run()