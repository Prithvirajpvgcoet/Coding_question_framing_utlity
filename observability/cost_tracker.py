"""Per-question LLM cost accumulation — Groq pricing."""

COST_PER_1M = {
    # Keys must exactly match MODEL_STRONG / MODEL_CODE / MODEL_CHEAP env values
    "openai/gpt-oss-120b": {"input": 0.59,  "output": 0.79},
    "openai/gpt-oss-20b":  {"input": 0.075, "output": 0.30},
    "qwen/qwen3.8-27b":    {"input": 0.60,  "output": 3.00},
    # Legacy aliases (safe to keep)
    "llama-3.3-70b-versatile": {"input": 0.59,  "output": 0.79},
    "llama-3.1-8b-instant":    {"input": 0.05,  "output": 0.08},
    "qwen/qwen3.6-27b":        {"input": 0.60,  "output": 3.00},
}

MODEL_ROLES = {
    "openai/gpt-oss-120b": "strong",
    "qwen/qwen3.8-27b":    "code",
    "openai/gpt-oss-20b":  "cheap",
}

def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    p = COST_PER_1M.get(model, {"input": 0.59, "output": 0.79})
    return (input_tokens / 1_000_000 * p["input"]) + \
           (output_tokens / 1_000_000 * p["output"])

def estimate_question_cost() -> dict:
    return {
        "agent_a_intake":      compute_cost("openai/gpt-oss-20b",    300,   200),
        "agent_a_blueprint":   compute_cost("openai/gpt-oss-120b", 800,   500),
        "agent_c_question":    compute_cost("openai/gpt-oss-120b", 2700,  800),
        "agent_c_html":        compute_cost("openai/gpt-oss-20b",    1500, 1000),
        "agent_c_solution":    compute_cost("openai/gpt-oss-120b", 1400,  600),
        "agent_c_code":        compute_cost("qwen/qwen3.8-27b",        2100,  600),
        "agent_c_tests":       compute_cost("openai/gpt-oss-120b", 2200,  800),
        "agent_c_sandbox":     0.002,
        "agent_d_quality":     compute_cost("openai/gpt-oss-120b", 1600,  400),
        "agent_d_consistency": compute_cost("openai/gpt-oss-120b", 2400,  400),
        "agent_e_feedback":    compute_cost("openai/gpt-oss-20b",    1100,  300),
        "agent_g_qa":          compute_cost("openai/gpt-oss-120b", 2300,  400),
        "embeddings":          0.000016,
    }
