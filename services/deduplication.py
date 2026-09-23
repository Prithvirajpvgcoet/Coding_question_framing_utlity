"""
Anti-duplication: cosine similarity (pgvector) + shingled n-gram overlap.
Verdict: PASS | FLAG | REJECT
"""
import os

HARD_REJECT = float(os.getenv("DEDUP_REJECT_THRESHOLD", 0.92))
FLAG        = float(os.getenv("DEDUP_FLAG_THRESHOLD",   0.80))


def ngram_overlap(text1: str, text2: str, n: int = 3) -> float:
    """Jaccard similarity on character n-grams."""
    def shingles(t): return set(t[i:i+n] for i in range(max(0, len(t)-n+1)))
    s1, s2 = shingles(text1.lower()), shingles(text2.lower())
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)


async def check_duplication(question_text: str, client_id: str) -> dict:
    # TODO Phase 2: embed question, pgvector ANN search, compute overlap
    return {
        "max_cosine_similarity": 0.0,
        "matched_reference_id":  None,
        "lexical_overlap_score": 0.0,
        "verdict":               "PASS",
    }