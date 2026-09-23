"""
Phase 1 live test — calls real Groq API.
Skipped automatically if GROQ_API_KEY is not set.
"""
import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set — skipping live Groq test"
)


@pytest.mark.asyncio
async def test_extract_requirements_live():
    from agents.agent_a.intake import extract_requirements
    result = await extract_requirements(
        "I need a medium difficulty graph problem on BFS in Python, 30 minutes"
    )
    assert result["topic"].lower() in ("graph", "graphs", "bfs")
    assert result["difficulty"] == "MEDIUM"
    assert result["target_language"] == "python"
    assert result["max_solve_time_minutes"] == 30
    print(f"\n✅ Intake result: {result}")


@pytest.mark.asyncio
async def test_design_blueprint_live():
    from agents.agent_a.blueprint import design_blueprint
    from agents.agent_a.curriculum import map_topic

    requirements = {
        "topic": "Graphs", "subtopic": "BFS",
        "difficulty": "MEDIUM", "target_language": "python",
        "question_type": "ALGORITHMIC", "max_solve_time_minutes": 30,
        "custom_constraints": []
    }
    curriculum    = await map_topic("Graphs", "BFS")
    client_config = {"question_style": "standard", "difficulty_bias": 0.0,
                     "html_template": "", "code_template": "def solution(): pass"}

    blueprint = await design_blueprint(requirements, curriculum, client_config, [])

    assert "scenario" in blueprint
    assert "key_concepts" in blueprint
    assert "approach_hint" in blueprint
    assert len(blueprint["scenario"]) > 20
    print(f"\n✅ Blueprint scenario: {blueprint['scenario']}")
    print(f"   Approach: {blueprint['approach_hint']}")
    print(f"   Cost: ${blueprint.get('_blueprint_usage', {}).get('cost_usd', 0):.5f}")


@pytest.mark.asyncio
async def test_full_agent_a_live(sample_state):
    """Full Agent A run with real Groq calls."""
    from agents.agent_a import run

    state = {
        **sample_state,
        "requirements": {
            "topic": "Dynamic Programming",
            "subtopic": "Knapsack",
            "difficulty": "HARD",
            "target_language": "python",
            "question_type": "ALGORITHMIC",
            "max_solve_time_minutes": 45,
            "custom_constraints": ["no recursion allowed"],
            "raw_request": "Hard DP Knapsack problem in Python",
        }
    }
    result = await run(state)

    assert result["current_agent"] == "agent_a"
    assert result["blueprint"]["scenario"] != ""
    assert len(result["blueprint"]["key_concepts"]) > 0
    print(f"\n✅ Agent A complete!")
    print(f"   Topic: {result['requirements']['topic']}")
    print(f"   Blueprint: {result['blueprint']['scenario'][:100]}...")