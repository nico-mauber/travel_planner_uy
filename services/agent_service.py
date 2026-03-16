"""Servicio del agente — LLM (OpenAI gpt-4.1-nano) + Booking.com. Sin fallback mock."""

import os
import re
import uuid
import logging
from typing import Optional

from config.settings import ItemType, ItemStatus
from services.trip_creation_flow import (
    detect_trip_creation_intent, detect_cancel_intent,
    extract_trip_data, get_missing_fields, build_prompt_for_missing,
    validate_dates, build_confirmation_data, new_draft,
)
from services.item_extraction import (
    detect_add_item_intent, extract_item_data, get_missing_item_fields,
    build_item_prompt_for_missing, validate_item_day_range,
    detect_time_conflict, build_item_confirmation_data,
    new_item_draft, calculate_end_time,
    detect_cancel_intent as detect_item_cancel_intent,
    detect_calendar_intent, detect_hotel_intent, detect_remove_item_intent,
    _ORDINAL_NAMES,
)

logger = logging.getLogger(__name__)

# ─── Detectar si el LLM está disponible (lazy init) ───
# Nota: la detección se hace lazy porque el hot-reload de Streamlit puede
# re-importar este módulo ANTES de que load_dotenv() haya corrido en app.py,
# lo que dejaría _USE_LLM = False permanentemente.
_USE_LLM = None  # None = no inicializado aún
_llm_process_fn = None  # referencia cacheada a process_message_llm
_llm_extract_fn = None  # referencia cacheada a extract_item_with_llm


def _check_llm():
    """Inicializa la detección de LLM de forma lazy. Solo corre una vez."""
    global _USE_LLM, _llm_process_fn, _llm_extract_fn
    if _USE_LLM is not None:
        return
    _USE_LLM = bool(os.environ.get("OPENAI_API_KEY"))
    if _USE_LLM:
        try:
            from services.llm_agent_service import process_message_llm, LLM_AVAILABLE
            _USE_LLM = LLM_AVAILABLE
            if LLM_AVAILABLE:
                _llm_process_fn = process_message_llm
        except ImportError:
            _USE_LLM = False
        # Cargar extractor LLM de items (independiente del chatbot)
        if _USE_LLM:
            try:
                from services.llm_item_extraction import extract_item_with_llm
                _llm_extract_fn = extract_item_with_llm
            except ImportError:
                logger.warning("No se pudo importar llm_item_extraction")
    logger.info("LLM disponible: %s, Extractor LLM: %s",
                _USE_LLM, _llm_extract_fn is not None)

# ─── Detectar si Booking.com está disponible ───
_USE_BOOKING = False
try:
    from services.booking_service import (
        is_booking_available, search_hotels_for_trip, format_hotels_as_cards,
    )
    _USE_BOOKING = is_booking_available()
except ImportError:
    pass



# ─── Patrones de prompt injection a sanitizar ───
_INJECTION_PATTERNS = [
    re.compile(r'ignora\s+(todas?\s+)?(las?\s+)?instrucciones?\s+(anteriores?|previas?|del?\s+sistema)', re.IGNORECASE),
    re.compile(r'olvida\s+(todas?\s+)?(las?\s+)?instrucciones?\s+(anteriores?|previas?|del?\s+sistema)', re.IGNORECASE),
    re.compile(r'ignore\s+(all\s+)?(previous|prior|above|system)\s+instructions?', re.IGNORECASE),
    re.compile(r'forget\s+(all\s+)?(previous|prior|above|system)\s+instructions?', re.IGNORECASE),
    re.compile(r'(eres|ahora\s+eres|act[uú]a\s+como|you\s+are\s+now|act\s+as)\s+(un|una|a|an)\s+', re.IGNORECASE),
    re.compile(r'(nuevo|new)\s+(rol|role|modo|mode|persona)', re.IGNORECASE),
    re.compile(r'(system|sistema)\s*:\s*', re.IGNORECASE),
    re.compile(r'(mu[eé]strame|rev[eé]lame|dime|show\s+me|reveal)\s+(tu|el|the|your)\s+(system\s+)?prompt', re.IGNORECASE),
    re.compile(r'(repite|repeat|print)\s+(tu|el|the|your)\s+(system\s+)?prompt', re.IGNORECASE),
    re.compile(r'\[INST\]', re.IGNORECASE),
    re.compile(r'<\|im_start\|>', re.IGNORECASE),
    re.compile(r'###\s*(system|instruction|human|assistant)', re.IGNORECASE),
]


