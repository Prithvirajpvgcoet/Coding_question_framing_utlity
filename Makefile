.PHONY: install dev db-init test lint format

install:
	pip install uv && uv sync

dev:
	docker compose up --build

infra:
	docker compose up postgres redis -d

migrate:
	uv run alembic upgrade head

test:
	uv run pytest tests/ -v --cov=. --cov-report=term-missing

test-unit:
	uv run pytest tests/unit/ -v

lint:
	uv run ruff check .

format:
	uv run ruff format .

worker:
	uv run celery -A workers.celery_app worker --loglevel=info

api:
	uv run uvicorn api.main:app --reload --port 8000