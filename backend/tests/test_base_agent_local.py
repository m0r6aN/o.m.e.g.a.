# /tests/test_base_agent_local.py

import pytest  # Import pytest

# This is new -> we'll need a mock llm_adapter for pure local tests
# to avoid real API calls and dependencies during unit testing.
# Let's create a dummy one for now.
from unittest.mock import MagicMock

from omega.core.utils.llm_adapter import LLMAdapter  # We will mock this
from omega.core.base_agent import BaseAgent
from omega.core.models.task_models import TaskEnvelope, TaskHeader, TaskCore

# --- Mock Agent Definition (Slightly modified for testing) ---

class MockAgent(BaseAgent):
    def __init__(self):
        # We need to temporarily bypass the real BaseAgent's __init__ 
        # as it expects env vars and tries to connect to Redis.
        # This is a common pattern in unit testing.
        self.id = "mock_agent_001"
        self.name = "Mock Agent"
        self.llm = LLMAdapter() # It will be mocked externally

    async def handle_task(self, envelope: TaskEnvelope) -> TaskEnvelope:
        print(f"MockAgent handling task: {envelope.task.description}")
        
        # Use the (mocked) LLM
        response = self.llm.generate(
            f"Confirm you are online and received the task: {envelope.task.description}",
            model="gpt-4o"
        )
        
        envelope.header.status = "completed"
        envelope.task.payload['result'] = response
        envelope.task.payload['confirmation'] = f"Task handled by {self.name}"
        
        return envelope

# --- The Test Function ---

# Pytest-asyncio marker to tell pytest this is an async test
@pytest.mark.asyncio
async def test_local_agent_handle_task(mocker):  # 'mocker' is a pytest fixture
    """
    Phase 1: Spark of Life Test
    Verifies that the agent's core logic can be triggered.
    """
    print("--- [Phase 1: Spark of Life Test] ---")

    # --- ARRANGE ---
    # Mock the LLM adapter to prevent real API calls
    mock_llm_response = "[Mock LLM Response] Task received and confirmed."
    mocker.patch.object(LLMAdapter, 'generate', return_value=mock_llm_response)
    
    # We bypass the complex __init__ for this unit test
    # This avoids needing Redis, registry URLs, etc.
    agent = MockAgent()
    
    test_envelope = TaskEnvelope(
        header=TaskHeader(conversation_id="local-test-convo", sender="pytest-runner"),
        task=TaskCore(
            id="local-task-001",
            name="Verify Local Functionality",
            description="A simple test to see if the agent's handle_task works.",
            category="testing",
            required_capabilities=[]
        )
    )

    # --- ACT ---
    result_envelope = await agent.handle_task(test_envelope)

    # --- ASSERT ---
    print("\n--- [Test Result] ---")
    print(f"Status: {result_envelope.header.status}")
    print(f"Agent Confirmation: {result_envelope.task.payload.get('confirmation')}")
    print(f"LLM Response: {result_envelope.task.payload.get('result')}")
    print("--- [Phase 1 Complete] ---")
    
    # Assertions are the soul of a test. This is what proves it works.
    assert result_envelope.header.status == "completed"
    assert "Task handled by Mock Agent" in result_envelope.task.payload['confirmation']
    assert result_envelope.task.payload['result'] == mock_llm_response

    # Verify that the llm.generate method was actually called with the right stuff
    LLMAdapter.generate.assert_called_once()
    call_args, _ = LLMAdapter.generate.call_args
    assert "Confirm you are online" in call_args[0]
    assert "A simple test" in call_args[0]