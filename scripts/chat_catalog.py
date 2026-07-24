from app.dependencies import get_catalog_service
from app.models.conversation import ConversationAction
from app.services.conversation import ConversationService

def main() -> None:
    catalog = get_catalog_service()
    try:
        report = catalog.refresh(force=True)
    except Exception as exc:
        print(f"\nNo se pudo cargar el catálogo: {exc}")
        print("Revisa .env, las credenciales y el acceso al Google Sheet.")
        raise SystemExit(1) from exc

    print("\nKumaBot Catálogo — simulador local")
    print("Consulta precio, stock o descripción. Escribe 'salir' para terminar.")
    print(f"Catálogo cargado: {report.valid_products} válidos, {report.invalid_rows} inválidos, {report.ignored_inactive} inactivos ignorados.\n")
    bot = ConversationService(catalog)

    while True:
        try:
            user_message = input("Cliente > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBot > Conversación finalizada.")
            break

        response = bot.respond(user_message)
        print(f"Bot > {response.message}\n")
        if response.action == ConversationAction.HANDOFF:
            print(f"[DERIVACIÓN] motivo={response.handoff_reason} mensaje={user_message!r}\n")
        if response.action == ConversationAction.EXIT:
            break

if __name__ == "__main__":
    main()
