import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_catalog_service
from app.main import app
from app.services.catalog import CatalogService


class FakeCatalogSource:
    def __init__(self, rows):
        self.rows = rows
        self.calls = 0

    def fetch_rows(self):
        self.calls += 1
        return self.rows


@pytest.fixture
def rows():
    return [
        {
            "sku": "CAM-001",
            "nombre": "Camisa Oxford Azul",
            "categoria": "Camisas",
            "descripcion": "Camisa de algodón de manga larga",
            "precio": "89.90",
            "moneda": "PEN",
            "stock": "12",
            "estado": "activo",
            "marca": "Kuma",
            "variantes": "S, M, L, XL",
            "palabras_clave": "camisa azul, oficina",
            "url_producto": "",
            "actualizado_en": "2026-07-22 10:30",
        },
        {
            "sku": "POL-001",
            "nombre": "Polo básico negro",
            "categoria": "Polos",
            "descripcion": "Polo negro de algodón",
            "precio": "39,90",
            "moneda": "PEN",
            "stock": "0",
            "estado": "activo",
            "marca": "Kuma",
            "variantes": "M, L",
            "palabras_clave": "polo negro",
            "url_producto": "",
            "actualizado_en": "",
        },
        {
            "sku": "OLD-001",
            "nombre": "Producto retirado",
            "categoria": "Otros",
            "descripcion": "No debe mostrarse",
            "precio": "10",
            "moneda": "PEN",
            "stock": "1",
            "estado": "inactivo",
        },
    ]


@pytest.fixture
def source(rows):
    return FakeCatalogSource(rows)


@pytest.fixture
def service(source):
    return CatalogService(source, cache_ttl_seconds=3600, min_score=0.25)


@pytest.fixture
def client(service):
    app.dependency_overrides[get_catalog_service] = lambda: service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