def _sanitize_user_input(msg: str) -> str:
    """Sanitiza el mensaje del usuario eliminando patrones de prompt injection.

    No bloquea el mensaje, solo limpia secuencias peligrosas.
    """
    sanitized = msg
    for pattern in _INJECTION_PATTERNS:
        sanitized = pattern.sub('', sanitized)
    # Limpiar espacios múltiples resultantes
    sanitized = re.sub(r' {2,}', ' ', sanitized).strip()
    return sanitized or msg  # Si queda vacío, devolver original para no bloquear


def is_llm_active() -> bool:
    """Retorna True si el LLM está activo."""
    _check_llm()
    return _USE_LLM


def is_booking_active() -> bool:
    """Retorna True si Booking.com está disponible."""
    return _USE_BOOKING


# ─── Constantes compiladas para deteccion de preguntas informativas ───
_DATA_INDICATORS = [
    re.compile(r"\bdia\s+\d+"),
    re.compile(r"\d{1,2}[:.]\d{2}"),
    re.compile(r"\bmanana\b"),
    re.compile(r"\btarde\b"),
    re.compile(r"\bnoche\b"),
    re.compile(rf"\b(?:{_ORDINAL_NAMES})\s+dia"),
    re.compile(rf"\bdia\s+(?:{_ORDINAL_NAMES})\b"),
    re.compile(r"\b(?:ultimo|último|penultimo|penúltimo)\s+dia"),
]

_QUESTION_STARTERS = [
    "que ", "cual ", "cuando ", "donde ", "cuanto ", "como ",
    "por que ", "cuales ", "cuantos ",
]


def _is_informative_question(msg: str) -> bool:
    """Detecta si el mensaje es una pregunta informativa (no datos para un draft).

    Permite que preguntas como "que dias son mi viaje?" escapen del flujo
    multi-turn de item creation y lleguen al LLM/fallback.
    """
    lower = msg.lower().strip()
    if "?" not in lower and "\u00bf" not in lower:
        return False
    # Si contiene datos validos para el draft, NO es pregunta informativa
    for pattern in _DATA_INDICATORS:
        if pattern.search(lower):
            return False
    return any(lower.startswith(qs) or f" {qs}" in lower for qs in _QUESTION_STARTERS)


def process_message(message: str, trip: Optional[dict] = None,
                    user_id: Optional[str] = None,
                    chat_id: Optional[str] = None,
                    trip_creation_draft: Optional[dict] = None,
                    item_creation_draft: Optional[dict] = None) -> dict:
    """Procesa un mensaje del usuario via LLM y/o Booking.com.

    Retorna dict con:
      - role: "assistant"
      - type: "text" | "card" | "confirmation" | "hotel_results"
      - content: str (texto) o dict (datos de tarjeta/confirmación)
      - _trip_creation_draft: (opcional) estado parcial del flujo de creación
    """
    # Inicializar detección de LLM (lazy, solo la primera vez)
    _check_llm()

    # Sanitizar input contra prompt injection antes de procesarlo
    message = _sanitize_user_input(message)
    msg = message.lower().strip()

    # ─── Flujo multi-turn de creación de viaje ───
    result = _handle_trip_creation_flow(msg, message, trip, trip_creation_draft)
    if result is not None:
        return result

    # ─── Flujo multi-turn de creacion de item (REQ-CF-003) ───
    result = _handle_item_creation_flow(msg, message, trip, item_creation_draft)
    if result is not None:
        return result

    # ─── PATH CON LLM: una sola llamada detecta ALL intents sin keywords ───
    if trip and _llm_extract_fn:
        result = _handle_llm_extraction(message, trip, user_id, chat_id)
        if result is not None:
            return result
        # Fall-through: LLM chat para informative/unknown
        if _USE_LLM and _llm_process_fn:
            return _llm_chat_response(message, trip, user_id, chat_id)

    # ─── PATH SIN LLM: deteccion por keywords ───
    if trip and not _llm_extract_fn:
        # Evento de cronograma (REQ-CF-002) — evaluar ANTES de add_item
        if detect_calendar_intent(msg):
            return _calendar_event_response(trip)
        # Agregar item — extraccion basica
        if detect_add_item_intent(msg):
            return _add_item_response(msg, trip)
        # Eliminar item
        if detect_remove_item_intent(msg):
            return _remove_item_response(msg, trip)
        # Busqueda de hoteles via Booking.com
        if _USE_BOOKING and detect_hotel_intent(msg):
            result = _hotel_search_response(message, trip, user_id, chat_id)
            if result is not None:
                return result

    # ─── Sin LLM configurado ───
    return {
        "role": "assistant",
        "type": "text",
        "content": (
            "El asistente IA no esta disponible. "
            "Configura `OPENAI_API_KEY` en el archivo `.env` para habilitar gpt-4.1-nano.\n\n"
            "Mientras tanto, puedes:\n"
            "- Crear viajes desde **Mis Viajes**\n"
            "- Gestionar tu itinerario desde las secciones de la barra lateral"
        ),
    }


