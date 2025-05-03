import os
import asyncio
import json
import uvicorn
import uuid
from typing import Any, List, Dict, Optional
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from contextlib import asynccontextmanager

# Original imports
from fastmcp import MCPServer
from omega.core.models.task_models import TaskEnvelope

# New A2A imports
from python_a2a import A2AServer, agent, skill
from python_a2a import TaskStatus, TaskState, Message, TextContent, MessageRole

class DualModeAgent(A2AServer):
    """
    Enhanced base class for agents that serve dual purposes:
    1. As a standard agent with Redis stream communication (original mode)
    2. As an A2A compliant agent that can interact with other A2A agents
    
    Every agent owns its own Redis stream <agent_id>.inbox
    Orchestrator/CapabilityMatcher writes TaskEnvelope objects there.
    """

    STREAM_KEY_TEMPLATE = "{agent_id}.inbox"
    RESULT_STREAM = "task.events"

    def __init__(
        self, 
        agent_id: str, 
        tool_name: str, 
        description: str = "A dual-mode agent",
        version: str = "1.0.0",
        skills: List[str] = None,
        mcp_tools: List = None
    ):
        # Initialize A2A server
        A2AServer.__init__(self)
        
        # Set up agent properties
        self.agent_id = agent_id
        self.tool_name = tool_name
        self.description = description
        self.version = version
        self.skills_list = skills or []
        
        # Set up Redis connection
        self.stream_key = self.STREAM_KEY_TEMPLATE.format(agent_id=agent_id)
        self.redis: Redis = Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True,
        )
        
        # Set up FastAPI
        self.app = FastAPI()
        self._setup_routes()
        self.app.router.lifespan_context = self._lifespan
        
        # Set up MCP server
        self.mcp = MCPServer(agent_name=agent_id, tools=mcp_tools or [])
        
        # Register A2A agent capabilities
        self._register_a2a_capabilities()
    
    def _register_a2a_capabilities(self):
        """Register capabilities for the A2A protocol"""
        # This will be overridden by child classes to add specific skills
        pass
    
    def _setup_routes(self):
        """Set up FastAPI routes including A2A protocol endpoints"""
        # Original tool endpoint
        @self.app.post(f"/tools/{self.tool_name}")
        async def tool_endpoint(payload: Any):
            result = await self.handle_task(payload)
            return JSONResponse(content=result)
        
        # A2A protocol endpoints
        @self.app.get("/.well-known/a2a/agent-card")
        async def agent_card():
            """
            A2A protocol: Return the agent card with metadata about this agent's capabilities
            """
            return {
                "name": self.agent_id,
                "description": self.description,
                "version": self.version,
                "skills": self.skills_list,
                "supported_content_formats": ["text"],
                "endpoints": {
                    "base_url": f"http://{os.getenv('HOST', 'localhost')}:{os.getenv('PORT', '8000')}",
                    "tasks_send": "/a2a/tasks/send",
                    "tasks_get": "/a2a/tasks/get",
                    "tasks_cancel": "/a2a/tasks/cancel",
                    "tasks_send_subscribe": "/a2a/tasks/sendSubscribe"
                }
            }
        
        @self.app.post("/a2a/tasks/send")
        async def a2a_tasks_send(request: Request):
            """A2A protocol: Handle a task request"""
            data = await request.json()
            task_id = data.get("task_id", str(uuid.uuid4()))
            message = data.get("message", {})
            
            # Convert A2A message to our internal format
            task = self.convert_a2a_to_task_envelope(task_id, message)
            
            # Process the task
            result = await self.handle_task(task)
            
            # Convert result back to A2A format
            a2a_response = self.convert_task_envelope_to_a2a(result)
            
            return JSONResponse(content=a2a_response)
        
        @self.app.get("/a2a/tasks/get")
        async def a2a_tasks_get(task_id: str):
            """A2A protocol: Get task status by ID"""
            # In a production system, you would retrieve the task status from storage
            # For simplicity, we're returning a placeholder
            return JSONResponse(content={
                "task_id": task_id,
                "status": {
                    "state": "completed",
                    "message": "Task completed successfully"
                },
                "artifacts": []
            })
        
        @self.app.post("/a2a/tasks/cancel")
        async def a2a_tasks_cancel(request: Request):
            """A2A protocol: Cancel a task"""
            data = await request.json()
            task_id = data.get("task_id")
            # Implement task cancellation logic here
            return JSONResponse(content={
                "task_id": task_id,
                "status": {
                    "state": "canceled",
                    "message": "Task canceled by request"
                }
            })

    @asynccontextmanager
    async def _lifespan(self, _app):
        await self._verify_connection()
        asyncio.create_task(self._consume_stream())
        asyncio.create_task(self._run_mcp_server())
        yield

    async def _verify_connection(self):
        try:
            await self.redis.ping()
            print(f"🧠 Redis OK for {self.agent_id}")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")

    async def _consume_stream(self):
        """
        Listen to the agent's Redis stream and process incoming tasks
        """
        group = f"{self.agent_id}-grp"
        consumer = f"{self.agent_id}-{uuid.uuid4().hex[:6]}"
        try:
            await self.redis.xgroup_create(self.stream_key, group, mkstream=True)
        except Exception:
            pass

        print(f"🔊 {self.agent_id} listening on stream {self.stream_key}…")
        while True:
            resp = await self.redis.xreadgroup(
                groupname=group,
                consumername=consumer,
                streams={self.stream_key: ">"},
                count=1,
                block=5_000,
            )
            if not resp:
                continue

            _, messages = resp[0]
            for _id, data in messages:
                try:
                    env = TaskEnvelope.model_validate_json(data["payload"])
                    result_env = await self.handle_task(env)
                    await self._publish_event(result_env)
                except Exception as e:
                    print(f"❌ {self.agent_id} task error: {e}")
                finally:
                    await self.redis.xack(self.stream_key, group, _id)

    async def _publish_event(self, env: TaskEnvelope):
        """Publish task results to the result stream"""
        await self.redis.xadd(self.RESULT_STREAM, {"payload": env.model_dump_json()})

    async def _run_mcp_server(self):
        """Run the MCP server for tool integration"""
        try:
            mcp_port = int(os.getenv("MCP_PORT", 9000))
            print(f"🔌 Starting MCPServer on port {mcp_port} for {self.agent_id}")
            await self.mcp.serve("0.0.0.0", mcp_port)
        except Exception as e:
            print(f"❌ MCP server failed for {self.agent_id}: {e}")

    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        """
        Process a task from any source (Redis stream or A2A)
        This method should be implemented by child classes
        """
        raise NotImplementedError
    
    def handle_a2a_task(self, task):
        """
        A2A protocol: Process an A2A task
        This method should be implemented by child classes
        """
        # Default implementation that delegates to the async handle_task method
        # Convert A2A task to internal format
        internal_task = self.convert_a2a_to_task_envelope(
            task.task_id, 
            task.message
        )
        
        # Use asyncio to call the async method
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(self.handle_task(internal_task))
        
        # Convert back to A2A format
        return self.convert_task_envelope_to_a2a(result)
    
    def convert_a2a_to_task_envelope(self, task_id: str, message: Dict) -> TaskEnvelope:
        """Convert an A2A message to our internal TaskEnvelope format"""
        # This is a simplified example - in a real implementation,
        # you would need to handle all A2A message fields
        content = message.get("content", {})
        text = content.get("text", "") if isinstance(content, dict) else ""
        
        # Create a simplified TaskEnvelope
        return TaskEnvelope(
            task_id=task_id,
            agent_id=self.agent_id,
            input={
                "text": text
            }
        )
    
    def convert_task_envelope_to_a2a(self, env: TaskEnvelope) -> Dict:
        """Convert our internal TaskEnvelope to A2A format"""
        # Extract results from the TaskEnvelope
        result_text = env.output.get("text", "") if env.output else ""
        
        # Create a basic A2A response
        return {
            "task_id": env.task_id,
            "status": {
                "state": "completed",
                "message": "Task completed successfully"
            },
            "artifacts": [
                {
                    "parts": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            ]
        }

    def run(self):
        """Run the FastAPI server"""
        uvicorn.run(self.app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))