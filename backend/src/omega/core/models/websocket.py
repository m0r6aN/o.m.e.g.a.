# --- WebSocket Message Model ---

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import datetime as dt

class WebSocketMessageType(str, Enum):
    """Enum for different types of WebSocket messages."""
    CHAT_MESSAGE = "chat_message"
    START_TASK = "start_task"
    AGENT_UPDATE = "agent_update"
    SYSTEM_INFO = "system_info"
    ERROR = "error"

class WebSocketMessage(BaseModel):
    """Model for messages exchanged via WebSocket between Frontend and WS Server."""
    type: WebSocketMessageType # Type of message (e.g., chat, task update, etc.)
    payload: Dict[str, Any] # Contains the actual data, could be a serialized Message, Task, etc.
    client_id: Optional[str] = None # Optional: Identifier for the frontend client connection
    timestamp: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))

    def serialize(self) -> str:
        return self.model_dump_json()

    @classmethod
    def deserialize(cls, data: str) -> 'WebSocketMessage':
        return cls.model_validate_json(data)