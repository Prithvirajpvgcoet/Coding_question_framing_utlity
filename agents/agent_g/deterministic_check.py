"""Code-only checks — never delegate to LLM."""

def run_checks(state: dict) -> dict:
    test_cases    = state.get("test_cases", [])
    visible_count = sum(1 for t in test_cases if t.get("type") == "VISIBLE")
    hidden_count  = sum(1 for t in test_cases if t.get("type") == "HIDDEN")
    html_valid    = state.get("html", {}).get("html_valid", False)
    code_compiles = state.get("execution", {}).get("all_passed", False)

    return {
        "visible_count": visible_count,
        "hidden_count":  hidden_count,
        "html_valid":    html_valid,
        "code_compiles": code_compiles,
        "all_pass":      visible_count >= 3 and hidden_count >= 3 and html_valid and code_compiles,
    }