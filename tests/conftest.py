from dotenv import load_dotenv
load_dotenv()  # Loads GROQ_API_KEY from your .env file

import pytest
import datetime
# ... rest of your conftest.py ...


@pytest.fixture
def sample_state():
    """Minimal valid QSO for unit tests."""
    now = datetime.datetime.utcnow().isoformat()
    return {
        "request_id":           "test-request-001",
        "question_id":          "test-question-001",
        "client_id":            "00000000-0000-0000-0000-000000000001",
        "version":              1,
        "status":               "PROCESSING",
        "current_agent":        "",
        "retry_counts":         {},
        "internal_retry_count": 0,
        "revision_count":       0,
        "error_log":            [],
        "requirements": {
            "topic":                  "Arrays",
            "subtopic":               "Two Pointers",
            "difficulty":             "MEDIUM",
            "question_type":          "ALGORITHMIC",
            "target_language":        "python",
            "max_solve_time_minutes": 30,
            "raw_request":            '{"topic":"Arrays","difficulty":"MEDIUM"}',
        },
        "agent_run_ids": [],
        "created_at":    now,
        "updated_at":    now,
    }