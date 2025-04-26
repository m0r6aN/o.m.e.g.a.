import os
import json
import uuid
import asyncio
import openai
from fastapi import Body, FastAPI
from pydantic import BaseModel
from fastmcp.decorators import tool
from omega.agents.dual_mode_base_mcpserver import DualModeAgent
from omega.core.models.task_models import TaskEnvelope, TaskHeader, TaskStatus, TaskEvent, TaskCore

@tool
def orchestrate_request(text: str, target_lang: str = "es", skip_translation: bool = False) -> dict:
    return asyncio.run(OrchestratorAgent._orchestrate_static(text, target_lang, skip_translation))

class RunRequest(BaseModel):
    text: str
    target_lang: str = "es"
    skip_translation: bool = False

class OrchestratorAgent(DualModeAgent):
    def __init__(self):
        super().__init__(
            agent_id="orchestrator",
            tool_name="orchestrate_request",
            mcp_tools=[orchestrate_request]
        )
        self.client = openai.OpenAI()
        self.app.post("/run")(self.handle_request)

    @staticmethod
    async def _orchestrate_static(text: str, target_lang: str, skip_translation: bool) -> dict:
        redis = await OrchestratorAgent._get_redis()
        task_id = str(uuid.uuid4())
        payload = {
            "task_id": task_id,
            "type": "summarize",
            "payload": text,
            "reply_to": "results"
        }

        if not skip_translation:
            payload["follow_up"] = json.dumps({
                "type": "translate",
                "target_lang": target_lang
            })

        await redis.xadd("tasks", payload)

        while True:
            res = await redis.xread({"results": 0}, count=1, block=0)
            for _, entries in res:
                for _, fields in entries:
                    if fields.get("task_id") == task_id and fields.get("stage") == "done":
                        return {"summary_and_translation": fields["result"]}

    async def handle_request(self, req: RunRequest):
        return await self._orchestrate_static(req.text, req.target_lang, req.skip_translation)

    @staticmethod
    async def _get_redis():
        from redis.asyncio import Redis
        return Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True,
        )

    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        env.header.status = TaskStatus.COMPLETED
        env.header.last_event = TaskEvent.COMPLETE
        return env

if __name__ == "__main__":
    print("🧭 OrchestratorAgent online (DualMode + MCPServer + Redis Commander)")
    OrchestratorAgent().run()