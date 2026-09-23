"""
BaseAgent utilities — all LLM calls go through Groq API.
Phase 1: real groq_chat() enabled.
"""
import datetime
import hashlib
import logging
import os

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")

MODEL_STRONG = os.getenv("MODEL_STRONG", "openai/gpt-oss-120b")
MODEL_CODE   = os.getenv("MODEL_CODE",   "qwen/qwen3.8-27b")
MODEL_CHEAP  = os.getenv("MODEL_CHEAP",  "openai/gpt-oss-20b")


def utcnow() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def load_prompt(filename: str) -> str:
    path = os.path.join("prompts", f"{filename}.txt")
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        log.warning(f"Prompt not found: {path}")
        return f"# TODO: Write prompt for {filename}"


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()[:16]


def _compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    PRICING = {
        "llama-3.3-70b-versatile": {"input": 0.59,  "output": 0.79},
        "qwen/qwen3.6-27b":        {"input": 0.60,  "output": 3.00},
        "gpt-oss-20b":             {"input": 0.075, "output": 0.30},
        "llama-3.1-8b-instant":    {"input": 0.05,  "output": 0.08},
    }
    p = PRICING.get(model, {"input": 0.59, "output": 0.79})
    return (input_tokens / 1_000_000 * p["input"]) + \
           (output_tokens / 1_000_000 * p["output"])


async def groq_chat(
    model: str,
    system: str,
    user: str,
    agent_name: str = "",
    temperature: float = 0.7,
    json_mode: bool = False,
) -> tuple[str, dict]:
    """
    Call Groq via OpenAI-compatible SDK.
    Returns (content_string, usage_dict).
    Set json_mode=True to force JSON output (faster + safer for extraction tasks).
    """
    import time
    from openai import AsyncOpenAI

    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set in .env")

    client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL, timeout=60.0)

    kwargs = dict(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=temperature,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    t0 = time.time()
    response      = await client.chat.completions.create(**kwargs)
    latency_ms    = int((time.time() - t0) * 1000)
    content       = response.choices[0].message.content or "{}"
    input_tokens  = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    cost_usd      = _compute_cost(model, input_tokens, output_tokens)

    usage = {
        "input_tokens":  input_tokens,
        "output_tokens": output_tokens,
        "latency_ms":    latency_ms,
        "model":         model,
        "prompt_hash":   prompt_hash(system),
        "cost_usd":      cost_usd,
    }
    log.info(f"[{agent_name}] model={model} in={input_tokens} out={output_tokens} "
             f"latency={latency_ms}ms cost=${cost_usd:.5f}")
    return content, usage


# Keep llm_call as an alias for backward compat with Phase 0 stubs
async def llm_call(model, system, user, agent_name="", question_id="", temperature=0.7):
    return await groq_chat(model, system, user, agent_name, temperature)


def increment_retry(state: dict, key: str) -> dict:
    counts = dict(state.get("retry_counts", {}))
    counts[key] = counts.get(key, 0) + 1
    return {"retry_counts": counts}


def append_error(state: dict, agent: str, reason: str) -> dict:
    return {"error_log": state.get("error_log", []) + [{
        "agent": agent, "reason": reason, "timestamp": utcnow(),
    }]}