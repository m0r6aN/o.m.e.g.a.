import os
import json
import asyncio
import openai
from typing import Dict, Any
from fastmcp.decorators import tool
from omega.core.models.message import LLM_Response
from omega.core.models.task_models import TaskEvent, TaskEnvelope

# Import the RegisterableDualModeAgent base class instead of DualModeAgent
from registerable_dual_mode_agent import RegisterableDualModeAgent

@tool
def optimize_prompt(raw_prompt: str) -> dict:
    """
    Optimize a prompt for clarity, specificity, and LLM suitability.

    Args:
        raw_prompt: The original prompt to optimize

    Returns:
        A dictionary containing the optimized prompt and metadata
    """
    return asyncio.run(PromptOptimizerAgent._optimize_static(raw_prompt))

class PromptOptimizerAgent(RegisterableDualModeAgent):
    """
    Agent that optimizes prompts using OpenAI's Responses API.
    This agent improves prompts for clarity, reduces ambiguity,
    and makes them more suitable for LLM processing.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="prompt_optimizer",
            tool_name="optimize_prompt",
            description="Optimizes prompts for clarity and LLM suitability",
            version="1.0.0",
            skills=["optimize_prompt", "clarify_instructions"],
            agent_type="agent",
            tags=["prompt", "optimization", "llm"]
        )
        self.client = openai.OpenAI()
        
        # Register the MCP tool
        self.mcp.add_tool(optimize_prompt)

    @staticmethod
    async def _optimize_static(raw_prompt: str) -> Dict[str, Any]:
        """
        Static method to optimize a prompt using OpenAI's Responses API.
        
        Args:
            raw_prompt: The original prompt to optimize
            
        Returns:
            Dictionary containing the optimized prompt and metadata
        """
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
        optimization_prompt = "You are a prompt optimization agent. Improve the given prompt for clarity and LLM suitability.\n\n"
        f"{json.dumps(example_response, indent=2)}\n\n"
        f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
        f"Optimize this:\n'{raw_prompt}'"
        

        response = await client.responses.create(
            model="gpt-4o",
            input=optimization_prompt,
            response_format=schema,
            temperature=0.4,
            max_tokens=2000
        )

        return json.loads(response.output_text)

    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        """
        Process a task envelope containing a prompt to optimize.
        
        Args:
            env: Task envelope containing the prompt
            
        Returns:
            Updated task envelope with optimized prompt
        """
        try:
            # Extract the raw prompt from the task envelope
            raw_prompt = env.task.payload.get("raw_prompt", env.task.description)
            
            # Optimize the prompt
            optimized = await self._optimize_static(raw_prompt)
            
            # Update the task envelope
            env.header.sender = self.agent_id
            env.header.last_event = TaskEvent.COMPLETE
            env.task.payload["optimized_prompt"] = optimized
            env.header.assigned_agent = None
            
            # Send to the matcher for further processing
            await self.redis.xadd("task.to_match", {"payload": env.model_dump_json()})
            
            # Return the updated envelope
            return env
            
        except Exception as e:
            # Handle errors
            print(f"❌ Error optimizing prompt: {str(e)}")
            env.header.last_event = TaskEvent.FAIL
            env.task.payload["error"] = str(e)
            return env

    def _register_a2a_capabilities(self):
        """Register A2A capabilities"""
        # For now, we'll just implement the basic required method
        # Later we can add A2A skills if needed
        pass

if __name__ == "__main__":
    print("🧠 PromptOptimizerAgent online (RegisterableDualMode + MCPServer + Responses API)")
    agent = PromptOptimizerAgent()
    agent.run()