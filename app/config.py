from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./outbound.db"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    serpapi_key: str | None = None
    outreach_from_name: str = "Joaquin"
    outreach_product_name: str = "ENVI"
    whatsapp_template_language: str = "es_AR"
    whatsapp_template_initial_name: str = "envi_diagnostico_inicial_v1"
    whatsapp_template_follow_up_1_name: str = "envi_diagnostico_followup_1_v1"
    whatsapp_template_follow_up_2_name: str = "envi_diagnostico_followup_2_v1"
    whatsapp_template_breakup_name: str = "envi_diagnostico_cierre_v1"
    chatwoot_dry_run: bool = True
    chatwoot_base_url: str | None = None
    chatwoot_account_id: int | None = None
    chatwoot_api_access_token: str | None = None
    chatwoot_inbox_identifier: str | None = None
    whatsapp_max_sends_per_day: int = 50
    whatsapp_max_sends_per_hour: int = 10
    whatsapp_min_seconds_between_sends: int = 120
    whatsapp_lead_cooldown_hours: int = 72

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
