# tool_registry.py

from enum import Enum
from typing import Any, Dict, List, Optional
from omega.core.models.task import TaskOutcome

class ExecutionMode(str, Enum):
    SYNC = "sync"
    ASYNC = "async"
    STREAMING = "streaming"
    
class ToolIntent(str, Enum):
    DISCOVER = "discover"             # Find tools for a task
    EXECUTE = "execute"               # Execute a tool with parameters
    DOCUMENT = "document"             # Document the tool's capabilities or results
    REFINE = "refine"                 # Refine the tool's output or parameters

class Tool:
    tool_id: str  # Unique identifier
    name: str  # Human-readable name
    description: str  # What the tool does
    parameters: Dict  # JSON schema of parameters
    required_capabilities: List[str]  # What agents need to use it
    execution_mode: ExecutionMode  # SYNC, ASYNC, STREAMING
    version: str  # Semantic versioning
    tags: List[str]  # For discovery and categorization

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self.tools.get(name)

    def list_tools(self):
        return {name: tool.description for name, tool in self.tools.items()}
        
class ToolRequest:
    request_id: str
    agent_id: str
    request_type: ToolIntent  # DISCOVER, EXECUTE, DOCUMENT
    query: str  # Natural language description of need
    parameters: Optional[Dict]  # For execution requests
    tool_id: Optional[str]  # For execution/documentation
    context: Optional[Dict]  # Additional context about the task
    
class ToolResult:
    request_id: str
    agent_id: str
    tool_id: str  # The tool that was used
    result: Any  # The result of the tool execution
    status: TaskOutcome  # SUCCESS, FAILURE, PENDING, etc.
    metadata: Optional[Dict]  # Additional context or metadata about the result
    error: Optional[str]  # Error message if the execution failed

# Singleton instance
tool_registry = ToolRegistry()