# Payload Cache Service

FastAPI payload caching microservice. **Stage 3:** database schema, migrations, and Docker Compose deployment. Payload generation and caching endpoints will follow in later stages.

## Reviewer quickstart

Only Docker Engine with the Compose plugin (or Docker Desktop) is required.

```bash
cp .env.example .env
docker compose up --build -d
curl http://127.0.0.1:8005/health
```

Set `API_PORT` in `.env` if port 8005 is occupied. API docs: http://localhost:8005/docs (adjust port if changed).

PostgreSQL is not published by default, preventing collisions with a locally installed database. Containers connect to PostgreSQL at `db:5432`. Docker named volumes `postgres_data` and `payload_files` preserve the database and generated JSON files independently. `docker compose down` preserves them; `docker compose down -v` **deletes both volumes and all data**.

`migrate` applies committed migrations using `alembic upgrade head` once PostgreSQL is healthy; `api` starts only after that command succeeds. Compose never generates migration files.

## Local development and Alembic

Install Python 3.12, uv and Docker Compose. Enable the *optional* PostgreSQL host port:

```bash
cp .env.example .env
docker compose -f compose.yaml -f compose.db-port.yaml up -d db
uv sync
uv run alembic upgrade head
uv run uvicorn payload_cache.main:app --app-dir src --reload --port 8005
```

If port 5433 is occupied, update `DB_PORT` **and the port inside `DATABASE_URL`** in `.env`.

After changing SQLAlchemy models, generate and review new migrations locally:

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
uv run alembic check
```

Commit each migration file alongside its model changes. The `uv.lock` file from stage 2 needs updating for these new dependencies: run `uv lock` locally and commit it before final submission. Docker resolves project dependencies itself until that lockfile is refreshed.

## Quality checks

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
```

## Schema

- `transformation_cache`: unique original string and its transformed result.
- `payloads`: UUID, unique input hash, and unique JSON filename.

File writing, hash calculation, transformer invocation and payload endpoints are planned for subsequent stages.

**Security:** development database credentials are examples only. Use strong secrets outside local development. PostgreSQL initialization credentials do not automatically update an existing persisted data volume.
