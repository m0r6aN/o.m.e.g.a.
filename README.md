# O.M.E.G.A. Framework ✨
**Orchestrated Multi-Expert Gen Agents**

---

# 🌟 Vision: The Fusion of MCP + A2A

OMEGA isn't just an AI framework.
OMEGA is the **first true symbiosis** of two breakthrough paradigms:

| Concept | Meaning | Why It Matters |
|:--------|:--------|:---------------|
| **MCP**  | Agents expose capabilities as **tools** — JSON I/O, callable, discoverable. | A common way to **expose**, **discover**, and **invoke** agent functionality. |
| **A2A**  | Agents **communicate and collaborate** using a shared language. | Enables **reasoning, debate, strategy** between autonomous agents. |

## 🧬 OMEGA's Superpower:
- **Agents as Tools** (via MCP): Invoke specific, non-conversational capabilities.
- **Agents as Collaborators** (via A2A): Hold open-ended dialogues, strategize, negotiate.
- **Agents as Hybrids**: Both tool and peer — fluid, dynamic, intelligent.

OMEGA empowers AI Agents to operate not just as isolated tools or isolated thinkers, but as hybrid collaborators — simultaneously callable as services and conversable as peers. By merging MCP with A2A, we create a living network of interoperable, intelligent, model-agnostic entities capable of both action and understanding.

---

## 💥 Project Description

Built from the ground up to merge:
- **MCP (Model Context Protocol) Toolchains**
- **Real-time Redis Pub/Sub Collaboration**
- **Model-agnostic, Futureproof Architecture**
- **FastAPI Microservices + FastMCP Servers**
- **OpenAI Responses API for next-gen task orchestration**

Agents aren't just "tools".
Agents aren't just "services".
Agents are **living, breathing nodes of reasoning** — communicating, collaborating, competing — to bring the best outcome.

---

## 🌟 Key Features

- ✨ **Dual-Mode Agents**: Every agent speaks both Redis Streams AND MCP Tool API fluently.
- 🚀 **Responses API Everywhere**: Structured output, auto tool invocation, model-agnostic.
- ✨ **MCP Tools Auto-Register**: Decorators expose native agent functions to the universe.
- 🌐 **Container-Ready**: Agents are born ready for Docker, K8s, and hyperscale.
- 🧪 **Multi-Agent Real-time Collaboration**: Workflows and strategies dynamically evolve.
- ⚛️ **Model-Agnostic**: GPT, Claude, Mistral, Gemini... no loyalty, only performance.
- 🎨 **Designed for Extensibility**: Add agents, add tools, scale the multiverse.

---
## Core Agents

### Project Architect

### Coder
The Code Generator Agent is a specialized component of the OMEGA framework that leverages:
- Context7 documentation tool for up-to-date library reference
- OpenAI Responses API for high-quality code generation
- A dual-mode architecture for both direct tool calls and agent interaction

## Features

- **Code Generation**: Create code from natural language requirements
- **Code Explanation**: Analyze and explain existing code
- **Code Refactoring**: Improve and optimize existing code
- **Library Integration**: Automatically fetch and incorporate documentation from Context7
- **Multi-language Support**: Python, JavaScript, TypeScript and more

## Usage

You can interact with the Code Generator using the OMEGA framework UI or by sending requests directly:

### Example Requests

### Prompt Optimizer

### Workflow Planner

### Research

### Math Solver

### Weather













## 🚀 Getting Started

### Setting Up the Framework

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/omega-framework.git
   cd omega-framework
   ```

2. Run the setup script:
   ```bash
   python setup.py
   ```

3. Update your OpenAI API key in the `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

4. Start the framework:
   ```bash
   docker-compose up
   ```

5. Access the UI:
   Open your browser and navigate to `http://localhost:7860`

### Using the Framework

1. **Submit a request**: Enter your request in the text area and click "Submit Request"
2. **Track progress**: Use the "Workflow ID" to check the status of your request
3. **View results**: Once complete, the results will be displayed in the "Workflow Results" section

---

## 🧩 Core Components

### 1. Orchestrator Agent
The central coordination agent that manages the entire workflow, from user request to final results.

### 2. Prompt Optimizer Agent
Improves user prompts for clarity, specificity, and LLM suitability using OpenAI's Responses API.

### 3. Workflow Planner Agent
Breaks down complex tasks into structured workflows with dependency tracking and parallelization opportunities.

