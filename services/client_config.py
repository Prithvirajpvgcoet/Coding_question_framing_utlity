"""
Load client preferences and templates.
Phase 1: hardcoded dev config — no DB required.
Phase 5+: replace with real DB queries.
"""

LANGUAGE_TIERS = {
    "T1": ["python", "javascript", "java", "cpp", "csharp", "go"],
    "T2": ["typescript", "ruby", "php", "swift", "kotlin", "r"],
    "T3": ["sql", "html", "css", "react", "system_design"],
}

def get_language_tier(language: str) -> str:
    for tier, langs in LANGUAGE_TIERS.items():
        if language.lower() in langs:
            return tier
    return "T2"  # Unknown -> conservative default

DEV_CLIENT_CONFIG = {
    "question_style":   "standard",
    "difficulty_bias":  0.0,
    "html_template_id": "default",
    "html_template": """
<div class="question-container">
  <h2 class="question-title">{{title}}</h2>
  <div class="question-body">{{description}}</div>
  <div class="examples">{{examples}}</div>
  <div class="constraints">
    <strong>Constraints:</strong>
    {{constraints}}
  </div>
</div>""",
    "code_template_id": "default",
    "code_template": {
        "python":     "def solution():\n    # Write your solution here\n    pass\n",
        "javascript": "function solution() {\n    // Write your solution here\n}\n",
        "java":       "class Solution {\n    public void solution() {\n        // Write here\n    }\n}\n",
        "cpp":        "#include <bits/stdc++.h>\nusing namespace std;\n\nvoid solution() {\n    // Write here\n}\n",
        "go":         "package main\n\nfunc solution() {\n    // Write here\n}\n",
        "typescript": "function solution(): void {\n    // Write your solution here\n}\n",
    },
}


async def load_client_config(
    client_id:     str,
    language:      str,
    question_type: str = "ALGORITHMIC",
) -> dict:
    """
    Phase 1: returns hardcoded dev config for any client_id.
    Phase 5+: query client_preferences, html_templates, code_templates tables.
    """
    config          = dict(DEV_CLIENT_CONFIG)
    templates       = config.pop("code_template", {})
    config["code_template"] = templates.get(language, templates["python"])
    return config