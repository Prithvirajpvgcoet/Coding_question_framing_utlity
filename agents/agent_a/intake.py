"""
Step 1: Extract structured requirements from raw client request.
Model: llama-3.1-8b-instant — fast + cheap for JSON extraction.
"""
import json
import re
from agents.base import groq_chat, load_prompt, MODEL_CHEAP

SYSTEM = load_prompt("agent_a_intake")


def _clean_json(text: str) -> str:
    """Strip markdown fences if model wraps output in ```json ... ```"""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


VALID_DIFFICULTIES = {"EASY", "MEDIUM", "HARD", "EXPERT"}
VALID_TYPES       = {"ALGORITHMIC", "SQL", "SYSTEM_DESIGN", "DEBUG", "FILL_IN_BLANK"}
VALID_LANGUAGES   = {"python", "javascript", "java", "cpp", "go", "typescript"}


def _canonical_topic(raw_topic: str, raw_request: str) -> str:
    """Normalize topic to standard primary categories."""
    t_lower = (raw_topic or "").lower()
    r_lower = (raw_request or "").lower()

    if any(k in t_lower or k in r_lower for k in ("bfs", "dfs", "graph", "breadth-first", "depth-first", "shortest path")):
        return "Graphs"
    if any(k in t_lower or k in r_lower for k in ("dp", "dynamic programming", "knapsack", "memoization")):
        return "Dynamic Programming"
    if any(k in t_lower or k in r_lower for k in ("tree", "binary search tree", "bst", "trie")):
        return "Trees"
    if any(k in t_lower or k in r_lower for k in ("string", "palindrome", "anagram")):
        return "Strings"
    if any(k in t_lower or k in r_lower for k in ("binary search", "search")):
        return "Binary Search"
    if any(k in t_lower or k in r_lower for k in ("sort", "quicksort", "mergesort")):
        return "Sorting"
    
    return raw_topic if raw_topic else "Arrays"


async def extract_requirements(raw_request: str) -> dict:
    """
    Call LLM to extract structured requirements.
    Falls back to sensible defaults on any parse error.
    """
    content, usage = await groq_chat(
        model=MODEL_CHEAP,
        system=SYSTEM,
        user=f"Client request: {raw_request}\nReturn a JSON object with fields: topic, subtopic, difficulty, question_type, target_language, max_solve_time_minutes, custom_constraints.",
        agent_name="agent_a.intake",
        temperature=0.1,
        json_mode=True,
    )

    try:
        data = json.loads(_clean_json(content))
        if not isinstance(data, dict):
            data = {}
    except (json.JSONDecodeError, ValueError):
        data = {}

    topic = _canonical_topic(data.get("topic", ""), raw_request)

    # Sanitize and apply defaults
    return {
        "topic":                  topic,
        "subtopic":               str(data.get("subtopic", "")).strip(),
        "difficulty":             data.get("difficulty", "MEDIUM").upper()
                                      if data.get("difficulty", "").upper() in VALID_DIFFICULTIES
                                      else "MEDIUM",
        "question_type":          data.get("question_type", "ALGORITHMIC").upper()
                                      if data.get("question_type", "").upper() in VALID_TYPES
                                      else "ALGORITHMIC",
        "target_language":        data.get("target_language", "python").lower()
                                      if data.get("target_language", "").lower() in VALID_LANGUAGES
                                      else "python",
        "max_solve_time_minutes": int(data.get("max_solve_time_minutes", 30))
                                      if str(data.get("max_solve_time_minutes", "")).isdigit()
                                      else 30,
        "custom_constraints":     data.get("custom_constraints", []),
        "raw_request":            raw_request,
        "_intake_usage":          usage,
    }
