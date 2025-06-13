# backend/factories/message_factory.py

"""
Factory for creating standard Message objects used for agent communication.
"""

import datetime as dt
from typing import Optional
import uuid

# Assuming models are in backend.models.models
from omega.core.models.message import Message, MessageIntent
# Assuming logger is in backend.core.config
from omega.core.config import logger


class MessageFactory:
    """Generates Message objects for agent communication."""

    @staticmethod
    def create_message(
        task_id: str,
        agent: str,
        content: str,
        intent: MessageIntent = MessageIntent.CHAT,
        target_agent: Optional[str] = None,
        message_id: Optional[str] = None, # Allow specifying ID
        timestamp: Optional[dt.datetime] = None
    ) -> Message:
        """
        Creates a standard Message object.
        """
        msg_id = message_id or str(uuid.uuid4())
        ts = timestamp or dt.datetime.now(dt.timezone.utc)
        logger.debug(f"Creating Message (ID: {msg_id}, TaskID: {task_id}): Agent={agent}, Intent={intent.value}, Target={target_agent or 'broadcast'}")
        return Message(
            message_id=msg_id,
            task_id=task_id,
            agent=agent,
            content=content,
            intent=intent,
            target_agent=target_agent,
            timestamp=ts
        )