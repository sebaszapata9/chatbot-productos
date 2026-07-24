from app.models.conversation import ConversationAction
from app.services.conversation import ConversationService

def test_greeting_asks_for_product(service):
    assert ConversationService(service).respond("Hola").action == ConversationAction.CLARIFY

def test_answers_price_question(service):
    response = ConversationService(service).respond("¿Cuánto cuesta la camisa azul?")
    assert response.action == ConversationAction.ANSWERED
    assert "S/ 89.90" in response.message

def test_answers_zero_stock_question(service):
    response = ConversationService(service).respond("¿Hay stock del polo negro?")
    assert response.action == ConversationAction.ANSWERED
    assert "sin stock" in response.message.lower()

def test_unknown_product_is_handed_off(service):
    response = ConversationService(service).respond("¿Tienen escritorio gamer?")
    assert response.action == ConversationAction.HANDOFF
    assert response.handoff_reason == "producto_no_encontrado"

def test_quote_request_is_handed_off(service):
    response = ConversationService(service).respond("Necesito una cotización por 80 camisas")
    assert response.action == ConversationAction.HANDOFF

def test_human_request_is_handed_off(service):
    assert ConversationService(service).respond("Quiero hablar con un asesor").action == ConversationAction.HANDOFF

def test_exit_command(service):
    assert ConversationService(service).respond("salir").action == ConversationAction.EXIT
