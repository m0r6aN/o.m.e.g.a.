from typing import Dict
from pydantic import Field
from omega.core.models.message import BaseMessage

class SystemStatusMessage(BaseMessage):
    system_ready: bool = Field(..., description="Whether the system is ready")
    agent_status: Dict[str, str] = Field(..., description="Status of each agent")
    
    # Set the type field automatically
    type: str = "system_status_update"