D:\Repos\o.m.e.g.a/
├── Directory_Structure.md
├── README.md
├── backend
│   D:\Repos\o.m.e.g.a\backend/
│   ├── .python-version
│   ├── __init__.py
│   ├── data
│   │   D:\Repos\o.m.e.g.a\backend\data/
│   ├── docker-compose.yml
│   ├── docs
│   │   D:\Repos\o.m.e.g.a\backend\docs/
│   │   └── agent-tests.md
│   ├── logs
│   │   D:\Repos\o.m.e.g.a\backend\logs/
│   ├── main.py
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── setup.py
│   ├── src
│   │   D:\Repos\o.m.e.g.a\backend\src/
│   │   └── omega
│   │       D:\Repos\o.m.e.g.a\backend\src\omega/
│   │       ├── __init__.py
│   │       ├── agents
│   │       │   D:\Repos\o.m.e.g.a\backend\src\omega\agents/
│   │       │   ├── __init__.py
│   │       │   ├── capability_matcher
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\agents\capability_matcher/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── agent.py
│   │       │   │   └── requirements.txt
│   │       │   ├── code_generator
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\agents\code_generator/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── agent.py
│   │       │   │   └── requirements.txt
│   │       │   ├── devops_discovery
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\agents\devops_discovery/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── agent.py
│   │       │   │   └── requirements.txt
│   │       │   ├── math_solver
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\agents\math_solver/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── agent.py
│   │       │   │   └── requirements.txt
│   │       │   ├── migration_assistant
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\agents\migration_assistant/
│   │       │   │   └── agent.py
│   │       │   ├── moderator
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\agents\moderator/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── agent.py
│   │       │   │   └── requirements.txt
│   │       │   ├── orchestrator
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\agents\orchestrator/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── agent.py
│   │       │   │   └── requirements.txt
│   │       │   ├── project_architect
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\agents\project_architect/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── agent.py
│   │       │   │   ├── agent.py.backup
│   │       │   │   └── requirements.txt
│   │       │   ├── prompt_optimizer
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\agents\prompt_optimizer/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── agent.py
│   │       │   │   └── requirements.txt
│   │       │   ├── research
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\agents\research/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── agent.py
│   │       │   │   └── requirements.txt
│   │       │   ├── weather
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\agents\weather/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── agent.py
│   │       │   │   └── requirements.txt
│   │       │   └── workflow_planner
│   │       │       D:\Repos\o.m.e.g.a\backend\src\omega\agents\workflow_planner/
│   │       │       ├── Dockerfile
│   │       │       ├── agent.py
│   │       │       └── requirements.txt
│   │       ├── cli
│   │       │   D:\Repos\o.m.e.g.a\backend\src\omega\cli/
│   │       │   └── __init__.py
│   │       ├── core
│   │       │   D:\Repos\o.m.e.g.a\backend\src\omega\core/
│   │       │   ├── __init__.py
│   │       │   ├── agent_discovery.py
│   │       │   ├── communication
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\core\communication/
│   │       │   │   ├── bus.py
│   │       │   │   ├── connection_manager.py
│   │       │   │   ├── redis_client.py
│   │       │   │   └── websocket_server.py
│   │       │   ├── config.py
│   │       │   ├── dual_mode_agent.py
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
│   │       │   │   ├── message.py
│   │       │   │   ├── reasoning.py
│   │       │   │   ├── system.py
│   │       │   │   ├── task_models.py
│   │       │   │   ├── tool.py
│   │       │   │   └── websocket.py
│   │       │   ├── orchestrator
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\core\orchestrator/
│   │       │   │   ├── Dockerfile
│   │       │   │   └── requirements.txt
│   │       │   ├── registerable_dual_mode_agent.py
│   │       │   ├── registerable_mcp_tool.py
│   │       │   ├── schemas
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\core\schemas/
│   │       │   │   ├── agent_feedback.json
│   │       │   │   ├── message_envelope.json
│   │       │   │   ├── task_result.json
│   │       │   │   └── workflow_schema.json
│   │       │   ├── schemas.py
│   │       │   └── utils
│   │       │       D:\Repos\o.m.e.g.a\backend\src\omega\core\utils/
│   │       │       ├── __init__.py
│   │       │       ├── event_schema.py
│   │       │       ├── mcp_tool_builder.py
│   │       │       ├── port_manger.py
│   │       │       ├── redis_listener.py
│   │       │       ├── redis_watcher.py
│   │       │       ├── registry_helpers.py
│   │       │       └── task_utils.py
│   │       ├── services
│   │       │   D:\Repos\o.m.e.g.a\backend\src\omega\services/
│   │       │   ├── agent_registry
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\services\agent_registry/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── requirements.txt
│   │       │   │   └── service.py
│   │       │   ├── collaborative_workflow_generator
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\services\collaborative_workflow_generator/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── requirements.txt
│   │       │   │   └── service.py
│   │       │   ├── mcp_registry
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\services\mcp_registry/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── requirements.txt
│   │       │   │   └── service.py
│   │       │   └── template_discovery
│   │       │       D:\Repos\o.m.e.g.a\backend\src\omega\services\template_discovery/
│   │       │       ├── Dockerfile
│   │       │       ├── requirements.txt
│   │       │       └── service.py
│   │       ├── tools
│   │       │   D:\Repos\o.m.e.g.a\backend\src\omega\tools/
│   │       │   ├── __init__.py
│   │       │   ├── calculator
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\tools\calculator/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── requirements.txt
│   │       │   │   └── tool.py
│   │       │   ├── code_analyzer
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\tools\code_analyzer/
│   │       │   │   ├── README.md
│   │       │   │   ├── dockerfile.txt
│   │       │   │   ├── documentation.md
│   │       │   │   ├── requirements.txt
│   │       │   │   ├── test_dependency_resolver.py
│   │       │   │   └── tool.py
│   │       │   ├── context7
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\tools\context7/
│   │       │   │   └── Dockerfile
│   │       │   ├── execute_sql
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\tools\execute_sql/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── requirements.txt
│   │       │   │   └── tool.py
│   │       │   ├── nlp_to_sql
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\tools\nlp_to_sql/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── requirements.txt
│   │       │   │   └── tool.py
│   │       │   ├── summarize_text
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\tools\summarize_text/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── requirements.txt
│   │       │   │   └── tool.py
│   │       │   ├── translate_text
│   │       │   │   D:\Repos\o.m.e.g.a\backend\src\omega\tools\translate_text/
│   │       │   │   ├── Dockerfile
│   │       │   │   ├── requirements.txt
│   │       │   │   └── tool.py
│   │       │   └── web_search
│   │       │       D:\Repos\o.m.e.g.a\backend\src\omega\tools\web_search/
│   │       │       ├── Dockerfile
│   │       │       ├── requirements.txt
│   │       │       └── tool.py
│   │       ├── ui
│   │       │   D:\Repos\o.m.e.g.a\backend\src\omega\ui/
│   │       │   ├── Dockerfile
│   │       │   ├── app.py
│   │       │   └── requirements.txt
│   │       └── workflows
│   │           D:\Repos\o.m.e.g.a\backend\src\omega\workflows/
│   │           ├── template_repository.py
│   │           ├── templates
│   │           │   D:\Repos\o.m.e.g.a\backend\src\omega\workflows\templates/
│   │           │   ├── README.md
│   │           │   └── database_driven_website.yaml
│   │           ├── workflow_template.py
│   │           └── workflow_templates.py
│   ├── tests
│   │   D:\Repos\o.m.e.g.a\backend\tests/
│   │   ├── __init__.py
│   │   ├── agent_inbox_test.py
│   │   ├── dual_mode_base.py
│   │   ├── e2e_test_orchestrator.py
│   │   ├── e2e_trigger.py
│   │   ├── integration
│   │   │   D:\Repos\o.m.e.g.a\backend\tests\integration/
│   │   │   └── __init__.py
│   │   ├── redis_test.py
│   │   ├── run_finance_agent.py
│   │   ├── run_research_agent.py
│   │   ├── run_triage_agent_flow.py
│   │   ├── temp.py
│   │   ├── test_capability_matching.py
│   │   ├── test_migration_assistant_agent.py
│   │   └── unit
│   │       D:\Repos\o.m.e.g.a\backend\tests\unit/
│   │       └── __init__.py
├── dev_ops
│   D:\Repos\o.m.e.g.a\dev_ops/
│   └── github_workflows_ci.yaml
├── docs
│   D:\Repos\o.m.e.g.a\docs/
│   ├── AI Code Migration Platform Backend Implementation Directives.md
│   ├── bootstrap.md
│   ├── docker-containers.md
│   ├── dual_mode_agent_readme.md
│   ├── instructions.txt
│   ├── mcp-integration-guide.md
│   ├── omega-next-steps.md
│   ├── omega_progress_report.md
│   ├── tool_builder_pattern.md
│   ├── write_code (1).zip
│   └── write_code.zip
├── frontend
│   D:\Repos\o.m.e.g.a\frontend/
│   ├── OMEGA UI_README.md
│   ├── components.json
│   ├── next.config.js
│   ├── omega-workflow-integration.md
│   ├── package-lock.json
│   ├── package.json
│   ├── postcss.config.js
│   ├── public
│   │   D:\Repos\o.m.e.g.a\frontend\public/
│   │   ├── icons
│   │   │   D:\Repos\o.m.e.g.a\frontend\public\icons/
│   │   └── images
│   │       D:\Repos\o.m.e.g.a\frontend\public\images/
│   ├── scripts
│   │   D:\Repos\o.m.e.g.a\frontend\scripts/
│   │   └── setup-env.js
│   ├── setup.ps1
│   ├── src
│   │   D:\Repos\o.m.e.g.a\frontend\src/
│   │   ├── app
│   │   │   D:\Repos\o.m.e.g.a\frontend\src\app/
│   │   │   ├── agents
│   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\agents/
│   │   │   │   ├── [id]
│   │   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\agents\[id]/
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── create
│   │   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\agents\create/
│   │   │   │   │   └── page.tsx
│   │   │   │   └── page.tsx
│   │   │   ├── api
│   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\api/
│   │   │   │   ├── agents
│   │   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\api\agents/
│   │   │   │   │   ├── [id]
│   │   │   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\api\agents\[id]/
│   │   │   │   │   │   ├── route.ts
│   │   │   │   │   │   ├── start
│   │   │   │   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\api\agents\[id]\start/
│   │   │   │   │   │   │   └── route.ts
│   │   │   │   │   │   ├── stop
│   │   │   │   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\api\agents\[id]\stop/
│   │   │   │   │   │   │   └── route.ts
│   │   │   │   │   │   └── tasks
│   │   │   │   │   │       D:\Repos\o.m.e.g.a\frontend\src\app\api\agents\[id]\tasks/
│   │   │   │   │   │       └── route.ts
│   │   │   │   │   └── route.ts
│   │   │   │   ├── tools
│   │   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\api\tools/
│   │   │   │   │   ├── [id]
│   │   │   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\api\tools\[id]/
│   │   │   │   │   │   └── route.ts
│   │   │   │   │   ├── call
│   │   │   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\api\tools\call/
│   │   │   │   │   │   └── route.ts
│   │   │   │   │   └── route.ts
│   │   │   │   ├── workflow-executions
│   │   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\api\workflow-executions/
│   │   │   │   │   └── [id]
│   │   │   │   │       D:\Repos\o.m.e.g.a\frontend\src\app\api\workflow-executions\[id]/
│   │   │   │   │       └── route.ts
│   │   │   │   ├── workflows
│   │   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\api\workflows/
│   │   │   │   │   ├── [id]
│   │   │   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\api\workflows\[id]/
│   │   │   │   │   │   └── execute
│   │   │   │   │   │       D:\Repos\o.m.e.g.a\frontend\src\app\api\workflows\[id]\execute/
│   │   │   │   │   │       └── route.ts
│   │   │   │   │   └── route.ts
│   │   │   │   └── ws
│   │   │   │       D:\Repos\o.m.e.g.a\frontend\src\app\api\ws/
│   │   │   │       └── workflows
│   │   │   │           D:\Repos\o.m.e.g.a\frontend\src\app\api\ws\workflows/
│   │   │   │           └── executions
│   │   │   │               D:\Repos\o.m.e.g.a\frontend\src\app\api\ws\workflows\executions/
│   │   │   │               └── [id]
│   │   │   │                   D:\Repos\o.m.e.g.a\frontend\src\app\api\ws\workflows\executions\[id]/
│   │   │   │                   └── route.ts
│   │   │   ├── dashboard
│   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\dashboard/
│   │   │   │   ├── layout.tsx
│   │   │   │   └── page.tsx
│   │   │   ├── globals.css
│   │   │   ├── layout.tsx
│   │   │   ├── login
│   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\login/
│   │   │   ├── page.tsx
│   │   │   ├── register
│   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\register/
│   │   │   ├── settings
│   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\settings/
│   │   │   │   ├── appearance
│   │   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\settings\appearance/
│   │   │   │   └── profile
│   │   │   │       D:\Repos\o.m.e.g.a\frontend\src\app\settings\profile/
│   │   │   ├── tools
│   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\tools/
│   │   │   │   ├── [id]
│   │   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\tools\[id]/
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── create
│   │   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\app\tools\create/
│   │   │   │   │   └── page.tsx
│   │   │   │   └── page.tsx
│   │   │   └── workflows
│   │   │       D:\Repos\o.m.e.g.a\frontend\src\app\workflows/
│   │   │       ├── [id]
│   │   │       │   D:\Repos\o.m.e.g.a\frontend\src\app\workflows\[id]/
│   │   │       │   └── page.tsx
│   │   │       ├── create
│   │   │       │   D:\Repos\o.m.e.g.a\frontend\src\app\workflows\create/
│   │   │       │   └── page.tsx
│   │   │       └── page.tsx
│   │   ├── components
│   │   │   D:\Repos\o.m.e.g.a\frontend\src\components/
│   │   │   ├── agents
│   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\components\agents/
│   │   │   │   ├── agent-create.tsx
│   │   │   │   ├── agent-detail.tsx
│   │   │   │   ├── agent-list.tsx
│   │   │   │   └── page.tsx
│   │   │   ├── dashboard
│   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\components\dashboard/
│   │   │   ├── layout
│   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\components\layout/
│   │   │   │   ├── sidebar.tsx
│   │   │   │   └── theme-toggle.tsx
│   │   │   ├── tools
│   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\components\tools/
│   │   │   │   ├── tool-caller.tsx
│   │   │   │   ├── tool-detail.tsx
│   │   │   │   ├── tool-list.tsx
│   │   │   │   ├── tool-register.tsx
│   │   │   │   └── tool-tabs
│   │   │   │       D:\Repos\o.m.e.g.a\frontend\src\components\tools\tool-tabs/
│   │   │   │       ├── capabilities-tab.tsx
│   │   │   │       ├── index.ts
│   │   │   │       ├── overview-tab.tsx
│   │   │   │       ├── settings-tab.tsx
│   │   │   │       └── usage-tab.tsx
│   │   │   ├── ui
│   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\components\ui/
│   │   │   │   ├── accordion.tsx
│   │   │   │   ├── alert-dialog.tsx
│   │   │   │   ├── alert.tsx
│   │   │   │   ├── badge.tsx
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── checkbox.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   ├── dropdown-menu.tsx
│   │   │   │   ├── form.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── label.tsx
│   │   │   │   ├── scroll-area.tsx
│   │   │   │   ├── select.tsx
│   │   │   │   ├── skeleton.tsx
│   │   │   │   ├── tabs.tsx
│   │   │   │   ├── textarea.tsx
│   │   │   │   └── tooltip.tsx
│   │   │   ├── visualizations
│   │   │   │   D:\Repos\o.m.e.g.a\frontend\src\components\visualizations/
│   │   │   │   ├── agent-network-graph.tsx
│   │   │   │   └── network-graph.tsx
│   │   │   └── workflows
│   │   │       D:\Repos\o.m.e.g.a\frontend\src\components\workflows/
│   │   │       ├── index.ts
│   │   │       ├── nodes
│   │   │       │   D:\Repos\o.m.e.g.a\frontend\src\components\workflows\nodes/
│   │   │       │   ├── agent-node.tsx
│   │   │       │   ├── base-node.tsx
│   │   │       │   ├── index.ts
│   │   │       │   ├── tool-node.tsx
│   │   │       │   └── trigger-node.tsx
│   │   │       ├── workflow-builder.tsx
│   │   │       ├── workflow-create-form.tsx
│   │   │       ├── workflow-detail.tsx
│   │   │       └── workflow-list.tsx
│   │   ├── hooks
│   │   │   D:\Repos\o.m.e.g.a\frontend\src\hooks/
│   │   │   ├── use-mcp.ts
│   │   │   ├── use-workflow-execution.ts
│   │   │   └── use-workflows.ts
│   │   ├── providers
│   │   │   D:\Repos\o.m.e.g.a\frontend\src\providers/
│   │   │   ├── agent-provider.tsx
│   │   │   ├── query-provider.tsx
│   │   │   └── theme-provider.tsx
│   │   └── types
│   │       D:\Repos\o.m.e.g.a\frontend\src\types/
│   │       └── index.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── types-and-workflow-integration-summary.md
│   ├── websocket-integration-summary.md
│   └── workflow-builder-integration-summary.md
├── index.html
├── keys
│   D:\Repos\o.m.e.g.a\keys/
│   ├── claude
│   └── claude.pub
├── package-lock.json
├── package.json
└── temp.py
