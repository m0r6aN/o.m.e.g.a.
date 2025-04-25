from enum import Enum

class ReasoningEffort(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
        
def get_reasoning_strategy(effort: ReasoningEffort) -> str:
    """
    Maps reasoning effort to a cognitive strategy the agent should use.
    """
    if effort == ReasoningEffort.LOW:
        return "direct_answer"
    elif effort == ReasoningEffort.MEDIUM:
        return "chain-of-thought"
    elif effort == ReasoningEffort.HIGH:
        return "chain-of-draft"
    return "unknown"
    
class ReasoningStrategy(str, Enum):
    DIRECT = "direct_answer"
    COT = "chain-of-thought"
    COD = "chain-of-draft"