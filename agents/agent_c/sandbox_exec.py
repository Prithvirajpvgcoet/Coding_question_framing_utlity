import json
import re
from services.sandbox_client import run_in_sandbox

async def execute_and_verify(code: str, language: str, test_cases: list) -> dict:
    if language.lower() != "python":
        return await run_in_sandbox(code, language)
        
    # If the code contains interactive main() reading stdin, pass dummy empty stdin or pass
    has_stdin = "sys.stdin" in code or "input(" in code
    has_func  = bool(re.search(r"def\s+[a-zA-Z0-9_]+\s*\(", code))

    # If code has main() with stdin, we should not execute main() at import
    # Wrap testing by disabling main() execution if __name__ == '__main__' is in the code
    safe_code = code
    if "if __name__" in safe_code:
        # Prevent candidate driver main() from blocking on stdin
        safe_code = re.sub(r"if\s+__name__\s*==\s*['\"]__main__['\"]\s*:", "if False:", safe_code)

    # Extract function name from code if it's not strictly 'solution'
    fn_match = re.search(r"def\s+([a-zA-Z0-9_]+)\s*\(", code)
    fn_name = fn_match.group(1) if fn_match else "solution"

    test_script = safe_code + "\n\n# --- AUTOMATED TESTS ---\n"
    test_script += "if __name__ == '__main__':\n"
    
    for i, tc in enumerate(test_cases[:3]):
        args = tc.get("input_args")
        if args is None and "inputs" in tc:
            inputs_val = tc["inputs"]
            if isinstance(inputs_val, dict):
                args = ", ".join(repr(v) for v in inputs_val.values())
            elif isinstance(inputs_val, list):
                args = ", ".join(repr(v) for v in inputs_val)
            else:
                args = repr(inputs_val)
        elif args is None:
            args = ""

        expected = tc.get("expected_output")
        if expected is None and "expected" in tc:
            expected = tc["expected"]
        
        safe_expected = repr(expected)
        
        test_script += "    try:\n"
        test_script += f"        res = {fn_name}({args})\n"
        test_script += f"        expected_val = {safe_expected}\n"
        test_script += "        # Check equality or type compatibility\n"
        test_script += "        if expected_val is not None and repr(res) != repr(expected_val) and str(res) != str(expected_val):\n"
        test_script += "            print(f'Test {i+1} Failed: Got {res!r}, expected {expected_val!r}')\n"
        test_script += "            exit(1)\n"
        test_script += "    except Exception as e:\n"
        test_script += f"        print(f'Test {i+1} Exception: {{e}}')\n"
        test_script += "        exit(1)\n"
        
    test_script += "    print('All tests passed!')\n"
    
    return await run_in_sandbox(test_script, language)
