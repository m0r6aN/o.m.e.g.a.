# /omega/core/agents/mock_agent.py

from omega.core.agents.base_agent import BaseAgent
from omega.core.models import AgentCapability, TaskEnvelope, TaskHeader, TaskCore

class MockAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="mock_agent_001",
            name="Mock Agent",
            description="A test agent to verify BaseAgent functionality.",
            capabilities=[AgentCapability(name="mocking", description="Mocks things.")]
        )

    async def handle_task(self, envelope: TaskEnvelope) -> TaskEnvelope:
        logger.info(f"MockAgent handling task: {envelope.task.description}")
        
        # Use the LLM to prove it's connected
        response = self.llm.generate(f"Confirm you are online and received the task: {envelope.task.description}", model="gpt-4o")
        
        # Update the envelope with the result
        envelope.header.status = "completed"
        envelope.task.payload['result'] = response
        envelope.task.payload['confirmation'] = f"Task handled by {self.name} at {envelope.header.timestamp}"
        
        return envelope