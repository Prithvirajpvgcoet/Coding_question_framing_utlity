"""
Hybrid retrieval: pgvector HNSW + BM25 keyword + metadata filter.
RLS-scoped per client_id automatically by PostgreSQL policies.
"""
from orchestrator.state import QuestionStateObject


async def retrieve_references(state: QuestionStateObject) -> list:
    # TODO Phase 2: real hybrid search
    return []