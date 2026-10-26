"""PostgreSQL and filesystem integration tests; opt in with RUN_DB_TESTS=1."""

import json
import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session

from payload_cache.api.routes.payload import get_payload_service
from payload_cache.core.config import get_settings
from payload_cache.db.models import Payload, TransformationCache
from payload_cache.main import create_app
from payload_cache.repositories.payload_repository import PayloadRepository
from payload_cache.repositories.transformation_repository import (
    TransformationRepository,
)
from payload_cache.services.payload_service import PayloadService, hash_request
from payload_cache.services.transformation_service import TransformationService
from payload_cache.storage.file_storage import PayloadFileStorage

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="Set RUN_DB_TESTS=1 to run PostgreSQL integration tests",
)


@pytest.mark.parametrize("concurrent", [False, True])
def test_payload_roundtrip_with_postgres(tmp_path: Path, concurrent: bool) -> None:
    engine = create_engine(get_settings().database_url)
    prefix = f"integration-{uuid4()}-"
    left = [prefix + "hello", prefix + "python"]
    right = [prefix + "world", prefix + "fastapi"]
    values = left + right
    request = {"list_1": left, "list_2": right}
    request_hash = hash_request(left, right)
    app = create_app()

    def test_service() -> Iterator[PayloadService]:
        # Session scope matches the request; files stay isolated in tmp_path.
        with Session(engine) as session:
            yield PayloadService(
                repository=PayloadRepository(session),
                transformation_service=TransformationService(
                    TransformationRepository(session)
                ),
                storage=PayloadFileStorage(tmp_path),
            )

    app.dependency_overrides[get_payload_service] = test_service
    try:
        with TestClient(app) as client:
            if concurrent:
                with ThreadPoolExecutor(max_workers=4) as pool:
                    responses = list(
                        pool.map(
                            lambda _: client.post("/payload", json=request),
                            range(4),
                        )
                    )
            else:
                responses = [client.post("/payload", json=request) for _ in range(3)]
            assert all(response.status_code == 201 for response in responses)
            ids = {UUID(response.json()["id"]) for response in responses}
            assert len(ids) == 1
            payload_id = ids.pop()

            expected = ", ".join(
                value.upper()
                for pair in zip(left, right, strict=True)
                for value in pair
            )
            response = client.get(f"/payload/{payload_id}")
            assert response.status_code == 200
            assert response.json() == {"output": expected}

            with Session(engine) as session:
                assert (
                    session.scalar(
                        select(func.count())
                        .select_from(Payload)
                        .where(Payload.request_hash == request_hash)
                    )
                    == 1
                )
                assert session.scalar(
                    select(func.count())
                    .select_from(TransformationCache)
                    .where(TransformationCache.original_text.in_(values))
                ) == len(values)

            files = list(tmp_path.glob("*.json"))
            assert len(files) == 1
            assert json.loads(files[0].read_text(encoding="utf-8")) == {
                "output": expected
            }
    finally:
        app.dependency_overrides.clear()
        try:
            with Session(engine) as session:
                session.execute(
                    delete(Payload).where(Payload.request_hash == request_hash)
                )
                session.execute(
                    delete(TransformationCache).where(
                        TransformationCache.original_text.in_(values)
                    )
                )
                session.commit()
        finally:
            engine.dispose()
