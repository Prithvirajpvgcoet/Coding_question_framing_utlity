from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from starlette.testclient import TestClient
from api.main import app
from api.deps import get_db

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": "test-key-001"}


@pytest.fixture(autouse=True)
def override_db_dependency():
    """Mock the get_db dependency for fast unit tests without live Postgres."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.execute = AsyncMock()
    
    # Mock result for queries
    mock_result = MagicMock()
    mock_result.all.return_value = [("PROCESSING", 5), ("APPROVED", 10), ("AWAITING_REVIEW", 3)]
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    async def _mock_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = _mock_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "A" in data["agents"]


def test_auth_missing():
    res = client.get("/api/v1/dashboard/stats")
    assert res.status_code == 401
    assert "Missing X-API-Key" in res.json()["detail"]


@patch("workers.tasks.run_question_generation.delay")
def test_generate_single(mock_celery):
    mock_celery.return_value = MagicMock(id="task-123")
    payload = {
        "topic": "Arrays",
        "subtopic": "Sliding Window",
        "difficulty": "MEDIUM",
        "question_type": "ALGORITHMIC",
        "target_language": "python",
        "max_solve_time_minutes": 25,
    }
    res = client.post("/api/v1/generate", json=payload, headers=AUTH_HEADERS)
    assert res.status_code == 202
    data = res.json()
    assert "question_id" in data
    assert data["status"] == "PROCESSING"
    assert mock_celery.called


@patch("workers.tasks.run_question_generation.delay")
def test_generate_batch(mock_celery):
    mock_celery.return_value = MagicMock(id="task-batch-123")
    payload = {
        "items": [
            {"topic": "Trees", "difficulty": "HARD", "target_language": "python"},
            {"topic": "Graphs", "difficulty": "MEDIUM", "target_language": "python"},
        ]
    }
    res = client.post("/api/v1/generate/batch", json=payload, headers=AUTH_HEADERS)
    assert res.status_code == 202
    data = res.json()
    assert data["count"] == 2
    assert len(data["items"]) == 2
    assert mock_celery.call_count >= 2


def test_dashboard_stats():
    res = client.get("/api/v1/dashboard/stats", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "generated" in data
    assert "approved" in data
    assert "awaiting_review" in data
    assert data["generated"] == 18


def test_list_runs():
    res = client.get("/api/v1/runs", headers=AUTH_HEADERS)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_list_banks():
    res = client.get("/api/v1/banks", headers=AUTH_HEADERS)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_list_uploads():
    res = client.get("/api/v1/uploads", headers=AUTH_HEADERS)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@patch("workers.upload_tasks.run_upload_job.delay")
def test_create_upload_job(mock_upload):
    mock_upload.return_value = MagicMock(id="task-up-1")
    payload = {
        "question_id": "00000000-0000-0000-0000-000000000001",
        "bank_id": "embedded-capgemini"
    }
    res = client.post("/api/v1/uploads", json=payload, headers=AUTH_HEADERS)
    assert res.status_code == 202
    data = res.json()
    assert "job_id" in data
    assert data["status"] == "QUEUED"
