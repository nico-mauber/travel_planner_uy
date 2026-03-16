"""Servicio del agente LLM — wrapper sobre TripChatbot."""

from typing import Optional

LLM_AVAILABLE = False

try:
    from services.llm_chatbot import TripChatbot
    LLM_AVAILABLE = True
except Exception:
    pass


def process_message_llm(message: str, trip: Optional[dict] = None,
                         user_profile: Optional[dict] = None,
                         user_id: Optional[str] = None,
                         chat_id: Optional[str] = None) -> dict:
    """Procesa mensaje usando el LLM. Retorna {role, type, content}."""
    if not LLM_AVAILABLE:
        raise RuntimeError("LLM no disponible")

    chatbot = TripChatbot.get_instance()
    _chat_id = chat_id or (trip["id"] if trip else "__no_trip__")
    _user_id = user_id or "demo"

    return chatbot.chat(
        message=message,
        trip=trip,
        user_profile=user_profile,
        user_id=_user_id,
        chat_id=_chat_id,
    )
