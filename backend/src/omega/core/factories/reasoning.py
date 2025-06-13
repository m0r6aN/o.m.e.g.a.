# backend/factories/reasoning.py

"""
Core functionality for estimating reasoning effort based on content and context.
"""

from typing import Optional
from enum import Enum

# Assuming models are in backend.core.models
from omega.core.models.reasoning import ReasoningEffort, ReasoningStrategy
from omega.core.models.task_models import TaskEvent
from omega.core.models.message import MessageIntent

# Assuming logger is in backend.core.config
from omega.core.config import logger


# --- Basic Reasoning Effort Estimation ---

def estimate_reasoning_effort(content: str, event: Optional[str] = None, intent: Optional[str] = None) -> ReasoningEffort:
    """
    Automatically determines computational effort required for tasks based on content and context.
    This is a basic version used where the full TaskFactory context isn't available/needed.
    """
    if not isinstance(content, str):
        logger.warning(f"Invalid content type for reasoning effort estimation: {type(content)}. Defaulting to LOW.")
        return ReasoningEffort.LOW

    keywords = {"analyze", "evaluate", "optimize", "debate", "compare", "hypothesize", "refactor", "critique", "reconcile", "arbitrate", "generate", "summarize"}
    word_count = len(content.split())
    content_lower = content.lower()
    has_keywords = any(kw in content_lower for kw in keywords)

    # Base effort on length and keywords
    if word_count <= 10 and not has_keywords:
        effort = ReasoningEffort.LOW
    elif word_count > 50 or has_keywords: # Increased threshold for high
        effort = ReasoningEffort.HIGH
    elif word_count > 15: # Medium range
        effort = ReasoningEffort.MEDIUM
    else:
        effort = ReasoningEffort.LOW # Default short non-keyword to low

    # Adjust based on context (event/intent)
    high_effort_events = {TaskEvent.REFINE.value, TaskEvent.ESCALATE.value, TaskEvent.CRITIQUE.value, TaskEvent.CONCLUDE.value}
    high_effort_intents = {MessageIntent.MODIFY_TASK.value, MessageIntent.START_TASK.value} # Starting a task often needs more effort

    if event and event in high_effort_events:
        # logger.debug(f"Effort overridden to HIGH due to event: {event}")
        effort = ReasoningEffort.HIGH
    elif intent and intent in high_effort_intents and effort != ReasoningEffort.HIGH:
         # Bump medium to high, keep low as low unless keywords/length triggered high
         if effort == ReasoningEffort.MEDIUM:
             # logger.debug(f"Effort promoted to HIGH due to intent: {intent}")
             effort = ReasoningEffort.HIGH
         elif effort == ReasoningEffort.LOW and (word_count > 15 or has_keywords): # If it was borderline low but has some indicators
              effort = ReasoningEffort.MEDIUM
              # logger.debug(f"Effort promoted to MEDIUM due to intent: {intent} and content indicators")

    logger.trace(f"Estimated effort (basic): {effort.value} for content (first 50 chars): '{content[:50]}...' (Event: {event}, Intent: {intent})")
    return effort