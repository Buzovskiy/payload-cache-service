from typing import Protocol


class TransformationServiceProtocol(Protocol):
    def transform_many(self, texts: list[str]) -> list[str]: ...
