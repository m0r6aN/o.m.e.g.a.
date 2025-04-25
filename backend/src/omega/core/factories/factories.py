# Enhanced factories.py - Consolidated TaskFactory Implementation

from collections import defaultdict
import datetime as dt
import json
import os
import re
import statistics
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import uuid

from omega.core.models.models import (
    Message,
    ReasoningStrategy,
    Task,
    TaskResult,
    MessageIntent,
    TaskEvent,
    TaskOutcome,
    ReasoningEffort,
    get_reasoning_strategy,
)
from omega.core.config import logger

# --- Reasoning Effort Estimation ---

def estimate_reasoning_effort(content: str, event: Optional[str] = None, intent: Optional[str] = None) -> ReasoningEffort:
    """
    Automatically determines computational effort required for tasks based on content and context.
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

    logger.trace(f"Estimated effort: {effort.value} for content (first 50 chars): '{content[:50]}...' (Event: {event}, Intent: {intent})")
    return effort

# --- Tool Cache System ---

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
        self.tool_associations[tool_id] = set()
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
        
        for key, timestamp in self.last_accessed.items():
            if (now - timestamp).total_seconds() > self.ttl:
                expired_keys.append(key)
                
        for key in expired_keys:
            if key in self.cache:
                del self.cache[key]
            del self.last_accessed[key]
            
            # Remove from tool associations
            for tool_id, keys in self.tool_associations.items():
                if key in keys:
                    keys.remove(key)
                    
        return len(expired_keys)


# --- Object Factories ---

class TaskFactory:
    """
    Enhanced TaskFactory for reasoning effort assessment in multi-agent systems.
    Implements sophisticated keyword-based task classification with contextual adjustments.
    """
    # Version tracking
    VERSION = "1.0.0"
    
    # Configuration flags (can be controlled via env vars or settings)
    AUTO_TUNING_ENABLED = os.getenv("TASK_FACTORY_AUTOTUNE", "true").lower() == "true"
    RETAIN_HISTORY = True
    HISTORY_LIMIT = 1000
    MIN_SAMPLES_FOR_TUNING = 10
    
    # Tool cache instance
    tool_cache = ToolCache()
    
    # Outcome tracking for future model improvement
    outcome_history = []
    
    # Keyword categories with their respective weights
    KEYWORD_WEIGHTS = {
        "analytical": {
            "keywords": {"analyze", "evaluate", "assess", "research", "investigate", "study", 
                        "examine", "review", "diagnose", "audit", "survey", "inspect"},
            "weight": 1.0
        },
        "comparative": {
            "keywords": {"compare", "contrast", "differentiate", "versus", "pros and cons", 
                        "trade-off", "benchmark", "measure against", "weigh", "rank"},
            "weight": 1.5
        },
        "creative": {
            "keywords": {"design", "create", "optimize", "improve", "innovate", "develop",
                        "build", "construct", "craft", "devise", "formulate", "invent"},
            "weight": 2.0
        },
        "complex": {
            "keywords": {"hypothesize", "synthesize", "debate", "refactor", "architect",
                        "theorize", "model", "simulate", "predict", "extrapolate", 
                        "integrate", "transform", "restructure"},
            "weight": 2.5
        }
    }
    
    # Task events categorized by typical reasoning effort
    EVENT_EFFORT_MAP = {
        "high": {"refine", "escalate", "critique", "conclude", "analyze", "evaluate", "compare", "refactor"},
        "medium": {"plan", "execute"},
        "low": {"complete", "info"}
    }
    
    # Base thresholds for word count
    WORD_COUNT_THRESHOLDS = {
        "base": {
            "high": 50,
            "medium": 20
        },
        # How much to reduce threshold per point of complexity score
        "scaling_factor": {
            "high": 5,
            "medium": 2
        }
    }
    
    @classmethod
    async def prepare_tools_for_task(cls, task: Task, redis_client) -> Task:
        """Preload likely needed tools for a task and attach to metadata"""
        if not task.metadata:
            task.metadata = {}
        
        # Extract key terms that might indicate tool needs
        content = task.content.lower()
        
        # Predict tools based on task content and complexity
        predicted_tools = []
        
        # Check analytical needs
        if any(kw in content for kw in cls.KEYWORD_WEIGHTS["analytical"]["keywords"]):
            predicted_tools.append("data_analysis")
            
        # Check web-based needs
        if "search" in content or "find" in content or "lookup" in content:
            predicted_tools.append("web_search")
            
        # Check coding needs
        if "code" in content or "program" in content or "script" in content:
            predicted_tools.append("code_execution")
            
        # Check file handling needs
        if "file" in content or "document" in content or "read" in content:
            predicted_tools.append("file_operations")
            
        # Add more predictive rules based on task complexity
        if task.reasoning_effort == ReasoningEffort.HIGH:
            # Complex tasks might need specialized tools
            predicted_tools.append("advanced_reasoning")
        
        # Cache lookup and updates
        cache_updates = []
        for tool_type in predicted_tools:
            cache_key = cls.tool_cache.compute_key(tool_type)
            
            # Check if in cache
            cached_tools = cls.tool_cache.get(cache_key)
            if not cached_tools:
                # Cache miss - add to list for update
                cache_updates.append(tool_type)
            else:
                # Add cached tools to task metadata
                if "available_tools" not in task.metadata:
                    task.metadata["available_tools"] = {}
                task.metadata["available_tools"][tool_type] = cached_tools
        
        # If any cache misses, publish tool cache update request
        if cache_updates:
            await redis_client.publish(
                "frontend_channel",
                json.dumps({
                    "type": "tool_cache_update",
                    "status": "loading",
                    "tool_types": cache_updates,
                    "task_id": task.task_id,
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat()
                })
            )
            
            # Also publish to tools agent channel
            await redis_client.publish(
                "tools_agent_channel",
                json.dumps({
                    "type": "cache_tools",
                    "tool_types": cache_updates,
                    "task_id": task.task_id,
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat()
                })
            )
        
        return task
    
    @classmethod
    async def update_tool_cache(cls, tool_type: str, tools: List[Dict], ttl: int = None):
        """Update the tool cache with new tools"""
        cache_key = cls.tool_cache.compute_key(tool_type)
        tool_ids = [tool.get("id") for tool in tools if "id" in tool]
        cls.tool_cache.set(cache_key, tools, tool_ids)
    
    @staticmethod
    def count_keyword_occurrences(content: str, keywords: set) -> int:
        """Count all occurrences of each keyword in the content."""
        content_lower = content.lower()
        count = 0
        
        # Handle multi-word keywords
        for keyword in keywords:
            if " " in keyword:
                count += content_lower.count(keyword)
            else:
                # For single-word keywords, ensure we match whole words
                count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', content_lower))
                
        return count
    
    @classmethod
    def calculate_complexity_score(cls, content: str) -> Tuple[float, Dict[str, Any]]:
        """Calculate complexity score based on keyword categories with detailed breakdown."""
        scores_by_category = {}
        matched_keywords = {}
        total_score = 0.0
        
        for category, data in cls.KEYWORD_WEIGHTS.items():
            # Find which specific keywords were matched
            matched = set()
            content_lower = content.lower()
            
            for keyword in data["keywords"]:
                if " " in keyword:
                    if keyword in content_lower:
                        matched.add(keyword)
                else:
                    # For single-word keywords, ensure we match whole words
                    if re.search(r'\b' + re.escape(keyword) + r'\b', content_lower):
                        matched.add(keyword)
            
            # Count total occurrences
            category_count = cls.count_keyword_occurrences(content, data["keywords"])
            category_score = category_count * data["weight"]
            
            scores_by_category[category] = category_count
            if matched:
                matched_keywords[category] = list(matched)
            total_score += category_score
        
        # Apply category overlap penalty - if task spans multiple domains, it's likely more complex
        active_categories = sum(1 for count in scores_by_category.values() if count > 0)
        if active_categories > 2:
            overlap_bonus = 0.5 * (active_categories - 2)
            total_score += overlap_bonus
            scores_by_category["overlap_bonus"] = overlap_bonus
            
        return total_score, {"scores": scores_by_category, "matched_keywords": matched_keywords}
    
    @classmethod
    def estimate_reasoning_effort(
        cls,
        content: str, 
        event: Optional[str] = None, 
        intent: Optional[str] = None,
        confidence: Optional[float] = None,
        deadline_pressure: Optional[float] = None
    ) -> Tuple[ReasoningEffort, Dict[str, any]]:
        """
        Estimate the reasoning effort required for a task based on multiple factors.
        Returns the effort level and a diagnostic object explaining the decision.
        """
        diagnostics = {
            "word_count": 0,
            "complexity_score": 0.0,
            "category_scores": {},
            "matched_keywords": {},
            "base_effort": None,
            "event_adjustment": None,
            "intent_adjustment": None,
            "confidence_adjustment": None,
            "category_adjustment": None,
            "deadline_adjustment": None,
            "final_effort": None
        }
        
        # Calculate complexity score and get diagnostic data
        complexity_score, complexity_details = cls.calculate_complexity_score(content)
        word_count = len(content.split())
        
        diagnostics["word_count"] = word_count
        diagnostics["complexity_score"] = complexity_score
        diagnostics["category_scores"] = complexity_details["scores"]
        diagnostics["matched_keywords"] = complexity_details["matched_keywords"]
        
        # Calculate dynamic thresholds based on complexity
        high_threshold = max(10, cls.WORD_COUNT_THRESHOLDS["base"]["high"] - 
                            (complexity_score * cls.WORD_COUNT_THRESHOLDS["scaling_factor"]["high"]))
        medium_threshold = max(5, cls.WORD_COUNT_THRESHOLDS["base"]["medium"] - 
                            (complexity_score * cls.WORD_COUNT_THRESHOLDS["scaling_factor"]["medium"]))
        
        # Determine base effort from content complexity and length
        if complexity_score >= 3 or word_count > high_threshold:
            base_effort = ReasoningEffort.HIGH
        elif complexity_score >= 1 or word_count > medium_threshold:
            base_effort = ReasoningEffort.MEDIUM
        else:
            base_effort = ReasoningEffort.LOW
            
        diagnostics["base_effort"] = base_effort.value
        diagnostics["thresholds"] = {
            "high": high_threshold,
            "medium": medium_threshold
        }
        
        # Final effort starts with base effort
        final_effort = base_effort
        
        # Event-based adjustment
        if event:
            for effort_level, events in cls.EVENT_EFFORT_MAP.items():
                if event in events:
                    event_effort = ReasoningEffort(effort_level)
                    if event_effort.value == "high" and final_effort != ReasoningEffort.HIGH:
                        final_effort = ReasoningEffort.HIGH
                        diagnostics["event_adjustment"] = f"Increased to HIGH due to {event} event"
                    elif event_effort.value == "medium" and final_effort == ReasoningEffort.LOW:
                        final_effort = ReasoningEffort.MEDIUM
                        diagnostics["event_adjustment"] = f"Increased to MEDIUM due to {event} event"
                    break
        
        # Intent-based adjustment
        if intent == "modify_task":
            if final_effort != ReasoningEffort.HIGH:
                final_effort = ReasoningEffort.HIGH
                diagnostics["intent_adjustment"] = "Increased to HIGH due to modify_task intent"
        
        # Confidence-based adjustment
        if confidence is not None and confidence < 0.7:
            if final_effort == ReasoningEffort.LOW:
                final_effort = ReasoningEffort.MEDIUM
                diagnostics["confidence_adjustment"] = f"Increased to MEDIUM due to low confidence ({confidence})"
            elif final_effort == ReasoningEffort.MEDIUM:
                final_effort = ReasoningEffort.HIGH
                diagnostics["confidence_adjustment"] = f"Increased to HIGH due to low confidence ({confidence})"
                
        # Deadline pressure adjustment
        if deadline_pressure is not None and deadline_pressure > 0.8:
            if final_effort != ReasoningEffort.HIGH:
                prev_effort = final_effort
                final_effort = ReasoningEffort.HIGH
                diagnostics["deadline_adjustment"] = f"Increased from {prev_effort.value} to HIGH due to high deadline pressure ({deadline_pressure})"
        
        # Edge case guardrail: Complex keywords should never result in LOW effort
        complex_count = diagnostics["category_scores"].get("complex", 0)
        if complex_count > 0 and final_effort == ReasoningEffort.LOW:
            final_effort = ReasoningEffort.MEDIUM
            diagnostics["category_adjustment"] = "Bumped to MEDIUM due to presence of complex keywords"
                
        diagnostics["final_effort"] = final_effort.value
        
        return final_effort, diagnostics
    
    @classmethod
    def record_task_outcome(cls, task_id: str, diagnostics: Dict, actual_duration: float, 
                           success: bool, feedback: Optional[str] = None) -> None:
        """
        Record the outcome of a task for future model refinement.
        
        Parameters:
        - task_id: The ID of the completed task
        - diagnostics: The diagnostic data returned when creating the task
        - actual_duration: How long the task took to complete (seconds)
        - success: Whether the task completed successfully
        - feedback: Optional feedback about the task difficulty
        """
        outcome_data = {
            "task_id": task_id,
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "diagnostics": diagnostics,
            "actual_duration": actual_duration,
            "success": success,
            "feedback": feedback
        }
        
        cls.outcome_history.append(outcome_data)
        
        # If we have sufficient data, analyze and potentially adjust weights
        if len(cls.outcome_history) >= 100:
            cls._analyze_outcomes()
    
    @classmethod
    def _analyze_outcomes(cls) -> None:
        """
        Analyze recorded outcomes to refine the model based on real-world performance.
        This method is called automatically after accumulating enough task outcomes.
        """
        logger.info(f"Analyzing {len(cls.outcome_history)} task outcomes for model refinement")
        
        if len(cls.outcome_history) < 50:
            logger.warning("Not enough data for meaningful analysis - need at least 50 tasks")
            return
        
        # Group tasks by reasoning effort level
        tasks_by_effort = defaultdict(list)
        for outcome in cls.outcome_history:
            effort = outcome["diagnostics"]["final_effort"]
            tasks_by_effort[effort].append(outcome)
        
        # Calculate average completion time and success rate by effort level
        effort_stats = {}
        for effort, tasks in tasks_by_effort.items():
            durations = [task["actual_duration"] for task in tasks]
            success_rate = sum(1 for task in tasks if task["success"]) / len(tasks)
            
            effort_stats[effort] = {
                "count": len(tasks),
                "avg_duration": sum(durations) / len(durations),
                "median_duration": sorted(durations)[len(durations) // 2],
                "std_duration": statistics.stdev(durations) if len(durations) > 1 else 0,
                "success_rate": success_rate,
                "task_ids": [task["task_id"] for task in tasks]
            }
        
        logger.info(f"Effort level statistics: {effort_stats}")
        
        # Look for miscategorized tasks
        misclassifications = []
        
        # If LOW effort tasks are taking longer than MEDIUM ones, they're miscategorized
        if ("low" in effort_stats and "medium" in effort_stats and 
            effort_stats["low"]["avg_duration"] > effort_stats["medium"]["avg_duration"] * 0.8):
            misclassifications.append({
                "issue": "LOW tasks taking too long",
                "recommendation": "Adjust LOW effort thresholds or increase analytical weight"
            })
        
        # If HIGH tasks are completing very quickly with high success, they might be overestimated
        if ("high" in effort_stats and "medium" in effort_stats and 
            effort_stats["high"]["avg_duration"] < effort_stats["medium"]["avg_duration"] * 1.5 and
            effort_stats["high"]["success_rate"] > 0.9):
            misclassifications.append({
                "issue": "HIGH tasks completing quickly with high success",
                "recommendation": "Adjust HIGH thresholds or decrease complex weights"
            })
        
        # Analyze which adjustment factors are most influential
        adjustment_counts = defaultdict(int)
        for outcome in cls.outcome_history:
            diagnostics = outcome["diagnostics"]
            for key in diagnostics:
                if key.endswith("_adjustment") and diagnostics[key] is not None:
                    adjustment_counts[key] += 1
        
        # Find the factors that are most frequently causing adjustments
        top_adjustments = sorted(adjustment_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Analyze keyword category impact
        category_impact = defaultdict(lambda: {"count": 0, "duration": 0, "keywords": defaultdict(int)})
        
        for outcome in cls.outcome_history:
            diagnostics = outcome["diagnostics"]
            duration = outcome["actual_duration"]
            
            # Track impact by keyword category
            for category, count in diagnostics.get("category_scores", {}).items():
                if count > 0 and category in cls.KEYWORD_WEIGHTS:
                    category_impact[category]["count"] += 1
                    category_impact[category]["duration"] += duration
                    
                    # Track which specific keywords were matched
                    for keyword in diagnostics.get("matched_keywords", {}).get(category, []):
                        category_impact[category]["keywords"][keyword] += 1
        
        # Calculate average duration per category
        for category, data in category_impact.items():
            if data["count"] > 0:
                data["avg_duration"] = data["duration"] / data["count"]
                
                # Find most impactful keywords in this category
                data["top_keywords"] = sorted(
                    data["keywords"].items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:5]  # Top 5 keywords
        
        # Generate tuning recommendations
        tuning_recommendations = []
        
        # Check if any keyword categories are causing much longer task durations
        category_avg_durations = {c: d["avg_duration"] for c, d in category_impact.items() 
                                if d["count"] >= cls.MIN_SAMPLES_FOR_TUNING and c in cls.KEYWORD_WEIGHTS}
        
        if category_avg_durations:
            avg_all = statistics.mean(category_avg_durations.values())
            std_all = statistics.stdev(category_avg_durations.values()) if len(category_avg_durations) > 1 else 0
            
            for category, avg_duration in category_avg_durations.items():
                # Only consider statistically significant deviations with enough samples
                significant_deviation = abs(avg_duration - avg_all) > std_all * 1.5  # 1.5 standard deviations
                
                if significant_deviation and category_impact[category]["count"] >= cls.MIN_SAMPLES_FOR_TUNING:
                    if avg_duration > avg_all * 1.3:  # 30% longer than average
                        tuning_recommendations.append({
                            "target": f"{category}_weight",
                            "current": cls.KEYWORD_WEIGHTS[category]["weight"],
                            "suggested": min(5.0, cls.KEYWORD_WEIGHTS[category]["weight"] * 1.2),
                            "reason": f"{category} tasks taking {avg_duration:.1f}s vs {avg_all:.1f}s average"
                        })
                    elif avg_duration < avg_all * 0.7:  # 30% shorter than average
                        tuning_recommendations.append({
                            "target": f"{category}_weight",
                            "current": cls.KEYWORD_WEIGHTS[category]["weight"],
                            "suggested": max(0.5, cls.KEYWORD_WEIGHTS[category]["weight"] * 0.8),
                            "reason": f"{category} tasks taking only {avg_duration:.1f}s vs {avg_all:.1f}s average"
                        })
        
        # Check for threshold adjustment needs
        if len(misclassifications) > 0:
            if "LOW tasks taking too long" in [m["issue"] for m in misclassifications]:
                tuning_recommendations.append({
                    "target": "word_count_medium_threshold",
                    "current": cls.WORD_COUNT_THRESHOLDS["base"]["medium"],
                    "suggested": min(30, cls.WORD_COUNT_THRESHOLDS["base"]["medium"] + 5),
                    "reason": "LOW tasks consistently exceeding expected duration"
                })
            
            if "HIGH tasks completing quickly with high success" in [m["issue"] for m in misclassifications]:
                tuning_recommendations.append({
                    "target": "word_count_high_threshold",
                    "current": cls.WORD_COUNT_THRESHOLDS["base"]["high"],
                    "suggested": max(30, cls.WORD_COUNT_THRESHOLDS["base"]["high"] - 5),
                    "reason": "HIGH tasks completing faster than expected"
                })
        
        # Make weight adjustments if authorized
        if cls.AUTO_TUNING_ENABLED and tuning_recommendations:
            logger.info(f"Applying {len(tuning_recommendations)} automatic tuning adjustments")
            
            for rec in tuning_recommendations:
                if rec["target"].endswith("_weight"):
                    category = rec["target"].replace("_weight", "")
                    if category in cls.KEYWORD_WEIGHTS:
                        old_weight = cls.KEYWORD_WEIGHTS[category]["weight"]
                        new_weight = rec["suggested"]
                        
                        # Apply the change
                        cls.KEYWORD_WEIGHTS[category]["weight"] = new_weight
                        
                        logger.info(f"Adjusted {category} weight: {old_weight:.1f} -> {new_weight:.1f}: {rec['reason']}")
                
                elif rec["target"] == "word_count_medium_threshold":
                    old_value = cls.WORD_COUNT_THRESHOLDS["base"]["medium"]
                    new_value = rec["suggested"]
                    cls.WORD_COUNT_THRESHOLDS["base"]["medium"] = new_value
                    logger.info(f"Adjusted medium word threshold: {old_value} -> {new_value}: {rec['reason']}")
                
                elif rec["target"] == "word_count_high_threshold":
                    old_value = cls.WORD_COUNT_THRESHOLDS["base"]["high"]
                    new_value = rec["suggested"]
                    cls.WORD_COUNT_THRESHOLDS["base"]["high"] = new_value
                    logger.info(f"Adjusted high word threshold: {old_value} -> {new_value}: {rec['reason']}")
        
        # Log all findings
        analysis_results = {
            "timestamp": dt.datetime.now().isoformat(),
            "version": cls.VERSION,
            "sample_size": len(cls.outcome_history),
            "effort_stats": effort_stats,
            "misclassifications": misclassifications,
            "top_adjustments": top_adjustments,
            "category_impact": {k: {kk: vv for kk, vv in v.items() if kk != "keywords"} 
                                for k, v in category_impact.items()},
            "keyword_impact": {k: dict(v["top_keywords"]) for k, v in category_impact.items() if "top_keywords" in v},
            "tuning_recommendations": tuning_recommendations,
            "applied_changes": cls.AUTO_TUNING_ENABLED
        }
        
        logger.info(f"Analysis complete: {len(tuning_recommendations)} recommendations generated")
        
        # In a production system, we might store these results in a database
        try:
            with open("task_factory_analysis_results.json", "w") as f:
                json.dump(analysis_results, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save analysis results: {e}")
        
        # Retain or clear history based on configuration
        if cls.RETAIN_HISTORY:
            # Keep the most recent N tasks
            cls.outcome_history = cls.outcome_history[-cls.HISTORY_LIMIT:]
        else:
            # Start fresh
            cls.outcome_history = []
    
    @classmethod
    async def create_task(
        cls,
        task_id: str,
        agent: str,
        content: str,
        target_agent: str,
        intent: MessageIntent = MessageIntent.START_TASK,
        event: TaskEvent = TaskEvent.PLAN,
        confidence: Optional[float] = 0.9,
        timestamp: Optional[dt.datetime] = None,
        priority: Optional[int] = None,
        deadline_pressure: Optional[float] = None,
        redis_client = None
    ) -> Tuple[Task, Dict]:
        """
        Create a Task object with dynamically estimated reasoning effort.
        Returns both the Task and diagnostic information about the reasoning effort estimation.
        
        Parameters:
        - task_id: Unique identifier for the task
        - agent: The agent creating the task
        - content: The task description
        - target_agent: The agent who will perform the task
        - intent: The message intent
        - event: The task event type
        - confidence: Confidence level in this task (0.0-1.0)
        - timestamp: When the task was created (default: now)
        - priority: Optional priority level (higher = more important)
        - deadline_pressure: Optional value indicating time pressure (0.0-1.0)
        - redis_client: Optional Redis client for tool preparation
        """
        # Add context factors to diagnostics for comprehensive tracking
        context_factors = {
            "priority": priority,
            "deadline_pressure": deadline_pressure
        }
        
        # Estimate the reasoning effort
        reasoning_effort, diagnostics = cls.estimate_reasoning_effort(
            content, 
            event.value, 
            intent.value,
            confidence,
            deadline_pressure
        )
        
        # Add context factors to diagnostics
        diagnostics["context_factors"] = context_factors
        
        # Determine the appropriate reasoning strategy based on effort
        reasoning_strategy = ReasoningStrategy(get_reasoning_strategy(reasoning_effort))
        
        # Create the task with reasoning effort and strategy
        task = Task(
            type="task",  # Set type for BaseMessage
            task_id=task_id,
            agent=agent,
            content=content,
            intent=intent,
            target_agent=target_agent,
            event=event,
            confidence=confidence,
            timestamp=timestamp or dt.datetime.now(dt.timezone.utc),
            reasoning_effort=reasoning_effort,
            reasoning_strategy=reasoning_strategy,
            metadata={"diagnostics": diagnostics}  # Include diagnostics in metadata
        )
        
        # Prepare tools for this task if Redis client provided
        if redis_client:
            try:
                # This is awaitable, so we need to use await
                task = await cls.prepare_tools_for_task(task, redis_client)
            except Exception as e:
                logger.error(f"Error preparing tools for task {task_id}: {e}")
                # Continue despite error - tools are enhancement, not critical
        
        # Store diagnostics with version info for future reference
        diagnostics["model_version"] = cls.VERSION
        
        logger.debug(f"Created task with ID {task_id}, targeting {target_agent}, effort: {reasoning_effort.value}, strategy: {reasoning_strategy.value}")
        
        return task, diagnostics


class MessageFactory:
    """Generates Message objects for agent communication."""
    @staticmethod
    def create_message(
        task_id: str,
        agent: str,
        content: str,
        intent: MessageIntent = MessageIntent.CHAT,
        target_agent: Optional[str] = None,
        timestamp: Optional[dt.datetime] = None
    ) -> Message:
        """
        Creates a standard Message object.
        """
        logger.debug(f"Creating Message (TaskID: {task_id}): Agent={agent}, Intent={intent.value}, Target={target_agent}")
        return Message(
            task_id=task_id,
            agent=agent,
            content=content,
            intent=intent,
            target_agent=target_agent,
            timestamp=timestamp or dt.datetime.now(dt.timezone.utc)
        )


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
        confidence: Optional[float] = 0.9,
        reasoning_effort: Optional[ReasoningEffort] = None, # Can be passed if known, otherwise estimated
        timestamp: Optional[dt.datetime] = None
    ) -> TaskResult:
        """
        Creates a TaskResult object. Estimates reasoning effort if not provided.
        """
        if reasoning_effort is None:
            # Estimate effort based on the *result* content and context
            reasoning_effort = estimate_reasoning_effort(content, event.value, MessageIntent.MODIFY_TASK.value) # Assume modify intent for results

        logger.debug(f"Creating TaskResult (TaskID: {task_id}): Agent={agent}, Event={event.value}, Outcome={outcome.value}, Effort={reasoning_effort.value}")

        return TaskResult(
            task_id=task_id,
            agent=agent,
            content=content,
            # Intent is tricky for results, MODIFY_TASK seems most appropriate for updates/feedback
            intent=MessageIntent.MODIFY_TASK,
            target_agent=target_agent,
            event=event,
            outcome=outcome,
            contributing_agents=contributing_agents or [agent], # Default to self if not specified
            confidence=confidence,
            reasoning_effort=reasoning_effort,
            timestamp=timestamp or dt.datetime.now(dt.timezone.utc)
        )