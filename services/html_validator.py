"""html5lib wrapper — deterministic HTML validation (never trust LLM claims)."""
import html5lib


def validate_html(html: str) -> tuple[bool, list[str]]:
    """Returns (is_valid, list_of_error_strings)."""
    try:
        parser = html5lib.HTMLParser(strict=True)
        parser.parseFragment(html)
        return True, []
    except Exception as e:
        return False, [str(e)]