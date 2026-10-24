# Payload Cache Service

A FastAPI microservice for generating and caching string payloads.

> Current stage: application foundation. Payload endpoints, persistence, and caching will follow in subsequent commits.

## Prerequisites

- Python 3.12 or newer (before 3.15)
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
cp .env.example .env
```

The database URL is a configuration placeholder for the upcoming persistence stage; no database is used yet.

## Run

```bash
uv run uvicorn payload_cache.main:app --app-dir src --reload --port 8000
```

- Health check: http://127.0.0.1:8000/health
- OpenAPI UI: http://127.0.0.1:8000/docs

## Quality checks

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
```

## Project layout

- `src/payload_cache/api/`: HTTP routes
- `src/payload_cache/core/`: configuration
- `src/payload_cache/main.py`: application factory
- `tests/`: automated tests

## Next steps

Database models and migrations, transformation caching, payload endpoints, CLI, and containerization.
