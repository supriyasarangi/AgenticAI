import os
from pydantic import BaseModel, Field


class Settings(BaseModel):
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = Field(default_factory=lambda: os.getenv("CARTA_MODEL", "claude-sonnet-5"))
    max_retries: int = Field(default_factory=lambda: int(os.getenv("CARTA_MAX_RETRIES", "4")))
    timeout_seconds: int = Field(default_factory=lambda: int(os.getenv("CARTA_TIMEOUT_SECONDS", "30")))

    class Config:
        validate_default = True


def load_settings() -> Settings:
    return Settings()
