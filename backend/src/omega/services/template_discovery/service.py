# omega/services/template_discovery/service.py

from typing import Dict, List, Optional

class TemplateDiscoveryService:
    """
    Service for intelligently discovering and recommending templates.
    Enhanced with support for collaborative workflows.
    """
    
    def __init__(self, repository: TemplateRepository):
        """
        Initialize the discovery service.
        
        Args:
            repository: Template repository
        """
        self.repository = repository
    
    def find_template_for_request(self, request_text: str, workflow_type: str = None) -> List[WorkflowTemplate]:
        """
        Find templates that match a request.
        
        Args:
            request_text: The user's request
            workflow_type: Optional workflow type filter
            
        Returns:
            List of matching templates, ordered by relevance
        """
        # Extract potential keywords from the request
        keywords = self._extract_keywords(request_text)
        
        # Detect workflow type from request if not specified
        detected_type = workflow_type or self._detect_workflow_type(request_text)
        
        # Find templates by tags
        tag_matches = self.repository.find_templates_by_tags(keywords, match_all=False)
        
        # Find templates by name
        name_matches = []
        for keyword in keywords:
            name_matches.extend(self.repository.find_templates_by_name(keyword))
        
        # Filter by workflow type if specified
        if detected_type:
            type_matches = self.repository.find_templates_by_type(detected_type)
            # Combine matches giving priority to type
            combined = {t.template_id: t for t in type_matches}
            # Add tag matches that weren't already included
            for t in tag_matches:
                combined.setdefault(t.template_id, t)
            # Add name matches that weren't already included
            for t in name_matches:
                combined.setdefault(t.template_id, t)
        else:
            # Combine results without filtering by type
            combined = {t.template_id: t for t in tag_matches + name_matches}
        
        # Sort by relevance
        results = list(combined.values())
        results.sort(key=lambda t: self._calculate_relevance(t, keywords, request_text, detected_type), reverse=True)
        
        return results
    
    def _detect_workflow_type(self, text: str) -> Optional[str]:
        """
        Detect the likely workflow type from request text.
        
        Args:
            text: Request text
            
        Returns:
            Detected workflow type or None
        """
        text_lower = text.lower()
        
        # Check for debate indicators
        debate_indicators = ["debate", "discuss", "argument", "perspective", "opinion", "viewpoint", "ethics"]
        if any(indicator in text_lower for indicator in debate_indicators):
            return "debate"
        
        # Check for collaborative indicators
        collab_indicators = ["collaborate", "brainstorm", "ideate", "together", "team", "group", "multiple perspectives", "critique"]
        if any(indicator in text_lower for indicator in collab_indicators):
            return "collaborative"
        
        # Check for sequential/build indicators
        build_indicators = ["build", "create", "develop", "generate", "implement", "make", "setup", "design"]
        if any(indicator in text_lower for indicator in build_indicators):
            return "sequential"
        
        # If no clear indicators, return None
        return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract potential keywords from text."""
        # This is a simple keyword extraction - in a real implementation,
        # you might use NLP techniques for better extraction
        
        # Convert to lowercase and split
        words = text.lower().replace(',', ' ').replace('.', ' ').split()
        
        # Remove common words
        common_words = {"the", "and", "a", "an", "in", "for", "to", "of", "with", "on", "at", "by", "as", "is", "are", "was", "were", "be", "this", "that", "it", "they", "I", "you", "he", "she", "we", "what", "which", "who", "when", "where", "how", "why", "can", "will", "should", "could", "would"}
        keywords = [w for w in words if w not in common_words and len(w) > 2]
        
        return keywords
    
    def _calculate_relevance(self, template: WorkflowTemplate, keywords: List[str], request_text: str, workflow_type: str = None) -> float:
        """
        Calculate relevance score for a template.
        
        Args:
            template: The template to score
            keywords: Extracted keywords
            request_text: Original request text
            workflow_type: Detected workflow type
            
        Returns:
            Relevance score
        """
        score = 0.0
        
        # Workflow type match (highest priority)
        if workflow_type and template.workflow_type == workflow_type:
            score += 10.0
        
        # Tag matches
        tag_matches = sum(1 for tag in template.tags if tag in keywords)
        score += tag_matches * 2.0
        
        # Name matches
        if any(keyword in template.name.lower() for keyword in keywords):
            score += 3.0
        
        # Description matches
        if any(keyword in template.description.lower() for keyword in keywords):
            score += 1.0
        
        # Interaction pattern relevance
        # Check for debate patterns
        if "debate" in request_text.lower() and template.has_debate_phases():
            score += 5.0
        
        # Check for collaboration patterns
        collab_terms = ["collaborate", "together", "team", "group"]
        if any(term in request_text.lower() for term in collab_terms) and template.is_collaborative():
            score += 5.0
        
        # Success rate factor
        total_executions = template.success_count + template.failure_count
        if total_executions > 0:
            success_rate = template.success_count / total_executions
            score *= (0.5 + (success_rate * 0.5))  # Scale by success rate (50% - 100% of original score)
        
        return score
    
    def recommend_templates_by_category(self) -> Dict[str, List[WorkflowTemplate]]:
        """
        Recommend templates organized by category.
        
        Returns:
            Dictionary mapping categories to lists of templates
        """
        categories = {
            "Most Successful": [],
            "Sequential Workflows": [],
            "Collaborative Workflows": [],
            "Debate Workflows": [],
            "Hybrid Workflows": [],
            "Recently Added": []
        }
        
        # Get all templates
        all_templates = self.repository.get_all_templates()
        
        # Most successful templates (by success rate)
        for template in all_templates:
            total = template.success_count + template.failure_count
            if total > 0:
                template.success_rate = template.success_count / total
            else:
                template.success_rate = 0
        
        successful = sorted(
            [t for t in all_templates if t.success_count + t.failure_count > 0],
            key=lambda t: t.success_rate,
            reverse=True
        )
        categories["Most Successful"] = successful[:5]
        
        # Templates by workflow type
        categories["Sequential Workflows"] = self.repository.find_templates_by_type("sequential")[:5]
        categories["Collaborative Workflows"] = self.repository.find_templates_by_type("collaborative")[:5]
        categories["Debate Workflows"] = self.repository.find_templates_by_type("debate")[:5]
        categories["Hybrid Workflows"] = self.repository.find_templates_by_type("hybrid")[:5]
        
        # Recently added templates
        categories["Recently Added"] = sorted(
            all_templates,
            key=lambda t: t.created_at,
            reverse=True
        )[:5]
        
        return categories