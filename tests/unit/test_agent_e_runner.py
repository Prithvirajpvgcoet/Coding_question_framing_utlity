import asyncio
import json
from pathlib import Path

import pytest

from agents.agent_e import runner as agent_e_runner
from agents.agent_f import runner as agent_f_runner
from orchestrator.edges import route_after_agent_f


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("category", "expected_route"),
    [("REQUIREMENTS", "agent_a"), ("LOGIC", "agent_c"), ("FORMATTING", "agent_d")],
)
async def test_feedback_classification_flows_to_revision_route(
    monkeypatch, category, expected_route
):
    feedback = load_fixture("agent_e_feedback.json")
    expected_classification = {
        **load_fixture("agent_e_formatted_response.json"),
        "category": category,
    }
    scheduled_logs = []
    llm_call = {}
    logged_runs = []

    async def fake_groq_chat(**kwargs):
        llm_call.update(kwargs)
        return f"```json\n{json.dumps(expected_classification)}\n```", {
            "model": "fixture-model",
            "input_tokens": 10,
            "output_tokens": 8,
            "latency_ms": 1,
            "prompt_hash": "fixture-hash",
            "cost_usd": 0.0,
        }

    async def fake_log_agent_run(**kwargs):
        logged_runs.append(kwargs)

    monkeypatch.setattr(agent_e_runner, "groq_chat", fake_groq_chat)
    monkeypatch.setattr(
        agent_e_runner.asyncio,
        "ensure_future",
        lambda coroutine: scheduled_logs.append(coroutine),
    )
    monkeypatch.setattr("observability.agent_logger.log_agent_run", fake_log_agent_run)

    agent_e_result = await agent_e_runner.run(feedback)
    state = {**feedback, **agent_e_result}
    agent_f_result = await agent_f_runner.run(state)
    state.update(agent_f_result)

    await asyncio.gather(*scheduled_logs)

    assert llm_call["user"] == (
        "Human feedback: Please fix the typo in the question description "
        "and keep the algorithm unchanged."
    )
    assert "Return ONLY a valid JSON object" in llm_call["system"]
    assert agent_e_result["current_agent"] == "agent_e"
    assert agent_e_result["feedback_classification"] == expected_classification
    assert state["current_agent"] == "agent_f"
    assert state["revision_route"] == expected_route
    assert route_after_agent_f(state) == expected_route
    assert len(logged_runs) == 1
    assert logged_runs[0]["status"] == "SUCCESS"
