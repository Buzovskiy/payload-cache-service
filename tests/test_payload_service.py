from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest

from payload_cache.services.payload_service import (
    PayloadFileMissingError,
    PayloadNotFoundError,
    PayloadService,
    hash_request,
)
from payload_cache.storage.file_storage import PayloadFileStorage


class MemoryPayloadRepository:
    def __init__(self) -> None:
        self.by_hash: dict[str, SimpleNamespace] = {}
        self.by_id: dict[UUID, SimpleNamespace] = {}

    def get_by_hash(self, request_hash: str) -> SimpleNamespace | None:
        return self.by_hash.get(request_hash)

    def get_by_id(self, payload_id: UUID) -> SimpleNamespace | None:
        return self.by_id.get(payload_id)

    def create_or_get(
        self, payload_id: UUID, request_hash: str, filename: str
    ) -> tuple[SimpleNamespace, bool]:
        existing = self.get_by_hash(request_hash)
        if existing is not None:
            return existing, False
        record = SimpleNamespace(id=payload_id, filename=filename)
        self.by_hash[request_hash] = record
        self.by_id[payload_id] = record
        return record, True


class FakeTransformations:
    def __init__(self) -> None:
        self.calls = 0

    def transform_many(self, texts: list[str]) -> list[str]:
        self.calls += 1
        return [text.upper() for text in texts]


def build_service(
    directory: Path,
) -> tuple[PayloadService, MemoryPayloadRepository, FakeTransformations]:
    repository = MemoryPayloadRepository()
    transformer = FakeTransformations()
    # Replace implementations in this isolated unit test; no database is required.
    service = PayloadService(  # type: ignore[arg-type]
        repository, transformer, PayloadFileStorage(directory)
    )
    return service, repository, transformer


def test_roundtrip_and_identical_request_reuses_id(tmp_path: Path) -> None:
    service, repository, transformer = build_service(tmp_path)
    first = service.create(["hello", "python"], ["world", "fastapi"])
    second = service.create(["hello", "python"], ["world", "fastapi"])

    assert first == second
    assert service.get(first) == "HELLO, WORLD, PYTHON, FASTAPI"
    assert transformer.calls == 1
    assert len(repository.by_id) == 1
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_hash_preserves_order_and_list_identity() -> None:
    assert hash_request(["a"], ["b"]) != hash_request(["b"], ["a"])
    assert hash_request(["a", "b"], ["c", "d"]) != hash_request(
        ["b", "a"], ["c", "d"]
    )


def test_empty_lists(tmp_path: Path) -> None:
    service, _, _ = build_service(tmp_path)
    payload_id = service.create([], [])
    assert service.get(payload_id) == ""


def test_missing_payload_and_missing_file(tmp_path: Path) -> None:
    service, _, _ = build_service(tmp_path)
    with pytest.raises(PayloadNotFoundError):
        service.get(UUID(int=0))
    payload_id = service.create(["a"], ["b"])
    (tmp_path / f"{payload_id}.json").unlink()
    with pytest.raises(PayloadFileMissingError):
        service.get(payload_id)


def test_invalid_lengths(tmp_path: Path) -> None:
    service, _, _ = build_service(tmp_path)
    with pytest.raises(ValueError):
        service.create(["a"], [])
