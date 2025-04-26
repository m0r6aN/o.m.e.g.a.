import os
import json
import asyncio
import openai
from datetime import datetime, timezone
from fastmcp.decorators import tool
from omega.core.models.message import LLM_Response
from omega.core.models.task_models import TaskEvent, TaskEnvelope
from omega.agents.dual_mode_base_mcpserver import DualModeAgent

@tool
def optimize_prompt(raw_prompt: str) -> dict:
    return asyncio.run(PromptOptimizerAgent._optimize_static(raw_prompt))

class PromptOptimizerAgent(DualModeAgent):
    def __init__(self):
        super().__init__(
            agent_id="prompt_optimizer",
            tool_name="optimize_prompt",
            mcp_tools=[optimize_prompt]
        )
        self.client = openai.OpenAI()

    @staticmethod
    async def _optimize_static(raw_prompt: str) -> dict:
        client = openai.OpenAI()
        example_response = {
            "content": "Summarize how artificial intelligence is changing human interactions with technology.",
            "reasoning_effort": "low",
            "tools_used": ["openai:gpt-4o"],
            "references": [
                {
                    "note": "Simplified structure to reduce ambiguity and make it more task-specific.",
                    "example": "Original: 'Artificial intelligence is transforming the way humans interact with technology.'"
                }
            ]
        }

        schema = LLM_Response.model_json_schema(indent=2)
        optimization_prompt = (
            "You are a prompt optimization agent. Improve the given prompt for clarity and LLM suitability.\n\n"
            f"{json.dumps(example_response, indent=2)}\n\n"
            f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
            f"Optimize this:\n"{raw_prompt}""
        )

        response = await client.responses.create(
            model="gpt-4o",
            input=optimization_prompt,
            response_format=schema,
            temperature=0.4,
            max_tokens=2000
        )

        return json.loads(response.output_text)

    async def handle_task(self, env: TaskEnvelope):
        raw_prompt = env.task.payload.get("raw_prompt", env.task.description)
        optimized = await self._optimize_static(raw_prompt)

        env.header.sender = self.agent_id
        env.header.last_event = TaskEvent.COMPLETE
        env.task.payload["optimized_prompt"] = optimized
        env.header.assigned_agent = None
        await self.redis.xadd("task.to_match", {"payload": env.model_dump_json()})
        return env

if __name__ == "__main__":
    print("🧠 PromptOptimizerAgent online (DualMode + MCPServer + Responses API)")
    PromptOptimizerAgent().run()