import os
import json
import yaml
from typing import Dict, List, Any, Optional, Union, Set
from datetime import datetime
import uuid

class TemplateRepository:
    """
    Repository for storing, retrieving, and managing workflow templates.
    Enhanced with support for collaborative workflows.
    """
    
    def __init__(self, storage_dir: str = None):
        """
        Initialize the template repository.
        
        Args:
            storage_dir: Directory where templates are stored
        """
        self.storage_dir = storage_dir or os.path.join("data", "templates")
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Cache of loaded templates
        self.templates: Dict[str, WorkflowTemplate] = {}
        
        # Load templates from storage
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load all templates from the storage directory."""
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(('.json', '.yaml', '.yml')):
                file_path = os.path.join(self.storage_dir, filename)
                try:
                    template = self._load_template_file(file_path)
                    if template:
                        self.templates[template.template_id] = template
                except Exception as e:
                    print(f"Error loading template {filename}: {str(e)}")
    
    def _load_template_file(self, file_path: str) -> Optional[WorkflowTemplate]:
        """Load a template from a file."""
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                else:  # YAML file
                    data = yaml.safe_load(f)
                
                return WorkflowTemplate.from_dict(data)
        except Exception as e:
            print(f"Error parsing template file {file_path}: {str(e)}")
            return None
    
    def _save_template_file(self, template: WorkflowTemplate) -> None:
        """Save a template to a file."""
        file_path = os.path.join(self.storage_dir, f"{template.template_id}.json")
        with open(file_path, 'w') as f:
            json.dump(template.to_dict(), f, indent=2)
    
    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """
        Get a template by ID.
        
        Args:
            template_id: ID of the template to retrieve
            
        Returns:
            The template or None if not found
        """
        return self.templates.get(template_id)
    
    def get_all_templates(self) -> List[WorkflowTemplate]:
        """
        Get all templates.
        
        Returns:
            List of all templates
        """
        return list(self.templates.values())
    
    def find_templates_by_type(self, workflow_type: str) -> List[WorkflowTemplate]:
        """
        Find templates by workflow type.
        
        Args:
            workflow_type: Type of workflow (sequential, collaborative, debate, hybrid)
            
        Returns:
            List of matching templates
        """
        return [t for t in self.templates.values() if t.workflow_type == workflow_type]
    
    def find_templates_by_tags(self, tags: List[str], match_all: bool = False) -> List[WorkflowTemplate]:
        """
        Find templates by tags.
        
        Args:
            tags: List of tags to search for
            match_all: If True, all tags must be present
            
        Returns:
            List of matching templates
        """
        if not tags:
            return []
        
        result = []
        for template in self.templates.values():
            if match_all:
                if all(tag in template.tags for tag in tags):
                    result.append(template)
            else:
                if any(tag in template.tags for tag in tags):
                    result.append(template)
        
        return result
    
    def find_templates_by_pattern(self, pattern: str) -> List[WorkflowTemplate]:
        """
        Find templates that use a specific interaction pattern.
        
        Args:
            pattern: Interaction pattern to search for
            
        Returns:
            List of matching templates
        """
        return [t for t in self.templates.values() if pattern in t.get_interaction_patterns()]
    
    def find_debate_templates(self) -> List[WorkflowTemplate]:
        """
        Find templates that include debate phases.
        
        Returns:
            List of templates with debate phases
        """
        return [t for t in self.templates.values() if t.has_debate_phases()]
    
    def find_templates_by_name(self, search_term: str) -> List[WorkflowTemplate]:
        """
        Find templates by name (partial match).
        
        Args:
            search_term: Term to search for in template names
            
        Returns:
            List of matching templates
        """
        search_term = search_term.lower()
        return [t for t in self.templates.values() if search_term in t.name.lower()]
    
    def find_templates_by_agents(self, agent_ids: List[str], match_all: bool = False) -> List[WorkflowTemplate]:
        """
        Find templates that use specific agents.
        
        Args:
            agent_ids: List of agent IDs to search for
            match_all: If True, all agents must be present
            
        Returns:
            List of matching templates
        """
        if not agent_ids:
            return []
        
        result = []
        for template in self.templates.values():
            template_agent_ids = [agent["id"] for agent in template.agents]
            
            if match_all:
                if all(aid in template_agent_ids for aid in agent_ids):
                    result.append(template)
            else:
                if any(aid in template_agent_ids for aid in agent_ids):
                    result.append(template)
        
        return result
    
    def find_templates_for_agent_role(self, role: str) -> List[WorkflowTemplate]:
        """
        Find templates that include a specific agent role.
        
        Args:
            role: Agent role to search for
            
        Returns:
            List of matching templates
        """
        result = []
        for template in self.templates.values():
            for agent in template.agents:
                if agent.get("role") == role:
                    result.append(template)
                    break
        
        return result
    
    def add_template(self, template: WorkflowTemplate) -> str:
        """
        Add a new template to the repository.
        
        Args:
            template: The template to add
            
        Returns:
            ID of the added template
        """
        self.templates[template.template_id] = template
        self._save_template_file(template)
        return template.template_id
    
    def update_template(self, template: WorkflowTemplate) -> bool:
        """
        Update an existing template.
        
        Args:
            template: The template to update
            
        Returns:
            True if successful, False if template not found
        """
        if template.template_id not in self.templates:
            return False
        
        # Increment version
        template.version = float(template.version) + 0.1
        template.updated_at = datetime.now().isoformat()
        
        self.templates[template.template_id] = template
        self._save_template_file(template)
        return True
    
    def clone_template(self, template_id: str, new_name: str = None) -> Optional[str]:
        """
        Clone an existing template with a new ID.
        
        Args:
            template_id: ID of the template to clone
            new_name: Optional new name for the cloned template
            
        Returns:
            ID of the cloned template, or None if source template not found
        """
        source = self.get_template(template_id)
        if not source:
            return None
        
        # Create a copy of the template data
        template_data = source.to_dict()
        
        # Update fields for the clone
        template_data["template_id"] = f"template_{uuid.uuid4().hex[:8]}"
        if new_name:
            template_data["name"] = new_name
        else:
            template_data["name"] = f"Copy of {source.name}"
        
        template_data["version"] = 1.0
        template_data["created_at"] = datetime.now().isoformat()
        template_data["updated_at"] = template_data["created_at"]
        template_data["success_count"] = 0
        template_data["failure_count"] = 0
        template_data["average_duration"] = 0.0
        
        # Create the new template
        clone = WorkflowTemplate.from_dict(template_data)
        
        # Add to repository
        return self.add_template(clone)
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.
        
        Args:
            template_id: ID of the template to delete
            
        Returns:
            True if successful, False if template not found
        """
        if template_id not in self.templates:
            return False
        
        # Remove from memory
        del self.templates[template_id]
        
        # Remove from disk
        file_path = os.path.join(self.storage_dir, f"{template_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return True
    
    def update_metrics(self, template_id: str, success: bool, duration: float, satisfaction_score: float = None) -> bool:
        """
        Update metrics for a template.
        
        Args:
            template_id: ID of the template
            success: Whether the execution was successful
            duration: Duration of the execution in seconds
            satisfaction_score: Optional user satisfaction score (0-5)
            
        Returns:
            True if successful, False if template not found
        """
        template = self.get_template(template_id)
        if not template:
            return False
        
        template.update_metrics(success, duration, satisfaction_score)
        self._save_template_file(template)
        return True
    
    def get_template_metrics(self, template_id: str) -> Dict[str, Any]:
        """
        Get performance metrics for a template.
        
        Args:
            template_id: ID of the template
            
        Returns:
            Dictionary of metrics or empty dict if template not found
        """
        template = self.get_template(template_id)
        if not template:
            return {}
        
        total_executions = template.success_count + template.failure_count
        success_rate = template.success_count / total_executions if total_executions > 0 else 0
        
        metrics = {
            "template_id": template.template_id,
            "name": template.name,
            "total_executions": total_executions,
            "success_count": template.success_count,
            "failure_count": template.failure_count,
            "success_rate": success_rate,
            "average_duration": template.average_duration,
            "version": template.version,
            "last_updated": template.updated_at
        }
        
        # Add custom metrics if available
        if hasattr(template, 'custom_metrics'):
            metrics.update(template.custom_metrics)
        
        return metrics