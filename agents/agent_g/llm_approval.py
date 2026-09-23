"""Subjective LLM approval gate. Model: Mistral Large 3 (temp=0.1)"""
from agents.base import llm_call, load_prompt, MODEL_STRONG_GENERAL

SYSTEM = load_prompt("agent_g_final_qa")

async def approve(state: dict) -> dict:
    # TODO Phase 5: real LLM call
    return {"approved": True, "approval_notes": "stub", "rejection_reasons": []}