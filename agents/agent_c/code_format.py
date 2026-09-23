import black

def format_code(code: str, language: str) -> str:
    """Format Python code using Black. Ignore other languages for now."""
    if language.lower() != "python":
        return code
    try:
        return black.format_str(code, mode=black.Mode())
    except black.parsing.InvalidInput:
        return code
