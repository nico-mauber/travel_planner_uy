"""Servicio del agente — LLM (Gemini) + Booking.com. Sin fallback mock."""

import os
import uuid
import re
import logging
from typing import Optional

from config.settings import ItemType, ItemStatus
from services.trip_creation_flow import (
    detect_trip_creation_intent, detect_cancel_intent,
    extract_trip_data, get_missing_fields, build_prompt_for_missing,
    validate_dates, build_confirmation_data, new_draft,
)

logger = logging.getLogger(__name__)

# ─── Detectar si el LLM está disponible ───
_USE_LLM = bool(os.environ.get("GOOGLE_API_KEY"))

if _USE_LLM:
    try:
        from services.llm_agent_service import process_message_llm, LLM_AVAILABLE
        _USE_LLM = LLM_AVAILABLE
    except ImportError:
        _USE_LLM = False

# ─── Detectar si Booking.com está disponible ───
_USE_BOOKING = False
try:
    from services.booking_service import (
        is_booking_available, search_hotels_for_trip, format_hotels_as_cards,
    )
    _USE_BOOKING = is_booking_available()
except ImportError:
    pass

_HOTEL_KEYWORDS = [
    "hotel", "hoteles", "alojamiento", "hospedaje", "hostel",
    "donde dormir", "donde alojar", "donde quedar",
    "habitacion", "habitación", "reservar hotel",
    "booking", "alojarnos", "hospedarnos",
]


def is_llm_active() -> bool:
    """Retorna True si el LLM está activo."""
    return _USE_LLM


def is_booking_active() -> bool:
    """Retorna True si Booking.com está disponible."""
    return _USE_BOOKING


def _detect_hotel_intent(msg: str) -> bool:
    """Detecta si el mensaje tiene intencion de buscar hoteles."""
    return any(kw in msg for kw in _HOTEL_KEYWORDS)


def process_message(message: str, trip: Optional[dict] = None,
                    user_id: Optional[str] = None,
                    chat_id: Optional[str] = None,
                    trip_creation_draft: Optional[dict] = None) -> dict:
    """Procesa un mensaje del usuario via LLM y/o Booking.com.

    Retorna dict con:
      - role: "assistant"
      - type: "text" | "card" | "confirmation" | "hotel_results"
      - content: str (texto) o dict (datos de tarjeta/confirmación)
      - _trip_creation_draft: (opcional) estado parcial del flujo de creación
    """
    msg = message.lower().strip()

    # ─── Flujo multi-turn de creación de viaje ───
    result = _handle_trip_creation_flow(msg, message, trip, trip_creation_draft)
    if result is not None:
        return result

    # Agregar item — siempre confirmación
    if trip and any(w in msg for w in ["agregar", "añadir", "agrega", "añade"]):
        return _add_item_response(msg, trip)

    # Eliminar item — siempre confirmación
    if trip and any(w in msg for w in ["eliminar", "quitar", "elimina", "quita", "borrar"]):
        return _remove_item_response(msg, trip)

    # ─── Busqueda de hoteles via Booking.com ───
    if trip and _USE_BOOKING and _detect_hotel_intent(msg):
        try:
            hotels = search_hotels_for_trip(trip, limit=5)
            if hotels:
                cards = format_hotels_as_cards(hotels)
                # Obtener respuesta contextual del LLM si esta disponible
                llm_text = ""
                if _USE_LLM:
                    try:
                        import streamlit as st
                        user_profile = st.session_state.get("user_profile")
                        llm_resp = process_message_llm(
                            message, trip, user_profile,
                            user_id=user_id, chat_id=chat_id,
                        )
                        llm_text = llm_resp.get("content", "")
                    except Exception:
                        pass

                dest = trip.get("destination", "tu destino")
                return {
                    "role": "assistant",
                    "type": "hotel_results",
                    "content": {
                        "text": llm_text or (
                            f"Encontre estos hoteles en **{dest}** "
                            f"para tus fechas ({trip.get('start_date', '')} — "
                            f"{trip.get('end_date', '')}):"
                        ),
                        "hotels": cards,
                    },
                }
        except Exception as e:
            logger.warning("Error en busqueda Booking.com: %s", e)

    # ─── LLM (Gemini) ───
    if _USE_LLM:
        try:
            import streamlit as st
            user_profile = st.session_state.get("user_profile")
            return process_message_llm(
                message, trip, user_profile,
                user_id=user_id, chat_id=chat_id,
            )
        except Exception as e:
            logger.warning("Error en LLM: %s", e)
            return {
                "role": "assistant",
                "type": "text",
                "content": "Hubo un error al procesar tu mensaje. Por favor, intenta de nuevo.",
            }

    # ─── Sin LLM configurado ───
    return {
        "role": "assistant",
        "type": "text",
        "content": (
            "El asistente IA no esta disponible. "
            "Configura `GOOGLE_API_KEY` en el archivo `.env` para habilitar Gemini.\n\n"
            "Mientras tanto, puedes:\n"
            "- Crear viajes desde **Mis Viajes**\n"
            "- Gestionar tu itinerario desde las secciones de la barra lateral"
        ),
    }


