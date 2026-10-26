# Payload Cache Service

FastAPI microservice for generating and caching payloads. Includes the payload API, transformation cache, JSON file storage and a CLI client.

## Quickstart (reviewers)

The API requires Docker Compose; the optional local CLI requires Python 3.12 and [uv](https://docs.astral.sh/uv/). Default host ports: API **8005**, PostgreSQL **5432**. No `.env` required if these ports are free.

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

## CLI client

Use `uv sync` to install the CLI locally and `docker compose up --build -d` to start the API. The production Docker image runs the API only; the CLI is a separate HTTP client.
The CLI submits POST then GET on each iteration. For a single iteration it emits
a JSON object with `id` and `output`; for repeated calls it emits a JSON array.

```bash
uv run cache-cli -j '{"list_1":["hello"],"list_2":["world"]}'
uv run cache-cli -r 3 -i request.json -o result.json
cat request.json | uv run cache-cli --input - --output -
uv run cache-cli --host http://127.0.0.1:8005 --json '{"list_1":[],"list_2":[]}'
uv run cache-cli --help
```

Flags: `--host` defaults to http://127.0.0.1:8005;
`-r/--repeat` is a positive integer (default 1);
`-i/--input` accepts a file or `-` for stdin;
`-j/--json` accepts inline JSON;
`-o/--output` accepts a file or `-` for stdout (default).
Specify exactly one input source. Invalid input or HTTP errors exit nonzero,
with diagnostics on stderr. The task's `-h` alias is ambiguous; it is reserved
for `--help`, while the host uses `--host`.

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

To create migration files after changing models:

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
uv run alembic check
```

## Tests and quality

```bash
uv run pytest  # Fast unit/API/CLI tests (database tests skipped)
RUN_DB_TESTS=1 uv run pytest  # All tests, including real PostgreSQL
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
```

PostgreSQL integration tests are opt-in and require a migrated development database.
They use unique request data and remove their own database rows; payload files live
only in pytest temporary directories. Tests cover repeated and concurrent POSTs,
GET, persisted transformations, and JSON files. Other API tests use in-memory
repositories; CLI tests use an HTTPX mock transport.

**Scope:** Simple synchronous implementation. Physical files were chosen to follow the "payload files" wording in the task. If a file is externally removed, GET returns HTTP 500. No background queue or strict single-flight transformer locking is introduced. The CLI runs locally against the containerized API.


## Architecture and request lifecycle

1. FastAPI validates two equally long string lists using `PayloadRequest`.
2. `PayloadService` hashes a deterministic JSON representation of both lists and
   looks for an existing `payloads` row. A cache hit immediately returns its UUID.
3. On a miss, the service interleaves the lists and asks `TransformationService`
   to batch-read cached strings. Missing distinct strings are uppercased and stored
   in PostgreSQL (`transformation_cache`).
4. The result is written as a UUID-named JSON file and `PayloadRepository` stores
   metadata in PostgreSQL. A unique hash constraint resolves duplicate requests.
5. GET finds the filename by UUID and reads the physical JSON file.

The API uses synchronous SQLAlchemy sessions scoped to each request and a separate
named Docker volume for persisted JSON files. Logs report payload cache HIT/MISS
and transformation cache counts without recording input strings. Keep in mind that
PostgreSQL commits and filesystem writes are not one atomic transaction; an abrupt
process termination may leave an orphan file. Concurrent cache misses can perform
redundant transformations, although duplicate payload records are prevented.

Inspect output and logs:

```bash
docker compose logs -f api
docker compose exec api ls -lah /data/payloads/
```

## Submission checklist

- Publish this repository with full, unsquashed commit history.
- Verify Docker Compose and both HTTP endpoints with sample data.
- Run Ruff, mypy, unit tests and opt-in PostgreSQL integration tests.
- Record an English code walkthrough (camera on, screen shared, up to 15 minutes):
  explain the endpoint-to-database-and-back flow, demonstrate CLI and tests,
  and justify the architecture and trade-offs.
- Email the public repository URL and Loom/unlisted YouTube URL, and report the
  actual number of hours spent on the assignment.
