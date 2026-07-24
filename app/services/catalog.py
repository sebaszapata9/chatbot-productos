from __future__ import annotations

import logging
import threading
import time
from difflib import SequenceMatcher

from pydantic import ValidationError

from app.models.catalog import CatalogIssue, CatalogLoadReport
from app.models.product import Product, ProductSearchResult, normalize_text
from app.repositories.base import CatalogSource

logger = logging.getLogger(__name__)


class CatalogService:
    REQUIRED_COLUMNS = {
        "sku", "nombre", "categoria", "descripcion",
        "precio", "moneda", "stock", "estado",
    }

    def __init__(
        self,
        source: CatalogSource,
        cache_ttl_seconds: int = 45,
        min_score: float = 0.35,
    ) -> None:
        self.source = source
        self.cache_ttl_seconds = cache_ttl_seconds
        self.min_score = min_score
        self._products: tuple[Product, ...] = ()
        self._by_sku: dict[str, Product] = {}
        self._loaded_at_monotonic = 0.0
        self._lock = threading.RLock()
        self.last_report = CatalogLoadReport()

    def _cache_expired(self) -> bool:
        return (
            not self._products
            or time.monotonic() - self._loaded_at_monotonic >= self.cache_ttl_seconds
        )

    def ensure_loaded(self) -> None:
        if self._cache_expired():
            self.refresh()

    def refresh(self, force: bool = False) -> CatalogLoadReport:
        with self._lock:
            if not force and not self._cache_expired():
                return self.last_report

            rows = self.source.fetch_rows()
            report = CatalogLoadReport(total_rows=len(rows))
            products: list[Product] = []
            seen_skus: set[str] = set()

            if rows:
                missing = self.REQUIRED_COLUMNS - set(rows[0])
                if missing:
                    raise ValueError(
                        "Faltan columnas obligatorias: " + ", ".join(sorted(missing))
                    )

            for row_number, row in enumerate(rows, start=2):
                try:
                    product = Product.model_validate(row)
                    if product.sku in seen_skus:
                        report.duplicate_skus += 1
                        report.issues.append(
                            CatalogIssue(
                                row_number=row_number,
                                sku=product.sku,
                                message="SKU duplicado",
                            )
                        )
                        continue
                    seen_skus.add(product.sku)

                    if not product.is_active:
                        report.ignored_inactive += 1
                        continue
                    products.append(product)
                except ValidationError as exc:
                    report.invalid_rows += 1
                    message = "; ".join(
                        f"{'.'.join(map(str, error['loc']))}: {error['msg']}"
                        for error in exc.errors()
                    )
                    report.issues.append(
                        CatalogIssue(
                            row_number=row_number,
                            sku=str(row.get("sku") or "") or None,
                            message=message,
                        )
                    )

            self._products = tuple(products)
            self._by_sku = {product.sku: product for product in products}
            self._loaded_at_monotonic = time.monotonic()
            report.valid_products = len(products)
            self.last_report = report
            logger.info("catalog_refreshed", extra=report.model_dump())
            return report

    def list_products(self) -> tuple[Product, ...]:
        self.ensure_loaded()
        return self._products

    def get_by_sku(self, sku: str) -> Product | None:
        self.ensure_loaded()
        return self._by_sku.get(str(sku).strip().upper())

    def search(
        self,
        query: str,
        category: str | None = None,
        limit: int = 5,
    ) -> list[ProductSearchResult]:
        self.ensure_loaded()
        normalized_query = normalize_text(query)
        if not normalized_query:
            return []

        query_tokens = set(normalized_query.split())
        normalized_category = normalize_text(category or "")
        results: list[ProductSearchResult] = []

        for product in self._products:
            if normalized_category and normalized_category not in normalize_text(product.categoria):
                continue

            text = product.searchable_text
            product_tokens = set(text.split())
            overlap = len(query_tokens & product_tokens) / max(len(query_tokens), 1)
            phrase_score = SequenceMatcher(None, normalized_query, text).ratio()
            name_score = SequenceMatcher(
                None, normalized_query, normalize_text(product.nombre)
            ).ratio()
            exact_bonus = 0.25 if normalized_query in text else 0
            sku_bonus = 0.45 if normalized_query == normalize_text(product.sku) else 0

            score = min(
                1.0,
                0.45 * overlap
                + 0.20 * phrase_score
                + 0.35 * name_score
                + exact_bonus
                + sku_bonus,
            )
            if score >= self.min_score:
                results.append(ProductSearchResult(product=product, score=round(score, 4)))

        results.sort(key=lambda item: (-item.score, item.product.nombre))
        return results[: max(1, min(limit, 20))]
