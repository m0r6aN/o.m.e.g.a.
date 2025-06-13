# backend/factories/task_result_factory.py

"""
Factory for creating TaskResult objects to encapsulate task outcomes.
"""

import datetime as dt
from typing import Optional, List
import uuid

# Assuming models are in backend.models.models
from omega.core.models.task_models import TaskEvent, TaskOutcome, ReasoningEffort
from omega.core.models.message import MessageIntent
# Assuming logger is in backend.core.config
from omega.core.config import logger
# Import basic reasoning estimator from sibling module
from .reasoning import estimate_reasoning_effort


class TaskResultFactory:
    """Produces TaskResult objects to encapsulate task outcomes."""

    @staticmethod
    def create_task_result(
        task_id: str,
        agent: str, # The agent reporting the result
        content: str, # Description of the result or update
        target_agent: str, # Who should receive this result (e.g., orchestrator, original requester)
        event: TaskEvent, # The event associated with this result (e.g., COMPLETE, REFINE, INFO)
        outcome: TaskOutcome, # Success/failure status
        contributing_agents: Optional[List[str]] = None,
        confidence: Optional[float] = 1.0, # Default confidence for results
        reasoning_effort: Optional[ReasoningEffort] = None, # Can be passed if known, otherwise estimated
        result_id: Optional[str] = None, # Allow specifying ID
        timestamp: Optional[dt.datetime] = None
    ) -> TaskOutcome:
        """
        Creates a TaskOutcome object. Estimates reasoning effort based on result content if not provided.
        """
        res_id = result_id or str(uuid.uuid4())
        ts = timestamp or dt.datetime.now(dt.timezone.utc)

        estimated_effort = None
        if reasoning_effort is None:
            # Estimate effort based on the *result* content and context
            # Use a relevant intent, MODIFY_TASK often fits results/updates
            estimated_effort = estimate_reasoning_effort(content, event.value, MessageIntent.MODIFY_TASK.value)
            final_effort = estimated_effort
        else:
            final_effort = reasoning_effort # Use provided effort

        logger.debug(
            f"Creating TaskResult (ID: {res_id}, TaskID: {task_id}): "
            f"Agent={agent}, Event={event.value}, Outcome={outcome.value}, "
            f"Effort={'Provided: ' + final_effort.value if reasoning_effort else 'Estimated: ' + final_effort.value}"
        )

        return TaskOutcome(
            result_id=res_id,
            task_id=task_id,
            agent=agent,
            content=content,
            # Intent for results is often informational or signals task modification/completion state.
            # Using MODIFY_TASK as a general default, could be refined.
            intent=MessageIntent.MODIFY_TASK,
            target_agent=target_agent,
            event=event,
            outcome=outcome,
            contributing_agents=contributing_agents or [agent], # Default to self if not specified
            confidence=confidence,
            reasoning_effort=final_effort,
            timestamp=ts,
            # Add metadata if TaskResult model supports it, e.g., to store if effort was estimated
            # metadata={"effort_estimated": estimated_effort is not None}
        )