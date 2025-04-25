# backend/src/omega/core/models/task_models.py
from __future__ import annotations
import uuid
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from pydantic import BaseModel, Field, model_validator
from omega.core.models.capabilities import Capability
from omega.core.models.reasoning import ReasoningEffort, ReasoningStrategy


# ---- enums ------------------------------------------------------------------
class TaskStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed" 
    FAILED = "failed"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"

class TaskEvent(str, Enum):
    PLAN = "plan"                     # Agent is planning the task
    EXECUTE = "execute"               # Agent is executing the task (or sub-step)
    CRITIQUE = "critique"             # Agent is critiquing a response (Claude's role)
    REFINE = "refine"                 # Agent is refining based on critique/feedback (GPT-4o's role)
    CONCLUDE = "conclude"             # Agent is concluding the debate/task (Claude's role)
    COMPLETE = "complete"             # Task is successfully completed
    FAIL = "fail"                     # Task failed
    ESCALATE = "escalate"             # Task requires escalation or human intervention
    REJECT = "reject"                 # Task is rejected or invalid
    CANCEL = "cancel"                 # Task is cancelled
    HEARTBEAT = "heartbeat"           # Agent heartbeat signal (internal, might not be a full message)
    INFO = "info"                     # General informational update about the task
    AWAITING_TOOL = "awaiting_tool"   # Agent is waiting for a tool result
    TOOL_COMPLETE = "tool_complete"   # Tool execution finished

class TaskOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"
    REJECTED = "rejected"


# ---- immutable business definition ------------------------------------------
class TaskCore(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str
    required_capabilities: List[Capability]
    dependencies: List[str] = []
    parallelizable: bool = False
    payload: Dict[str, Any] = {}


# ---- mutable orchestration header -------------------------------------------
class TaskHeader(BaseModel):
    conversation_id: str
    sender: str
    candidate_agents: List[str] = []
    assigned_agent: Optional[str] = None
    status: TaskStatus = TaskStatus.NEW
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    effort: Optional[ReasoningEffort] = None
    strategy: Optional[ReasoningStrategy] = None
    last_event: TaskEvent = TaskEvent.PLAN
    history: List[Dict[str, Any]] = []
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Auto‑estimate effort if not provided
    @model_validator(mode="before")
    @classmethod
    def _auto_effort(cls, values):
        if values.get("effort") is None and "strategy" in values:
            strat = values["strategy"]
            values["effort"] = (
                ReasoningEffort.LOW
                if strat == ReasoningStrategy.DIRECT
                else ReasoningEffort.MEDIUM
                if strat == ReasoningStrategy.COT
                else ReasoningEffort.HIGH
            )
        return values


# ---- envelope shipped on the wire -------------------------------------------
class TaskEnvelope(BaseModel):
    header: TaskHeader
    task: TaskCore
