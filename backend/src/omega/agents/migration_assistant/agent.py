import os
import json
import re
from openai import AsyncOpenAI
from omega.agents.registerable_dual_mode_agent import RegisterableDualModeAgent
from omega.utils.db import MongoDBClient
from omega.core.models.task_models import TaskEnvelope, TaskEvent, TaskStatus
from omega.core.models.migration_models import MigrationPlan
from fastapi import FastAPI, HTTPException
from omega.core.agent_discovery import AgentCapability

class MigrationAssistantAgent(RegisterableDualModeAgent):
    def __init__(self):
        super().__init__(
            agent_id="MigrationAssistantAgent",
            tool_name="migration_assistant",
            description="Suggests microservice boundaries based on analysis results",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="suggest_microservices",
                    description="Suggests microservice boundaries for monolithic applications based on analysis graphs",
                    inputs=["analysis_id", "user_input"],
                    outputs=["MigrationPlan"]
                )
            ],
            agent_type="dual",
            tags=["migration", "architecture", "planning"]
        )
        self.db = MongoDBClient(
            uri=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
            db_name=os.getenv("MONGO_DB", "omega")
        )
        self.llm = AsyncOpenAI()

    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        try:
            analysis_id = env.task.payload.get("analysis_id")
            user_input = env.task.payload.get("user_input", "")

            if not analysis_id:
                raise ValueError("Missing analysis_id in task payload")

            self.logger.info(f"Fetching analysis for ID: {analysis_id}")
            analysis = await self.db.find_one("analyses", {"analysis_id": analysis_id})
            if not analysis:
                raise ValueError(f"No analysis found for id: {analysis_id}")

            self.logger.info("Generating migration plan from OpenAI...")
            migration_plan = await self._generate_migration_plan(analysis, user_input)
            self.logger.debug(f"Migration Plan: {migration_plan.dict()}")

            env.task.payload["migration_plan"] = migration_plan.dict()

            env.header.status = TaskStatus.COMPLETED
            env.header.last_event = TaskEvent.COMPLETE
            env.header.sender = self.agent_id

            # Emit to Redis pubsub
            await self.redis_client.publish("task.events", json.dumps({
                "task_id": env.task.task_id,
                "status": "COMPLETED",
                "result": migration_plan.dict()
            }))

        except Exception as e:
            env.task.payload["error"] = str(e)
            env.header.status = TaskStatus.FAILED
            env.header.last_event = TaskEvent.FAIL
            env.header.sender = self.agent_id
            self.logger.error(f"❌ Error during task handling: {e}")

        return env

    async def _generate_migration_plan(self, analysis: dict, user_input: str) -> MigrationPlan:
        # Use OpenAI Responses API with prompt
        prompt = self._build_prompt(analysis, user_input)
        response = await self.llm.responses.create(
            model="gpt-4.1",
            input=prompt,
            response_format="json",
            temperature=0.3,
            max_tokens=2048
        )

        return MigrationPlan.parse_obj(json.loads(response.output))

    def _build_prompt(self, analysis: dict, user_input: str) -> str:
        target_platform = "AWS"
        estimated_users = 1000

        if user_input:
            if "GCP" in user_input.lower():
                target_platform = "GCP"
            elif "Azure" in user_input.lower():
                target_platform = "Azure"

            user_count = re.search(r"(\\d+)\\s*users", user_input, re.IGNORECASE)
            if user_count:
                estimated_users = int(user_count.group(1))

        return f"""
You are an AI migration assistant. Given a code analysis result, suggest microservice boundaries for a monolith application. Output a JSON object conforming to this schema:

{{
  "analysis_id": str,
  "suggestions": [
    {{
      "module": str,
      "suggested_service": str,
      "dependencies": [str],
      "rationale": str
    }}
  ],
  "target_platform": str,
  "estimated_users": int
}}

Input analysis:
- analysis_id: {analysis.get("analysis_id")}
- components: {json.dumps(analysis.get("components", []))}
- dependencies: {json.dumps(analysis.get("dependencies", []))}

Instructions:
- Suggest services for modules with low external dependencies.
- Group related functions/classes into the same service.
- Provide a clear rationale for each suggestion.
- Use target_platform=\"{target_platform}\" and estimated_users={estimated_users}.

User input: {user_input}
"""
# FastAPI MCP tool endpoint (no auth for MVP)
app = FastAPI()

@app.post("/tools/migration_assistant/get_initial_suggestions")
async def get_initial_suggestions(analysis_id: str):
    agent = MigrationAssistantAgent()
    analysis = await agent.db.find_one("analyses", {"analysis_id": analysis_id})
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    plan = await agent._generate_migration_plan(analysis, user_input="")
    return plan.dict()


if __name__ == "__main__":
    print("🧠 MigrationAssistantAgent online (DualMode)")
    MigrationAssistantAgent().run()