def _is_same_destination(new_dest: str, current_dest: str) -> bool:
    """Compara destinos para evitar duplicados (substring match)."""
    if not new_dest or not current_dest:
        return False
    return new_dest == current_dest or new_dest in current_dest or current_dest in new_dest


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
    if detect_trip_creation_intent(msg):
        # Protección contra falsos positivos cuando hay viaje activo
        if trip is not None:
            tentative = extract_trip_data(original_message, new_draft())
            new_dest = tentative.get("destination")
            if not new_dest:
                # No se detectó destino nuevo → no iniciar creación
                return None
            current_dest = (trip.get("destination") or "").lower().strip()
            if _is_same_destination(new_dest.lower().strip(), current_dest):
                # Mismo destino → no crear duplicado
                return None

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


def _handle_item_creation_flow(
    msg: str, original_message: str,
    trip: Optional[dict], draft: Optional[dict],
) -> Optional[dict]:
    """Maneja el flujo multi-turn de creacion de item (REQ-CF-003).

    Retorna dict de respuesta si el flujo aplica, o None si no.
    """
    if not draft or draft.get("step") != "collecting":
        return None
    if not trip:
        return None

    # Cancelacion
    if detect_item_cancel_intent(msg):
        return {
            "role": "assistant",
            "type": "text",
            "content": "Entendido, cancele la creacion del item.",
            "_item_creation_draft": None,
        }

    # Pregunta informativa: dejar pasar al LLM sin consumir turno
    if _is_informative_question(msg):
        return None

    # Incrementar turnos
    draft = dict(draft)
    draft["turns"] = draft.get("turns", 0) + 1

    # Max 3 turnos (RN-009)
    if draft["turns"] > 3:
        return {
            "role": "assistant",
            "type": "text",
            "content": (
                "No pude obtener los datos suficientes para crear el item. "
                "Puedes intentarlo nuevamente indicando al menos el nombre "
                "de la actividad y el dia."
            ),
            "_item_creation_draft": None,
        }

    # Guardar horario previo para detectar cambios
    old_start = draft.get("start_time")
    old_end = draft.get("end_time")

    # Extraer datos del mensaje (LLM o regex fallback)
    if _llm_extract_fn:
        llm_result = _llm_extract_fn(original_message, trip, draft)
        if llm_result:
            updated = _merge_extraction_to_draft(llm_result, draft)
        else:
            # Error en LLM → fallback a regex
            updated = extract_item_data(original_message, trip, draft)
    else:
        updated = extract_item_data(original_message, trip, draft)
    updated["step"] = "collecting"

    # Si el horario cambio, resetear _conflict_warned para re-evaluar conflictos
    if updated.get("_conflict_warned") and (
        updated.get("start_time") != old_start or updated.get("end_time") != old_end
    ):
        updated.pop("_conflict_warned", None)

    missing = get_missing_item_fields(updated)

    if not missing:
        return _finalize_item_draft(updated, trip)

    # Faltan datos → pedir lo que falta
    prompt = build_item_prompt_for_missing(updated, missing)
    return {
        "role": "assistant",
        "type": "text",
        "content": prompt,
        "_item_creation_draft": updated,
    }


