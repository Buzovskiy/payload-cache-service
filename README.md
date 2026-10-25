# Payload Cache Service

FastAPI payload caching microservice. **Stage 3:** database schema, migrations, and Docker Compose deployment. Payload generation and caching endpoints will follow in later stages.

## Reviewer quickstart

Only Docker Engine with Compose (or Docker Desktop) is required. No `.env` needed when default ports are available:

```bash
docker compose up --build -d
curl http://127.0.0.1:8005/health
```

API docs: http://localhost:8005/docs. By default, the PostgreSQL host port is **5432** and the API host port is **8005**. If either port is already in use, create `.env` from `.env.example` and edit `DB_PORT` / `API_PORT`.

```bash
cp .env.example .env
# For example, change DB_PORT=5435 in .env
docker compose up --build -d
```

Only **one** `compose.yaml` is needed. From within Docker, the API and Alembic always access the database at `db:5432`, regardless of the host's `DB_PORT`. Compose overrides `DB_HOST` and `DB_PORT` inside the app containers. PostgreSQL is only bound to the host loopback interface.

Named volumes `postgres_data` and `payload_files` preserve the database and generated JSON files independently. `docker compose down` preserves them; `docker compose down -v` **deletes both volumes and all data**.

`migrate` applies committed migrations using `alembic upgrade head` once PostgreSQL is healthy; `api` starts only after that command succeeds. Compose never generates migration files.

## Local development and Alembic

Install Python 3.12, uv and Docker Compose. For a machine where port 5432 is occupied:

```bash
cp .env.example .env
# Set DB_PORT=5435 inside .env
docker compose up -d db
uv lock
uv sync
uv run alembic upgrade head
uv run uvicorn payload_cache.main:app --app-dir src --reload --port 8005
```

`Settings.database_url` is built automatically from `DB_HOST`, `DB_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`. **Do not set DATABASE_URL.** Changing DB_PORT in `.env` changes both the host port published by Compose and the connection used by local Alembic/FastAPI.

After changing SQLAlchemy models, generate and review new migrations locally:

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
uv run alembic check
```

Commit each migration file alongside model changes. **The committed `uv.lock` still needs refreshing** for the stage 3 dependencies: run `uv lock` and commit its changes before final submission. Docker resolves dependencies independently until then.

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
