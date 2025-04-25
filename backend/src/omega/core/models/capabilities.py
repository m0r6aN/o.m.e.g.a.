# capabilities.py
from enum import Enum
from typing import Dict, List

class Capability(str, Enum):
    MATH_OPERATIONS = "math_operations"
    ACCOUNT_BALANCES = "account_balances"
    TEXT_SUMMARIZATION = "text_summarization"
    WEB_SEARCH = "web_search"
    QUERY_GENERATION = "query_generation"
    SQL_EXECUTION = "sql_execution"
    DATA_VALIDATION = "data_validation"
    DATA_CLEANING = "data_cleaning"

CAPABILITY_DESCRIPTIONS = {
    Capability.MATH_OPERATIONS: "Perform mathematical calculations and solve equations.",
    Capability.ACCOUNT_BALANCES: "Fetch account balances from financial services.",
    Capability.TEXT_SUMMARIZATION: "Summarize long bodies of text into concise summaries.",
    Capability.WEB_SEARCH: "Search the internet for up-to-date information.",
    Capability.QUERY_GENERATION: "Convert natural language into SQL queries.",
    Capability.SQL_EXECUTION: "Run SQL queries and return structured results.",
    Capability.DATA_VALIDATION: "Check data quality and correctness.",
    Capability.DATA_CLEANING: "Fix, format, or remove inconsistent or duplicate data."
}

def get_capability_description(capability: Capability) -> str:
    return CAPABILITY_DESCRIPTIONS.get(capability, "Unknown capability")

class AgentCapability:
    """
    Agents would publicly advertise their capabilities on initialization:
    """    
    agent_id: str
    supported_reasoning_modes: List[str]  # e.g., ["chain-of-thought", "recursive"]
    tool_proficiencies: List[str]  # Tool IDs this agent can use effectively
    specializations: List[str]  # "creative", "analytical", etc.
    performance_metrics: Dict  # Historical performance by task type