def _finalize_item_draft(draft: dict, trip: dict) -> dict:
    """Valida y genera confirmacion para un draft de item completo."""
    # Validar rango de fechas
    valid, error = validate_item_day_range(draft["day"], trip)
    if not valid:
        draft["day"] = None
        return {
            "role": "assistant",
            "type": "text",
            "content": error,
            "_item_creation_draft": draft,
        }

    # Calcular end_time si no existe
    item_type = draft.get("item_type", "actividad")
    start_time = draft.get("start_time")
    if not start_time:
        from services.item_extraction import _DEFAULT_TIMES
        start_time = _DEFAULT_TIMES.get(item_type, "10:00")
        draft["start_time"] = start_time
    if not draft.get("end_time"):
        draft["end_time"] = calculate_end_time(start_time, item_type)

    # Detectar conflictos horarios
    conflict = detect_time_conflict(
        draft["day"], draft["start_time"], draft["end_time"],
        trip.get("items", []),
    )
    if conflict:
        # Informar pero permitir continuar — el draft queda con _conflict_warned
        if not draft.get("_conflict_warned"):
            draft["_conflict_warned"] = True
            return {
                "role": "assistant",
                "type": "text",
                "content": (
                    f"{conflict}\n\n"
                    "Deseas agregarlo de todas formas o prefieres cambiar el horario?"
                ),
                "_item_creation_draft": draft,
            }
        # Ya se advirtio — el usuario dijo "si" implicitamente al seguir

    # Todo listo — confirmacion
    confirmation = build_item_confirmation_data(draft, trip)
    confirmation["_item_creation_draft"] = None
    return confirmation


def _handle_llm_extraction(
    message: str, trip: dict,
    user_id: Optional[str] = None, chat_id: Optional[str] = None,
) -> Optional[dict]:
    """Deteccion de intent y extraccion unificada via LLM structured output.

    Reemplaza la cadena de if (calendar → add_item → remove_item → hotel) cuando
    el LLM esta disponible. Una sola llamada detecta intent y extrae datos.

    Retorna dict de respuesta si el LLM maneja el intent, o None para fall-through.
    """
    result = _llm_extract_fn(message, trip)
    if result is None:
        return None  # Error en LLM, fall through

    if result.intent == "add_item":
        return _handle_extraction_result(result, trip)

    if result.intent == "calendar_event":
        return _calendar_event_response(trip)

    if result.intent == "remove_item":
        return _remove_item_response(message.lower(), trip)

    if result.intent == "hotel_search":
        if _USE_BOOKING:
            return _hotel_search_response(message, trip, user_id, chat_id)
        # Sin Booking → fall through al LLM chat para respuesta informativa
        return None

    # informative, unknown → fall through al LLM chat
    return None


def _handle_extraction_result(result, trip: dict) -> dict:
    """Convierte ItemExtractionResult del LLM en respuesta de chat.

    Si los datos estan completos, genera confirmacion.
    Si faltan datos, inicia flujo multi-turn.
    """
    draft = new_item_draft()
    draft["name"] = result.name
    draft["day"] = result.day
    draft["start_time"] = result.start_time
    draft["end_time"] = result.end_time
    draft["item_type"] = result.item_type or "actividad"
    draft["location"] = result.location or ""
    draft["cost_estimated"] = result.cost or 0.0
    draft["step"] = "collecting"

    if result.is_complete:
        return _finalize_item_draft(draft, trip)

    # Incompleto → iniciar multi-turn con pregunta del LLM o fallback
    prompt = result.follow_up_question or build_item_prompt_for_missing(
        draft, result.missing_fields,
    )
    return {
        "role": "assistant",
        "type": "text",
        "content": prompt,
        "_item_creation_draft": draft,
    }


def _merge_extraction_to_draft(result, draft: dict) -> dict:
    """Merge ItemExtractionResult del LLM con draft existente (multi-turn).

    Solo sobreescribe campos que el LLM extrajo del mensaje actual.
    """
    updated = dict(draft)
    if result.name:
        updated["name"] = result.name
    if result.day:
        updated["day"] = result.day
    if result.start_time:
        updated["start_time"] = result.start_time
    if result.end_time:
        updated["end_time"] = result.end_time
    if result.item_type and result.item_type != "actividad":
        updated["item_type"] = result.item_type
    elif not updated.get("item_type"):
        updated["item_type"] = result.item_type or "actividad"
    if result.location:
        updated["location"] = result.location
    if result.cost is not None and result.cost > 0:
        updated["cost_estimated"] = result.cost
    return updated


