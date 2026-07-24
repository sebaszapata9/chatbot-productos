from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Kumateq Catalog Service"
    spreadsheet_id: str = Field(default="", alias="GOOGLE_SPREADSHEET_ID")
    sheet_range: str = Field(default="productos!A:Z", alias="GOOGLE_SHEET_RANGE")
    credentials_file: str = Field(
        default="credentials/service-account.json",
        alias="GOOGLE_APPLICATION_CREDENTIALS",
    )
    cache_ttl_seconds: int = Field(default=45, ge=1, alias="CATALOG_CACHE_TTL_SECONDS")
    search_default_limit: int = Field(default=5, ge=1, le=20)
    search_min_score: float = Field(default=0.35, ge=0, le=1)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
