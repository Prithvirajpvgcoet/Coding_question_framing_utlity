"""
Conditional edge routing functions for the 7-agent LangGraph graph.
"""
from langgraph.graph import StateGraph, END
from orchestrator.state import QuestionStateObject
from orchestrator import edges

# Import runners
from agents.agent_a.runner import run as run_agent_a
from agents.agent_b.runner import run as run_agent_b
from agents.agent_c.runner import run as run_agent_c
from agents.agent_d.runner import run as run_agent_d
from agents.agent_e.runner import run as run_agent_e
from agents.agent_f.runner import run as run_agent_f
from agents.agent_g.runner import run as run_agent_g


async def run_dedup_check(state: QuestionStateObject) -> dict:
    """Agent B2 - Deduplication Check against references."""
    from agents.agent_b.runner import run_dedup
    return await run_dedup(state)


async def escalate_to_human(state: QuestionStateObject) -> dict:
    """Terminal node: marks question as needing human review after retries exhausted."""
    from agents.base import utcnow
    print(f"[Workflow] Retries exhausted for {state.get('question_id')} — escalating to human.")
    return {
        "current_agent": "human_escalation",
        "updated_at":    utcnow(),
        "status":        "NEEDS_HUMAN_REVIEW",
    }


# ── Graph builder ─────────────────────────────────────────────────────────────
def build_graph(entry_point: str = "agent_a") -> StateGraph:
    g = StateGraph(QuestionStateObject)

    # ── Register all nodes ────────────────────────────────────────────────────
    g.add_node("agent_a",          run_agent_a)
    g.add_node("agent_b",          run_agent_b)
    g.add_node("dedup_check",      run_dedup_check)
    g.add_node("agent_c",          run_agent_c)
    g.add_node("agent_d",          run_agent_d)
    g.add_node("agent_g",          run_agent_g)
    g.add_node("agent_e",          run_agent_e)
    g.add_node("agent_f",          run_agent_f)
    g.add_node("human_escalation", escalate_to_human)

    # ── Entry point ───────────────────────────────────────────────────────────
    g.set_entry_point(entry_point)

    # ── Main generation flow (linear happy path) ──────────────────────────────
    g.add_edge("agent_a", "agent_b")
    g.add_edge("agent_b", "agent_c")
    g.add_edge("agent_c", "dedup_check")

    # ── Dedup branch ──────────────────────────────────────────────────────────
    g.add_conditional_edges("dedup_check", edges.route_after_dedup, {
        "agent_a":          "agent_a",         # REJECT → rethink blueprint
        "agent_c":          "agent_c",         # REJECT compatibility route
        "agent_d":          "agent_d",         # Legacy route compatibility
        "human_escalation": "human_escalation",# Rejection budget exhausted
    })

    # ── Agent D branch ────────────────────────────────────────────────────────
    g.add_conditional_edges("agent_d", edges.route_after_agent_d, {
        "agent_g":          "agent_g",
        "agent_c":          "agent_c",          # External retry with failure context
        "human_escalation": "human_escalation",
    })

    # ── Agent G branch ────────────────────────────────────────────────────────
    g.add_conditional_edges("agent_g", edges.route_after_agent_g, {
        "__end__":          END,
        "agent_a":          "agent_a",          # Score too low → regenerate from scratch
        "agent_c":          "agent_c",          # Format/syntax fix
        "human_escalation": "human_escalation",
    })

    # ── Human revision flow: E → F → (A, C, or D) ────────────────────────────
    g.add_edge("agent_e", "agent_f")
    g.add_conditional_edges("agent_f", edges.route_after_agent_f, {
        "agent_a": "agent_a",
        "agent_c": "agent_c",
        "agent_d": "agent_d",
    })

    # ── Escalation node ends the graph ────────────────────────────────────────
    g.add_edge("human_escalation", END)

    return g.compile()


# Module-level compiled graph (default full generation entry point)
workflow = build_graph(entry_point="agent_a")
