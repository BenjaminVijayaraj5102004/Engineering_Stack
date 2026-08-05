"""Settings configuration for engineeringstack."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: Optional[str] = ""
    GITHUB_ACCESS_TOKEN: Optional[str] = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
