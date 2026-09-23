"""
Agent B — Reference Retrieval
Original Agent 4. NO LLM — pure deterministic hybrid search.

run()            → retrieves top-5 reference questions via pgvector + BM25
run_dedup_check() → checks generated question for duplication (runs AFTER Agent C step 1)
"""
import datetime
from orchestrator.state import QuestionStateObject


async def run(state: QuestionStateObject) -> dict:
    print(f"[Agent B] Running — question_id: {state.get('question_id')}")

    # TODO Phase 2: real pgvector HNSW search + BM25 metadata filter
    return {
        "references":    [],         # Stub: empty reference list
        "current_agent": "agent_b",
        "updated_at":    datetime.datetime.utcnow().isoformat(),
    }


async def run_dedup_check(state: QuestionStateObject) -> dict:
    """
    Deduplication check node — sits between Agent B and Agent C in the graph.
    Embeds the generated question and checks cosine similarity + n-gram overlap.
    """
    print(f"[Dedup Check] Running — question_id: {state.get('question_id')}")

    # TODO Phase 2: real deduplication via services/deduplication.py
    return {
        "deduplication": {
            "max_cosine_similarity": 0.0,
            "matched_reference_id":  None,
            "lexical_overlap_score": 0.0,
            "verdict":               "PASS",   # PASS | FLAG | REJECT
        },
        "current_agent": "dedup_check",
        "updated_at":    datetime.datetime.utcnow().isoformat(),
    }