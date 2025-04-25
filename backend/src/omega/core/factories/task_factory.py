# backend/factories/task_factory.py

"""
Factory for creating Task objects, including advanced reasoning effort estimation,
outcome tracking/analysis, and tool preparation logic.
"""

import datetime as dt
import json
import os
import re
import statistics
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

# Assuming models are in backend.models.models
from omega.core.models.models import (
    ReasoningStrategy,
    Task,
    MessageIntent,
    TaskEvent,
    TaskOutcome,
    ReasoningEffort,
    get_reasoning_strategy,
)
# Assuming logger is in backend.core.config
from omega.core.config import logger
# Import from sibling modules in the same package
from .tool_cache import ToolCache


class TaskFactory:
    """
    Enhanced TaskFactory for reasoning effort assessment in multi-agent systems.
    Implements sophisticated keyword-based task classification with contextual adjustments,
    outcome analysis, and tool preparation.
    """
    # Version tracking
    VERSION = "1.0.0"

    # Configuration flags (can be controlled via env vars or settings)
    AUTO_TUNING_ENABLED = os.getenv("TASK_FACTORY_AUTOTUNE", "true").lower() == "true"
    RETAIN_HISTORY = True
    HISTORY_LIMIT = 1000
    MIN_SAMPLES_FOR_TUNING = 10

    # Tool cache instance - initialize it here
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
        "high": {TaskEvent.REFINE.value, TaskEvent.ESCALATE.value, TaskEvent.CRITIQUE.value, TaskEvent.CONCLUDE.value, "analyze", "evaluate", "compare", "refactor"}, # Added enum values
        "medium": {TaskEvent.PLAN.value, TaskEvent.EXECUTE.value}, # Added enum values
        "low": {TaskEvent.COMPLETE.value, TaskEvent.INFO.value} # Added enum values
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

        # Remove duplicates
        predicted_tools = list(set(predicted_tools))

        # Cache lookup and updates
        cache_updates = []
        if "available_tools" not in task.metadata:
            task.metadata["available_tools"] = {}

        for tool_type in predicted_tools:
            cache_key = cls.tool_cache.compute_key(tool_type)

            # Check if in cache
            cached_tools = cls.tool_cache.get(cache_key)
            if not cached_tools:
                # Cache miss - add to list for update
                if tool_type not in cache_updates: # Avoid duplicates
                    cache_updates.append(tool_type)
            else:
                # Add cached tools to task metadata
                task.metadata["available_tools"][tool_type] = cached_tools

        # If any cache misses, publish tool cache update request
        if cache_updates:
            try:
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
            except Exception as e:
                 logger.error(f"Failed to publish tool cache update for task {task.task_id}: {e}")


        return task

    @classmethod
    async def update_tool_cache(cls, tool_type: str, tools: List[Dict], ttl: Optional[int] = None):
        """Update the tool cache with new tools"""
        cache_key = cls.tool_cache.compute_key(tool_type)
        tool_ids = [tool.get("id") for tool in tools if tool.get("id")] # Simplified check
        cls.tool_cache.set(cache_key, tools, tool_ids)
        # TTL handling might be needed if different from default
        if ttl is not None and ttl != cls.tool_cache.ttl:
             logger.warning(f"Per-item TTL ({ttl}s) requested but ToolCache currently uses global TTL ({cls.tool_cache.ttl}s).")
             # Potentially implement per-item TTL in ToolCache if needed

    @staticmethod
    def count_keyword_occurrences(content: str, keywords: set) -> int:
        """Count all occurrences of each keyword in the content."""
        content_lower = content.lower()
        count = 0

        # Handle multi-word keywords first to avoid partial matches later
        multi_word_keywords = {kw for kw in keywords if " " in kw}
        single_word_keywords = keywords - multi_word_keywords

        for keyword in multi_word_keywords:
            count += content_lower.count(keyword)
            # Optional: remove counted occurrences to prevent double counting with single words?
            # content_lower = content_lower.replace(keyword, "") # Be careful with overlaps

        # Now count single words using regex for whole word matching
        for keyword in single_word_keywords:
            try:
                # Use word boundaries to avoid matching parts of words
                count += len(re.findall(r'\b' + re.escape(keyword) + r'\b', content_lower))
            except re.error as e:
                logger.error(f"Regex error counting keyword '{keyword}': {e}")

        return count

    @classmethod
    def calculate_complexity_score(cls, content: str) -> Tuple[float, Dict[str, Any]]:
        """Calculate complexity score based on keyword categories with detailed breakdown."""
        scores_by_category = {}
        matched_keywords = {}
        total_score = 0.0
        content_lower = content.lower() # Lowercase once

        for category, data in cls.KEYWORD_WEIGHTS.items():
            keywords_in_category = data["keywords"]
            matched_in_category = set()

            # Find which specific keywords were matched
            for keyword in keywords_in_category:
                if " " in keyword:
                    if keyword in content_lower:
                        matched_in_category.add(keyword)
                else:
                    # For single-word keywords, ensure we match whole words
                    try:
                        if re.search(r'\b' + re.escape(keyword) + r'\b', content_lower):
                            matched_in_category.add(keyword)
                    except re.error as e:
                         logger.error(f"Regex error searching for keyword '{keyword}': {e}")


            # Count total occurrences using the helper method
            category_count = cls.count_keyword_occurrences(content, keywords_in_category) # Use original content for counting
            category_score = category_count * data["weight"]

            scores_by_category[category] = category_count
            if matched_in_category:
                matched_keywords[category] = list(matched_in_category)
            total_score += category_score

        # Apply category overlap bonus - if task spans multiple domains, it's likely more complex
        active_categories = sum(1 for count in scores_by_category.values() if count > 0)
        if active_categories > 1: # Changed from > 2 to start bonus earlier
            overlap_bonus = 0.25 * (active_categories - 1) # Adjusted bonus factor
            total_score += overlap_bonus
            scores_by_category["overlap_bonus"] = overlap_bonus

        return round(total_score, 2), {"scores": scores_by_category, "matched_keywords": matched_keywords}

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
        Estimate the reasoning effort required for a task based on multiple factors using TaskFactory's enhanced logic.
        Returns the effort level and a diagnostic object explaining the decision.
        """
        if not isinstance(content, str):
            logger.warning(f"Invalid content type for reasoning effort estimation: {type(content)}. Defaulting to LOW.")
            # Provide minimal diagnostics for invalid input
            diagnostics = {
                "word_count": 0, "complexity_score": 0.0, "category_scores": {},
                "matched_keywords": {}, "base_effort": ReasoningEffort.LOW.value,
                "final_effort": ReasoningEffort.LOW.value, "error": "Invalid content type"
            }
            return ReasoningEffort.LOW, diagnostics

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
        diagnostics["category_scores"] = complexity_details.get("scores", {})
        diagnostics["matched_keywords"] = complexity_details.get("matched_keywords", {})

        # Calculate dynamic thresholds based on complexity
        high_thresh_base = cls.WORD_COUNT_THRESHOLDS["base"]["high"]
        medium_thresh_base = cls.WORD_COUNT_THRESHOLDS["base"]["medium"]
        high_scale = cls.WORD_COUNT_THRESHOLDS["scaling_factor"]["high"]
        medium_scale = cls.WORD_COUNT_THRESHOLDS["scaling_factor"]["medium"]

        # Ensure thresholds don't go below a minimum sensible value (e.g., 10 and 5 words)
        high_threshold = max(10, high_thresh_base - (complexity_score * high_scale))
        medium_threshold = max(5, medium_thresh_base - (complexity_score * medium_scale))

        diagnostics["thresholds"] = {
            "high": round(high_threshold, 1),
            "medium": round(medium_threshold, 1),
            "config": cls.WORD_COUNT_THRESHOLDS # Include base config for context
        }

        # Determine base effort from content complexity and length
        # Using >= 2.0 for High complexity score might be more robust than 3.0
        if complexity_score >= 2.0 or word_count > high_threshold:
            base_effort = ReasoningEffort.HIGH
        elif complexity_score >= 0.5 or word_count > medium_threshold: # Lowered complexity threshold for Medium
            base_effort = ReasoningEffort.MEDIUM
        else:
            base_effort = ReasoningEffort.LOW

        diagnostics["base_effort"] = base_effort.value

        # --- Apply Adjustments ---
        final_effort_level = base_effort.value # Use 'low', 'medium', 'high' strings internally for easier comparison
        current_effort_enum = base_effort

        # Event-based adjustment
        if event:
            event_lower = event.lower() # Ensure case-insensitivity
            for effort_level, events in cls.EVENT_EFFORT_MAP.items():
                if event_lower in events:
                    target_effort_level = effort_level # 'low', 'medium', 'high'
                    if (target_effort_level == "high" and final_effort_level != "high"):
                        final_effort_level = "high"
                        diagnostics["event_adjustment"] = f"Increased to HIGH due to '{event}' event"
                    elif (target_effort_level == "medium" and final_effort_level == "low"):
                        final_effort_level = "medium"
                        diagnostics["event_adjustment"] = f"Increased to MEDIUM due to '{event}' event"
                    # No downgrades based on event
                    break # Stop checking once event is found

        # Intent-based adjustment (convert enum value if needed)
        intent_val = intent.value if isinstance(intent, Enum) else intent
        if intent_val == MessageIntent.MODIFY_TASK.value or intent_val == MessageIntent.START_TASK.value: # Check start task too
            if final_effort_level == "low":
                final_effort_level = "medium" # Modifying/Starting a low task might make it medium
                diagnostics["intent_adjustment"] = f"Increased to MEDIUM due to '{intent_val}' intent"
            elif final_effort_level == "medium":
                 final_effort_level = "high" # Modifying/Starting a medium task often requires high effort
                 diagnostics["intent_adjustment"] = f"Increased to HIGH due to '{intent_val}' intent"


        # Confidence-based adjustment (Lower confidence implies more checking/effort)
        if confidence is not None and confidence < 0.75: # Threshold adjustment
            if final_effort_level == "low":
                final_effort_level = "medium"
                diagnostics["confidence_adjustment"] = f"Increased to MEDIUM due to low confidence ({confidence:.2f})"
            elif final_effort_level == "medium":
                final_effort_level = "high"
                diagnostics["confidence_adjustment"] = f"Increased to HIGH due to low confidence ({confidence:.2f})"

        # Deadline pressure adjustment
        if deadline_pressure is not None and deadline_pressure > 0.7: # Threshold adjustment
            if final_effort_level != "high":
                prev_effort_level = final_effort_level
                final_effort_level = "high"
                diagnostics["deadline_adjustment"] = f"Increased from {prev_effort_level} to HIGH due to high deadline pressure ({deadline_pressure:.2f})"

        # Final guardrail: Complex keywords should not result in LOW effort
        complex_count = diagnostics["category_scores"].get("complex", 0)
        if complex_count > 0 and final_effort_level == "low":
            final_effort_level = "medium"
            diagnostics["category_adjustment"] = "Bumped LOW to MEDIUM due to presence of 'complex' keywords"

        # Convert back to Enum
        final_effort = ReasoningEffort(final_effort_level)
        diagnostics["final_effort"] = final_effort.value

        logger.trace(f"Estimated effort (TaskFactory): {final_effort.value} for content (first 50 chars): '{content[:50]}...' Diagnostics: {diagnostics}")
        return final_effort, diagnostics

    @classmethod
    def record_task_outcome(cls, task_id: str, diagnostics: Dict, actual_duration: float,
                           success: bool, feedback: Optional[str] = None) -> None:
        """
        Record the outcome of a task for future model refinement.
        """
        if not isinstance(diagnostics, dict):
             logger.error(f"Invalid diagnostics type received for task {task_id}: {type(diagnostics)}. Skipping outcome recording.")
             return

        outcome_data = {
            "task_id": task_id,
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "diagnostics": diagnostics, # Should contain final_effort etc.
            "actual_duration": actual_duration,
            "success": success,
            "feedback": feedback,
            "model_version": diagnostics.get("model_version", cls.VERSION) # Record version used
        }

        cls.outcome_history.append(outcome_data)
        logger.debug(f"Recorded outcome for task {task_id}. History size: {len(cls.outcome_history)}")


        # Trigger analysis periodically or when history reaches a certain size
        if len(cls.outcome_history) % cls.HISTORY_LIMIT == 0 and len(cls.outcome_history) > 0:
             logger.info(f"Outcome history reached {len(cls.outcome_history)}, triggering analysis.")
             cls._analyze_outcomes()
        elif len(cls.outcome_history) >= cls.MIN_SAMPLES_FOR_TUNING * 5 and len(cls.outcome_history) < 100:
             # Maybe trigger analysis earlier if enough samples exist but below full limit
             if len(cls.outcome_history) % (cls.MIN_SAMPLES_FOR_TUNING * 2) == 0: # Analyse every 2*min_samples
                logger.info(f"Intermediate analysis trigger at {len(cls.outcome_history)} samples.")
                cls._analyze_outcomes()


    @classmethod
    def _analyze_outcomes(cls) -> None:
        """
        Analyze recorded outcomes to refine the model based on real-world performance.
        """
        history_size = len(cls.outcome_history)
        if history_size < cls.MIN_SAMPLES_FOR_TUNING:
            logger.warning(f"Not enough data for meaningful analysis - need at least {cls.MIN_SAMPLES_FOR_TUNING} tasks, have {history_size}.")
            return

        logger.info(f"Analyzing {history_size} task outcomes (v{cls.VERSION}) for model refinement...")

        # --- Data Preparation ---
        tasks_by_effort = defaultdict(list)
        valid_outcomes = 0
        for outcome in cls.outcome_history:
            # Basic validation
            if not isinstance(outcome, dict) or "diagnostics" not in outcome or not isinstance(outcome["diagnostics"], dict):
                logger.warning(f"Skipping invalid outcome data: {outcome.get('task_id', 'Unknown ID')}")
                continue
            effort = outcome["diagnostics"].get("final_effort")
            duration = outcome.get("actual_duration")
            if effort and duration is not None:
                tasks_by_effort[effort].append(outcome)
                valid_outcomes += 1
            else:
                logger.warning(f"Skipping outcome with missing effort/duration: {outcome.get('task_id', 'Unknown ID')}")

        if valid_outcomes < cls.MIN_SAMPLES_FOR_TUNING:
             logger.warning(f"Not enough *valid* data for analysis ({valid_outcomes} valid outcomes). Need {cls.MIN_SAMPLES_FOR_TUNING}.")
             return


        # --- Calculate Effort Level Statistics ---
        effort_stats = {}
        all_durations = []
        for effort, tasks in tasks_by_effort.items():
            task_count = len(tasks)
            if task_count == 0: continue

            durations = [task["actual_duration"] for task in tasks if isinstance(task.get("actual_duration"), (int, float))]
            all_durations.extend(durations)
            if not durations: continue # Skip if no valid durations for this effort level

            success_rate = sum(1 for task in tasks if task.get("success") is True) / task_count

            effort_stats[effort] = {
                "count": task_count,
                "avg_duration": statistics.mean(durations),
                "median_duration": statistics.median(durations),
                "stdev_duration": statistics.stdev(durations) if task_count > 1 else 0,
                "min_duration": min(durations),
                "max_duration": max(durations),
                "success_rate": round(success_rate, 3),
                # "task_ids": [task.get("task_id") for task in tasks] # Potentially too verbose for logs
            }

        logger.info(f"Effort level statistics: {json.dumps(effort_stats, indent=2)}")

        # --- Identify Potential Misclassifications ---
        misclassifications = []
        low_stats = effort_stats.get(ReasoningEffort.LOW.value)
        med_stats = effort_stats.get(ReasoningEffort.MEDIUM.value)
        high_stats = effort_stats.get(ReasoningEffort.HIGH.value)

        # LOW tasks taking longer than MEDIUM
        if low_stats and med_stats and low_stats["avg_duration"] > med_stats["avg_duration"] * 0.9: # 90% threshold
             if low_stats["count"] >= cls.MIN_SAMPLES_FOR_TUNING // 2 and med_stats["count"] >= cls.MIN_SAMPLES_FOR_TUNING // 2:
                misclassifications.append({
                    "issue": "LOW tasks avg duration >= MEDIUM tasks avg duration",
                    "details": f"LOW: {low_stats['avg_duration']:.2f}s (n={low_stats['count']}), MED: {med_stats['avg_duration']:.2f}s (n={med_stats['count']})",
                    "recommendation": "Consider making LOW criteria stricter (e.g., lower word count, fewer keywords) or MEDIUM criteria looser."
                })

        # MEDIUM tasks taking longer than HIGH
        if med_stats and high_stats and med_stats["avg_duration"] > high_stats["avg_duration"] * 0.9:
            if med_stats["count"] >= cls.MIN_SAMPLES_FOR_TUNING // 2 and high_stats["count"] >= cls.MIN_SAMPLES_FOR_TUNING // 2:
                misclassifications.append({
                    "issue": "MEDIUM tasks avg duration >= HIGH tasks avg duration",
                    "details": f"MED: {med_stats['avg_duration']:.2f}s (n={med_stats['count']}), HIGH: {high_stats['avg_duration']:.2f}s (n={high_stats['count']})",
                    "recommendation": "Consider making MEDIUM criteria stricter or HIGH criteria looser (e.g., increase HIGH complexity/word thresholds)."
                })

        # HIGH tasks completing too quickly with high success (potentially overestimated)
        if high_stats and med_stats and high_stats["avg_duration"] < med_stats["avg_duration"] * 1.2 and high_stats["success_rate"] > 0.95:
             if high_stats["count"] >= cls.MIN_SAMPLES_FOR_TUNING:
                misclassifications.append({
                    "issue": "HIGH tasks are fast & successful, may be overestimated",
                    "details": f"HIGH: {high_stats['avg_duration']:.2f}s (n={high_stats['count']}, success={high_stats['success_rate']:.1%}), MED avg: {med_stats['avg_duration']:.2f}s",
                    "recommendation": "Consider increasing HIGH thresholds or reducing weights for certain keywords."
                })

        # --- Analyze Adjustment Factor Impact ---
        adjustment_counts = defaultdict(int)
        adjustment_impact = defaultdict(lambda: {"count": 0, "total_duration_diff": 0.0})
        avg_duration_overall = statistics.mean(all_durations) if all_durations else 0

        for outcome in cls.outcome_history:
            diagnostics = outcome.get("diagnostics", {})
            duration = outcome.get("actual_duration")
            if not isinstance(diagnostics, dict) or duration is None: continue

            base_effort = diagnostics.get("base_effort")
            final_effort = diagnostics.get("final_effort")

            for key, value in diagnostics.items():
                if key.endswith("_adjustment") and value is not None:
                    adj_type = key.replace("_adjustment", "")
                    adjustment_counts[adj_type] += 1
                    # Estimate impact: compare duration to overall average if effort changed
                    if base_effort != final_effort:
                         adjustment_impact[adj_type]["count"] += 1
                         adjustment_impact[adj_type]["total_duration_diff"] += (duration - avg_duration_overall)


        top_adjustments = sorted(adjustment_counts.items(), key=lambda x: x[1], reverse=True)
        # Calculate average impact per adjustment type
        for adj_type, impact_data in adjustment_impact.items():
             if impact_data["count"] > 0:
                 impact_data["avg_duration_diff"] = impact_data["total_duration_diff"] / impact_data["count"]

        logger.debug(f"Top adjustment factors: {top_adjustments}")
        logger.debug(f"Adjustment impact (avg duration diff from overall mean): {dict(adjustment_impact)}")


        # --- Analyze Keyword Category Impact ---
        category_impact = defaultdict(lambda: {"count": 0, "total_duration": 0, "keywords": defaultdict(int), "durations": []})

        for outcome in cls.outcome_history:
            diagnostics = outcome.get("diagnostics", {})
            duration = outcome.get("actual_duration")
            if not isinstance(diagnostics, dict) or duration is None: continue

            category_scores = diagnostics.get("category_scores", {})
            matched_keywords = diagnostics.get("matched_keywords", {})

            for category, count in category_scores.items():
                if count > 0 and category in cls.KEYWORD_WEIGHTS: # Only track configured categories
                    category_impact[category]["count"] += 1
                    category_impact[category]["total_duration"] += duration
                    category_impact[category]["durations"].append(duration)

                    # Track which specific keywords were matched within this category for this task
                    for keyword in matched_keywords.get(category, []):
                        category_impact[category]["keywords"][keyword] += 1

        # Calculate stats per category
        for category, data in category_impact.items():
            if data["count"] >= cls.MIN_SAMPLES_FOR_TUNING // 2: # Need min samples for stats
                data["avg_duration"] = statistics.mean(data["durations"])
                data["median_duration"] = statistics.median(data["durations"])
                data["stdev_duration"] = statistics.stdev(data["durations"]) if data["count"] > 1 else 0
                # Find most impactful keywords (most frequent in this category)
                data["top_keywords"] = sorted(data["keywords"].items(), key=lambda x: x[1], reverse=True)[:5]
            # Don't need to keep raw durations list after calculation
            del data["durations"]


        logger.debug(f"Category impact analysis: {json.dumps(category_impact, indent=2, default=str)}") # Use default=str for Decimal/other types if needed

        # --- Generate Tuning Recommendations ---
        tuning_recommendations = []
        category_avg_durations = {
            c: d["avg_duration"] for c, d in category_impact.items()
            if "avg_duration" in d and d["count"] >= cls.MIN_SAMPLES_FOR_TUNING
        }

        if category_avg_durations:
            overall_avg = statistics.mean(category_avg_durations.values())
            overall_std = statistics.stdev(category_avg_durations.values()) if len(category_avg_durations) > 1 else 0

            for category, avg_duration in category_avg_durations.items():
                # Check deviation from the overall average *of category averages*
                if overall_std > 0: # Avoid division by zero
                    z_score = (avg_duration - overall_avg) / overall_std
                else:
                    z_score = 0

                # Recommend increase if significantly above average (e.g., z-score > 1.0)
                if z_score > 1.0:
                     current_weight = cls.KEYWORD_WEIGHTS[category]["weight"]
                     suggested_weight = min(5.0, round(current_weight * (1 + 0.1 * z_score), 2)) # Increase proportional to deviation
                     if suggested_weight > current_weight: # Only add if suggestion is an increase
                        tuning_recommendations.append({
                            "target": f"{category}_weight",
                            "current": current_weight,
                            "suggested": suggested_weight,
                            "reason": f"{category} tasks avg duration ({avg_duration:.1f}s) is high (Z={z_score:.1f}). Top keywords: {category_impact[category].get('top_keywords',[])}"
                        })
                # Recommend decrease if significantly below average (e.g., z-score < -1.0)
                elif z_score < -1.0:
                     current_weight = cls.KEYWORD_WEIGHTS[category]["weight"]
                     suggested_weight = max(0.1, round(current_weight * (1 + 0.1 * z_score), 2)) # Decrease proportional (z is negative)
                     if suggested_weight < current_weight: # Only add if suggestion is a decrease
                        tuning_recommendations.append({
                            "target": f"{category}_weight",
                            "current": current_weight,
                            "suggested": suggested_weight,
                            "reason": f"{category} tasks avg duration ({avg_duration:.1f}s) is low (Z={z_score:.1f}). Top keywords: {category_impact[category].get('top_keywords',[])}"
                        })

        # Recommendations based on misclassifications
        for miscls in misclassifications:
            if miscls["issue"] == "LOW tasks avg duration >= MEDIUM tasks avg duration":
                tuning_recommendations.append({
                    "target": "word_count_medium_threshold",
                    "current": cls.WORD_COUNT_THRESHOLDS["base"]["medium"],
                    "suggested": max(5, cls.WORD_COUNT_THRESHOLDS["base"]["medium"] - 3), # Decrease Medium threshold
                    "reason": miscls["issue"]
                })
                tuning_recommendations.append({
                    "target": "complexity_medium_threshold",
                    "current": 0.5, # Based on current estimate_reasoning_effort logic
                    "suggested": 0.3, # Decrease Medium complexity threshold suggestion
                    "reason": miscls["issue"] + " - adjust complexity threshold"
                })
            elif miscls["issue"] == "MEDIUM tasks avg duration >= HIGH tasks avg duration":
                 tuning_recommendations.append({
                    "target": "word_count_high_threshold",
                    "current": cls.WORD_COUNT_THRESHOLDS["base"]["high"],
                    "suggested": max(10, cls.WORD_COUNT_THRESHOLDS["base"]["high"] - 5), # Decrease High threshold
                    "reason": miscls["issue"]
                })
                 tuning_recommendations.append({
                    "target": "complexity_high_threshold",
                    "current": 2.0, # Based on current estimate_reasoning_effort logic
                    "suggested": 1.5, # Decrease High complexity threshold suggestion
                    "reason": miscls["issue"] + " - adjust complexity threshold"
                })
            elif miscls["issue"] == "HIGH tasks are fast & successful, may be overestimated":
                tuning_recommendations.append({
                    "target": "word_count_high_threshold",
                    "current": cls.WORD_COUNT_THRESHOLDS["base"]["high"],
                    "suggested": min(100, cls.WORD_COUNT_THRESHOLDS["base"]["high"] + 10), # Increase High threshold
                    "reason": miscls["issue"]
                })
                # Also suggest reducing weight of complex keywords if applicable
                if "complex" in cls.KEYWORD_WEIGHTS:
                     tuning_recommendations.append({
                        "target": "complex_weight",
                        "current": cls.KEYWORD_WEIGHTS["complex"]["weight"],
                        "suggested": max(0.5, round(cls.KEYWORD_WEIGHTS["complex"]["weight"] * 0.85, 2)),
                        "reason": miscls["issue"] + " - reduce complex weight"
                     })


        # --- Apply Tuning (if enabled) ---
        applied_changes_log = []
        if cls.AUTO_TUNING_ENABLED and tuning_recommendations:
            logger.info(f"Applying {len(tuning_recommendations)} automatic tuning adjustments...")

            # Use a set to avoid applying conflicting recommendations for the same target
            applied_targets = set()

            for rec in tuning_recommendations:
                 target = rec["target"]
                 if target in applied_targets:
                     logger.warning(f"Skipping duplicate/conflicting recommendation for target '{target}'")
                     continue

                 suggested = rec["suggested"]
                 reason = rec["reason"]

                 applied = False
                 if target.endswith("_weight"):
                     category = target.replace("_weight", "")
                     if category in cls.KEYWORD_WEIGHTS:
                         old_weight = cls.KEYWORD_WEIGHTS[category]["weight"]
                         # Apply bounded change (e.g., max 30% change per cycle)
                         new_weight = round(max(0.1, min(5.0, suggested)), 2)
                         # Limit change magnitude
                         if abs(new_weight - old_weight) / old_weight > 0.3:
                              new_weight = round(old_weight * (1.3 if new_weight > old_weight else 0.7) , 2)

                         if new_weight != old_weight:
                             cls.KEYWORD_WEIGHTS[category]["weight"] = new_weight
                             log_msg = f"Adjusted {category} weight: {old_weight:.2f} -> {new_weight:.2f}. Reason: {reason}"
                             logger.info(log_msg)
                             applied_changes_log.append(log_msg)
                             applied = True

                 elif target == "word_count_medium_threshold":
                     old_value = cls.WORD_COUNT_THRESHOLDS["base"]["medium"]
                     new_value = max(5, int(suggested)) # Ensure integer and minimum
                     if new_value != old_value:
                         cls.WORD_COUNT_THRESHOLDS["base"]["medium"] = new_value
                         log_msg = f"Adjusted medium word threshold: {old_value} -> {new_value}. Reason: {reason}"
                         logger.info(log_msg)
                         applied_changes_log.append(log_msg)
                         applied = True

                 elif target == "word_count_high_threshold":
                     old_value = cls.WORD_COUNT_THRESHOLDS["base"]["high"]
                     new_value = max(10, int(suggested)) # Ensure integer and minimum
                     if new_value != old_value:
                         cls.WORD_COUNT_THRESHOLDS["base"]["high"] = new_value
                         log_msg = f"Adjusted high word threshold: {old_value} -> {new_value}. Reason: {reason}"
                         logger.info(log_msg)
                         applied_changes_log.append(log_msg)
                         applied = True

                 # Note: Complexity thresholds are currently hardcoded in estimate_reasoning_effort
                 # To make them tunable, they'd need to be moved to class variables like WORD_COUNT_THRESHOLDS.
                 elif target in ["complexity_medium_threshold", "complexity_high_threshold"]:
                      logger.warning(f"Recommendation for '{target}' ignored - currently not a tunable parameter.")


                 if applied:
                     applied_targets.add(target)


        # --- Log Analysis Summary ---
        analysis_summary = {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "model_version": cls.VERSION,
            "sample_size": history_size,
            "valid_outcomes": valid_outcomes,
            "effort_stats": effort_stats,
            "misclassifications": misclassifications,
            "top_adjustments": top_adjustments,
            # Filter category impact for summary log
            "category_impact_summary": {
                k: {kk: vv for kk, vv in v.items() if kk != "keywords"}
                for k, v in category_impact.items() if "avg_duration" in v # Only show categories with stats
            },
            "tuning_recommendations": tuning_recommendations,
            "auto_tuning_enabled": cls.AUTO_TUNING_ENABLED,
            "applied_changes_count": len(applied_changes_log),
            "applied_changes_log": applied_changes_log
        }

        logger.info(f"Task outcome analysis complete. Recommendations: {len(tuning_recommendations)}. Applied changes: {len(applied_changes_log)}")
        # Optionally save detailed results to a file
        try:
            analysis_file = f"task_factory_analysis_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            with open(analysis_file, "w") as f:
                json.dump(analysis_summary, f, indent=2, default=str)
            logger.info(f"Saved analysis results to {analysis_file}")
        except Exception as e:
            logger.error(f"Failed to save analysis results: {e}")

        # --- History Management ---
        if cls.RETAIN_HISTORY:
            # Keep only the most recent N tasks
            cls.outcome_history = cls.outcome_history[-cls.HISTORY_LIMIT:]
            logger.debug(f"Outcome history trimmed to last {len(cls.outcome_history)} entries.")
        else:
            # Start fresh after analysis
            cls.outcome_history = []
            logger.info("Outcome history cleared after analysis.")


    @classmethod
    async def create_task(
        cls,
        task_id: Optional[str] = None, # Make optional, generate if None
        agent: str = "system", # Default agent
        content: str = "", # Default content
        target_agent: str = "orchestrator", # Default target
        intent: MessageIntent = MessageIntent.START_TASK,
        event: TaskEvent = TaskEvent.PLAN,
        confidence: Optional[float] = 1.0, # Default confidence
        timestamp: Optional[dt.datetime] = None,
        priority: Optional[int] = None, # Keep optional
        deadline_pressure: Optional[float] = None, # Keep optional
        redis_client = None # Keep optional for tool prep
    ) -> Tuple[Task, Dict]:
        """
        Create a Task object with dynamically estimated reasoning effort using TaskFactory's enhanced logic.
        Returns both the Task object and diagnostic information about the reasoning effort estimation.
        """
        if task_id is None:
             task_id = str(uuid.uuid4())

        if not content:
             logger.warning(f"Creating task {task_id} with empty content.")
             # Handle empty content case - default to LOW effort?
             reasoning_effort = ReasoningEffort.LOW
             diagnostics = {"warning": "Empty content, defaulted effort to LOW", "final_effort": ReasoningEffort.LOW.value}
        else:
            # Estimate the reasoning effort using the class method
            reasoning_effort, diagnostics = cls.estimate_reasoning_effort(
                content,
                event.value if isinstance(event, Enum) else event,
                intent.value if isinstance(intent, Enum) else intent,
                confidence,
                deadline_pressure
            )

        # Add context factors to diagnostics for comprehensive tracking
        diagnostics["context_factors"] = {
            "priority": priority,
            "deadline_pressure": deadline_pressure,
            "initial_confidence": confidence,
            "initial_event": event.value if isinstance(event, Enum) else event,
            "initial_intent": intent.value if isinstance(intent, Enum) else intent,
        }
        diagnostics["model_version"] = cls.VERSION # Record version used for estimation

        # Determine the appropriate reasoning strategy based on effort
        reasoning_strategy = ReasoningStrategy(get_reasoning_strategy(reasoning_effort))

        # Create the task instance
        task = Task(
            type="task",  # Set type for BaseMessage compatibility
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
            metadata={"diagnostics": diagnostics} # Store diagnostics
            # Add priority if needed by Task model
            # priority=priority
        )

        # Prepare tools for this task if Redis client provided
        if redis_client:
            try:
                # This is awaitable, so we need to use await
                task = await cls.prepare_tools_for_task(task, redis_client)
                diagnostics["tool_preparation"] = "Initiated" # Add status to diagnostics
            except Exception as e:
                logger.error(f"Error preparing tools for task {task_id}: {e}")
                diagnostics["tool_preparation"] = f"Error: {e}"
                # Continue despite error - tools are enhancement, not critical

        logger.debug(f"Created task '{task_id}' -> {target_agent}. Effort: {reasoning_effort.value}, Strategy: {reasoning_strategy.value}")

        return task, diagnostics