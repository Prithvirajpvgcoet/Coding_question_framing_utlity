"""Per-question LLM cost accumulation — Groq pricing."""

# Groq pricing per 1M tokens (September 2026)
COST_PER_1M = {
    "llama-3.3-70b-versatile": {"input": 0.59,  "output": 0.79},
    "qwen/qwen3.6-27b":        {"input": 0.60,  "output": 3.00},
    "gpt-oss-20b":             {"input": 0.075, "output": 0.30},
    "llama-3.1-8b-instant":    {"input": 0.05,  "output": 0.08},
}

# Groq model → agent role mapping (for cost reports)
MODEL_ROLES = {
    "llama-3.3-70b-versatile": "strong",
    "qwen/qwen3.6-27b":        "code",
    "llama-3.1-8b-instant":    "cheap",
}


def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    p = COST_PER_1M.get(model, {"input": 0.59, "output": 0.79})
    return (input_tokens / 1_000_000 * p["input"]) + \
           (output_tokens / 1_000_000 * p["output"])


def estimate_question_cost() -> dict:
    """Estimated cost breakdown for one complete question (happy path)."""
    return {
        "agent_a_intake":      compute_cost("llama-3.1-8b-instant",    300,   200),
        "agent_a_blueprint":   compute_cost("llama-3.3-70b-versatile", 800,   500),
        "agent_c_question":    compute_cost("llama-3.3-70b-versatile", 2700,  800),
        "agent_c_html":        compute_cost("llama-3.1-8b-instant",    1500, 1000),
        "agent_c_solution":    compute_cost("llama-3.3-70b-versatile", 1400,  600),
        "agent_c_code":        compute_cost("qwen/qwen3.6-27b",        2100,  600),
        "agent_c_tests":       compute_cost("llama-3.3-70b-versatile", 2200,  800),
        "agent_c_sandbox":     0.002,    # Judge0 fixed cost
        "agent_d_quality":     compute_cost("llama-3.3-70b-versatile", 1600,  400),
        "agent_d_consistency": compute_cost("llama-3.3-70b-versatile", 2400,  400),
        "agent_e_feedback":    compute_cost("llama-3.1-8b-instant",    1100,  300),
        "agent_g_qa":          compute_cost("llama-3.3-70b-versatile", 2300,  400),
        "embeddings":          0.000016,  # text-embedding-3-small
    }