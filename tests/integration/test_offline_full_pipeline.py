import json
from pathlib import Path

import pytest

from agents.agent_c.code_format import format_code
from orchestrator import graph as graph_module


FIXTURES = Path(__file__).parents[1] / "fixtures"


@pytest.mark.asyncio
async def test_full_graph_runs_offline_with_dummy_inputs(monkeypatch):
    state = json.loads((FIXTURES / "offline_pipeline_input.json").read_text())
    reference_data = json.loads((FIXTURES / "offline_reference_data.json").read_text())

    async def intake(raw_request):
        return {**state["requirements"], "raw_request": raw_request}

    async def map_topic(topic, subtopic):
        return {"learning_objectives": ["Use two pointers"], "topic_alignment_score": 1.0}

    async def client_config(client_id, language, question_type):
        return {"code_template": "def solution(values, target):\n    pass\n"}

    async def blueprint(**kwargs):
        return {"scenario": "Match two sorted payments.", "constraints": ["O(n)"], "key_concepts": ["two pointers"]}

    async def retrieve(requirements, client_id, limit=3):
        return reference_data

    async def question(blueprint, references=None):
        return {"title": "Pair Sum", "description_markdown": "Find two values.", "purpose": "arrays"}

    async def html(markdown):
        return "<p>Find two values.</p>"

    async def tests(question):
        return [
            {"type": "VISIBLE", "input_args": "[1, 2, 4, 8], 6", "expected_output": [1, 2]},
            {"type": "HIDDEN", "input_args": "[2, 3], 10", "expected_output": []},
        ]

    async def architecture(question, blueprint):
        return {"algorithm": "two pointers", "time_complexity": "O(n)"}

    async def code(question, architecture, language, template):
        return {"solution_code": (FIXTURES / "dummy_solution_unformatted.py").read_text()}

    async def execute(code, language, test_cases):
        return {"passed": True, "output": "All tests passed!"}

    async def llm(**kwargs):
        return json.dumps({"scores": {"clarity": 5, "edge_cases": 5, "efficiency": 5, "formatting": 5}}), {}

    async def quality_gate(state):
        return {
            "current_agent": "agent_d",
            "quality": {"pass": True, "scores": {"clarity": 5}, "avg_score": 5},
            "consistency": {"consistent": True, "mismatches": []},
        }

    async def final_gate(state):
        return {
            "current_agent": "agent_g",
            "status": "AWAITING_REVIEW",
            "final_qa": {"approved": True, "deterministic_checks": {"html_valid": True}},
        }

    monkeypatch.setattr("agents.agent_a.runner.extract_requirements", intake)
    monkeypatch.setattr("agents.agent_a.runner.map_topic", map_topic)
    monkeypatch.setattr("agents.agent_a.runner.load_client_config", client_config)
    monkeypatch.setattr("agents.agent_a.runner.design_blueprint", blueprint)
    monkeypatch.setattr("agents.agent_b.runner.retrieve_references", retrieve)
    monkeypatch.setattr("agents.agent_c.runner.gen_question", question)
    monkeypatch.setattr("agents.agent_c.runner.format_html", html)
    monkeypatch.setattr("agents.agent_c.runner.generate_tests", tests)
    monkeypatch.setattr("agents.agent_c.runner.design_solution", architecture)
    monkeypatch.setattr("agents.agent_c.runner.gen_code", code)
    monkeypatch.setattr("agents.agent_c.runner.execute_and_verify", execute)
    monkeypatch.setattr("agents.agent_d.runner.groq_chat", llm)
    monkeypatch.setattr(graph_module, "run_agent_d", quality_gate)
    monkeypatch.setattr(graph_module, "run_agent_g", final_gate)
    monkeypatch.setattr("asyncio.ensure_future", lambda coroutine: coroutine.close())

    result = await graph_module.build_graph().ainvoke(state)

    assert result["status"] == "AWAITING_REVIEW"
    assert result["current_agent"] == "agent_g"
    assert result["question"]["title"] == "Pair Sum"
    assert result["code"]["solution"]
    assert result["execution"]["all_passed"] is True
    assert result["final_qa"]["approved"] is True
    assert format_code((FIXTURES / "dummy_solution_unformatted.py").read_text(), "python") != (
        FIXTURES / "dummy_solution_unformatted.py"
    ).read_text()
