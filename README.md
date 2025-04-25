# O.M.E.G.A. – Orchestrated Multi-Expert Gen Agents

**O.M.E.G.A.** is a modular, agent-based framework designed to orchestrate multi-agent reasoning workflows. Leveraging Redis streams for task distribution, Pydantic models for structured data, and OpenAI's Responses API for structured outputs, O.M.E.G.A. integrates the Model Context Protocol (MCP) and Agent2Agent (A2A) protocols to enable seamless agent and tool interoperability.

---

## 🚀 Features

- **Dynamic Task Routing** Tasks are routed to agents based on required capabilities, ensuring optimal handlin.
- **Structured Task Models** Utilizes Pydantic models (`TaskCore`, `TaskHeader`, `TaskEnvelope`) for clear and consistent task definition.
- **Agent Communication via Redis** Agents communicate through Redis streams, allowing for scalable and decoupled interaction.
- **OpenAI Responses API Integration** Structured outputs from OpenAI models are seamlessly integrated using defined schema.
- **MCP and A2A Protocol Support** Combines MCP for tool integration and A2A for agent-to-agent communication, enabling a flexible and interoperable agent ecosyste.
- **Provider and Model Agnostic** Agents are designed to work with various models and providers, ensuring flexibility and adaptabilit.

---

## 🛠️ Installation

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/yourusername/omega.git
    cd omega
    ```

2. **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3. **Set Environment Variables**:

    Ensure the following environment variables are set:

    - `REDIS_HOST`: Hostname for Redis (default: `localhost`)
    - `REDIS_PORT`: Port for Redis (default: `6379`)
    - `OPENAI_API_KEY`: Your OpenAI API key

4. **Run the Agents**:

    Start the agents using the provided scripts or your preferred process manager.

---

## 📦 Usage

To dispatch a new tsk:

```python
from redis.asyncio import Redis
from omega.core.models.task_models import TaskEnvelope, TaskCore, TaskHeader

env = TaskEnvelope(
    header=TaskHeader(conversation_id="conv-001", sender="frontend"),
    task=TaskCore(
        name="Summarize Article",
        description="Summarize the article at https://example.com/article",
        category="summarization",
        required_capabilities=["text_summarization"],
        payload={"url": "https://example.com/article"}
    )
)

redis = Redis(host="localhost", port=6379, decode_responses=True)
await redis.xadd("task.to_match", {"payload": env.model_dump_json()})
``

This task will be picked up by the `CapabilityMatcherAgent`, routed to the appropriate agent based on capabilities, and processed accordingly.

---

## Architecture Overview

- **Agent**: Each agent listens to its own Redis stream (`<agent_id>.inbox`) and processes tasks assigned t it.
- **Capability Matche**: Evaluates task requirements and assigns them to agents with matching capabiliies.
- **Task Model**: Structured using Pydantic for validation and claity.
- **Redis Stream**: Facilitate communication between agents and componnts.
- **OpenAI Responses AP**: Generates structured outputs based on defined schmas.
- **MCP Integratio**: Agents can expose themselves as tools via MCP, allowing other agents to utilize their capabilities seamlesly.
- **A2A Protoco**: Enables direct agent-to-agent communication, fostering collaboration and coordination among agnts.

---

## 🔮 Future Functionality

- **Interactive Dashboard**
  - Submit requests through a chat inteface.
  - Monitor live agent discussions and collaboraions.
  - Add and deploy tools (MCP servers) dynamially.
  - Participate in multi-agent collaboraions.

- **BYOM (Bring Your Own Model)**
  - Integrate custom models for training, benchmarking, and testing within the O.M.E.G.A. ecosstem.

---

## Contribting

Contributions are welcome! Please fork the repository and submit a pull request. For major changes, open an issue first to discuss yourideas.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Let me know if you need assistance with any other part of the project! 