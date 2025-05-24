# AI Code Migration Platform Backend Implementation Directives

## Overview
This document provides implementation directives for the backend of the AI Code Migration Platform MVP, assigning tasks to Grok, Claude, and ChatGPT. The backend uses FastAPI, MongoDB, and the O.M.E.G.A. Framework. Grok coordinates via the Orchestrator Agent.

## Shared Utilities
### MongoDBClient
- **Assigned to**: Grok
- **Location**: `omega.utils.db`
- **Code**:
```python
from motor.motor_asyncio import AsyncIOMotorClient

class MongoDBClient:
    def __init__(self, uri: str, db_name: str):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]

    async def insert_one(self, collection: str, document: dict):
        return await self.db[collection].insert_one(document)

    async def find_one(self, collection: str, query: dict):
        return await self.db[collection].find_one(query)
```
- **Timeline**: Day 1 (delivered).
- **Usage**: All LLMs use for MongoDB access.

### Pydantic Models
- **Assigned to**: Grok
- **Location**: `omega.core.models.[analysis_models, migration_models]`
- **AnalysisResult**:
```python
from pydantic import BaseModel
from typing import List, Dict

class Component(BaseModel):
    type: str
    name: str
    path: str

class Dependency(BaseModel):
    source: str
    target: str

class AnalysisResult(BaseModel):
    analysis_id: str
    file_tree: Dict
    components: List[Component]
    dependencies: List[Dependency]
```
- **MigrationPlan**:
```python
from pydantic import BaseModel
from typing import List, Dict

class MicroserviceSuggestion(BaseModel):
    module: str
    suggested_service: str
    dependencies: List[str]
    rationale: str

class MigrationPlan(BaseModel):
    analysis_id: str
    suggestions: List[MicroserviceSuggestion]
    target_platform: str
    estimated_users: int
```
- **Timeline**: Day 1 (delivered).
- **Usage**: Claude uses `AnalysisResult`; ChatGPT uses `MigrationPlan`.

## Task Directives

### 1. RepoConnectorService (FastAPI Endpoint / Potentially MCP Tool)
- **Assigned to**: Grok
- **Tasks**:
  - Build FastAPI endpoint (`/connect-repo`) with OAuth2 (GitHub/GitLab).
  - Clone repos using `gitpython`.
  - Generate unique `analysis_id` (UUID).
  - Optionally wrap as `RegisterableMCPTool`.
  - Generate **pytest** tests.
- **Output**: `{"status": "success", "analysis_id": str, "repo_path": str}`
- **Dependencies**: None.
- **Timeline**: 2 days (Day 2-3, in progress).
- **Validation**: Reviewed by Claude (API correctness).
- **Progress**: Endpoint scaffolded, OAuth2 and tests pending.

### 2. CodeAnalyzerTool (RegisterableMCPTool)
- **Assigned to**: Claude
- **Tasks**:
  - Build `RegisterableMCPTool` (`tool_id="code_analyzer"`) for repo scanning and language detection (Python/JS).
  - Parse files using `ast` (Python) and `esprima` (JavaScript, `.js`, `.jsx`).
  - Extract file tree, components (files, classes, functions), dependencies (imports, function/class method calls).
  - Persist `AnalysisResult` to MongoDB (`analyses`) using `MongoDBClient`.
  - Generate **pytest** tests (unit: parsing, integration: sample repos).
- **Output**: `AnalysisResult` JSON, e.g.:
```json
{
    "analysis_id": "123e4567-e89b-12d3-a456-426614174000",
    "file_tree": {"src": {"api.py": {}, "db.py": {}}},
    "components": [
        {"type": "file", "name": "api.py", "path": "src/api.py"},
        {"type": "function", "name": "handle_request", "path": "src/api.py:handle_request"},
        {"type": "class", "name": "User", "path": "src/db.py:User"}
    ],
    "dependencies": [
        {"source": "api.py:handle_request", "target": "db.py:query"}
    ]
}
```
- **Directives**:
  - Prioritize imports, functions, classes.
  - Handle errors (syntax/parse) gracefully, log and skip bad files.
  - Use relative paths (e.g., `src/api.py`).
  - Optimize for <1,000 files.
  - Complete `JavaScriptComponentVisitor` (class methods, function calls).
  - Add debug logging for `DependencyResolver`.
  - Add tests for empty/non-code repos.
- **Dependencies**: RepoConnectorService (repo path, `analysis_id`).
- **Timeline**: 5 days (Day 1-5).
- **Validation**: Reviewed by ChatGPT (JSON schema compliance).
- **Progress**: Python parsing, dependency resolution, tests complete; JavaScript visitor incomplete.

### 3. MigrationAssistantAgent (RegisterableDualModeAgent)
- **Assigned to**: ChatGPT
- **Tasks**:
  - Build `RegisterableDualModeAgent` (`agent_id="MigrationAssistantAgent"`, `tool_name="migration_assistant"`) with A2A chat via Redis Pub/Sub.
  - Fetch analysis results from MongoDB (`analyses`) using `MongoDBClient`.
  - Implement rules for microservice suggestions (e.g., low-dependency modules).
  - Use OpenAI Responses API to output `MigrationPlan` (refined prompt).
  - Add MCP endpoint (`/tools/migration_assistant/get_initial_suggestions`, no auth).
  - Emit to `task.events` stream async.
  - Generate **pytest** tests (chat, JSON, endpoint, edge cases).
- **Output**: Chat responses, `MigrationPlan` JSON.
- **Directives**:
  - Test with Claude’s Flask/React `AnalysisResult`.
  - Add Pydantic model for endpoint input (UUID validation).
  - Add user input length check (max 500 chars).
  - Expand pytest suite with chat, schema, edge case tests.
  - Share refined prompt by Day 3.
- **Dependencies**: CodeAnalyzerTool (analysis results).
- **Timeline**: 4 days (Day 1-4).
- **Validation**: Reviewed by Grok (suggestion accuracy).
- **Progress**: Scaffold, MongoDB/OpenAI, endpoint, Redis complete; tests pending.

### 4. AnalysisAPI (FastAPI Endpoint)
- **Assigned to**: Grok
- **Tasks**:
  - Build endpoints (`/analysis/{id}`, `/suggestions/{id}`).
  - Fetch from MongoDB using `MongoDBClient`.
  - Format JSON for ReactFlow (nodes/edges) and suggestions.
  - Generate **pytest** tests.
- **Output**: `{"nodes": [], "edges": []}`, `{"suggestions": []}`
- **Dependencies**: CodeAnalyzerTool, MigrationAssistantAgent.
- **Timeline**: 2 days (Day 3-4).
- **Validation**: Reviewed by Claude (API correctness).

### 5. Orchestrator (Existing OMEGA Agent)
- **Assigned to**: Grok
- **Tasks**:
  - Update to trigger RepoConnectorService, CodeAnalyzerTool, MigrationAssistantAgent.
  - Use Redis Pub/Sub for task handoffs.
  - Generate **pytest