from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from payload_cache.db.models import Payload


class PayloadRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_hash(self, request_hash: str) -> Payload | None:
        return self.session.scalar(
            select(Payload).where(Payload.request_hash == request_hash)
        )

    def get_by_id(self, payload_id: UUID) -> Payload | None:
        return self.session.get(Payload, payload_id)

    def create_or_get(
        self, payload_id: UUID, request_hash: str, filename: str
    ) -> tuple[Payload, bool]:
        statement = (
            insert(Payload)
            .values(id=payload_id, request_hash=request_hash, filename=filename)
            .on_conflict_do_nothing(index_elements=[Payload.request_hash])
            .returning(Payload.id)
        )
        try:
            inserted_id = self.session.scalar(statement)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        record = self.get_by_id(inserted_id) if inserted_id else self.get_by_hash(
            request_hash
        )
        if record is None:
            raise RuntimeError("Payload record disappeared after insert")
        return record, inserted_id is not None
