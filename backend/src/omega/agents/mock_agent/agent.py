# /src/omega/agents/mock_agent/agent.py

from omega.core.agents.base_agent import BaseAgent
from omega.core.models.task_models import TaskEnvelope
from omega.core.models.agent_models import AgentCapability

class MockAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="mock_agent_001",
            name="Mock Agent",
            description="A test agent to verify BaseAgent functionality.",
            capabilities=[AgentCapability(name="mocking", description="Mocks things.")]
        )

    async def handle_task(self, envelope: TaskEnvelope) -> TaskEnvelope:
        # For now, this is just for the local test. In Docker, it will respond to Redis.
        print(f"MockAgent handling task: {envelope.task.description}")
        envelope.header.status = "completed"
        envelope.task.payload['result'] = f"Task '{envelope.task.name}' completed by {self.name}."
        return envelope

if __name__ == "__main__":
    agent = MockAgent()
    agent.run()