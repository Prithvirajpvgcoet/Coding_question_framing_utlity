"""
Service for formatting, validating, and staging questions for the iMocha platform.
"""
from typing import Dict, Any, List, Tuple


def build_imocha_payload(state: Dict[str, Any], bank_id: str = "default") -> Dict[str, Any]:
    """
    Constructs the exact iMocha platform question structure from the Question state.
    """
    question_meta = state.get("question", {})
    requirements = state.get("requirements", {})
    html_block = state.get("html", {})
    code_block = state.get("code", {})
    test_cases_raw = state.get("test_cases", [])

    formatted_tests = []
    for idx, tc in enumerate(test_cases_raw, start=1):
        formatted_tests.append({
            "index": idx,
            "type": tc.get("type", "HIDDEN"),
            "is_sample": tc.get("type") == "VISIBLE",
            "input": tc.get("input_args", ""),
            "expected_output": tc.get("expected_output", ""),
            "points": tc.get("points", 1),
            "explanation": tc.get("explanation", ""),
        })

    title = question_meta.get("title") or f"{requirements.get('topic', 'Coding')} Assessment Problem"
    formatted_html = html_block.get("formatted_question") or f"<h2>{title}</h2><p>Solve the problem efficiently.</p>"
    solution_code = code_block.get("solution") or state.get("solution_code", "")
    starter_stub = code_block.get("stub", "")

    solve_time_min = requirements.get("max_solve_time_minutes", 30)

    payload = {
        "question_bank_id": bank_id,
        "title": title,
        "difficulty": requirements.get("difficulty", "MEDIUM").upper(),
        "question_type": requirements.get("question_type", "ALGORITHMIC"),
        "language": code_block.get("language") or requirements.get("target_language", "python"),
        "time_limit_seconds": solve_time_min * 60,
        "max_score": len(formatted_tests) * 10,
        "html_content": formatted_html,
        "instructions": html_block.get("instructions", ""),
        "starter_code": starter_stub,
        "solution_code": solution_code,
        "test_cases": formatted_tests,
        "topics": question_meta.get("topics", [requirements.get("topic", "General")]),
    }

    return payload


def validate_upload_payload(payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that a question payload meets iMocha's mandatory requirements.
    Returns (is_valid, list_of_errors).
    """
    errors = []

    if not payload.get("title") or len(payload["title"].strip()) < 3:
        errors.append("Question title must be at least 3 characters long.")

    if not payload.get("html_content") or len(payload["html_content"].strip()) < 20:
        errors.append("Question HTML content must be provided.")

    if not payload.get("solution_code") or len(payload["solution_code"].strip()) < 10:
        errors.append("Reference solution code is required.")

    tests = payload.get("test_cases", [])
    if not tests or len(tests) == 0:
        errors.append("At least one test case is required.")

    has_sample = any(t.get("is_sample") or t.get("type") == "VISIBLE" for t in tests)
    if not has_sample:
        errors.append("At least one sample/visible test case is recommended for candidates.")

    return len(errors) == 0, errors
