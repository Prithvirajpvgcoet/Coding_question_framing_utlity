"""
AST-based logic preservation check after code formatting.
Ensures formatter didn't alter algorithm structure.
"""
import ast
import re


def python_logic_signature(code: str) -> set:
    """Extract function calls + loop/branch keywords from Python AST."""
    try:
        tree = ast.parse(code)
        tokens = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and hasattr(node.func, 'id'):
                tokens.add(f"call:{node.func.id}")
            if isinstance(node, (ast.For, ast.While)):
                tokens.add(f"loop:{type(node).__name__}")
            if isinstance(node, ast.Return):
                tokens.add("return")
        return tokens
    except SyntaxError:
        return set()


def generic_logic_signature(code: str) -> set:
    """Simple keyword-based signature for non-Python languages."""
    keywords = re.findall(r'\b(for|while|return|if|else|switch|break|continue)\b', code)
    return set(keywords)


def logic_preserved(original: str, formatted: str, language: str = "python") -> bool:
    """Returns True if formatting did not change the algorithm logic."""
    if language == "python":
        return python_logic_signature(original) == python_logic_signature(formatted)
    return generic_logic_signature(original) == generic_logic_signature(formatted)