"""
Step 2: Map topic to curriculum (learning objectives + prerequisites).
Phase 1: hardcoded topic map — no DB required.
Phase 5+: replace with pgvector topic search.
"""

# Hardcoded curriculum for the 20 most common topics
CURRICULUM_MAP = {
    "arrays":              {"learning_objectives": ["Indexing & traversal","In-place modification","Prefix sums"],
                            "prerequisites": ["Basic programming"]},
    "strings":             {"learning_objectives": ["String manipulation","Pattern matching","Sliding window"],
                            "prerequisites": ["Arrays"]},
    "linked lists":        {"learning_objectives": ["Node traversal","Fast/slow pointers","List reversal"],
                            "prerequisites": ["Arrays","Pointers"]},
    "trees":               {"learning_objectives": ["DFS/BFS traversal","BST properties","Tree construction"],
                            "prerequisites": ["Recursion","Linked Lists"]},
    "graphs":              {"learning_objectives": ["DFS/BFS","Cycle detection","Shortest path"],
                            "prerequisites": ["Trees","Recursion"]},
    "dynamic programming": {"learning_objectives": ["Memoization","Tabulation","State design"],
                            "prerequisites": ["Recursion","Arrays"]},
    "sorting":             {"learning_objectives": ["Comparison sorts","Non-comparison sorts","Custom comparators"],
                            "prerequisites": ["Arrays","Recursion"]},
    "binary search":       {"learning_objectives": ["Search space reduction","Left/right boundary","Rotated arrays"],
                            "prerequisites": ["Arrays","Sorting"]},
    "heaps":               {"learning_objectives": ["Min/max heap ops","K-th element problems","Heap sort"],
                            "prerequisites": ["Trees","Arrays"]},
    "hash tables":         {"learning_objectives": ["Hash functions","Collision handling","Frequency counting"],
                            "prerequisites": ["Arrays"]},
    "stacks":              {"learning_objectives": ["LIFO operations","Monotonic stack","Expression evaluation"],
                            "prerequisites": ["Arrays"]},
    "queues":              {"learning_objectives": ["FIFO operations","BFS pattern","Sliding window maximum"],
                            "prerequisites": ["Arrays"]},
    "recursion":           {"learning_objectives": ["Base case design","Call stack","Backtracking"],
                            "prerequisites": ["Basic programming"]},
    "backtracking":        {"learning_objectives": ["State space search","Pruning","Permutations/combinations"],
                            "prerequisites": ["Recursion"]},
    "greedy":              {"learning_objectives": ["Local optimum choice","Proof of correctness","Interval problems"],
                            "prerequisites": ["Sorting","Arrays"]},
    "bit manipulation":    {"learning_objectives": ["Bitwise ops","XOR tricks","Bit masking"],
                            "prerequisites": ["Basic programming"]},
    "two pointers":        {"learning_objectives": ["Opposite direction","Same direction","Fast/slow"],
                            "prerequisites": ["Arrays","Sorting"]},
    "sliding window":      {"learning_objectives": ["Fixed size window","Variable size window","Window state"],
                            "prerequisites": ["Arrays","Hash Tables"]},
    "sql":                 {"learning_objectives": ["SELECT/JOIN/GROUP BY","Subqueries","Window functions"],
                            "prerequisites": ["Basic SQL"]},
    "system design":       {"learning_objectives": ["Scalability","CAP theorem","Data modeling"],
                            "prerequisites": ["Distributed systems basics"]},
}


async def map_topic(topic: str, subtopic: str) -> dict:
    """
    Return curriculum metadata for a given topic.
    Fuzzy match against CURRICULUM_MAP keys.
    Phase 5+: replace with pgvector topic graph query.
    """
    key = topic.lower().strip()

    # Direct match
    if key in CURRICULUM_MAP:
        curriculum = CURRICULUM_MAP[key]
    else:
        # Fuzzy: check if any known topic is a substring
        matched = next((k for k in CURRICULUM_MAP if k in key or key in k), None)
        curriculum = CURRICULUM_MAP.get(matched, {
            "learning_objectives": [f"Understand {topic}"],
            "prerequisites":       ["Basic programming"],
        })

    return {
        "topic_id":              key.replace(" ", "_"),
        "learning_objectives":   curriculum["learning_objectives"],
        "prerequisites":         curriculum["prerequisites"],
        "topic_alignment_score": 1.0,
        "subtopic":              subtopic,
    }