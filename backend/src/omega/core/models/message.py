from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from datetime import datetime, timezone

from omega.core.models.reasoning import ReasoningEffort

class MessageIntent(str, Enum):
    CHAT = "chat"                     # General communication between agents or user->agent
    START_TASK = "start_task"         # Initiate a new task for an agent
    CHECK_STATUS = "check_status"     # Request status update on a task
    MODIFY_TASK = "modify_task"       # Modify or provide feedback on an ongoing task/result
    TOOL_REQUEST = "tool_request"     # Agent requests execution of a tool
    TOOL_RESPONSE = "tool_response"   # ToolCore responds with tool execution result
    HEARTBEAT = "heartbeat"           # Agent heartbeat signal (internal, might not be a full message)
    SYSTEM = "system"                 # System-level messages (e.g., agent status, errors)
    ORCHESTRATION = "orchestration"   # Messages related to managing agent interaction
    PROMPT_OPTIMIZATION = "prompt_optimization" # Messages related to prompt optimization
    GENERATE_WORKFLOW = "generate_workflow" 
    WORKFLOW_STEP = "workflow_step"   

class BaseMessage(BaseModel):
    type: MessageIntent = Field(..., description="Message type identifier")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp"
    )
    
    model_config = {
        "json_encoders": {datetime: lambda v: v.isoformat()}
    }

    def serialize(self) -> str:
        # Pydantic v2 uses model_dump_json
        return self.model_dump_json()

    @classmethod
    def deserialize(cls, data: str) -> 'BaseMessage':
        # Pydantic v2 uses model_validate_json
        return cls.model_validate_json(data)

class Message(BaseMessage):
    """Model for general chat or informational messages."""
    content: str
    intent: MessageIntent = MessageIntent.CHAT
    target_agent: Optional[str] = None # Optional: Direct message to specific agent
    
class LLM_Response(BaseMessage):
    """Model for LLM responses."""
    content: str  # The generated text from the LLM
    reasoning_effort: ReasoningEffort  # Complexity assessment of the response
    tools_used: List[str]  # Tools utilized in generating the response
    references: List[Dict]  # Citations and references
    
class AgentMessage(BaseModel):
    """
    Represents a message exchanged between agents in the system.
    Each message has a unique ID, sender and receiver information, content, intent, reasoning effort,
    tools used, references, and a timestamp.
    """
    message_id: str  # Unique ID for the message
    conversation_id: str  # Groups related messages
    sender: str  # Agent ID
    receiver: str  # Target agent(s) or "broadcast"
    content: Dict  # Structured message content
    intent: MessageIntent  # Purpose of the message
    reasoning_effort: ReasoningEffort  # Complexity assessment
    tools_used: List[str]  # Tools utilized in response
    references: List[Dict]  # Citations and references
    timestamp: datetime
