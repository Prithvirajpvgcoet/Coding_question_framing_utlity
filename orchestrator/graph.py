"""
LangGraph StateGraph — Consolidated 7-Agent Workflow.

Main flow:     Agent A → Agent B → [Dedup] → Agent C → Agent D → Agent G → END
Feedback flow: Agent E → Agent F → (Agent A | Agent C | Agent D) → ... → Agent G → END
"""
import datetime
from langgraph.graph import StateGraph, END
from orchestrator.state import QuestionStateObject
from orchestrator import edges


# ── Import agent run functions ────────────────────────────────────────────────
from agents.agent_a import run as run_agent_a
from agents.agent_b import run as run_agent_b
from agents.agent_c import run as run_agent_c
from agents.agent_d import run as run_agent_d
from agents.agent_e import run as run_agent_e
from agents.agent_f import run as run_agent_f
from agents.agent_g import run as run_agent_g

# ── Deduplication check node ──────────────────────────────────────────────────
from agents.agent_b import run_dedup_check


# ── Human escalation node ─────────────────────────────────────────────────────
async def escalate_to_human(state: QuestionStateObject) -> dict:
    return {
        "status":        "NEEDS_HUMAN_REVIEW",
        "current_agent": "human_escalation",
        "updated_at":    datetime.datetime.utcnow().isoformat(),
    }


# ── Graph builder ─────────────────────────────────────────────────────────────
def build_graph() -> StateGraph:
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
    g.set_entry_point("agent_a")

    # ── Main generation flow (linear happy path) ──────────────────────────────
    g.add_edge("agent_a", "agent_b")
    g.add_edge("agent_b", "dedup_check")

    # ── Dedup branch ──────────────────────────────────────────────────────────
    g.add_conditional_edges("dedup_check", edges.route_after_dedup, {
        "agent_a": "agent_a",         # REJECT → rethink blueprint
        "agent_c": "agent_c",         # PASS/FLAG → continue
    })

    # ── Agent C → D ───────────────────────────────────────────────────────────
    g.add_edge("agent_c", "agent_d")

    # ── Agent D branch ────────────────────────────────────────────────────────
    g.add_conditional_edges("agent_d", edges.route_after_agent_d, {
        "agent_g":          "agent_g",
        "agent_c":          "agent_c",          # External retry with failure context
        "human_escalation": "human_escalation",
    })

    # ── Agent G branch ────────────────────────────────────────────────────────
    g.add_conditional_edges("agent_g", edges.route_after_agent_g, {
        "__end__":          END,
        "agent_a":          "agent_a",
        "agent_c":          "agent_c",
        "human_escalation": "human_escalation",
    })

    # ── Feedback loop (triggered separately via Celery task) ──────────────────
    g.add_edge("agent_e", "agent_f")

    g.add_conditional_edges("agent_f", edges.route_after_agent_f, {
        "agent_a": "agent_a",
        "agent_c": "agent_c",
        "agent_d": "agent_d",
    })

    # ── Human escalation terminal ─────────────────────────────────────────────
    g.add_edge("human_escalation", END)

    return g.compile()


# Singleton — imported by workers/tasks.py
workflow = build_graph()