import logging
from collections.abc import Callable, Sequence

from payload_cache.repositories.protocol import TransformationRepositoryProtocol
from payload_cache.services.transformer import transform


logger = logging.getLogger(__name__)


class TransformationService:
    def __init__(
        self,
        repository: TransformationRepositoryProtocol,
        transformer: Callable[[str], str] = transform,
    ) -> None:
        self.repository = repository
        self.transformer = transformer

    def transform(self, text: str) -> str:
        return self.transform_many([text])[0]

    def transform_many(self, texts: Sequence[str]) -> list[str]:
        if not texts:
            logger.info("Transformation cache: total=0, unique=0, hits=0, misses=0")
            return []

        unique = list(dict.fromkeys(texts))
        cached = self.repository.get_many(unique)
        missing = [text for text in unique if text not in cached]
        logger.info(
            "Transformation cache: total=%d, unique=%d, hits=%d, misses=%d",
            len(texts),
            len(unique),
            len(unique) - len(missing),
            len(missing),
        )
        if missing:
            fresh = {text: self.transformer(text) for text in missing}
            self.repository.save_many(fresh)
            # Read after ON CONFLICT: another writer's committed value wins.
            cached.update(self.repository.get_many(missing))

        return [cached[text] for text in texts]
