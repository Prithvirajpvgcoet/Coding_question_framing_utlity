"""text-embedding-3-small via OpenAI API."""
import os

MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

async def embed_text(text: str) -> list[float]:
    # TODO Phase 2: real OpenAI embeddings call
    return [0.0] * 1536   # 1536-dim zero vector stub