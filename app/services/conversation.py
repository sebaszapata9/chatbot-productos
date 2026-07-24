from __future__ import annotations
import re
from decimal import Decimal
from app.models.conversation import ConversationAction, ConversationResponse
from app.models.product import Product, normalize_text
from app.services.catalog import CatalogService

class ConversationService:
    EXIT_WORDS = {"salir", "exit", "quit", "cerrar", "terminar"}
    GREETINGS = {"hola", "buenas", "buenos dias", "buenas tardes", "buenas noches"}
    OUT_OF_SCOPE_PATTERNS = (
        r"\bcotiza(?:cion|r)?\b", r"\bdescuento(?:s)?\b", r"\bpor mayor\b",
        r"\breserv(?:a|ar|ame)\b", r"\bcomprar\b", r"\bpedido\b",
        r"\bpagar\b", r"\bdevolucion(?:es)?\b", r"\breclamo(?:s)?\b",
        r"\bgarantia(?:s)?\b", r"\bhablar con (?:un |una )?(?:asesor|persona|humano)\b",
        r"\basesor\b",
    )
    PRICE_WORDS = {"precio", "cuesta", "costar", "valor", "cuanto"}
    STOCK_WORDS = {"stock", "disponible", "disponibilidad", "quedan", "hay", "unidades", "existencias"}
    DESCRIPTION_PHRASES = {"descripcion", "caracteristicas", "detalle", "detalles", "informacion", "material", "como es"}

    def __init__(self, catalog: CatalogService) -> None:
        self.catalog = catalog

    def respond(self, raw_message: str) -> ConversationResponse:
        normalized = normalize_text((raw_message or "").strip())
        if not normalized:
            return ConversationResponse(action=ConversationAction.CLARIFY, message="Escribe el nombre, código o tipo de producto que deseas consultar.")
        if normalized in self.EXIT_WORDS:
            return ConversationResponse(action=ConversationAction.EXIT, message="Conversación finalizada.")
        if normalized in self.GREETINGS:
            return ConversationResponse(action=ConversationAction.CLARIFY, message="¡Hola! Puedo consultar productos, precios, descripciones y stock. ¿Qué producto buscas?")
        if any(re.search(pattern, normalized) for pattern in self.OUT_OF_SCOPE_PATTERNS):
            return ConversationResponse(action=ConversationAction.HANDOFF, message="Esta consulta necesita la atención de un asesor. La dejaré registrada para seguimiento.", handoff_reason="consulta_fuera_de_alcance")

        results = self.catalog.search(query=self._extract_product_query(normalized), limit=5)
        if not results:
            return ConversationResponse(action=ConversationAction.HANDOFF, message="No encontré un producto que coincida con tu consulta. Un asesor puede ayudarte a revisarlo.", handoff_reason="producto_no_encontrado")

        top = results[0]
        close = [item for item in results if top.score - item.score <= 0.08]
        if len(close) > 1:
            options = "\n".join(f"{i}. {item.product.nombre} ({item.product.sku})" for i, item in enumerate(close[:5], 1))
            return ConversationResponse(action=ConversationAction.CLARIFY, message="Encontré varias opciones. Indica el nombre o SKU exacto:\n" + options, matched_skus=[item.product.sku for item in close[:5]])

        product = top.product
        return ConversationResponse(action=ConversationAction.ANSWERED, message=self._format_product_answer(product, normalized), matched_skus=[product.sku])

    def _extract_product_query(self, normalized: str) -> str:
        removable = {"precio","cuesta","costar","cuanto","stock","disponible","disponibilidad","quedan","hay","unidades","descripcion","caracteristicas","detalle","detalles","informacion","producto","productos","tienen","tienes","del","de","el","la","los","las","un","una","por","favor","quisiera","quiero","saber"}
        query = " ".join(token for token in normalized.split() if token not in removable).strip()
        return query or normalized

    def _format_product_answer(self, product: Product, normalized: str) -> str:
        tokens = set(normalized.split())
        wants_price = bool(tokens & self.PRICE_WORDS)
        wants_stock = bool(tokens & self.STOCK_WORDS)
        wants_description = any(p in normalized for p in self.DESCRIPTION_PHRASES)
        if not any((wants_price, wants_stock, wants_description)):
            wants_price = wants_stock = wants_description = True

        parts = [f"{product.nombre} ({product.sku})."]
        if wants_description:
            parts.append(product.descripcion.rstrip(".") + ".")
        if wants_price:
            symbol = {"PEN": "S/", "USD": "US$", "EUR": "€"}.get(product.moneda.upper(), product.moneda.upper())
            parts.append(f"Precio registrado: {symbol} {product.precio:.2f}.")
        if wants_stock:
            parts.append("Actualmente figura sin stock." if product.stock == 0 else f"Actualmente figuran {product.stock} unidades disponibles.")
        if product.variantes:
            parts.append("Variantes registradas: " + ", ".join(product.variantes) + ".")
        parts.append("La disponibilidad corresponde al último registro del catálogo.")
        return " ".join(parts)
