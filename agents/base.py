"""
BaseAgent utilities — all LLM calls go through Groq API.
Phase 1: real groq_chat() enabled.
"""
import datetime
import hashlib
import json
import logging
import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Ensure environment variables from .env are loaded
load_dotenv(override=False)

from observability.cost_tracker import compute_cost

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "").strip('"').strip("'")

MODEL_STRONG = os.getenv("MODEL_STRONG", "openai/gpt-oss-120b")
MODEL_CODE   = os.getenv("MODEL_CODE",   "qwen/qwen3.8-27b")
MODEL_CHEAP  = os.getenv("MODEL_CHEAP",  "openai/gpt-oss-20b")
MODEL_FAST   = os.getenv("MODEL_FAST",   MODEL_CHEAP)


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()[:16]


def _compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    return compute_cost(model, input_tokens, output_tokens)


estimate_cost = _compute_cost


async def groq_chat(
    model: str,
    system: str,
    user: str,
    agent_name: str = "agent",
    temperature: float = 0.7,
    json_mode: bool = False,
    max_tokens: int = 2048,
) -> tuple[str, dict]:
    """
    Make an async chat completion request to the Groq API.
    Returns (response_text, usage_dict).
    """
    # Check OFFLINE_MODE
    offline_mode = os.getenv("OFFLINE_MODE", "false").lower() in ("true", "1", "yes")
    if offline_mode:
        log.info(f"[{agent_name}] OFFLINE_MODE active. Returning mock completion.")
        mock_resp = "{}" if json_mode else "Offline response"
        return mock_resp, {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "latency_ms": 0}

    import time
    from openai import AsyncOpenAI

    api_key = os.getenv("GROQ_API_KEY", GROQ_API_KEY).strip('"').strip("'")
    base_url = os.getenv("GROQ_BASE_URL", GROQ_BASE_URL)

    client = AsyncOpenAI(
        base_url=base_url,
        api_key=api_key,
        timeout=float(os.getenv("GROQ_TIMEOUT_SECONDS", "60.0")),
    )

    # Groq OpenAI requirement: if response_format is json_object, system or user MUST contain 'json'
    if json_mode and "json" not in system.lower() and "json" not in user.lower():
        system = f"{system}\nYou must output valid JSON."

    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]

    kwargs = {
        "model":       model,
        "messages":    messages,
        "temperature": temperature,
        "max_tokens":  max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    start = time.perf_counter()
    try:
        response = await client.chat.completions.create(**kwargs)
        latency_ms = int((time.perf_counter() - start) * 1000)

        choice = response.choices[0]
        content = choice.message.content or ""

        usage_obj = response.usage
        in_tok  = usage_obj.prompt_tokens     if usage_obj else 0
        out_tok = usage_obj.completion_tokens if usage_obj else 0
        cost    = compute_cost(model, in_tok, out_tok)

        usage = {
            "input_tokens":  in_tok,
            "output_tokens": out_tok,
            "cost_usd":      cost,
            "latency_ms":    latency_ms,
            "model":         model,
            "prompt_hash":   prompt_hash(system + user),
        }
        log.info(f"[{agent_name}] {model} completed in {latency_ms}ms | tokens: {in_tok}+{out_tok} | ${cost:.5f}")
        return content, usage

    except Exception as exc:
        # If Groq strict JSON validator failed on output, extract the failed_generation payload if present
        err_msg = str(exc)
        if "json_validate_failed" in err_msg or "failed_generation" in err_msg:
            match = re.search(r"'failed_generation':\s*['\"](.*)['\"]}}", err_msg)
            if match:
                try:
                    raw_extracted = match.group(1).encode().decode('unicode_escape')
                    log.warning(f"[{agent_name}] Recovered JSON payload from Groq failed_generation")
                    return raw_extracted, {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "latency_ms": 0}
                except Exception:
                    pass

        latency_ms = int((time.perf_counter() - start) * 1000)
        log.error(f"[{agent_name}] Groq API error after {latency_ms}ms: {exc}")
        raise