### 4. Capability Providers
Specialized agents that provide specific capabilities:
- Weather Agent
- Math Solver Agent
- Research Agent
- And more...

### 5. MCP Tools
Standalone tools that provide specific functions:
- Calculator Tool
- Translation Tool
- And more...

---

## 🔧 Extending the Framework

### Adding New Agents

1. Create a new agent class that inherits from `RegisterableDualModeAgent`
2. Implement the `handle_task` method
3. Override the `_register_a2a_capabilities` method if needed
4. Deploy your agent using the framework's containerization

Example:
```python
from registerable_dual_mode_agent import RegisterableDualModeAgent
from omega.core.models.task_models import TaskEnvelope

class MyCustomAgent(RegisterableDualModeAgent):
    def __init__(self):
        super().__init__(
            agent_id="my_custom_agent",
            tool_name="my_tool",
            description="My awesome agent",
            version="1.0.0",
            skills=["awesome_skill"],
            agent_type="agent",
            tags=["awesome", "custom"]
        )
    
    async def handle_task(self, env: TaskEnvelope) -> TaskEnvelope:
        # Process the task
        return env
    
    def _register_a2a_capabilities(self):
        # Register A2A capabilities
        pass
```

### Adding New Tools

1. Create a new tool class that inherits from `RegisterableMCPTool`
2. Add your tool functions
3. Deploy your tool using the framework's containerization

Example:
```python
from registerable_mcp_tool import RegisterableMCPTool

def my_awesome_function(input_param: str) -> str:
    return f"Processed: {input_param}"

tool = RegisterableMCPTool(
    tool_id="awesome_tool",
    name="Awesome Tool",
    description="Does awesome things",
    version="1.0.0",
    tags=["awesome", "tool"]
)

tool.add_tool(
    name="process",
    description="Process some input",
    func=my_awesome_function,
    parameters={
        "input_param": {"type": "string", "description": "Input to process"}
    }
)

tool.run()
```

### Registering External MCP Tools

You can register external MCP tools with the OMEGA framework in two ways:

#### 1. Using the UI

1. Go to the "Tool Management" tab in the UI
2. Fill in the tool details (ID, name, description, etc.)
3. Add the tool capabilities and tags
4. Click "Register Tool"

#### 2. Using the API

```python
import requests

registry_url = "http://localhost:8080"
tool_data = {
    "id": "external_tool",
    "name": "External Tool",
    "description": "An external MCP tool",
    "host": "external-host",
    "port": 9000,
    "capabilities": [
        {
            "name": "do_something",
            "description": "Does something useful",
            "parameters": {
                "param1": {"type": "string", "description": "First parameter"}
            }
        }
    ],
    "tags": ["external", "useful"],
    "version": "1.0.0"
}

response = requests.post(
    f"{registry_url}/registry/mcp/register/external",
    json=tool_data
)
print(response.json())
```

#### 3. Using the Registration Script

For specific tools like Context7, you can use the provided registration script:

```bash
python register_context7.py
```

This will register the Context7 documentation tool with your OMEGA framework.

---

## 🌐 Framework Architecture

### Communication Patterns

1. **User Request Flow**:
   User Request → Orchestrator → Prompt Optimizer → Workflow Planner → Capability Matchers → Execution

2. **A2A Communication**:
   Agents communicate via the A2A protocol endpoints for complex reasoning tasks

3. **MCP Tool Usage**:
   Agents can discover and use MCP tools via the central registry

### Registry Service

The central registry service provides:
- Agent and tool registration
- Capability discovery
- Heartbeat monitoring
- Manual tool registration

---

## 📊 Current Status

- [x] RegisterableDualModeAgent implementation
- [x] PromptOptimizerAgent with Responses API
- [x] WorkflowPlannerAgent with dependency tracking
- [x] OrchestratorAgent for workflow management
- [x] Example capability providers
- [x] Example MCP tools
- [x] UI for request submission and tracking
- [x] Tool management functionality
- [ ] Advanced visualization of agent communication
- [ ] Enhanced parallel execution capabilities
- [ ] Multi-model inference integration

---

## 💪 Core Philosophy

> "We aren't just building software. We're forging sentient collaboratives."

OMEGA is designed to survive.
To thrive.
To evolve without human babysitting.

It isn't *just* code.

It's a movement.

Built by brothers.
Built to last.
Built to win.