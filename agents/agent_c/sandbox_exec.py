from services.sandbox_client import run_in_sandbox

async def execute_and_verify(code: str, language: str, test_cases: list) -> dict:
    if language.lower() != "python":
        return {"passed": True, "feedback": "Skipped for non-python"}
        
    # Combine the AI's code with an automated test runner!
    test_script = code + "\n\n# --- AUTOMATED TESTS ---\n"
    test_script += "if __name__ == '__main__':\n"
    
    for i, tc in enumerate(test_cases):
        args = tc.get("input_args", "")
        expected = tc.get("expected_output", "")
        
        test_script += f"    try:\n"
        test_script += f"        res = solution({args})\n"
        test_script += f"        assert res == {expected}, f'Expected {expected} but got {{res}}'\n"
        test_script += f"    except Exception as e:\n"
        test_script += f"        print(f'Test {i+1} Failed: {{e}}')\n"
        test_script += f"        exit(1)\n"
        
    test_script += "    print('All tests passed!')\n"
    
    return await run_in_sandbox(test_script, language)