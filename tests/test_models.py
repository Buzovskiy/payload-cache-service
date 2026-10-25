import uuid
from typing import cast

from sqlalchemy import Table, UniqueConstraint

from payload_cache.db.base import Base
from payload_cache.db.models import Payload, TransformationCache


def test_models_registered() -> None:
    assert set(Base.metadata.tables) == {"payloads", "transformation_cache"}
    assert Payload.__table__.c.id.type.python_type is uuid.UUID
    table = cast(Table, TransformationCache.__table__)
    assert any(
        isinstance(item, UniqueConstraint) and "original_text" in item.columns
        for item in table.constraints
    )
