"""
Agent B — Reference Retrieval & Deduplication
Hybrid retrieval over ingested knowledge datasets to provide Agent C with personalized context.
"""
import datetime
import os
from orchestrator.state import QuestionStateObject
from services.reference_retriever import retrieve_references
from services.deduplication import ngram_overlap


async def run(state: QuestionStateObject) -> dict:
    question_id = state.get("question_id")
    print(f"[Agent B] Running retrieval for question_id: {question_id}")

    requirements = state.get("requirements", {})
    client_id = state.get("client_id", "00000000-0000-0000-0000-000000000001")
    retrieval_limit = int(os.environ.get("REFERENCE_RETRIEVAL_LIMIT", "3"))

    # Retrieve relevant domain scenarios and reference problems
    references = await retrieve_references(requirements, client_id, limit=retrieval_limit)

    print(f"[Agent B] Retrieved {len(references)} reference scenarios for topic: {requirements.get('topic')}")

    return {
        "references":    references,
        "current_agent": "agent_b",
        "updated_at":    datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


async def run_dedup(state: QuestionStateObject) -> dict:
    """
    Deduplication check node — sits after Agent C.
    Checks generated question for high lexical / structural overlap against references.
    """
    question_id = state.get("question_id")
    print(f"[Dedup Check] Running — question_id: {question_id}")

    question_meta = state.get("question", {})
    gen_text = f"{question_meta.get('title', '')} {question_meta.get('purpose', '')}"
    references = state.get("references", [])

    max_overlap = 0.0
    matched_id = None

    for ref in references:
        ref_text = f"{ref.get('title', '')} {ref.get('scenario', '')}"
        overlap = ngram_overlap(gen_text, ref_text, n=3)
        if overlap > max_overlap:
            max_overlap = overlap
            matched_id = ref.get("id") or ref.get("title")

    # Read configurable thresholds from environment variables
    reject_threshold = float(os.environ.get("DEDUP_REJECT_THRESHOLD", "0.90"))
    flag_threshold   = float(os.environ.get("DEDUP_FLAG_THRESHOLD", "0.75"))

    verdict = "PASS"
    if max_overlap >= reject_threshold:
        verdict = "REJECT"
    elif max_overlap >= flag_threshold:
        verdict = "FLAG"

    return {
        "deduplication": {
            "max_cosine_similarity": 0.0,
            "matched_reference_id":  matched_id,
            "lexical_overlap_score": round(max_overlap, 4),
            "verdict":               verdict,
        },
        "current_agent": "dedup_check",
        "updated_at":    datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


# Backwards compatibility alias
run_dedup_check = run_dedup
