from fastapi import FastAPI

from payload_cache.api.routes.health import router as health_router
from payload_cache.api.routes.payload import router as payload_router
from payload_cache.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.include_router(health_router)
    app.include_router(payload_router)
    return app


app = create_app()
