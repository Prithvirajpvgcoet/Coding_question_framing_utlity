"""Weighted quality score aggregator. Collects sub-scores from each responsible agent."""

WEIGHTS = {
    "technical_correctness":  0.20,
    "problem_clarity":        0.15,
    "topic_alignment":        0.10,
    "difficulty_accuracy":    0.15,
    "originality":            0.10,
    "solution_correctness":   0.15,
    "test_coverage":          0.10,
    "html_compliance":        0.025,
    "code_format_compliance": 0.025,
}


def compute_aggregate_score(state: dict) -> float:
    # TODO Phase 5: collect sub-scores from all agents and compute weighted sum
    return 0.0