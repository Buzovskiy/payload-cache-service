import logging
import sys

from fastapi import FastAPI

from payload_cache.api.routes.health import router as health_router
from payload_cache.api.routes.payload import router as payload_router
from payload_cache.core.config import get_settings


def configure_logging() -> None:
    logger = logging.getLogger("payload_cache")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.include_router(health_router)
    app.include_router(payload_router)
    return app


app = create_app()
