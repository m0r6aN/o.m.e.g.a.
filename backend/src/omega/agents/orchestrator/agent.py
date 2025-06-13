# /omega/agents/orchestrator/agent.py
"""
OMEGA Orchestrator Agent V2.0 - The Central Command 🚀
Built on the EnhancedBaseAgent foundation for enterprise-grade operation.

This is the Tony Stark of our agent constellation - the strategic mastermind
that coordinates all other agents to achieve complex objectives.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from omega.core.agents.enhanced_base_agent import EnhancedBaseAgent
from omega.core.models.task_models import TaskEnvelope, TaskStatus, Task
from omega.core.agent_discovery import AgentCapability
from omega.core.utils.llm_adapter import LLMAdapter

class OrchestratorAgent(EnhancedBaseAgent):
    """
    The Orchestrator Agent - Central Command for OMEGA operations.
    
    Responsibilities:
    - Workflow decomposition and planning
    - Agent coordination and task delegation
    - Progress monitoring and error recovery
    - Result aggregation and synthesis
    - Strategic decision making
    """
    
    def __init__(self):
        # Define orchestrator capabilities
        capabilities = [
            AgentCapability(
                name="workflow_orchestration",
                description="Decomposes complex tasks into agent-specific subtasks and coordinates execution",
                confidence=0.95,
                category="coordination"
            ),
            AgentCapability(
                name="task_delegation",
                description="Intelligently assigns tasks to the most capable agents based on requirements",
                confidence=0.90,
                category="management"
            ),
            AgentCapability(
                name="progress_monitoring",
                description="Tracks task progress and handles failures or delays in real-time",
                confidence=0.85,
                category="monitoring"
            ),
            AgentCapability(
                name="result_synthesis",
                description="Aggregates and synthesizes results from multiple agents into cohesive outcomes",
                confidence=0.88,
                category="synthesis"
            ),
            AgentCapability(
                name="strategic_planning",
                description="Makes high-level strategic decisions about workflow execution and optimization",
                confidence=0.82,
                category="strategy"
            )
        ]
        
        super().__init__(
            agent_id="orchestrator_001",
            name="OMEGA Orchestrator",
            description="Central command agent for coordinating complex multi-agent workflows and strategic planning",
            capabilities=capabilities,
            port=9000,
            mcp_port=9001,
            version="2.0.0"
        )
        
        # Orchestrator-specific state
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.agent_capabilities_cache: Dict[str, List[AgentCapability]] = {}
        self.workflow_templates: Dict[str, Dict[str, Any]] = {}
        
        # Enhanced LLM configuration for strategic thinking
        self.strategic_llm = LLMAdapter(
            model="gpt-4",  # Use the big guns for orchestration
            temperature=0.1,  # Low temperature for consistent strategic decisions
            max_tokens=4000
        )

    async def handle_task(self, envelope: TaskEnvelope) -> TaskEnvelope:
        """
        The cognitive core - orchestrates complex workflows with strategic intelligence.
        """
        task = envelope.task
        
        try:
            # Log the incoming task
            print(f"🎯 Orchestrator received task: {task.name}")
            
            # Determine the orchestration strategy
            strategy = await self._determine_strategy(task)
            
            # Execute based on strategy type
            if strategy["type"] == "single_agent":
                result = await self._delegate_to_single_agent(task, strategy)
            elif strategy["type"] == "sequential_workflow":
                result = await self._execute_sequential_workflow(task, strategy)
            elif strategy["type"] == "parallel_workflow":
                result = await self._execute_parallel_workflow(task, strategy)
            elif strategy["type"] == "collaborative_workflow":
                result = await self._execute_collaborative_workflow(task, strategy)
            else:
                result = await self._handle_direct_execution(task)
            
            # Update the envelope with results
            envelope.task.payload.update(result)
            envelope.header.status = TaskStatus.COMPLETED
            envelope.header.completed_at = datetime.utcnow()
            
            print(f"✅ Orchestrator completed task: {task.name}")
            return envelope
            
        except Exception as e:
            print(f"❌ Orchestrator failed on task {task.name}: {e}")
            envelope.header.status = TaskStatus.FAILED
            envelope.header.error = str(e)
            envelope.task.payload["error"] = str(e)
            return envelope

    async def _determine_strategy(self, task: Task) -> Dict[str, Any]:
        """
        Uses AI to analyze the task and determine the optimal orchestration strategy.
        """
        # Analyze task complexity and requirements
        analysis_prompt = f"""
        Analyze this task and determine the optimal orchestration strategy:
        
        Task: {task.name}
        Description: {task.description}
        Requirements: {task.payload.get('requirements', 'None specified')}
        
        Available strategies:
        1. single_agent - Delegate to one specialized agent
        2. sequential_workflow - Chain of dependent tasks
        3. parallel_workflow - Independent tasks that can run simultaneously  
        4. collaborative_workflow - Agents work together iteratively
        
        Consider:
        - Task complexity and scope
        - Dependencies between subtasks
        - Opportunities for parallelization
        - Need for agent collaboration
        
        Respond with a JSON strategy including:
        - type: strategy type
        - reasoning: explanation of choice
        - agents_needed: list of agent types required
        - estimated_duration: time estimate in minutes
        - confidence: confidence in strategy (0-1)
        """
        
        try:
            response = await self.strategic_llm.complete(analysis_prompt)
            strategy = self._parse_strategy_response(response)
            return strategy
        except Exception as e:
            print(f"⚠️ Strategy analysis failed, falling back to simple delegation: {e}")
            return {
                "type": "single_agent",
                "reasoning": "Fallback due to analysis failure",
                "agents_needed": ["code_generator"],  # Safe default
                "estimated_duration": 5,
                "confidence": 0.5
            }

    def _parse_strategy_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into a structured strategy."""
        try:
            import json
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except Exception as e:
            print(f"⚠️ Failed to parse strategy response: {e}")
            return {
                "type": "single_agent",
                "reasoning": "Parsing fallback",
                "agents_needed": ["code_generator"],
                "estimated_duration": 5,
                "confidence": 0.3
            }

    async def _delegate_to_single_agent(self, task: Task, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to the most appropriate single agent."""
        agent_type = strategy["agents_needed"][0]
        
        # Find the best agent for this task
        best_agent = await self._find_best_agent(agent_type, task)
        
        if not best_agent:
            return {"error": f"No suitable {agent_type} agent found"}
        
        # Send task to the selected agent
        result = await self._send_task_to_agent(best_agent["id"], task)
        
        return {
            "strategy": "single_agent_delegation",
            "agent_used": best_agent["id"],
            "result": result
        }

    async def _execute_sequential_workflow(self, task: Task, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a sequential workflow where each step depends on the previous."""
        workflow_id = f"seq_{task.id}_{int(asyncio.get_event_loop().time())}"
        self.active_workflows[workflow_id] = {
            "type": "sequential",
            "status": "running",
            "steps": [],
            "current_step": 0
        }
        
        try:
            # Break down the task into sequential steps
            steps = await self._decompose_into_steps(task, "sequential")
            results = []
            
            for i, step in enumerate(steps):
                print(f"🔄 Executing step {i+1}/{len(steps)}: {step['name']}")
                
                # Find and execute with appropriate agent
                agent = await self._find_best_agent(step["agent_type"], step)
                if agent:
                    step_result = await self._send_task_to_agent(agent["id"], step)
                    results.append(step_result)
                    
                    # Update workflow state
                    self.active_workflows[workflow_id]["current_step"] = i + 1
                    self.active_workflows[workflow_id]["steps"].append({
                        "step": step["name"],
                        "agent": agent["id"],
                        "result": step_result,
                        "completed_at": datetime.utcnow().isoformat()
                    })
                else:
                    raise Exception(f"No suitable agent found for step: {step['name']}")
            
            # Mark workflow as completed
            self.active_workflows[workflow_id]["status"] = "completed"
            
            return {
                "strategy": "sequential_workflow",
                "workflow_id": workflow_id,
                "steps_completed": len(steps),
                "results": results
            }
            
        except Exception as e:
            self.active_workflows[workflow_id]["status"] = "failed"
            raise e

    async def _execute_parallel_workflow(self, task: Task, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parallel tasks that can run simultaneously."""
        workflow_id = f"par_{task.id}_{int(asyncio.get_event_loop().time())}"
        
        # Decompose into parallel tasks
        parallel_tasks = await self._decompose_into_steps(task, "parallel")
        
        # Create coroutines for each parallel task
        task_coroutines = []
        for subtask in parallel_tasks:
            agent = await self._find_best_agent(subtask["agent_type"], subtask)
            if agent:
                coro = self._send_task_to_agent(agent["id"], subtask)
                task_coroutines.append(coro)
        
        # Execute all tasks in parallel
        print(f"🚀 Executing {len(task_coroutines)} parallel tasks...")
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # Process results and handle any exceptions
        successful_results = []
        failed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    "task": parallel_tasks[i]["name"],
                    "error": str(result)
                })
            else:
                successful_results.append(result)
        
        return {
            "strategy": "parallel_workflow",
            "workflow_id": workflow_id,
            "successful_tasks": len(successful_results),
            "failed_tasks": len(failed_results),
            "results": successful_results,
            "failures": failed_results
        }

    async def _execute_collaborative_workflow(self, task: Task, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Execute collaborative workflow where agents work together iteratively."""
        workflow_id = f"collab_{task.id}_{int(asyncio.get_event_loop().time())}"
        
        # This is where agents would engage in back-and-forth collaboration
        # For now, implementing a simplified version
        
        agents_needed = strategy["agents_needed"]
        collaboration_rounds = 3  # Number of iteration rounds
        
        current_result = {"content": task.description}
        
        for round_num in range(collaboration_rounds):
            print(f"🤝 Collaboration round {round_num + 1}/{collaboration_rounds}")
            
            round_results = []
            for agent_type in agents_needed:
                agent = await self._find_best_agent(agent_type, task)
                if agent:
                    # Create a collaborative task with current context
                    collab_task = Task(
                        id=f"{task.id}_collab_{round_num}_{agent_type}",
                        name=f"Collaborative input from {agent_type}",
                        description=f"Provide {agent_type} perspective on: {current_result['content']}",
                        payload={"context": current_result, "round": round_num}
                    )
                    
                    result = await self._send_task_to_agent(agent["id"], collab_task)
                    round_results.append(result)
            
            # Synthesize results from this round
            current_result = await self._synthesize_collaborative_results(round_results, round_num)
        
        return {
            "strategy": "collaborative_workflow",
            "workflow_id": workflow_id,
            "collaboration_rounds": collaboration_rounds,
            "final_result": current_result
        }

    async def _handle_direct_execution(self, task: Task) -> Dict[str, Any]:
        """Handle tasks that the orchestrator can execute directly."""
        # Simple orchestrator-level tasks (status checks, simple queries, etc.)
        
        if "status" in task.name.lower():
            return await self._get_system_status()
        elif "agents" in task.name.lower() and "list" in task.name.lower():
            return await self._list_available_agents()
        else:
            return {
                "strategy": "direct_execution",
                "result": f"Orchestrator processed: {task.name}",
                "message": "Task handled directly by orchestrator"
            }

    async def _decompose_into_steps(self, task: Task, workflow_type: str) -> List[Dict[str, Any]]:
        """Use AI to decompose a complex task into manageable steps."""
        decomposition_prompt = f"""
        Decompose this task into {workflow_type} steps:
        
        Task: {task.name}
        Description: {task.description}
        Workflow Type: {workflow_type}
        
        Available agent types:
        - code_generator: Generates code in various languages
        - research: Conducts research and gathers information
        - prompt_optimizer: Optimizes prompts and requirements
        - capability_matcher: Finds the right agent for tasks
        - math_solver: Handles mathematical calculations
        - project_architect: Designs system architecture
        
        Provide a JSON array of steps, each with:
        - name: step name
        - description: what needs to be done
        - agent_type: which agent should handle this
        - dependencies: which previous steps this depends on (for sequential)
        - estimated_time: time estimate in minutes
        
        Focus on logical decomposition and proper agent assignment.
        """
        
        try:
            response = await self.strategic_llm.complete(decomposition_prompt)
            steps = self._parse_steps_response(response)
            return steps
        except Exception as e:
            print(f"⚠️ Task decomposition failed: {e}")
            # Fallback to simple single-step delegation
            return [{
                "name": task.name,
                "description": task.description,
                "agent_type": "code_generator",
                "dependencies": [],
                "estimated_time": 5
            }]

    def _parse_steps_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse the LLM response into structured steps."""
        try:
            import json
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except Exception as e:
            print(f"⚠️ Failed to parse steps response: {e}")
            return []

    async def _find_best_agent(self, agent_type: str, task: Any) -> Optional[Dict[str, Any]]:
        """Find the best available agent of the specified type."""
        try:
            # Query the agent registry for available agents
            response = await self.http_client.get(
                f"{self.registry_url}/agents?type={agent_type}&status=active",
                timeout=5.0
            )
            
            if response.status_code == 200:
                agents = response.json().get("agents", [])
                if agents:
                    # For now, return the first available agent
                    # In the future, this could use sophisticated matching logic
                    return agents[0]
            
            return None
        except Exception as e:
            print(f"⚠️ Failed to find agent of type {agent_type}: {e}")
            return None

    async def _send_task_to_agent(self, agent_id: str, task: Any) -> Dict[str, Any]:
        """Send a task to a specific agent and wait for the result."""
        try:
            # Get agent details from registry
            agent_response = await self.http_client.get(
                f"{self.registry_url}/agents/{agent_id}",
                timeout=5.0
            )
            
            if agent_response.status_code != 200:
                raise Exception(f"Agent {agent_id} not found in registry")
            
            agent_info = agent_response.json()
            agent_url = f"http://{agent_info['host']}:{agent_info['port']}"
            
            # Create task envelope
            envelope = TaskEnvelope(
                task=task if isinstance(task, Task) else Task(**task),
                header={
                    "source_agent": self.id,
                    "target_agent": agent_id,
                    "created_at": datetime.utcnow(),
                    "status": TaskStatus.PENDING
                }
            )
            
            # Send task to agent
            response = await self.http_client.post(
                f"{agent_url}/tasks",
                json=envelope.model_dump(),
                timeout=60.0  # Give agents time to process
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("task", {}).get("payload", {})
            else:
                raise Exception(f"Agent {agent_id} returned status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Failed to send task to agent {agent_id}: {e}")
            return {"error": str(e)}

    async def _synthesize_collaborative_results(self, results: List[Dict[str, Any]], round_num: int) -> Dict[str, Any]:
        """Synthesize results from collaborative agents."""
        synthesis_prompt = f"""
        Synthesize these collaborative inputs from round {round_num + 1}:
        
        Results: {results}
        
        Create a cohesive synthesis that:
        1. Combines the best insights from each input
        2. Resolves any conflicts or contradictions
        3. Builds toward a comprehensive solution
        4. Maintains coherence and quality
        
        Return a JSON object with:
        - content: the synthesized content
        - insights: key insights discovered
        - next_steps: what should happen in the next round
        """
        
        try:
            response = await self.strategic_llm.complete(synthesis_prompt)
            return self._parse_synthesis_response(response)
        except Exception as e:
            print(f"⚠️ Synthesis failed: {e}")
            return {
                "content": f"Combined results from round {round_num + 1}",
                "insights": ["Synthesis failed"],
                "next_steps": ["Continue with available results"]
            }

    def _parse_synthesis_response(self, response: str) -> Dict[str, Any]:
        """Parse synthesis response from LLM."""
        try:
            import json
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            return json.loads(json_str)
        except:
            return {"content": response}

    async def _get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            # Query registry for all agents
            response = await self.http_client.get(f"{self.registry_url}/agents", timeout=5.0)
            
            if response.status_code == 200:
                agents = response.json().get("agents", [])
                
                return {
                    "system_status": "operational",
                    "total_agents": len(agents),
                    "active_agents": len([a for a in agents if a.get("status") == "active"]),
                    "active_workflows": len(self.active_workflows),
                    "orchestrator_uptime": asyncio.get_event_loop().time() - self.metrics.start_time
                }
            else:
                return {"system_status": "degraded", "error": "Cannot reach agent registry"}
        except Exception as e:
            return {"system_status": "error", "error": str(e)}

    async def _list_available_agents(self) -> Dict[str, Any]:
        """List all available agents in the system."""
        try:
            response = await self.http_client.get(f"{self.registry_url}/agents", timeout=5.0)
            
            if response.status_code == 200:
                agents = response.json().get("agents", [])
                
                return {
                    "available_agents": agents,
                    "count": len(agents),
                    "agent_types": list(set(agent.get("type", "unknown") for agent in agents))
                }
            else:
                return {"error": "Cannot reach agent registry"}
        except Exception as e:
            return {"error": str(e)}


# Entry point for the agent
if __name__ == "__main__":
    orchestrator = OrchestratorAgent()
    orchestrator.run()