"""Langfuse trace wrapper — stub for Phase 0."""
import os
import functools

ENABLED = bool(os.getenv("LANGFUSE_PUBLIC_KEY"))


def trace_agent(agent_name: str):
    """Decorator — wraps agent in Langfuse span. Activates in Phase 1."""
    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            # TODO Phase 1: wrap with real Langfuse trace/span
            return await fn(*args, **kwargs)
        return wrapper
    return decorator