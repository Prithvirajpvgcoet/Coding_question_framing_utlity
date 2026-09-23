"""
Groq API client — thin wrapper around OpenAI SDK pointing at Groq.
Used by all agents. Single place to configure retry, timeout, rate-limits.
"""
import os
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog

log = structlog.get_logger()

GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

# Singleton client
_client: AsyncOpenAI | None = None


def get_groq_client() -> AsyncOpenAI:
    """Return a singleton AsyncOpenAI client pointed at Groq."""
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY environment variable not set")
        _client = AsyncOpenAI(
            api_key=GROQ_API_KEY,
            base_url=GROQ_BASE_URL,
            timeout=60.0,
            max_retries=0,    # We handle retries in LangGraph, not here
        )
    return _client


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def groq_chat(
    model: str,
    system: str,
    user: str,
    temperature: float = 0.7,
    response_format: dict | None = None,
) -> tuple[str, dict]:
    """
    Call Groq chat completions API.
    Returns (content_string, usage_dict).

    Supports JSON mode via response_format={"type": "json_object"}.
    Rate limit: free tier = 30 RPM, paid = 6000 RPM per model.
    """
    import time
    from agents.base import _compute_cost, prompt_hash

    client = get_groq_client()
    t0     = time.time()

    kwargs = dict(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=temperature,
    )
    if response_format:
        kwargs["response_format"] = response_format

    response = await client.chat.completions.create(**kwargs)

    latency_ms    = int((time.time() - t0) * 1000)
    content       = response.choices[0].message.content or "{}"
    input_tokens  = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens

    usage = {
        "input_tokens":  input_tokens,
        "output_tokens": output_tokens,
        "latency_ms":    latency_ms,
        "model":         model,
        "prompt_hash":   prompt_hash(system),
        "cost_usd":      _compute_cost(model, input_tokens, output_tokens),
    }

    log.info(
        "groq_call",
        model=model,
        tokens_in=input_tokens,
        tokens_out=output_tokens,
        latency_ms=latency_ms,
        cost_usd=usage["cost_usd"],
    )
    return content, usage