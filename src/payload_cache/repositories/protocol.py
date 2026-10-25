from collections.abc import Collection, Mapping
from typing import Protocol
from uuid import UUID


class TransformationRepositoryProtocol(Protocol):
    """Storage operations needed by the transformation service."""

    def get_many(self, texts: Collection[str]) -> dict[str, str]: ...

    def save_many(self, values: Mapping[str, str]) -> None: ...


class PayloadRecordProtocol(Protocol):
    @property
    def id(self) -> UUID: ...

    @property
    def filename(self) -> str: ...


class PayloadRepositoryProtocol(Protocol):
    def get_by_hash(self, request_hash: str) -> PayloadRecordProtocol | None: ...

    def get_by_id(self, payload_id: UUID) -> PayloadRecordProtocol | None: ...

    def create_or_get(
        self, payload_id: UUID, request_hash: str, filename: str
    ) -> tuple[PayloadRecordProtocol, bool]: ...
