# backend/factories/tool_cache.py

"""
Provides a caching mechanism for tool recommendations and results.
"""

import datetime as dt
import json
from collections import defaultdict
from typing import Any, Dict, List, Optional

class ToolCache:
    """Caches tool recommendations and results for efficient reuse."""

    def __init__(self, ttl: int = 3600):
        self.cache = {}
        self.ttl = ttl  # Default 1-hour TTL
        self.last_accessed = {}
        self.tool_associations = defaultdict(set)  # Maps tools to cache keys that contain them

    def get(self, key: str) -> Optional[Any]:
        """Get a cached item if it exists and is not expired."""
        if key not in self.cache:
            return None

        item = self.cache[key]
        self.last_accessed[key] = dt.datetime.now(dt.timezone.utc)
        return item

    def set(self, key: str, value: Any, tool_ids: List[str] = None) -> None:
        """Set a cache item with optional tool associations."""
        self.cache[key] = value
        self.last_accessed[key] = dt.datetime.now(dt.timezone.utc)

        # Record tool associations for invalidation
        if tool_ids:
            for tool_id in tool_ids:
                self.tool_associations[tool_id].add(key)

    def invalidate_for_tool(self, tool_id: str) -> List[str]:
        """Invalidate all cache entries containing a specific tool."""
        if tool_id not in self.tool_associations:
            return []

        keys_to_invalidate = list(self.tool_associations[tool_id])
        for key in keys_to_invalidate:
            if key in self.cache:
                del self.cache[key]
            if key in self.last_accessed:
                del self.last_accessed[key]

        # Clear the association
        del self.tool_associations[tool_id] # Fix: Use del instead of assigning set()
        return keys_to_invalidate

    def compute_key(self, query: str, context: Dict = None) -> str:
        """Compute a cache key from a query and optional context."""
        context_str = json.dumps(context or {}, sort_keys=True)
        normalized = query.lower().strip()
        return f"{normalized}:{context_str}"

    def cleanup_expired(self) -> int:
        """Remove expired cache entries. Returns count of removed entries."""
        now = dt.datetime.now(dt.timezone.utc)
        expired_keys = []

        for key, timestamp in list(self.last_accessed.items()): # Iterate over a copy for safe deletion
            if (now - timestamp).total_seconds() > self.ttl:
                expired_keys.append(key)

        removed_count = 0
        for key in expired_keys:
            if key in self.cache:
                del self.cache[key]
                removed_count += 1
            if key in self.last_accessed:
                 del self.last_accessed[key]

            # Remove from tool associations
            # Iterate through a copy of items for safe modification
            for tool_id, keys in list(self.tool_associations.items()):
                if key in keys:
                    keys.remove(key)
                    # Optional: remove tool_id if set becomes empty
                    if not keys:
                        del self.tool_associations[tool_id]

        return removed_count