from collections.abc import Collection, Mapping
from unittest.mock import Mock

from payload_cache.services.transformation_service import TransformationService


class MemoryRepository:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get_many(self, texts: Collection[str]) -> dict[str, str]:
        return {text: self.values[text] for text in texts if text in self.values}

    def save_many(self, values: Mapping[str, str]) -> None:
        self.values.update(values)


def test_deduplicates_and_preserves_order() -> None:
    repository = MemoryRepository()
    transformer = Mock(side_effect=str.upper)
    service = TransformationService(repository, transformer)

    assert service.transform_many(["hello", "world", "hello"]) == [
        "HELLO",
        "WORLD",
        "HELLO",
    ]
    assert transformer.call_count == 2
    assert service.transform_many(["world", "hello"]) == ["WORLD", "HELLO"]
    assert transformer.call_count == 2


def test_empty_list_and_empty_string() -> None:
    transformer = Mock(side_effect=str.upper)
    service = TransformationService(MemoryRepository(), transformer)
    assert service.transform_many([]) == []
    transformer.assert_not_called()
    assert service.transform("") == ""
    transformer.assert_called_once_with("")


def test_single_string_uses_cache() -> None:
    transformer = Mock(side_effect=str.upper)
    service = TransformationService(MemoryRepository(), transformer)
    assert service.transform("hello") == "HELLO"
    assert service.transform("hello") == "HELLO"
    transformer.assert_called_once_with("hello")
