from collections.abc import Collection, Mapping

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from payload_cache.db.models import TransformationCache


class TransformationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_many(self, texts: Collection[str]) -> dict[str, str]:
        if not texts:
            return {}
        rows = self.session.execute(
            select(
                TransformationCache.original_text,
                TransformationCache.transformed_text,
            ).where(TransformationCache.original_text.in_(texts))
        ).all()
        return {original: transformed for original, transformed in rows}

    def save_many(self, values: Mapping[str, str]) -> None:
        if not values:
            return
        # Concurrent writers may race; the unique constraint keeps one cache entry.
        statement = insert(TransformationCache).values(
            [
                {"original_text": original, "transformed_text": transformed}
                for original, transformed in values.items()
            ]
        )
        self.session.execute(
            statement.on_conflict_do_nothing(constraint="uq_transform_original")
        )
        self.session.commit()
