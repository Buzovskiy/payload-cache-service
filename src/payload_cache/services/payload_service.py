import hashlib
import json
from collections.abc import Sequence
from uuid import UUID, uuid4

from payload_cache.repositories.protocol import PayloadRepositoryProtocol
from payload_cache.services.protocol import TransformationServiceProtocol
from payload_cache.storage.file_storage import PayloadFileStorage


class PayloadNotFoundError(Exception):
    pass


class PayloadFileMissingError(Exception):
    pass


def hash_request(list_1: Sequence[str], list_2: Sequence[str]) -> str:
    serialized = json.dumps(
        {"list_1": list_1, "list_2": list_2},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class PayloadService:
    def __init__(
        self,
        repository: PayloadRepositoryProtocol,
        transformation_service: TransformationServiceProtocol,
        storage: PayloadFileStorage,
    ) -> None:
        self.repository = repository
        self.transformation_service = transformation_service
        self.storage = storage

    def create(self, list_1: list[str], list_2: list[str]) -> UUID:
        if len(list_1) != len(list_2):
            raise ValueError("Input lists must have the same length")

        request_hash = hash_request(list_1, list_2)
        existing = self.repository.get_by_hash(request_hash)
        if existing is not None:
            return existing.id

        interleaved = [
            value for pair in zip(list_1, list_2, strict=True) for value in pair
        ]
        transformed = self.transformation_service.transform_many(interleaved)
        output = ", ".join(transformed)

        payload_id = uuid4()
        filename = f"{payload_id}.json"
        self.storage.write(filename, output)
        try:
            record, created = self.repository.create_or_get(
                payload_id, request_hash, filename
            )
        except Exception:
            self.storage.delete(filename)
            raise

        if not created:
            # A concurrent request inserted the same hash first.
            self.storage.delete(filename)
        return record.id

    def get(self, payload_id: UUID) -> str:
        record = self.repository.get_by_id(payload_id)
        if record is None:
            raise PayloadNotFoundError
        try:
            return self.storage.read(record.filename)
        except FileNotFoundError as exc:
            raise PayloadFileMissingError from exc
