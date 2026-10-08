"""
Agent C — Content & Solution Generation (Full Loop)
"""
from agents.base import utcnow
from orchestrator.state import QuestionStateObject

from .question_gen import generate as gen_question
from .html_format import format_html
from .solution_arch import design_solution
from .code_gen import generate as gen_code
from .code_format import format_code
from .test_case_gen import generate_tests
from .sandbox_exec import execute_and_verify

async def run(state: QuestionStateObject) -> dict:
    print(f"[Agent C] Starting generation for: {state.get('question_id')}")

    blueprint = state.get("blueprint", {})
    language = state.get("requirements", {}).get("target_language", "python")
    template = state.get("client_config", {}).get("code_template", "")

    # Step 1 & 2: Content generation (Only happens once)
    print("[Agent C] 1. Generating question...")
    question = await gen_question(blueprint)
    
    print("[Agent C] 2. Formatting HTML...")
    question["description_html"] = await format_html(question.get("description_markdown", ""))

    # Step 5: Test Case Gen (We generate tests early so we can test the code against them)
    print("[Agent C] 5. Generating test cases...")
    test_cases = await generate_tests(question)
    
    # Internal Retry Loop (Max 3 attempts)
    max_retries = 3
    passed = False
    feedback = ""
    
    for attempt in range(1, max_retries + 1):
        print(f"\n[Agent C] Attempt {attempt}/{max_retries}...")
        
        # We append error feedback to the blueprint so the AI learns from its mistake
        blueprint_with_feedback = dict(blueprint)
        if feedback:
            blueprint_with_feedback["previous_error"] = feedback

        print("  - Designing architecture...")
        solution_arch = await design_solution(question, blueprint_with_feedback)

        print("  - Writing code...")
        code_result = await gen_code(question, solution_arch, language, template)
        formatted_code = format_code(code_result.get("solution_code", ""), language)
        
        print("  - Executing in Sandbox...")
        sandbox_res = await execute_and_verify(formatted_code, language, test_cases)
        
        if sandbox_res.get("passed"):
            print("  ✅ All sandbox tests passed!")
            passed = True
            break
        else:
            feedback = sandbox_res.get("output", "Unknown error")
            print(f"  ❌ Sandbox Failed! Error: {feedback.strip().splitlines()[-1] if feedback else 'None'}")
            print("  🔄 Retrying...")

    return {
        "current_agent": "agent_c",
        "updated_at": utcnow(),
        "generated_question": question,
        "solution_architecture": solution_arch,
        "solution_code": formatted_code,
        "test_cases": test_cases,
        "sandbox_passed": passed,
        "internal_retry_count": attempt - 1
    }
