"""Observability module providing structured JSON logging, tracing decorators, and latency/cost tracking metrics."""

from __future__ import annotations

import json
import logging
import time
from functools import wraps
from typing import Any, Dict, Callable
from fastapi import APIRouter

logger = logging.getLogger("nephele.observability")

# In-memory accumulator for tracking system-wide latencies and token/cost metrics
METRICS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "stt_latency": {"total_seconds": 0.0, "count": 0},
    "tts_latency": {"total_seconds": 0.0, "count": 0},
    "evaluation_latency": {"total_seconds": 0.0, "count": 0},
    "traversal_latency": {"total_seconds": 0.0, "count": 0},
    "question_generation_latency": {"total_seconds": 0.0, "count": 0},
    "provider_tokens": {
        "gemini": {"prompt": 0, "completion": 0, "total": 0, "cost": 0.0},
        "groq": {"prompt": 0, "completion": 0, "total": 0, "cost": 0.0},
        "openai": {"prompt": 0, "completion": 0, "total": 0, "cost": 0.0},
    }
}

router = APIRouter(prefix="/api/observability", tags=["Observability"])


class StructuredJSONFormatter(logging.Formatter):
    """Custom Formatter to output logs as structured JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        # Include custom dynamic fields attached to log records
        if hasattr(record, "custom_fields"):
            log_entry.update(record.custom_fields)
        return json.dumps(log_entry)


def setup_structured_logging() -> None:
    """Configure the root or target loggers to output structured JSON."""
    handler = logging.StreamHandler()
    formatter = StructuredJSONFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplicates
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    logger.info("Structured JSON logging initialized.")


def track_metric(metric_name: str, duration: float) -> None:
    """Record execution latency duration into the central metrics registry."""
    if metric_name in METRICS_REGISTRY:
        METRICS_REGISTRY[metric_name]["total_seconds"] += duration
        METRICS_REGISTRY[metric_name]["count"] += 1
        
        # Log structured metric
        extra = {"custom_fields": {"metric": metric_name, "duration_seconds": round(duration, 3)}}
        logger.info(f"Metric tracked: {metric_name} = {duration:.3f}s", extra=extra)


def trace_latency(metric_name: str) -> Callable:
    """Decorator to measure and record execution latency of a function."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                track_metric(metric_name, duration)
        return wrapper
    return decorator


def record_token_usage(provider: str, prompt_tokens: int, completion_tokens: int, cost: float = 0.0) -> None:
    """Record token volume and approximate financial costs into registry."""
    provider = provider.lower()
    if "gemini" in provider:
        p_key = "gemini"
    elif "groq" in provider:
        p_key = "groq"
    else:
        p_key = "openai"

    registry = METRICS_REGISTRY["provider_tokens"][p_key]
    registry["prompt"] += prompt_tokens
    registry["completion"] += completion_tokens
    registry["total"] += (prompt_tokens + completion_tokens)
    registry["cost"] += cost

    extra = {
        "custom_fields": {
            "provider": p_key,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": cost
        }
    }
    logger.info(f"Token usage recorded for {p_key}: {prompt_tokens + completion_tokens} tokens", extra=extra)


@router.get("/metrics")
def get_metrics() -> Dict[str, Any]:
    """Retrieve system latency averages, counts, and cost metrics."""
    averages = {}
    for metric_name, stats in METRICS_REGISTRY.items():
        if metric_name == "provider_tokens":
            continue
        count = stats["count"]
        total = stats["total_seconds"]
        averages[metric_name] = {
            "average_seconds": round(total / count, 3) if count > 0 else 0.0,
            "invocation_count": count
        }
    
    return {
        "latencies": averages,
        "provider_costs": METRICS_REGISTRY["provider_tokens"]
    }
