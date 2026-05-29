from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Finance Data Copilot"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg2://finance_copilot:finance_copilot@localhost:5432/finance_data_copilot"
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_model: str = "mock-finance-sql-explainer"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
