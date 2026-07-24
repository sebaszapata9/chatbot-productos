from functools import lru_cache

from app.config import get_settings
from app.repositories.google_sheets import GoogleSheetsCatalogSource
from app.services.catalog import CatalogService


@lru_cache
def get_catalog_service() -> CatalogService:
    settings = get_settings()
    source = GoogleSheetsCatalogSource(
        spreadsheet_id=settings.spreadsheet_id,
        sheet_range=settings.sheet_range,
        credentials_file=settings.credentials_file,
    )
    return CatalogService(
        source=source,
        cache_ttl_seconds=settings.cache_ttl_seconds,
        min_score=settings.search_min_score,
    )
