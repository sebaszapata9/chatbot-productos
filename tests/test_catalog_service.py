def test_refresh_loads_only_active_products(service, source):
    report = service.refresh(force=True)
    assert report.total_rows == 3
    assert report.valid_products == 2
    assert report.ignored_inactive == 1
    assert source.calls == 1


def test_cache_avoids_repeated_sheet_reads(service, source):
    service.list_products()
    service.list_products()
    assert source.calls == 1


def test_get_by_sku_is_case_insensitive(service):
    product = service.get_by_sku("cam-001")
    assert product is not None
    assert product.nombre == "Camisa Oxford Azul"


def test_search_by_natural_words(service):
    results = service.search("camisa azul")
    assert results
    assert results[0].product.sku == "CAM-001"


def test_search_by_exact_sku(service):
    results = service.search("POL-001")
    assert results[0].product.sku == "POL-001"


def test_search_filters_category(service):
    assert service.search("negro", category="Camisas") == []


def test_out_of_catalog_returns_empty(service):
    assert service.search("escritorio gamer") == []


def test_zero_stock_product_remains_queryable(service):
    product = service.get_by_sku("POL-001")
    assert product is not None
    assert product.stock == 0


def test_duplicate_sku_is_reported(rows):
    from app.services.catalog import CatalogService
    from tests.conftest import FakeCatalogSource

    duplicate = dict(rows[0])
    duplicate["nombre"] = "Duplicado"
    service = CatalogService(FakeCatalogSource(rows + [duplicate]))
    report = service.refresh(force=True)
    assert report.duplicate_skus == 1
    assert report.valid_products == 2


def test_invalid_row_is_ignored(rows):
    from app.services.catalog import CatalogService
    from tests.conftest import FakeCatalogSource

    invalid = dict(rows[0])
    invalid["sku"] = "BAD-1"
    invalid["precio"] = "gratis"
    service = CatalogService(FakeCatalogSource(rows + [invalid]))
    report = service.refresh(force=True)
    assert report.invalid_rows == 1
    assert report.valid_products == 2
