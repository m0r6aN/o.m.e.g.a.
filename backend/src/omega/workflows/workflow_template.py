# omega/core/workflows/workflow_template.py

from typing import Dict, List, Any, Optional, Union, Set
from datetime import datetime
import uuid

class WorkflowTemplate:
    """
    Represents a workflow template in the OMEGA framework.
    Supports both sequential and non-sequential collaborative workflows.
    """
    
    def __init__(
        self,
        template_id: str = None,
        name: str = "",
        description: str = "",
        agents: List[Dict[str, Any]] = None,
        execution_flow: List[Dict[str, Any]] = None,
        interaction_patterns: Dict[str, Dict[str, Any]] = None,
        parameters: List[Dict[str, Any]] = None,
        improvement_metrics: List[str] = None,
        tags: List[str] = None,
        workflow_type: str = "sequential",  # sequential, collaborative, debate, hybrid
        version: float = 1.0,
        created_at: str = None,
        updated_at: str = None,
        success_count: int = 0,
        failure_count: int = 0,
        average_duration: float = 0.0
    ):
        self.template_id = template_id or f"template_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.description = description
        self.agents = agents or []
        self.execution_flow = execution_flow or []
        self.interaction_patterns = interaction_patterns or {}
        self.parameters = parameters or []
        self.improvement_metrics = improvement_metrics or ["execution_time", "success_rate", "user_satisfaction"]
        self.tags = tags or []
        self.workflow_type = workflow_type
        self.version = version
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or self.created_at
        self.success_count = success_count
        self.failure_count = failure_count
        self.average_duration = average_duration
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowTemplate':
        """Create a template from a dictionary."""
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to a dictionary."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "agents": self.agents,
            "execution_flow": self.execution_flow,
            "interaction_patterns": self.interaction_patterns,
            "parameters": self.parameters,
            "improvement_metrics": self.improvement_metrics,
            "tags": self.tags,
            "workflow_type": self.workflow_type,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "average_duration": self.average_duration
        }
    
    def update_metrics(self, success: bool, duration: float, satisfaction_score: float = None) -> None:
        """
        Update the template metrics based on execution results.
        
        Args:
            success: Whether execution was successful
            duration: Execution duration in seconds
            satisfaction_score: Optional user satisfaction score (0-5)
        """
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        # Update average duration using a weighted approach
        total_executions = self.success_count + self.failure_count
        if total_executions > 1:
            # Weighted average: keep 90% of old average, add 10% of new value
            self.average_duration = (self.average_duration * 0.9) + (duration * 0.1)
        else:
            self.average_duration = duration
        
        # Update user satisfaction if provided (stored in custom_metrics)
        if satisfaction_score is not None:
            if not hasattr(self, 'custom_metrics'):
                self.custom_metrics = {}
            
            if 'satisfaction' not in self.custom_metrics:
                self.custom_metrics['satisfaction'] = satisfaction_score
            else:
                # Weighted average for satisfaction
                old_score = self.custom_metrics['satisfaction']
                self.custom_metrics['satisfaction'] = (old_score * 0.9) + (satisfaction_score * 0.1)
        
        # Update timestamp
        self.updated_at = datetime.now().isoformat()
    
    def get_required_agents(self) -> Set[str]:
        """Get the set of agent IDs required for this workflow."""
        return {agent["id"] for agent in self.agents}
    
    def get_agent_roles(self) -> Dict[str, str]:
        """Get a mapping of agent IDs to their roles."""
        return {agent["id"]: agent.get("role", "participant") for agent in self.agents}
    
    def get_interaction_patterns(self) -> List[str]:
        """Get the list of interaction patterns used in this workflow."""
        patterns = []
        for phase in self.execution_flow:
            if "pattern" in phase:
                patterns.append(phase["pattern"])
        return list(set(patterns))
    
    def is_sequential(self) -> bool:
        """Check if this workflow is primarily sequential."""
        return self.workflow_type == "sequential"
    
    def is_collaborative(self) -> bool:
        """Check if this workflow is collaborative."""
        return self.workflow_type in ["collaborative", "debate", "hybrid"]
    
    def has_debate_phases(self) -> bool:
        """Check if this workflow includes debate phases."""
        for phase in self.execution_flow:
            if phase.get("pattern") == "debate":
                return True
        return False
    
    def get_moderator_agents(self) -> List[str]:
        """Get agent IDs that act as moderators in this workflow."""
        moderators = []
        for agent in self.agents:
            if agent.get("role") == "moderator":
                moderators.append(agent["id"])
        
        # Also check for moderators specified in debate phases
        for phase in self.execution_flow:
            if "moderator" in phase:
                moderators.append(phase["moderator"])
        
        return list(set(moderators))