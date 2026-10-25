import os
import uuid

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from payload_cache.core.config import get_settings
from payload_cache.db.models import TransformationCache
from payload_cache.repositories.transformation_repository import (
    TransformationRepository,
)


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="Set RUN_DB_TESTS=1 to run PostgreSQL integration tests",
)
def test_postgresql_cache_persists_and_avoids_duplicates() -> None:
    # Requires an already migrated, disposable development database.
    prefix = f"test-{uuid.uuid4()}-"
    original = prefix + "hello"
    engine = create_engine(get_settings().database_url)
    try:
        with Session(engine) as session:
            repository = TransformationRepository(session)
            try:
                assert repository.get_many([original]) == {}
                repository.save_many({original: "HELLO"})
                repository.save_many({original: "CHANGED"})
                assert repository.get_many([original]) == {original: "HELLO"}
            finally:
                session.execute(
                    delete(TransformationCache).where(
                        TransformationCache.original_text == original
                    )
                )
                session.commit()
    finally:
        engine.dispose()
