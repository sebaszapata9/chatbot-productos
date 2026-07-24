from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(value.lower().strip().split())


class Product(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, frozen=True)

    sku: str = Field(min_length=1, max_length=100)
    nombre: str = Field(min_length=1, max_length=250)
    categoria: str = Field(min_length=1, max_length=150)
    descripcion: str = Field(min_length=1, max_length=2000)
    precio: Decimal = Field(ge=0)
    moneda: str = Field(default="PEN", min_length=3, max_length=3)
    stock: int = Field(ge=0)
    estado: str = Field(default="activo")
    marca: str | None = None
    variantes: tuple[str, ...] = ()
    palabras_clave: tuple[str, ...] = ()
    url_producto: str | None = None
    actualizado_en: str | None = None

    @field_validator("sku", "moneda", "estado", mode="before")
    @classmethod
    def normalize_codes(cls, value: Any) -> str:
        return str(value or "").strip().upper()

    @field_validator("precio", mode="before")
    @classmethod
    def parse_price(cls, value: Any) -> Decimal:
        if isinstance(value, str):
            value = value.strip().replace("S/", "").replace("$", "").replace(" ", "")
            if "," in value and "." not in value:
                value = value.replace(",", ".")
            elif "," in value and "." in value:
                value = value.replace(",", "")
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("precio debe ser numérico") from exc

    @field_validator("stock", mode="before")
    @classmethod
    def parse_stock(cls, value: Any) -> int:
        try:
            parsed = float(str(value).strip())
        except (TypeError, ValueError) as exc:
            raise ValueError("stock debe ser entero") from exc
        if not parsed.is_integer():
            raise ValueError("stock debe ser entero")
        return int(parsed)

    @field_validator("variantes", "palabras_clave", mode="before")
    @classmethod
    def parse_list(cls, value: Any) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        if isinstance(value, (list, tuple)):
            return tuple(str(item).strip() for item in value if str(item).strip())
        return tuple(item.strip() for item in str(value).split(",") if item.strip())

    @model_validator(mode="after")
    def validate_active_state(self) -> "Product":
        if self.estado not in {"ACTIVO", "INACTIVO"}:
            raise ValueError("estado debe ser activo o inactivo")
        return self

    @property
    def is_active(self) -> bool:
        return self.estado == "ACTIVO"

    @property
    def searchable_text(self) -> str:
        parts = [
            self.sku,
            self.nombre,
            self.categoria,
            self.descripcion,
            self.marca or "",
            *self.variantes,
            *self.palabras_clave,
        ]
        return normalize_text(" ".join(parts))


class ProductSearchResult(BaseModel):
    product: Product
    score: float = Field(ge=0, le=1)