def _handle_trip_creation_flow(
    msg: str, original_message: str,
    trip: Optional[dict], draft: Optional[dict],
) -> Optional[dict]:
    """Maneja el flujo multi-turn de creación de viaje.

    Retorna un dict de respuesta si el flujo aplica, o None si no.
    """
    # ─── Draft activo: el usuario está en medio del flujo ───
    if draft and draft.get("step") == "collecting":
        # Cancelación
        if detect_cancel_intent(msg):
            return {
                "role": "assistant",
                "type": "text",
                "content": "Entendido, cancelé la creación del viaje. ¿En qué más puedo ayudarte?",
                "_trip_creation_draft": None,
            }

        # Extraer datos del mensaje y combinar con draft
        updated = extract_trip_data(original_message, draft)
        updated["step"] = "collecting"

        missing = get_missing_fields(updated)

        if not missing:
            # Validar fechas
            valid, error = validate_dates(updated["start_date"], updated["end_date"])
            if not valid:
                # Limpiar fechas inválidas para que las pida de nuevo
                updated["start_date"] = None
                updated["end_date"] = None
                return {
                    "role": "assistant",
                    "type": "text",
                    "content": error,
                    "_trip_creation_draft": updated,
                }

            # Todo completo → confirmación
            updated["step"] = "ready"
            confirmation = build_confirmation_data(updated)
            confirmation["_trip_creation_draft"] = None
            return confirmation

        # Faltan datos → pedir lo que falta
        prompt = build_prompt_for_missing(updated, missing)
        return {
            "role": "assistant",
            "type": "text",
            "content": prompt,
            "_trip_creation_draft": updated,
        }

    # ─── Sin draft: detectar intención de crear viaje ───
    if trip is None and detect_trip_creation_intent(msg):
        draft = new_draft()
        updated = extract_trip_data(original_message, draft)
        updated["step"] = "collecting"

        missing = get_missing_fields(updated)

        if not missing:
            # Mensaje completo con todo → validar y confirmar directamente
            valid, error = validate_dates(updated["start_date"], updated["end_date"])
            if not valid:
                updated["start_date"] = None
                updated["end_date"] = None
                prompt = error + "\n\n" + build_prompt_for_missing(updated, get_missing_fields(updated))
                return {
                    "role": "assistant",
                    "type": "text",
                    "content": prompt,
                    "_trip_creation_draft": updated,
                }
            updated["step"] = "ready"
            confirmation = build_confirmation_data(updated)
            confirmation["_trip_creation_draft"] = None
            return confirmation

        # Faltan datos → iniciar flujo multi-turn
        prompt = build_prompt_for_missing(updated, missing)
        return {
            "role": "assistant",
            "type": "text",
            "content": prompt,
            "_trip_creation_draft": updated,
        }

    return None


def _add_item_response(msg: str, trip: dict) -> dict:
    return {
        "role": "assistant",
        "type": "confirmation",
        "content": {
            "action": "add_item",
            "summary": "Agregar actividad al itinerario",
            "details": {
                "name": "Nueva actividad",
                "item_type": ItemType.ACTIVITY.value,
                "day": 1,
                "start_time": "10:00",
                "end_time": "12:00",
                "cost_estimated": 25.0,
                "location": trip["destination"].split(",")[0],
            },
        },
    }


def _remove_item_response(msg: str, trip: dict) -> dict:
    items = trip.get("items", [])
    if items:
        last_item = items[-1]
        return {
            "role": "assistant",
            "type": "confirmation",
            "content": {
                "action": "remove_item",
                "summary": f"Eliminar '{last_item['name']}' del itinerario",
                "details": {
                    "item_id": last_item["id"],
                    "item_name": last_item["name"],
                },
            },
        }
    return {
        "role": "assistant",
        "type": "text",
        "content": "No hay items en el itinerario para eliminar.",
    }


def apply_confirmed_action(action: dict, trip: dict, trips: list) -> str:
    """Aplica una acción confirmada por el usuario. Retorna mensaje de resultado."""
    from services.trip_service import sync_trip_changes, create_trip

    action_type = action.get("action")
    details = action.get("details", {})

    if action_type == "add_item":
        new_item = {
            "id": f"item-{uuid.uuid4().hex[:8]}",
            "trip_id": trip["id"],
            "name": details.get("name", "Item sin nombre"),
            "item_type": details.get("item_type", ItemType.ACTIVITY.value),
            "day": details.get("day", 1),
            "start_time": details.get("start_time", "10:00"),
            "end_time": details.get("end_time", "12:00"),
            "status": ItemStatus.PENDING.value,
            "location": details.get("location", ""),
            "address": details.get("address", ""),
            "notes": details.get("notes", ""),
            "cost_estimated": details.get("cost_estimated", 0.0),
            "cost_real": 0.0,
            "booking_url": "",
            "provider": details.get("provider", ""),
        }
        trip["items"].append(new_item)
        sync_trip_changes(trips, trip)
        return f"✅ Se agregó '{new_item['name']}' al Día {new_item['day']} del itinerario."

    elif action_type == "remove_item":
        item_id = details.get("item_id")
        item_name = details.get("item_name", "item")
        for i, item in enumerate(trip["items"]):
            if item["id"] == item_id:
                trip["items"].pop(i)
                sync_trip_changes(trips, trip)
                return f"✅ Se eliminó '{item_name}' del itinerario."
        return "❌ No se encontró el item a eliminar."

    elif action_type == "create_trip":
        # Esto se maneja de forma especial en el chat
        return "✅ Viaje creado exitosamente."

    return "❌ Acción no reconocida."
