FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
WORKDIR /app
COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app/src PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN mkdir -p /data/payloads && useradd --system --uid 10001 appuser && chown -R appuser:appuser /data
USER appuser
EXPOSE 8000
CMD ["uvicorn", "payload_cache.main:app", "--host", "0.0.0.0", "--port", "8000"]
