# backend/src/omega/agents/dual_mode_agent.py
import os, asyncio, json, uvicorn, uuid
from typing import Any
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from contextlib import asynccontextmanager

from omega.core.models.task_models import TaskEnvelope


class DualModeAgent:
    """
    Base class: every agent owns its own Redis stream `<agent_id>.inbox`.
    Orchestrator/CapabilityMatcher writes TaskEnvelope objects there.
    """

    STREAM_KEY_TEMPLATE = "{agent_id}.inbox"
    RESULT_STREAM = "task.events"          # central multiplexed event log

    def __init__(self, agent_id: str, tool_name: str):
        self.agent_id = agent_id
        self.stream_key = self.STREAM_KEY_TEMPLATE.format(agent_id=agent_id)
        self.tool_name = tool_name
        self.redis: Redis = Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True,
        )
        self.app = FastAPI()
        self._setup_routes()
        self.app.router.lifespan_context = self._lifespan

    # ------------------ FastAPI endpoint -------------------------------------
    def _setup_routes(self):
        @self.app.post(f"/tools/{self.tool_name}")
        async def tool_endpoint(payload: Any):
            result = await self.handle_task(payload)
            return JSONResponse(content=result)

    # ------------------ lifecycle --------------------------------------------
    @asynccontextmanager
    async def _lifespan(self, _app):
        await self._verify_connection()
        asyncio.create_task(self._consume_stream())
        yield

    async def _verify_connection(self):
        try:
            await self.redis.ping()
            print(f"🧠 Redis OK for {self.agent_id}")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")

    # ------------------ pub‑sub via streams ----------------------------------
    async def _consume_stream(self):
        group = f"{self.agent_id}-grp"
        consumer = f"{self.agent_id}-{uuid.uuid4().hex[:6]}"
        try:
            await self.redis.xgroup_create(self.stream_key, group, mkstream=True)
        except Exception:
            pass  # already exists

        print(f"🔊 {self.agent_id} listening on stream {self.stream_key}…")
        while True:
            resp = await self.redis.xreadgroup(
                groupname=group,
                consumername=consumer,
                streams={self.stream_key: ">"},
                count=1,
                block=5_000,
            )
            if not resp:
                continue

            _, messages = resp[0]
            for _id, data in messages:
                try:
                    env = TaskEnvelope.model_validate_json(data["payload"])
                    result_env = await self.handle_task(env)
                    await self._publish_event(result_env)
                except Exception as e:
                    print(f"❌ {self.agent_id} task error: {e}")
                finally:
                    await self.redis.xack(self.stream_key, group, _id)

    async def _publish_event(self, env: TaskEnvelope):
        await self.redis.xadd(self.RESULT_STREAM, {"payload": env.model_dump_json()})

    # ------------------ to be implemented ------------------------------------
    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        raise NotImplementedError

    # ------------------ blocking run -----------------------------------------
    def run(self):
        uvicorn.run(self.app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
