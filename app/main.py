from fastapi import Depends, FastAPI, HTTPException, Query

from app.config import get_settings
from app.dependencies import get_catalog_service
from app.models.catalog import CatalogLoadReport
from app.models.product import Product, ProductSearchResult
from app.services.catalog import CatalogService

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/catalog/refresh", response_model=CatalogLoadReport)
def refresh_catalog(
    service: CatalogService = Depends(get_catalog_service),
) -> CatalogLoadReport:
    try:
        return service.refresh(force=True)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="No se pudo actualizar el catálogo") from exc


@app.get("/products/{sku}", response_model=Product)
def get_product(
    sku: str,
    service: CatalogService = Depends(get_catalog_service),
) -> Product:
    product = service.get_by_sku(sku)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


@app.get("/products", response_model=list[ProductSearchResult])
def search_products(
    q: str = Query(min_length=1, max_length=200),
    category: str | None = Query(default=None, max_length=150),
    limit: int = Query(default=5, ge=1, le=20),
    service: CatalogService = Depends(get_catalog_service),
) -> list[ProductSearchResult]:
    return service.search(q, category=category, limit=limit)
