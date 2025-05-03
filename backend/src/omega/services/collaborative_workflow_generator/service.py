# omega/services/collaborative_workflow_generator/service.py

from typing import List
import uuid

class CollaborativeWorkflowGenerator:
    """
    Service that can generate new collaborative workflow templates
    based on specified interaction patterns and requirements.
    """
    
    def __init__(self, repository: TemplateRepository):
        """
        Initialize the generator.
        
        Args:
            repository: Template repository
        """
        self.repository = repository
        
        # Define available interaction patterns
        self.patterns = {
            "debate": {
                "description": "Agents argue different perspectives and critique each other",
                "formats": ["round_robin", "panel_debate", "structured_critique"]
            },
            "collaborative": {
                "description": "Agents work together, building on each other's outputs",
                "formats": ["sequential_contribution", "consensus_building", "iterative_refinement"]
            },
            "parallel": {
                "description": "Agents work independently on different aspects",
                "formats": ["independent_tasks", "divide_and_conquer"]
            },
            "synthesis": {
                "description": "Combining multiple inputs into a coherent output",
                "formats": ["weighted_integration", "expert_evaluation"]
            },
            "sequential": {
                "description": "Agents take turns without direct interaction",
                "formats": ["predetermined_order", "dynamic_handoff"]
            }
        }
    
    def generate_template(
        self,
        name: str,
        description: str,
        primary_pattern: str,
        required_agent_types: List[str],
        num_phases: int = 3,
        tags: List[str] = None
    ) -> WorkflowTemplate:
        """
        Generate a new workflow template based on parameters.
        
        Args:
            name: Template name
            description: Template description
            primary_pattern: Primary interaction pattern
            required_agent_types: Types of agents required
            num_phases: Number of phases to include
            tags: Optional tags for the template
            
        Returns:
            Generated workflow template
        """
        if primary_pattern not in self.patterns:
            raise ValueError(f"Unknown interaction pattern: {primary_pattern}")
        
        # Generate a template ID
        template_id = f"{primary_pattern}_{uuid.uuid4().hex[:8]}"
        
        # Determine workflow type based on primary pattern
        if primary_pattern == "debate":
            workflow_type = "debate"
        elif primary_pattern in ["collaborative", "synthesis"]:
            workflow_type = "collaborative"
        elif primary_pattern == "sequential":
            workflow_type = "sequential"
        else:
            workflow_type = "hybrid"
        
        # Create agents
        agents = []
        for agent_type in required_agent_types:
            if agent_type == "moderator":
                role = "moderator"
            elif agent_type == "critic":
                role = "critic"
            elif agent_type == "advocate":
                role = "advocate"
            else:
                role = "participant"
            
            agent = {
                "id": f"{agent_type}_agent",
                "role": role,
                "type": agent_type
            }
            agents.append(agent)
        
        # Generate phases based on primary pattern
        execution_flow = []
        
        # Add opening phase
        opening_phase = {
            "phase": "opening",
            "pattern": "sequential",
            "participants": [agent["id"] for agent in agents if agent["role"] != "moderator"],
            "actions": [
                {
                    "action": "present_initial_thoughts",
                    "input_from": "user_requirements",
                    "output_to": "initial_thoughts"
                }
            ]
        }
        execution_flow.append(opening_phase)
        
        # Add middle phases
        for i in range(num_phases - 2):
            phase_name = f"phase_{i+2}"
            
            # Use primary pattern for middle phases
            if primary_pattern == "debate":
                phase = {
                    "phase": phase_name,
                    "pattern": "debate",
                    "participants": [agent["id"] for agent in agents if agent["role"] != "moderator"],
                    "moderator": next((agent["id"] for agent in agents if agent["role"] == "moderator"), None),
                    "actions": [
                        {
                            "action": "debate_topic",
                            "input_from": "initial_thoughts" if i == 0 else f"phase_{i+1}_output",
                            "output_to": f"{phase_name}_output",
                            "debate_format": "round_robin",
                            "rounds": 3
                        }
                    ]
                }
            elif primary_pattern == "collaborative":
                phase = {
                    "phase": phase_name,
                    "pattern": "collaborative",
                    "participants": [agent["id"] for agent in agents],
                    "actions": [
                        {
                            "action": "collaborate_on_solution",
                            "input_from": "initial_thoughts" if i == 0 else f"phase_{i+1}_output",
                            "output_to": f"{phase_name}_output",
                            "collaboration_type": "iterative_refinement"
                        }
                    ]
                }
            elif primary_pattern == "parallel":
                # For parallel, assign each participant a different task
                steps = []
                participants = [agent["id"] for agent in agents if agent["role"] != "moderator"]
                for j, participant in enumerate(participants):
                    steps.append({
                        "action": f"parallel_task_{j+1}",
                        "agent": participant,
                        "input_from": "initial_thoughts" if i == 0 else f"phase_{i+1}_output",
                        "output_to": f"{participant}_output"
                    })
                
                phase = {
                    "phase": phase_name,
                    "pattern": "parallel",
                    "participants": participants,
                    "actions": steps
                }
            else:  # sequential or other
                phase = {
                    "phase": phase_name,
                    "pattern": "sequential",
                    "participants": [agent["id"] for agent in agents],
                    "actions": [
                        {
                            "action": "sequential_step",
                            "input_from": "initial_thoughts" if i == 0 else f"phase_{i+1}_output",
                            "output_to": f"{phase_name}_output"
                        }
                    ]
                }
            
            execution_flow.append(phase)
        
        # Add final synthesis phase
        final_phase = {
            "phase": "final",
            "pattern": "synthesis",
            "participants": [agent["id"] for agent in agents],
            "actions": [
                {
                    "action": "synthesize_output",
                    "input_from": f"{num_phases}_output",
                    "output_to": "final_output"
                }
            ]
        }
        execution_flow.append(final_phase)
        
        # Create template
        template = WorkflowTemplate(
            id=template_id,
            name=name,
            description=description,
            workflow_type=workflow_type,
            execution_flow=execution_flow,
            tags=tags
        )
        
        # Save template
        self.repository.save_template(template)
        
        return template