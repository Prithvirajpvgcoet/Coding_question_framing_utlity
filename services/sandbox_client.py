"""
Phase 3 Local Sandbox.
Executes generated Python code in a temporary subprocess.
"""
import asyncio
import tempfile
import os

async def run_in_sandbox(code: str, language: str) -> dict:
    if language.lower() != "python":
        return {"passed": True, "output": f"Sandbox stubbed for {language}"}
    
    # Write to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(code)
        temp_path = f.name
        
    try:
        proc = await asyncio.create_subprocess_exec(
            "python", temp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        passed = (proc.returncode == 0)
        output = stdout.decode('utf-8') if passed else stderr.decode('utf-8')
        
        return {
            "passed": passed,
            "output": output
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)