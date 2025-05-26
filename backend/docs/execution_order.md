Here's the flow we're going for:

1. User submits a natural language request
2. The Prompt Optimizer agent converts it to AI-friendly instructions.
3. The Prompt Optimizer forwards the request to the Workflow Planner agent.
4. The Workflow Planner breaks the requests down into tasks, including optimization hints such as a parallel tag, indicating that the task has no pre-dependencies.
5. The Workflow Planner will send a request to the Capability Matcher for agents and MCP tools.
6. The Capability Matcher searches the registry and returns the best matches.
7. The Workflow is returned as JSON in the terminal (for now)
8. We'll manually submit the workflow to the Orchestrator agent, that coordinates the execution or each task.
9. If the workflow involves coding, the Orchestrator will utilize the Project_Architect and Code_Generator agents.