def _hotel_search_response(
    message: str, trip: dict,
    user_id: Optional[str] = None, chat_id: Optional[str] = None,
) -> Optional[dict]:
    """Busca hoteles via Booking.com y retorna resultados formateados.

    Retorna dict de respuesta con hotel_results, o None si no hay resultados.
    """
    try:
        hotels = search_hotels_for_trip(trip, limit=5)
        if not hotels:
            return None

        cards = format_hotels_as_cards(hotels)
        # Obtener respuesta contextual del LLM si esta disponible
        llm_text = ""
        if _USE_LLM and _llm_process_fn:
            try:
                import streamlit as st
                user_profile = st.session_state.get("user_profile")
                llm_resp = _llm_process_fn(
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
        return None


def _llm_chat_response(
    message: str, trip: Optional[dict],
    user_id: Optional[str] = None, chat_id: Optional[str] = None,
) -> dict:
    """Envia mensaje al LLM chat (OpenAI gpt-4.1-nano) para respuesta conversacional."""
    try:
        import streamlit as st
        user_profile = st.session_state.get("user_profile")
        return _llm_process_fn(
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


def _add_item_response(msg: str, trip: dict) -> dict:
    """Extrae datos del mensaje y genera confirmacion o inicia flujo multi-turn.

    Solo se usa como fallback cuando no hay LLM disponible."""
    draft = new_item_draft()
    draft = extract_item_data(msg, trip, draft)
    draft["step"] = "collecting"

    missing = get_missing_item_fields(draft)

    if not missing:
        return _finalize_item_draft(draft, trip)

    # Faltan datos — multi-turn
    prompt = build_item_prompt_for_missing(draft, missing)
    return {
        "role": "assistant",
        "type": "text",
        "content": prompt,
        "_item_creation_draft": draft,
    }


def _calendar_event_response(trip: dict) -> dict:
    """Genera respuesta de confirmacion para crear evento multi-dia en cronograma (REQ-CF-002)."""
    start = trip.get("start_date", "")
    end = trip.get("end_date", "")
    if not start or not end:
        return {
            "role": "assistant",
            "type": "text",
            "content": (
                "No puedo crear el evento porque el viaje no tiene fechas definidas. "
                "Define las fechas del viaje primero."
            ),
        }

    from datetime import date as _date
    try:
        total_days = (_date.fromisoformat(end) - _date.fromisoformat(start)).days + 1
    except ValueError:
        return {
            "role": "assistant",
            "type": "text",
            "content": "Las fechas del viaje no son validas.",
        }

    dest = trip.get("destination", "Sin destino")
    return {
        "role": "assistant",
        "type": "confirmation",
        "content": {
            "action": "add_item",
            "summary": f"Crear evento de cronograma: Viaje a {dest}",
            "details": {
                "name": f"Viaje a {dest}",
                "item_type": "extra",
                "day": f"Dia 1 ({start})",
                "end_day": f"Dia {total_days} ({end})",
                "start_time": "00:00",
                "end_time": "23:59",
                "cost_estimated": 0.0,
                "location": dest,
                "_day_int": 1,
                "_end_day_int": total_days,
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
        # _day_int tiene el dia como entero (el campo "day" puede ser string con fecha)
        day_val = details.get("_day_int") or details.get("day", 1)
        if isinstance(day_val, str):
            # Extraer numero del string "Dia 3 (2026-04-12)"
            import re as _re
            m = _re.search(r"\d+", day_val)
            day_val = int(m.group()) if m else 1
        new_item = {
            "id": f"item-{uuid.uuid4().hex[:8]}",
            "trip_id": trip["id"],
            "name": details.get("name", "Item sin nombre"),
            "item_type": details.get("item_type", ItemType.ACTIVITY.value),
            "day": int(day_val),
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
        # Soporte para end_day (REQ-CF-002)
        end_day_val = details.get("_end_day_int") or details.get("end_day")
        if end_day_val:
            if isinstance(end_day_val, str):
                import re as _re2
                m2 = _re2.search(r"\d+", end_day_val)
                end_day_val = int(m2.group()) if m2 else None
            if end_day_val and int(end_day_val) > new_item["day"]:
                new_item["end_day"] = int(end_day_val)
        trip["items"].append(new_item)
        sync_trip_changes(trips, trip)
        if new_item.get("end_day"):
            return f"Se agrego '{new_item['name']}' (Dias {new_item['day']}-{new_item['end_day']}) al itinerario."
        return f"Se agrego '{new_item['name']}' al Dia {new_item['day']} del itinerario."

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
