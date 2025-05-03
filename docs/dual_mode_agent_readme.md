# 🚀 Dual Mode Agent Framework

A powerful framework for creating agents that can serve as both traditional AI Agents and AI Tools, using Python A2A and the Google A2A protocol.

## What's This?

The Dual Mode Agent framework provides a foundation for building AI agents that can:

1. **Operate as traditional agents** with Redis stream-based communication
2. **Expose themselves as tools** via FastAPI endpoints
3. **Communicate using the A2A protocol** with other agents

This gives you the best of both worlds - you can deploy your agents as standalone services that are discoverable and interoperable with the broader AI agent ecosystem.

## Key Features

- 🔄 **Dual Interface**: Both traditional Redis stream + FastAPI endpoints and A2A protocol endpoints
- 🧩 **Modular Design**: Easy to extend for specific use cases
- 🔌 **Integration Ready**: Seamlessly works with other agents via the A2A protocol
- 🛠️ **Tool Exposure**: Agents can be used as tools by other agents
- 🚢 **Docker Ready**: Designed to run in containerized environments

## Requirements

- Python 3.9+
- Redis
- FastAPI
- Python A2A library
- Model Context Protocol (MCP) support

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/dual-mode-agent.git
cd dual-mode-agent

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

1. Import the base `DualModeAgent` class
2. Create a subclass with your specific functionality
3. Implement the `handle_task` method to process tasks
4. Optionally override `handle_a2a_task` for custom A2A handling
5. Run your agent

## Example: Weather Agent

The repository includes a complete example of a Weather Agent that:

- Provides current weather information
- Provides weather forecasts
- Exposes its capabilities via A2A agent card
- Handles both Redis stream tasks and A2A protocol requests

To run the example:

```bash
# Set environment variables
export REDIS_HOST=localhost
export REDIS_PORT=6379
export PORT=8000
export MCP_PORT=9000

# Run the agent
python weather_agent.py
```

## Agent Card Example

When an A2A client discovers your agent, it will receive an agent card like this:

```json
{
  "name": "weather_agent",
  "description": "Provides weather information for locations worldwide",
  "version": "1.0.0",
  "skills": ["get_weather", "get_forecast"],
  "supported_content_formats": ["text"],
  "endpoints": {
    "base_url": "http://localhost:8000",
    "tasks_send": "/a2a/tasks/send",
    "tasks_get": "/a2a/tasks/get",
    "tasks_cancel": "/a2a/tasks/cancel",
    "tasks_send_subscribe": "/a2a/tasks/sendSubscribe"
  }
}
```

## Creating Your Own Agent

1. Create a new class that extends `DualModeAgent`
2. Implement your skills and capabilities
3. Override necessary methods

```python
from dual_mode_agent import DualModeAgent
from omega.core.models.task_models import TaskEnvelope
from python_a2a import skill

class MyCustomAgent(DualModeAgent):
    def __init__(self):
        super().__init__(
            agent_id="my_custom_agent",
            tool_name="my_tool",
            description="My awesome agent"
        )
    
    def _register_a2a_capabilities(self):
        @skill(name="My Skill", description="Does something cool")
        def my_skill(self, param1: str, param2: int = 0):
            # Implement skill
            return {"result": "Something cool"}
        
        self.my_skill = my_skill.__get__(self)
    
    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        # Process task
        # ...
        return env
```

## Docker Deployment

A Dockerfile is included to help you containerize your agents:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PORT=8000
ENV MCP_PORT=9000
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379

CMD ["python", "my_custom_agent.py"]
```

Build and run:

```bash
docker build -t my-custom-agent .
docker run -p 8000:8000 -p 9000:9000 my-custom-agent
```

## License

MIT License
