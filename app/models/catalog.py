from pydantic import BaseModel, Field


class CatalogIssue(BaseModel):
    row_number: int = Field(ge=2)
    sku: str | None = None
    message: str


class CatalogLoadReport(BaseModel):
    total_rows: int = 0
    valid_products: int = 0
    ignored_inactive: int = 0
    invalid_rows: int = 0
    duplicate_skus: int = 0
    issues: list[CatalogIssue] = []
