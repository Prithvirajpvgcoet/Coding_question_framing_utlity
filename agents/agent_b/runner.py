"""
Agent B — Reference Retrieval & Deduplication
Hybrid retrieval over ingested knowledge datasets to provide Agent C with personalized context.
"""
import datetime
from orchestrator.state import QuestionStateObject
from services.reference_retriever import retrieve_references
from services.deduplication import ngram_overlap


async def run(state: QuestionStateObject) -> dict:
    question_id = state.get("question_id")
    print(f"[Agent B] Running retrieval for question_id: {question_id}")

    requirements = state.get("requirements", {})
    client_id = state.get("client_id", "00000000-0000-0000-0000-000000000001")

    # Retrieve relevant domain scenarios and reference problems
    references = await retrieve_references(requirements, client_id, limit=3)

    print(f"[Agent B] Retrieved {len(references)} reference scenarios for topic: {requirements.get('topic')}")

    return {
        "references":    references,
        "current_agent": "agent_b",
        "updated_at":    datetime.datetime.now(datetime.UTC).isoformat(),
    }


async def run_dedup_check(state: QuestionStateObject) -> dict:
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

    # Hard rejection threshold 0.90, flag threshold 0.75
    verdict = "PASS"
    if max_overlap >= 0.90:
        verdict = "REJECT"
    elif max_overlap >= 0.75:
        verdict = "FLAG"

    return {
        "deduplication": {
            "max_cosine_similarity": 0.0,
            "matched_reference_id":  matched_id,
            "lexical_overlap_score": round(max_overlap, 4),
            "verdict":               verdict,
        },
        "current_agent": "dedup_check",
        "updated_at":    datetime.datetime.now(datetime.UTC).isoformat(),
    }