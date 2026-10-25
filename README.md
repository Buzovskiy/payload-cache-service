# Payload Cache Service

FastAPI microservice for generating and caching payloads. **Stage 5:** complete payload API, transformation cache and JSON file storage. CLI is planned next.

## Quickstart (reviewers)

Requires Docker Compose only. Default host ports: API **8005**, PostgreSQL **5432**. No `.env` required if these ports are free.

```bash
docker compose up --build -d
curl http://127.0.0.1:8005/health
curl -X POST http://127.0.0.1:8005/payload \
  -H 'Content-Type: application/json' \
  -d '{"list_1":["first","second"],"list_2":["other","another"]}'
```

The POST response contains an `id`. Retrieve the JSON result:

```bash
curl http://127.0.0.1:8005/payload/<id-from-post>
```

Example response: `{"output":"FIRST, OTHER, SECOND, ANOTHER"}`. The same input lists in the same order return the same ID. Swagger UI: http://localhost:8005/docs.

If either host port is occupied, copy `.env.example` to `.env` and set `API_PORT` or `DB_PORT` (for example, `DB_PORT=5435`). Inside Compose, PostgreSQL is always reached at `db:5432`.

## Persistence and migrations

Compose starts `db`, applies committed migrations through the one-shot `migrate` container, then starts `api`. No migration files are generated automatically. `postgres_data` retains the PostgreSQL database and `payload_files` retains JSON files across container restarts. `docker compose down -v` **destroys both volumes and their data**.

The `transformation_cache` table stores one transformed result per original string. The `payloads` table stores UUID, SHA-256 of canonical input JSON, and JSON filename. Files use UUID names and are written with an atomic replace. An input hash collision is assumed impractical; concurrent identical POST requests resolve to the existing record via `ON CONFLICT DO NOTHING`, with the losing request's temporary output removed. Concurrent cache misses can still invoke the transformer more than once.

## Local development

Install Python 3.12, uv and Docker Compose:

```bash
cp .env.example .env
# Set DB_PORT=5435 here if required
docker compose up -d db
uv sync
uv run alembic upgrade head
uv run uvicorn payload_cache.main:app --app-dir src --reload --port 8005
```

`Settings.database_url` is derived from `DB_HOST`, `DB_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`.

To create migration files after changing models (not necessary for stage 5):

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
uv run alembic check
```

## Tests and quality

```bash
uv run pytest
RUN_DB_TESTS=1 uv run pytest tests/test_transformation_repository.py
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
```

The PostgreSQL integration test requires an already migrated disposable development database. Additional API tests use in-memory repositories and a temporary directory.

**Scope:** Simple synchronous implementation. Physical files were chosen to follow the "payload files" wording in the task. If a file is externally removed, GET returns HTTP 500. No background queue or strict single-flight transformer locking is introduced. The CLI is part of the next stage.
