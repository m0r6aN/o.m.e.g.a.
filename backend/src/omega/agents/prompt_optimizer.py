
import os
import json
import asyncio
import uuid
from datetime import datetime, timezone
from omega.core.models.task_models import TaskEvent
from omega.core.models.task_models import TaskEnvelope
from omega.agents.dual_mode_base import DualModeAgent

class PromptOptimizerAgent(DualModeAgent):
    def __init__(self):
        super().__init__(
            agent_id="prompt_optimizer",
            redis_channel=os.getenv("REDIS_CHANNEL_PROMPT", "prompt_channel"),
            result_channel=os.getenv("REDIS_CHANNEL_PLAN", "workflow_plan_channel"),
            tool_name="optimize_prompt"
        )

    async def handle_task(self, env: TaskEnvelope):
        raw_prompt = env.task.payload.get("raw_prompt", env.task.description)
        optimized = raw_prompt.strip().capitalize() + "."
        env.header.sender = self.agent_id
        env.header.last_event = TaskEvent.COMPLETE
        env.task.payload["optimized_prompt"] = optimized
        # clear assignment so matcher can pick next agent
        env.header.assigned_agent = None
        await self.redis.xadd("task.to_match", {"payload": env.model_dump_json()})
        return env

if __name__ == "__main__":
    print("🧠 PromptOptimizerAgent online (DualMode)")
    PromptOptimizerAgent().run()
