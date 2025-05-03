from omega.workflows.workflow_template import WorkflowTemplate    

class WorkflowTemplates:
    """
    Provides access to predefined workflow templates.
    """
    @staticmethod
    def get_collaborative_template():
        return WorkflowTemplate(
    template_id="ai_business_ideation",
    name="AI Business Ideation & Planning",
    description="Collaborative workflow where multiple agents research, ideate, and develop a business plan for an AI-powered business",
    agents=[
        {"id": "research_agent", "role": "market_research", "group": "ideation"},
        {"id": "idea_generator", "role": "business_ideation", "group": "ideation"},
        {"id": "business_planner", "role": "plan_creation", "group": "planning"},
        {"id": "marketing_specialist", "role": "marketing_strategy", "group": "planning"},
        {"id": "critic", "role": "critical_analysis", "group": "evaluation"} 
    ],
    execution_flow=[
        {
            "phase": "research",
            "pattern": "parallel",
            "participants": ["research_agent"],
            "actions": [
                {
                    "action": "research_market_trends",
                    "input_from": "user_requirements",
                    "output_to": "market_research"
                },
                {
                    "action": "identify_unmet_needs",
                    "input_from": "user_requirements",
                    "output_to": "unmet_needs"
                }
            ]
        },
        {
            "phase": "ideation",
            "pattern": "collaborative",
            "participants": ["research_agent", "idea_generator"],
            "actions": [
                {
                    "action": "generate_business_ideas",
                    "input_from": ["market_research", "unmet_needs"],
                    "output_to": "business_ideas",
                    "collaboration_type": "iterative_refinement",
                    "rounds": 2
                }
            ]
        },
        {
            "phase": "planning",
            "pattern": "parallel",
            "participants": ["business_planner", "marketing_specialist"],
            "actions": [
                {
                    "action": "create_business_plan",
                    "agent": "business_planner",
                    "input_from": "business_ideas",
                    "output_to": "business_plan"
                },
                {
                    "action": "develop_marketing_strategy",
                    "agent": "marketing_specialist",
                    "input_from": "business_ideas",
                    "output_to": "marketing_strategy"
                }
            ]
        },
        {
            "phase": "evaluation",
            "pattern": "debate",
            "participants": ["critic", "business_planner", "marketing_specialist"],
            "actions": [
                {
                    "action": "debate_feasibility",
                    "input_from": ["business_plan", "marketing_strategy"],
                    "output_to": "feasibility_analysis",
                    "debate_format": "critique_defense_refinement",
                    "rounds": 3
                }
            ]
        },
        {
            "phase": "finalization",
            "pattern": "synthesis",
            "participants": ["business_planner"],
            "actions": [
                {
                    "action": "finalize_business_plan",
                    "input_from": ["business_plan", "marketing_strategy", "feasibility_analysis"],
                    "output_to": "final_business_plan"
                }
            ]
        }
    ],
    interaction_patterns={
        "collaborative": {
            "description": "Agents work together, building on each other's outputs",
            "coordination": "sequential_contribution"
        },
        "debate": {
            "description": "Agents challenge and critique each other's ideas",
            "format": "structured_rounds",
            "roles": ["proposer", "critic", "moderator"]
        },
        "parallel": {
            "description": "Agents work independently on different aspects",
            "synchronization": "end_of_phase"
        },
        "synthesis": {
            "description": "Combining multiple inputs into a coherent output",
            "method": "weighted_integration"
        }
    },
    parameters=[
        {
            "name": "ideation_rounds",
            "default": 2,
            "description": "Number of collaborative rounds during ideation"
        },
        {
            "name": "debate_depth",
            "default": 3,
            "description": "Number of rounds in the debate phase"
        },
        {
            "name": "market_focus",
            "default": "general",
            "options": ["b2b", "b2c", "enterprise", "general"]
        }
    ],
    tags=["business", "ideation", "collaborative", "debate", "ai"],
    version=1.0
)

    @staticmethod
    def get_debate_template():
        return WorkflowTemplate(
    template_id="philosophical_debate",
    name="Philosophical Debate",
    description="A structured debate between multiple viewpoints on a philosophical topic",
    agents=[
        {"id": "utilitarian_agent", "role": "advocate", "perspective": "utilitarian"},
        {"id": "deontological_agent", "role": "advocate", "perspective": "deontological"},
        {"id": "virtue_ethics_agent", "role": "advocate", "perspective": "virtue_ethics"},
        {"id": "moderator_agent", "role": "moderator", "perspective": "neutral"}
    ],
    execution_flow=[
        {
            "phase": "opening_statements",
            "pattern": "sequential",
            "participants": ["utilitarian_agent", "deontological_agent", "virtue_ethics_agent"],
            "actions": [
                {
                    "action": "present_opening_argument",
                    "input_from": "debate_topic",
                    "output_to": "opening_statements"
                }
            ]
        },
        {
            "phase": "cross_examination",
            "pattern": "debate",
            "participants": ["utilitarian_agent", "deontological_agent", "virtue_ethics_agent"],
            "moderator": "moderator_agent",
            "actions": [
                {
                    "action": "question_and_respond",
                    "input_from": "opening_statements",
                    "output_to": "examination_results",
                    "debate_format": "round_robin",
                    "rounds": 3
                }
            ]
        },
        {
            "phase": "rebuttal",
            "pattern": "sequential",
            "participants": ["utilitarian_agent", "deontological_agent", "virtue_ethics_agent"],
            "actions": [
                {
                    "action": "present_rebuttal",
                    "input_from": ["opening_statements", "examination_results"],
                    "output_to": "rebuttals"
                }
            ]
        },
        {
            "phase": "synthesis",
            "pattern": "collaborative",
            "participants": ["utilitarian_agent", "deontological_agent", "virtue_ethics_agent", "moderator_agent"],
            "actions": [
                {
                    "action": "synthesize_perspectives",
                    "input_from": ["opening_statements", "examination_results", "rebuttals"],
                    "output_to": "synthesis",
                    "collaboration_type": "moderated_integration"
                }
            ]
        },
        {
            "phase": "conclusion",
            "pattern": "solo",
            "participants": ["moderator_agent"],
            "actions": [
                {
                    "action": "summarize_debate",
                    "input_from": ["opening_statements", "examination_results", "rebuttals", "synthesis"],
                    "output_to": "debate_summary"
                }
            ]
        }
    ],
    interaction_patterns={
        "debate": {
            "description": "Structured argument and counter-argument",
            "formats": {
                "round_robin": "Each agent questions each other agent in turn",
                "panel_debate": "Panel of questioners and respondents",
                "structured_critique": "Formal critique followed by defense"
            }
        },
        "sequential": {
            "description": "Agents take turns without direct interaction",
            "turn_taking": "predetermined_order"
        },
        "collaborative": {
            "description": "Agents work together to synthesize ideas",
            "integration": "moderated_consensus"
        },
        "solo": {
            "description": "Single agent performs an action",
            "purpose": "summarization_or_evaluation"
        }
    },
    parameters=[
        {
            "name": "debate_topic",
            "default": "trolley_problem",
            "description": "The philosophical topic to debate"
        },
        {
            "name": "examination_rounds",
            "default": 3,
            "description": "Number of rounds during cross-examination"
        },
        {
            "name": "time_constraints",
            "default": "balanced",
            "options": ["brief", "balanced", "in_depth"]
        }
    ],
    tags=["philosophy", "debate", "ethics", "collaborative"],
    version=1.0
)