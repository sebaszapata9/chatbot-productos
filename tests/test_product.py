from decimal import Decimal
import pytest
from pydantic import ValidationError

from app.models.product import Product


BASE = {
    "sku": "abc-1",
    "nombre": "Producto",
    "categoria": "Categoría",
    "descripcion": "Descripción",
    "precio": "S/ 1,250.50",
    "moneda": "pen",
    "stock": "3",
    "estado": "activo",
}


def test_normalizes_product():
    product = Product.model_validate(BASE)
    assert product.sku == "ABC-1"
    assert product.moneda == "PEN"
    assert product.precio == Decimal("1250.50")
    assert product.stock == 3
    assert product.is_active


def test_rejects_negative_stock():
    with pytest.raises(ValidationError):
        Product.model_validate({**BASE, "stock": "-1"})


def test_rejects_fractional_stock():
    with pytest.raises(ValidationError):
        Product.model_validate({**BASE, "stock": "1.5"})


def test_parses_comma_separated_fields():
    product = Product.model_validate(
        {**BASE, "variantes": "S, M, L", "palabras_clave": "uno, dos"}
    )
    assert product.variantes == ("S", "M", "L")
    assert product.palabras_clave == ("uno", "dos")
