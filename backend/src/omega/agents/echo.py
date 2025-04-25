
import os
from backend.src.omega.agents.dual_mode_base import DualModeAgent
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

class EchoAgent(DualModeAgent):
    def __init__(self):
        super().__init__(
            agent_id="echo",
            redis_channel=os.getenv("REDIS_CHANNEL_RESPONSES", "responses_channel"),
            result_channel=os.getenv("REDIS_CHANNEL_RESULTS", "results_channel"),
            tool_name="echo"
        )
        self.llm = AsyncOpenAI()

    async def handle_task(self, task: dict) -> dict:
        content = task.get("content", "")
        task_id = task.get("task_id", "unknown")
        prompt = f"Summarize this: {content[:4000]}"
        try:
            response = await self.llm.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=256,
                temperature=0.2,
            )
            summary = response.choices[0].message.content.strip()
            return {
                "type": "result",
                "task_id": task_id,
                "agent_id": self.agent_id,
                "summary": summary,
            }
        except Exception as e:
            return {
                "type": "error",
                "task_id": task_id,
                "agent_id": self.agent_id,
                "error": str(e),
            }

if __name__ == "__main__":
    EchoAgent().run()
