# tests/test_migration_assistant_agent.py
import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch
from omega.utils.db import MongoDBClient
from omega.core.models.migration_models import MigrationPlan
from omega.agents.registerable_dual_mode_agent import RegisterableDualModeAgent
from code_analyzer_tool import analyze_repo  # For mock analysis

# Sample analysis from Claude's Flask repo
SAMPLE_ANALYSIS = {
    "analysis_id": str(uuid4()),
    "file_tree": {"src": {"app.py": {}, "db.py": {}, "utils.py": {}}},
    "components": [
        {"type": "file", "name": "app.py", "path": "src/app.py"},
        {"type": "function", "name": "user_detail", "path": "src/app.py:user_detail"},
        {"type": "function", "name": "get_user", "path": "src/db.py:get_user"}
    ],
    "dependencies": [
        {"source": "app.py:user_detail", "target": "db.py:get_user"}
    ]
}

@pytest.fixture
async def db_client():
    client = MongoDBClient("mongodb://localhost:27017", "omega")
    yield client
    await client.db["analyses"].drop()

@pytest.fixture
def agent():
    return RegisterableDualModeAgent(
        agent_id="MigrationAssistantAgent",
        tool_name="migration_assistant",
        description="Generates microservice migration plans",
        version="1.0.0",
        capabilities=[
            AgentCapability(
                name="migration_suggestions",
                description="Suggests microservice boundaries",
                parameters={"analysis_id": "string", "user_input": "string"},
                output_type="MigrationPlan"
            )
        ],
        skills=["migration", "microservices"],
        agent_type="dual",
        tags=["migration"]
    )

@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    @app.post("/tools/migration_assistant/get_initial_suggestions")
    async def get_suggestions(input: SuggestionsInput):
        agent = RegisterableDualModeAgent(
            agent_id="MigrationAssistantAgent",
            tool_name="migration_assistant"
        )
        analysis = await agent.db.find_one("analyses", {"analysis_id": str(input.analysis_id)})
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        plan = await agent._generate_migration_plan(analysis, "")
        return plan.dict()
    return TestClient(app)

class SuggestionsInput:
    analysis_id: UUID

@pytest.mark.asyncio
async def test_chat_flow(db_client, agent):
    # Insert sample analysis
    await db_client.insert_one("analyses", SAMPLE_ANALYSIS)
    
    # Simulate chat task
    env = {
        "task": {
            "task_id": str(uuid4()),
            "payload": {
                "analysis_id": SAMPLE_ANALYSIS["analysis_id"],
                "user_input": "Split into microservices, target GCP, 500 users"
            }
        },
        "header": {}
    }
    result = await agent.handle_task(env)
    
    assert result.header.status == TaskStatus.COMPLETED
    plan = MigrationPlan.parse_obj(result.task.payload["migration_plan"])
    assert len(plan.suggestions) > 0
    assert plan.target_platform == "GCP"
    assert plan.estimated_users == 500

@pytest.mark.asyncio
async def test_mcp_endpoint(client, db_client):
    # Insert sample analysis
    await db_client.insert_one("analyses", SAMPLE_ANALYSIS)
    
    response = client.post(
        "/tools/migration_assistant/get_initial_suggestions",
        json={"analysis_id": SAMPLE_ANALYSIS["analysis_id"]}
    )
    assert response.status_code == 200
    plan = MigrationPlan.parse_obj(response.json())
    assert len(plan.suggestions) > 0
    assert plan.target_platform == "AWS"  # Default for empty user_input

@pytest.mark.asyncio
async def test_invalid_analysis_id(db_client, agent):
    env = {
        "task": {
            "task_id": str(uuid4()),
            "payload": {
                "analysis_id": "invalid-uuid",
                "user_input": "Split into microservices"
            }
        },
        "header": {}
    }
    result = await agent.handle_task(env)
    
    assert result.header.status == TaskStatus.FAILED
    assert "No analysis found" in result.task.payload["error"]

@pytest.mark.asyncio
async def test_empty_components(db_client, agent):
    empty_analysis = {
        "analysis_id": str(uuid4()),
        "file_tree": {},
        "components": [],
        "dependencies": []
    }
    await db_client.insert_one("analyses", empty_analysis)
    
    env = {
        "task": {
            "task_id": str(uuid4()),
            "payload": {
                "analysis_id": empty_analysis["analysis_id"],
                "user_input": "Split into microservices"
            }
        },
        "header": {}
    }
    result = await agent.handle_task(env)
    
    assert result.header.status == TaskStatus.COMPLETED
    plan = MigrationPlan.parse_obj(result.task.payload["migration_plan"])
    assert len(plan.suggestions) == 0  # No components, no suggestions

@pytest.mark.asyncio
async def test_long_user_input(db_client, agent):
    await db_client.insert_one("analyses", SAMPLE_ANALYSIS)
    
    long_input = "x" * 501
    env = {
        "task": {
            "task_id": str(uuid4()),
            "payload": {
                "analysis_id": SAMPLE_ANALYSIS["analysis_id"],
                "user_input": long_input
            }
        },
        "header": {}
    }
    result = await agent.handle_task(env)
    
    assert result.header.status == TaskStatus.FAILED
    assert "exceeds 500 characters" in result.task.payload["error"]

@pytest.mark.asyncio
async def test_redis_emission(db_client, agent):
    await db_client.insert_one("analyses", SAMPLE_ANALYSIS)
    
    with patch.object(agent.redis_client, "publish", new=AsyncMock()) as mock_publish:
        env = {
            "task": {
                "task_id": str(uuid4()),
                "payload": {
                    "analysis_id": SAMPLE_ANALYSIS["analysis_id"],
                    "user_input": "Split into microservices"
                }
            },
            "header": {}
        }
        result = await agent.handle_task(env)
        
        assert mock_publish.called
        call_args = mock_publish.call_args[0]
        assert call_args[0] == "task.events"
        event = json.loads(call_args[1])
        assert event["task_id"] == env["task"]["task_id"]
        assert event["status"] == "COMPLETED"