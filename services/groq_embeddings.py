"""
Embedding options for prototype:
  Option A (default): OpenAI text-embedding-3-small (best quality, needs OPENAI_API_KEY)
  Option B (zero deps): sentence-transformers local model (no API key needed)

Set EMBEDDING_PROVIDER=local to use Option B.
"""
import os

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")  # "openai" | "local"
EMBEDDING_DIM      = 1536   # OpenAI text-embedding-3-small
LOCAL_MODEL        = "sentence-transformers/all-MiniLM-L6-v2"   # 384-dim, free


async def embed_text(text: str) -> list[float]:
    if EMBEDDING_PROVIDER == "local":
        return await _embed_local(text)
    return await _embed_openai(text)


async def _embed_openai(text: str) -> list[float]:
    """OpenAI text-embedding-3-small — best quality, 1536-dim."""
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp   = await client.embeddings.create(
        model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        input=text,
    )
    return resp.data[0].embedding


async def _embed_local(text: str) -> list[float]:
    """
    Local sentence-transformers — no API key needed.
    384-dim (not 1536) — schema.sql VECTOR(384) needed if using this.
    Install: pip install sentence-transformers
    """
    # from sentence_transformers import SentenceTransformer
    # model  = SentenceTransformer(LOCAL_MODEL)
    # vector = model.encode(text).tolist()
    # return vector
    return [0.0] * 384   # Stub