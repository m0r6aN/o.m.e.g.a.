D:\Repos\o.m.e.g.a/
├── Directory_Structure.md
├── README.md
├── a2a-workflow-diagram.svg
├── backend
│   D:\Repos\o.m.e.g.a\backend/
│   ├── .python-version
│   ├── __init__.py
│   ├── docker-compose.yml
│   ├── main.py
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── src
│   │   D:\Repos\o.m.e.g.a\backend\src/
│   │   └── omega
│   │       D:\Repos\o.m.e.g.a\backend\src\omega/
│   │       ├── __init__.py
│   │       ├── agents
│   │       │   D:\Repos\o.m.e.g.a\backend\src\omega\agents/
│   │       │   ├── __init__.py
│   │       │   ├── agent_base.py
│   │       │   ├── capability_matcher.py
│   │       │   ├── coder.py
│   │       │   ├── content.py
│   │       │   ├── echo.py
│   │       │   ├── instructions.txt
│   │       │   ├── orchestrator.py
│   │       │   ├── prompt_optimizer.py
│   │       │   ├── repository.py
│   │       │   ├── research.py
│   │       │   ├── task.py
│   │       │   ├── workflow_composer.py
│   │       │   └── workflow_planner_agent.py
│   │       ├── cli
│   │       │   D:\Repos\o.m.e.g.a\backend\src\omega\cli/
│   │       ├── core
│   │       │   D:\Repos\o.m.e.g.a\backend\src\omega\core/
│   │       │   ├── __init__.py
│   │       │   ├── communication
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\core\communication/
│   │       │   │   ├── bus.py
│   │       │   │   ├── connection_manager.py
│   │       │   │   ├── redis_client.py
│   │       │   │   └── websocket_server.py
│   │       │   ├── config.py
│   │       │   ├── factories
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\core\factories/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── factories.py
│   │       │   │   ├── message_factory.py
│   │       │   │   ├── reasoning.py
│   │       │   │   ├── task_factory.py
│   │       │   │   ├── task_result_factory.py
│   │       │   │   └── tool_cache.py
│   │       │   ├── logging.py
│   │       │   ├── models
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\core\models/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── capabilities.py
│   │       │   │   └── models.py
│   │       │   ├── orchestrator
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\core\orchestrator/
│   │       │   │   ├── Dockerfile
│   │       │   │   └── requirements.txt
│   │       │   ├── schemas
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\core\schemas/
│   │       │   │   ├── agent_feedback.json
│   │       │   │   ├── task_result.json
│   │       │   │   └── workflow_schema.json
│   │       │   ├── schemas.py
│   │       │   └── utils
│   │       │       D:\Repos\o.m.e.g.a\backend\src\omega\core\utils/
│   │       │       ├── __init__.py
│   │       │       ├── event_schema.py
│   │       │       ├── redis_listener.py
│   │       │       ├── redis_watcher.py
│   │       │       └── task_utils.py
│   │       ├── registry
│   │       │   D:\Repos\o.m.e.g.a\backend\src\omega\registry/
│   │       │   ├── agent_discovery_protocol.py
│   │       │   ├── api.py
│   │       │   ├── heartbeat.py
│   │       │   ├── storage.py
│   │       │   └── tool_registry.py
│   │       ├── tools
│   │       │   D:\Repos\o.m.e.g.a\backend\src\omega\tools/
│   │       │   ├── __init__.py
│   │       │   ├── base.py
│   │       │   ├── execute_sql.py
│   │       │   ├── nlp_to_sql.py
│   │       │   ├── summarize_text.py
│   │       │   ├── translate.py
│   │       │   └── web_search.py
│   │       └── workflows
│   │           D:\Repos\o.m.e.g.a\backend\src\omega\workflows/
│   ├── tests
│   │   D:\Repos\o.m.e.g.a\backend\tests/
│   │   ├── __init__.py
│   │   ├── run_finance_agent.py
│   │   ├── run_research_agent.py
│   │   └── run_triage_agent_flow.py
├── docker
│   D:\Repos\o.m.e.g.a\docker/
│   ├── agent.Dockerfile
│   ├── orchestrator.Dockerfile
│   └── tool.Dockerfile
├── docs
│   D:\Repos\o.m.e.g.a\docs/
├── infra
│   D:\Repos\o.m.e.g.a\infra/
