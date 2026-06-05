from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./outbound.db"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    serpapi_key: str | None = None
    outreach_from_name: str = "ENVI"
    outreach_product_name: str = "ENVI"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
