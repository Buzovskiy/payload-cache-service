from collections.abc import Collection, Mapping
from typing import Protocol


class TransformationRepositoryProtocol(Protocol):
    """Storage operations needed by the transformation service."""

    def get_many(self, texts: Collection[str]) -> dict[str, str]: ...

    def save_many(self, values: Mapping[str, str]) -> None: ...
