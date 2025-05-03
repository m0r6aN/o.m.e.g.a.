# omega/agents/capability_matcher.py

import os
import uuid
from typing import List
from redis.asyncio import Redis
import aiohttp

from omega.core.models.task_models import TaskEnvelope, TaskStatus

class CapabilityMatcherAgent:
    """
    Advanced capability matcher that routes tasks to the most appropriate agents
    based on sophisticated capability matching.
    """
    
    MATCHER_STREAM_IN = "task.to_match"
    MATCHER_STREAM_OUT = "task.dispatch"
    
    def __init__(self):
        self.redis = Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True,
        )
        
        self.registry_url = os.getenv("REGISTRY_URL", "http://registry:9401")
        self.session = None
    
    async def initialize(self):
        """Initialize the matcher"""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close resources"""
        if self.session:
            await self.session.close()
    
    async def run(self):
        """Run the capability matcher service"""
        await self.initialize()
        
        try:
            group = "matcher-grp"
            consumer = f"matcher-{uuid.uuid4().hex[:6]}"
            
            try:
                await self.redis.xgroup_create(self.MATCHER_STREAM_IN, group, mkstream=True)
            except Exception:
                pass
            
            print("🔍 CapabilityMatcher listening…")
            while True:
                resp = await self.redis.xreadgroup(
                    groupname=group,
                    consumername=consumer,
                    streams={self.MATCHER_STREAM_IN: ">"},
                    count=1,
                    block=5_000,
                )
                
                if not resp:
                    continue
                
                _, messages = resp[0]
                for _id, data in messages:
                    try:
                        env = TaskEnvelope.model_validate_json(data["payload"])
                        
                        # Skip if already assigned
                        if env.header.assigned_agent:
                            continue
                        
                        # Match capabilities
                        required_capabilities = env.task.required_capabilities
                        if not required_capabilities:
                            print("⚠️ Task has no required capabilities, using fallback")
                            env.header.assigned_agent = "fallback_agent"
                        else:
                            await self._match_and_assign_agent(env, required_capabilities)
                        
                        # Route to assigned agent
                        if env.header.assigned_agent:
                            # Push to winner's inbox
                            await self.redis.xadd(
                                f"{env.header.assigned_agent}.inbox",
                                {"payload": env.model_dump_json()},
                            )
                            
                            # Audit copy
                            await self.redis.xadd(
                                self.MATCHER_STREAM_OUT, 
                                {"payload": env.model_dump_json()}
                            )
                        else:
                            print("❌ Could not assign an agent for task")
                            env.status = TaskStatus.REJECTED
                            env.message = "No suitable agent found for required capabilities"
                            
                            # Send rejection notification
                            await self.redis.xadd(
                                "task.events",
                                {"payload": env.model_dump_json()}
                            )
                    
                    except Exception as e:
                        print(f"❌ Error in capability matcher: {str(e)}")
                    
                    finally:
                        await self.redis.xack(self.MATCHER_STREAM_IN, group, _id)
        
        finally:
            await self.close()
    
    async def _match_and_assign_agent(self, env: TaskEnvelope, required_capabilities: List[str]):
        """Match and assign the best agent for the required capabilities"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # For each capability, find matching agents
        capability_matches = {}
        
        for capability in required_capabilities:
            try:
                async with self.session.post(
                    f"{self.registry_url}/registry/capabilities/match",
                    json={"text": capability, "min_score": 0.6}
                ) as response:
                    if response.status == 200:
                        matches = await response.json()
                        if matches:
                            capability_matches[capability] = matches
            
            except Exception as e:
                print(f"❌ Error matching capability '{capability}': {str(e)}")
        
        # If no matches for any capability, return
        if not capability_matches:
            env.header.assigned_agent = "fallback_agent"
            env.header.candidate_agents = ["fallback_agent"]
            return
        
        # Find the best overall agent
        # Simple approach: use the agent with the highest average score across matched capabilities
        agent_scores = {}
        
        for capability, matches in capability_matches.items():
            for match in matches:
                agent_id = match["agent_id"]
                score = match["score"]
                
                if agent_id not in agent_scores:
                    agent_scores[agent_id] = {"total": 0, "count": 0}
                
                agent_scores[agent_id]["total"] += score
                agent_scores[agent_id]["count"] += 1
        
        # Calculate average scores
        for agent_id, data in agent_scores.items():
            data["average"] = data["total"] / data["count"]
        
        # Sort by average score
        sorted_agents = sorted(
            agent_scores.items(),
            key=lambda item: item[1]["average"],
            reverse=True
        )
        
        # Assign the winner
        if sorted_agents:
            winner = sorted_agents[0][0]
            env.header.assigned_agent = winner
            env.header.candidate_agents = [agent_id for agent_id, _ in sorted_agents]