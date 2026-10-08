"""
Phase 3 Local Sandbox.
Executes generated Python code in a temporary subprocess.
"""
import asyncio
import tempfile
import os

TIMEOUT = int(os.getenv("SANDBOX_TIMEOUT_SECONDS", "10"))

async def run_in_sandbox(code: str, language: str) -> dict:
    if language.lower() != "python":
        return {
            "passed": False,
            "output": f"[UNVERIFIED] No sandbox harness for {language}. Manual review required.",
            "unverified": True,
        }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(code)
        temp_path = f.name

    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            "python", temp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {"passed": False, "output": f"Timeout: exceeded {TIMEOUT}s", "unverified": False}

        passed = (proc.returncode == 0)
        return {
            "passed": passed,
            "output": stdout.decode("utf-8") if passed else stderr.decode("utf-8"),
            "unverified": False,
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
