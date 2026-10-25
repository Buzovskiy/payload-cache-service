from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """Local DB_PORT maps to the published PostgreSQL port; Docker uses db:5432."""

    app_name: str = "Payload Cache Service"
    debug: bool = False
    db_host: str = "localhost"
    db_port: int = Field(default=5432, ge=1, le=65535)
    postgres_user: str = "payload"
    postgres_password: str = "payload"
    postgres_db: str = "payload_cache"
    payload_directory: Path = Path("./data/payloads")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.db_host,
            port=self.db_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
