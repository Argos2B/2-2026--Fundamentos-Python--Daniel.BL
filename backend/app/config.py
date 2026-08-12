from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )

    database_url: str = Field("sqlite+aiosqlite:///./backend.db", env="DATABASE_URL")
    secret_key: str = Field("dev-secret-key", env="SECRET_KEY")
    google_client_id: str | None = Field(None, env="GOOGLE_CLIENT_ID")
    google_client_secret: str | None = Field(None, env="GOOGLE_CLIENT_SECRET")
    oauth_redirect_uri: str | None = Field(None, env="OAUTH_REDIRECT_URI")
    api_host: str = Field("127.0.0.1", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")


settings = Settings()
