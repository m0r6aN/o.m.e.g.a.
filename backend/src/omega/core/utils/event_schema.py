# Redis event schema for all channels

# Future Schema Upgrades

# Feature              | Description
# agent_id / task_id   | For linking events across a full trace
# reasoning_effort	   | Broadcast how much thought a task required
# tool_name	           | Auto-injected for tool-related events
# result_summary	   | A trimmed, LLM-readable result that can be indexed

import json
import datetime
from typing import Optional, Dict, Any

def current_utc_iso():
    return datetime.datetime.now(timezone.utc).isoformat() + "Z"

def format_event(
    event: str,
    channel_type: str,
    source: str,
    payload: Optional[Dict[str, Any]] = None,
    cached: Optional[bool] = None,
) -> str:
    event_dict = {
        "event": event,
        "channel_type": channel_type,
        "source": source,
        "timestamp": current_utc_iso(),
    }

    if payload:
        event_dict["payload"] = payload

    if cached is not None:
        event_dict["cached"] = cached

    return json.dumps(event_dict)
