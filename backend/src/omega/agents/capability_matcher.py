# backend/src/omega/agents/capability_matcher_agent.py
import os, asyncio, json, uuid
from redis.asyncio import Redis
from omega.core.models.task_models import TaskEnvelope, TaskHeader, TaskStatus
from omega.core.models.capabilities import Capability, AgentCapability

MATCHER_STREAM_IN = "task.to_match"
MATCHER_STREAM_OUT = "task.dispatch"

class CapabilityMatcherAgent:
    """
    Consumes envelopes without assigned_agent, selects best agent based on
    required_capabilities ∩ AgentCapability registry, writes to
    `<agent_id>.inbox` stream (also echoes to MATCHER_STREAM_OUT for audit).
    """

    def __init__(self):
        self.redis = Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True,
        )
        # Pretend registry in memory; swap for DB later
        self.registry: dict[str, AgentCapability] = {}

    async def run(self):
        group = "matcher-grp"
        consumer = f"matcher-{uuid.uuid4().hex[:6]}"
        try:
            await self.redis.xgroup_create(MATCHER_STREAM_IN, group, mkstream=True)
        except Exception:
            pass

        print("🎯 CapabilityMatcher listening…")
        while True:
            resp = await self.redis.xreadgroup(
                groupname=group,
                consumername=consumer,
                streams={MATCHER_STREAM_IN: ">"},
                count=1,
                block=5_000,
            )
            if not resp:
                continue

            _, messages = resp[0]
            for _id, data in messages:
                try:
                    env = TaskEnvelope.model_validate_json(data["payload"])
                    if env.header.assigned_agent:
                        await self.redis.xack(MATCHER_STREAM_IN, group, _id)
                        continue  # already routed

                    best = self._select_agent(env.task.required_capabilities)
                    env.header.candidate_agents = best["candidates"]
                    env.header.assigned_agent = best["winner"]

                    # Push to winner’s inbox
                    await self.redis.xadd(
                        f"{best['winner']}.inbox",
                        {"payload": env.model_dump_json()},
                    )
                    # Audit copy
                    await self.redis.xadd(
                        MATCHER_STREAM_OUT, {"payload": env.model_dump_json()}
                    )
                finally:
                    await self.redis.xack(MATCHER_STREAM_IN, group, _id)

    # --------------------------------------------------------------------- #
    def _select_agent(self, required: list[Capability]) -> dict:
        scored = []
        for aid, cap in self.registry.items():
            overlap = len(set(required) & set(cap.tool_proficiencies))
            if overlap:
                scored.append((aid, overlap))
        scored.sort(key=lambda t: t[1], reverse=True)
        winner = scored[0][0] if scored else "fallback_agent"
        return {"winner": winner, "candidates": [s[0] for s in scored]}

if __name__ == "__main__":
    asyncio.run(CapabilityMatcherAgent().run())
