"""Servicio del agente — LLM (OpenAI) + Booking.com. Sin fallback mock."""

import os
import re
import uuid
import logging
from typing import Optional

from config.settings import ItemType, ItemStatus
from services.trip_creation_flow import (
    detect_cancel_intent,
    extract_trip_data, get_missing_fields, build_prompt_for_missing,
    validate_dates, build_confirmation_data, new_draft,
)
from services.item_utils import (
    get_missing_item_fields,
    build_item_prompt_for_missing, validate_item_day_range,
    detect_time_conflict, build_item_confirmation_data,
    new_item_draft, calculate_end_time,
    _DEFAULT_TIMES,
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
        _filter_hotels,
    )
    _USE_BOOKING = is_booking_available()
except ImportError:
    pass

# ─── Detectar si búsqueda de vuelos está disponible ───
_USE_FLIGHTS = False
try:
    from services.flight_service import (
        is_flights_available, search_flights_for_trip, format_flights_as_cards,
    )
    _USE_FLIGHTS = is_flights_available()
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


def is_flights_active() -> bool:
    """Retorna True si la búsqueda de vuelos está disponible."""
    return _USE_FLIGHTS




def process_message(message: str, trip: Optional[dict] = None,
                    user_id: Optional[str] = None,
                    chat_id: Optional[str] = None,
                    trip_creation_draft: Optional[dict] = None,
                    item_creation_draft: Optional[dict] = None,
                    chat_history: Optional[list] = None) -> dict:
    """Procesa un mensaje del usuario via LLM.

    Retorna dict con:
      - role: "assistant"
      - type: "text" | "card" | "confirmation" | "hotel_results" | "flight_results"
      - content: str (texto) o dict (datos de tarjeta/confirmación)
      - _trip_creation_draft: (opcional) estado parcial del flujo de creación
    """
    _check_llm()

    # Paso 0: Sanitizar input contra prompt injection
    message = _sanitize_user_input(message)
    msg = message.lower().strip()
    logger.info("━━━ PROCESS_MESSAGE ━━━")
    logger.info("  mensaje: %s", message[:120])
    logger.info("  trip: %s", trip.get("destination") if trip else "None")
    logger.info("  LLM disponible: extract=%s, chat=%s", bool(_llm_extract_fn), bool(_llm_process_fn))

    # Paso 1: LLM extraction UNICA (con o sin viaje activo)
    llm_result = None
    if _llm_extract_fn:
        target_trip = trip
        if not trip:
            # Trip minimo para permitir deteccion de create_trip sin viaje activo
            target_trip = {"destination": "", "start_date": "", "end_date": "", "items": [], "expenses": []}
        partial = (item_creation_draft
                   if item_creation_draft and item_creation_draft.get("step") == "collecting"
                   else None)
        logger.info("  [Paso 1] Llamando _llm_extract_fn (trip=%s, partial_draft=%s)",
                    "activo" if trip else "vacio", bool(partial))
        llm_result = _llm_extract_fn(
            message, target_trip,
            partial_draft=partial,
            chat_history=chat_history,
        )
        if llm_result:
            logger.info("  [Paso 1] LLM result:")
            logger.info("    intent=%s", llm_result.intent)
            logger.info("    name=%s, day=%s, item_type=%s", llm_result.name, llm_result.day, llm_result.item_type)
            logger.info("    flight_origin=%s, result_count=%s", llm_result.flight_origin, llm_result.result_count)
            logger.info("    hotel_type=%s, hotel_location=%s, hotel_max_price=%s",
                        llm_result.hotel_type, llm_result.hotel_location, llm_result.hotel_max_price)
            logger.info("    trip_destination=%s, trip_start_date=%s, trip_end_date=%s",
                        llm_result.trip_destination, llm_result.trip_start_date, llm_result.trip_end_date)
            logger.info("    is_complete=%s, missing=%s", llm_result.is_complete, llm_result.missing_fields)
        else:
            logger.warning("  [Paso 1] LLM retorno None (error)")

    # Paso 1.5: Sin viaje activo + intent detectado por LLM
    if not trip and llm_result:
        if llm_result.intent == "create_trip":
            logger.info("  [Paso 1.5] Sin trip + intent create_trip → iniciar creacion")
            result = _handle_create_trip_from_llm(llm_result, message, trip)
            if result is not None:
                return result
        elif llm_result.intent in ("flight_search", "hotel_search", "add_item",
                                    "remove_item", "calendar_event",
                                    "add_expense", "modify_expense", "remove_expense"):
            logger.info("  [Paso 1.5] Sin trip + intent %s → necesita viaje activo", llm_result.intent)
            return {
                "role": "assistant",
                "type": "text",
                "content": (
                    "Para eso necesito que tengas un **viaje activo**. "
                    "Selecciona un viaje en el selector de arriba, o dime a donde quieres ir "
                    "para crear uno nuevo."
                ),
            }

    # Paso 2: Flujo multi-turn de creacion de viaje (draft activo)
    result = _handle_trip_creation_flow(msg, message, trip, trip_creation_draft)
    if result is not None:
        logger.info("  [Paso 2] Trip creation flow manejo el mensaje")
        return result

    # Paso 3: Escape de draft de item via LLM
    if item_creation_draft and item_creation_draft.get("step") == "collecting":
        if llm_result and llm_result.intent not in ("add_item", "unknown", "informative"):
            logger.info("  [Paso 3] Escapando draft de item (intent=%s)", llm_result.intent)
            item_creation_draft = None
            _clear_session_draft("_item_creation_draft")

    # Paso 4: Flujo multi-turn de creacion de item
    result = _handle_item_creation_flow(
        msg, message, trip, item_creation_draft,
        chat_history=chat_history, llm_result=llm_result,
    )
    if result is not None:
        logger.info("  [Paso 4] Item creation flow manejo el mensaje")
        return result

    # Paso 5: Sin viaje activo y sin intent accionable → LLM chat
    if not trip and _USE_LLM and _llm_process_fn:
        logger.info("  [Paso 5] Sin viaje + sin intent accionable → LLM chat")
        return _llm_chat_response(message, None, user_id, chat_id)

    # Paso 6: Dispatch por intent del LLM
    if trip and llm_result:
        logger.info("  [Paso 6] Dispatch intent=%s", llm_result.intent)
        result = _dispatch_llm_intent(
            llm_result, message, trip, user_id, chat_id, chat_history,
        )
        if result is not None:
            logger.info("  [Paso 6] Dispatch retorno tipo=%s", result.get("type"))
            return result
        # Fall-through: informative/unknown → LLM chat
        if _USE_LLM and _llm_process_fn:
            logger.info("  [Paso 6] Fall-through → LLM chat")
            return _llm_chat_response(message, trip, user_id, chat_id)

    # Paso 7: Sin LLM configurado
    logger.info("  [Paso 7] Sin LLM configurado")
    return {
        "role": "assistant",
        "type": "text",
        "content": (
            "El asistente IA no esta disponible. "
            "Contacta al administrador para habilitar el servicio de LLM.\n\n"
            "Mientras tanto, puedes:\n"
            "- Crear viajes desde **Mis Viajes**\n"
            "- Gestionar tu itinerario desde las secciones de la barra lateral"
        ),
    }


def _clear_session_draft(key: str):
    """Limpia un draft del session_state de Streamlit."""
    try:
        import streamlit as st
        st.session_state[key] = None
    except Exception:
        pass


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

    # Sin draft: el LLM detecta create_trip via _dispatch_llm_intent
    return None


def _handle_item_creation_flow(
    msg: str, original_message: str,
    trip: Optional[dict], draft: Optional[dict],
    chat_history: Optional[list] = None,
    llm_result=None,
) -> Optional[dict]:
    """Maneja el flujo multi-turn de creacion de item (REQ-CF-003).

    Retorna dict de respuesta si el flujo aplica, o None si no.
    """
    if not draft or draft.get("step") != "collecting":
        return None
    if not trip:
        return None

    # Cancelacion
    if detect_cancel_intent(msg):
        return {
            "role": "assistant",
            "type": "text",
            "content": "Entendido, cancele la creacion del item.",
            "_item_creation_draft": None,
        }

    # El LLM clasifico como informative → dejar pasar al LLM chat
    if llm_result and llm_result.intent == "informative":
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

    # Extraer datos del mensaje via LLM result (ya calculado en paso 1)
    if llm_result and llm_result.intent == "add_item":
        updated = _merge_extraction_to_draft(llm_result, draft)
    elif _llm_extract_fn:
        # Fallback: llamada directa si llm_result no aplica
        local_result = _llm_extract_fn(original_message, trip, draft, chat_history=chat_history)
        if local_result:
            updated = _merge_extraction_to_draft(local_result, draft)
        else:
            updated = dict(draft)
    else:
        updated = dict(draft)
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


def _dispatch_llm_intent(
    result,
    message: str, trip: dict,
    user_id: Optional[str] = None, chat_id: Optional[str] = None,
    chat_history: Optional[list] = None,
) -> Optional[dict]:
    """Dispatch por intent del LLM. El result ya existe, no se llama al LLM aqui.

    Retorna dict de respuesta si el intent es accionable, o None para fall-through.
    """
    logger.info("    [dispatch] intent=%s", result.intent)
    if result.intent == "add_item":
        return _handle_extraction_result(result, trip)

    if result.intent == "create_trip":
        return _handle_create_trip_from_llm(result, message, trip)

    if result.intent == "calendar_event":
        return _calendar_event_response(trip)

    if result.intent == "remove_item":
        return _remove_item_response(message.lower(), trip, result)

    if result.intent == "hotel_search":
        if _USE_BOOKING:
            return _hotel_search_response(message, trip, user_id, chat_id, llm_result=result)
        return None

    if result.intent == "flight_search":
        if _USE_FLIGHTS:
            return _flight_search_response(message, trip, user_id, chat_id, llm_result=result)
        return None

    if result.intent == "add_expense":
        return _handle_add_expense(result, trip)

    if result.intent == "modify_expense":
        return _handle_modify_expense(result, trip)

    if result.intent == "remove_expense":
        return _handle_remove_expense(result, trip)

    # informative, unknown → fall through al LLM chat
    return None


def _handle_create_trip_from_llm(result, message: str, trip: Optional[dict]) -> Optional[dict]:
    """Inicia flujo de creacion de viaje cuando el LLM detecta intent create_trip.

    Reutiliza la logica de trip_creation_flow.py para extraer datos y generar
    confirmacion o iniciar flujo multi-turn.
    """
    destination = getattr(result, "trip_destination", None) or None

    # Proteccion anti-duplicado: si hay viaje activo al mismo destino, no crear
    if trip and destination:
        current_dest = (trip.get("destination") or "").lower().strip()
        if _is_same_destination(destination.lower().strip(), current_dest):
            return None  # Fall through al LLM chat

    draft = new_draft()

    # Fuente primaria: datos extraidos por el LLM
    if destination:
        draft["destination"] = destination
    if getattr(result, "trip_start_date", None):
        draft["start_date"] = result.trip_start_date
    if getattr(result, "trip_end_date", None):
        draft["end_date"] = result.trip_end_date
    if getattr(result, "trip_name", None):
        draft["name"] = result.trip_name

    # Fallback: regex de fechas para lo que el LLM no extrajo
    updated = extract_trip_data(message, draft)
    updated["step"] = "collecting"

    missing = get_missing_fields(updated)

    if not missing:
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


def _handle_add_expense(result, trip: dict) -> Optional[dict]:
    """Genera confirmacion para agregar un gasto al presupuesto."""
    name = result.name or result.expense_category or "Gasto"
    amount = result.expense_amount or result.cost
    category = result.expense_category or "extras"

    if not amount or amount <= 0:
        return {
            "role": "assistant",
            "type": "text",
            "content": "¿Cuánto costó? Necesito el monto para registrar el gasto.",
        }

    # Formatear categoría para display
    from config.settings import BudgetCategory, BUDGET_CATEGORY_LABELS
    try:
        cat_enum = BudgetCategory(category)
        cat_label = BUDGET_CATEGORY_LABELS[cat_enum]
    except (ValueError, KeyError):
        cat_label = category

    return {
        "role": "assistant",
        "type": "confirmation",
        "content": {
            "action": "add_expense",
            "summary": f"Registrar gasto: {name}",
            "details": {
                "name": name,
                "category": cat_label,
                "amount": f"USD {amount:,.2f}",
                "_category_value": category,
                "_amount_value": amount,
                "_notes": result.location or "",
            },
        },
    }


def _handle_modify_expense(result, trip: dict) -> Optional[dict]:
    """Genera confirmacion para modificar un gasto existente."""
    expenses = trip.get("expenses", [])
    if not expenses:
        return {
            "role": "assistant",
            "type": "text",
            "content": "No hay gastos registrados en este viaje para modificar.",
        }

    # Buscar expense por ID
    target = None
    if result.expense_id:
        for exp in expenses:
            if exp["id"] == result.expense_id:
                target = exp
                break

    # Si no encontró por ID, buscar por nombre
    if not target and result.name:
        name_lower = result.name.lower()
        for exp in expenses:
            if name_lower in exp["name"].lower() or exp["name"].lower() in name_lower:
                target = exp
                break

    # Fallback: buscar por categoría
    if not target and result.expense_category:
        for exp in expenses:
            if exp.get("category") == result.expense_category:
                target = exp
                break
    if not target and result.name:
        # Fallback extra: el nombre del usuario puede ser la etiqueta de categoría
        from config.settings import BudgetCategory, BUDGET_CATEGORY_LABELS
        _label_to_value = {label.lower(): cat.value for cat, label in BUDGET_CATEGORY_LABELS.items()}
        name_lower = result.name.lower()
        matched_cat = _label_to_value.get(name_lower)
        if not matched_cat:
            for label, cat_val in _label_to_value.items():
                if name_lower in label or label in name_lower:
                    matched_cat = cat_val
                    break
        if matched_cat:
            for exp in expenses:
                if exp.get("category") == matched_cat:
                    target = exp
                    break

    if not target:
        return {
            "role": "assistant",
            "type": "text",
            "content": "No encontré el gasto que quieres modificar. ¿Puedes ser más específico?",
        }

    # Determinar qué cambios aplicar
    changes = {}
    if result.name and result.name != target["name"]:
        changes["name"] = result.name
    if result.expense_amount and result.expense_amount != target["amount"]:
        changes["amount"] = result.expense_amount
    if result.expense_category and result.expense_category != target["category"]:
        changes["category"] = result.expense_category

    if not changes:
        return {
            "role": "assistant",
            "type": "text",
            "content": f"El gasto '{target['name']}' ya tiene esos datos. ¿Qué quieres cambiar?",
        }

    # Formatear detalles para la confirmación
    details = {"_expense_id": target["id"]}
    details["Gasto actual"] = f"{target['name']} — USD {target['amount']:,.2f}"

    if "name" in changes:
        details["Nuevo nombre"] = changes["name"]
    if "amount" in changes:
        details["Nuevo monto"] = f"USD {changes['amount']:,.2f}"
    if "category" in changes:
        from config.settings import BudgetCategory, BUDGET_CATEGORY_LABELS
        try:
            cat_label = BUDGET_CATEGORY_LABELS[BudgetCategory(changes["category"])]
        except (ValueError, KeyError):
            cat_label = changes["category"]
        details["Nueva categoria"] = cat_label

    details["_changes"] = changes

    return {
        "role": "assistant",
        "type": "confirmation",
        "content": {
            "action": "modify_expense",
            "summary": f"Modificar gasto: {target['name']}",
            "details": details,
        },
    }


def _handle_remove_expense(result, trip: dict) -> Optional[dict]:
    """Genera confirmacion para eliminar un gasto."""
    expenses = trip.get("expenses", [])
    if not expenses:
        return {
            "role": "assistant",
            "type": "text",
            "content": "No hay gastos registrados en este viaje para eliminar.",
        }

    # Eliminar TODOS los gastos
    if getattr(result, "remove_all_expenses", False):
        total = sum(exp["amount"] for exp in expenses)
        names = ", ".join(exp["name"] for exp in expenses)
        return {
            "role": "assistant",
            "type": "confirmation",
            "content": {
                "action": "remove_all_expenses",
                "summary": f"Eliminar todos los gastos del viaje ({len(expenses)} gastos, USD {total:,.2f})",
                "details": {
                    "expense_count": len(expenses),
                    "expense_names": names,
                    "total_amount": f"USD {total:,.2f}",
                    "_expense_ids": [exp["id"] for exp in expenses],
                },
            },
        }

    # Buscar expense por ID
    target = None
    if result.expense_id:
        for exp in expenses:
            if exp["id"] == result.expense_id:
                target = exp
                break

    # Si no encontró por ID, buscar por nombre
    if not target and result.name:
        name_lower = result.name.lower()
        for exp in expenses:
            if name_lower in exp["name"].lower() or exp["name"].lower() in name_lower:
                target = exp
                break

    # Fallback: buscar por categoría (valor enum o etiqueta legible)
    if not target and result.expense_category:
        for exp in expenses:
            if exp.get("category") == result.expense_category:
                target = exp
                break
    if not target and result.name:
        # Fallback extra: el nombre del usuario puede ser la etiqueta de categoría
        from config.settings import BudgetCategory, BUDGET_CATEGORY_LABELS
        _label_to_value = {label.lower(): cat.value for cat, label in BUDGET_CATEGORY_LABELS.items()}
        name_lower = result.name.lower()
        matched_cat = _label_to_value.get(name_lower)
        if not matched_cat:
            # Substring match: "transporte" matchea "transporte local"
            for label, cat_val in _label_to_value.items():
                if name_lower in label or label in name_lower:
                    matched_cat = cat_val
                    break
        if matched_cat:
            for exp in expenses:
                if exp.get("category") == matched_cat:
                    target = exp
                    break

    if not target:
        return {
            "role": "assistant",
            "type": "text",
            "content": "No encontré el gasto que quieres eliminar. ¿Puedes ser más específico?",
        }

    return {
        "role": "assistant",
        "type": "confirmation",
        "content": {
            "action": "remove_expense",
            "summary": f"Eliminar gasto: {target['name']} (USD {target['amount']:,.2f})",
            "details": {
                "name": target["name"],
                "amount": f"USD {target['amount']:,.2f}",
                "_expense_id": target["id"],
            },
        },
    }


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
    llm_result=None,
) -> Optional[dict]:
    """Busca hoteles via Booking.com con filtros del LLM."""
    try:
        # Datos del LLM result (sin 2da llamada ni regex)
        limit = 5
        hotel_type = None
        location_hint = ""
        max_price = None
        if llm_result:
            limit = llm_result.result_count or 5
            hotel_type = getattr(llm_result, "hotel_type", None)
            location_hint = getattr(llm_result, "hotel_location", None) or ""
            max_price = getattr(llm_result, "hotel_max_price", None)
        logger.info("    [hotel_search] limit=%s, type=%s, location=%s, max_price=%s",
                    limit, hotel_type, location_hint, max_price)

        # Buscar mas resultados si hay filtros (para tener margen de filtrado)
        search_limit = limit * 3 if (hotel_type or max_price) else limit
        logger.info("    [hotel_search] Buscando con search_limit=%s, location_hint='%s'", search_limit, location_hint)
        hotels = search_hotels_for_trip(trip, limit=search_limit, location_hint=location_hint)
        logger.info("    [hotel_search] Resultados API: %d hoteles", len(hotels) if hotels else 0)

        if not hotels and location_hint:
            # Reintentar SIN location_hint (puede ser una zona que no existe en el destino)
            logger.info("    [hotel_search] Sin resultados con location_hint, reintentando sin filtro de zona")
            hotels = search_hotels_for_trip(trip, limit=search_limit)
            logger.info("    [hotel_search] Resultados retry: %d hoteles", len(hotels) if hotels else 0)

        if not hotels:
            dest = trip.get("destination", "tu destino")
            return {
                "role": "assistant",
                "type": "text",
                "content": f"No encontre alojamiento disponible en **{dest}** para esas fechas. Intenta con otras fechas o destino.",
            }

        # Aplicar filtros post-respuesta
        filter_matched = True
        if hotel_type or max_price:
            count_before = len(hotels)
            hotels = _filter_hotels(hotels, hotel_type=hotel_type or "", max_price=max_price or 0)
            if hotel_type and len(hotels) == count_before:
                filter_matched = False

        hotels = hotels[:limit]
        checkin = trip.get("start_date", "")
        checkout = trip.get("end_date", "")
        cards = format_hotels_as_cards(hotels, checkin=checkin, checkout=checkout)

        dest = trip.get("destination", "tu destino")
        text_parts = [f"Hoteles en **{dest}**"]
        if location_hint:
            text_parts[0] = f"Hoteles en **{location_hint}, {dest}**"
        if hotel_type:
            text_parts[0] = text_parts[0].replace("Hoteles", hotel_type.capitalize() + "s")
        text_parts.append(f"({checkin} — {checkout}):")
        if not filter_matched and hotel_type:
            text_parts.append(f"\n\n_No encontre {hotel_type}s en esta zona. Mostrando alojamientos disponibles._")

        return {
            "role": "assistant",
            "type": "hotel_results",
            "content": {
                "text": " ".join(text_parts),
                "hotels": cards,
            },
        }
    except Exception as e:
        logger.warning("Error en busqueda Booking.com: %s", e)
        return None


def _flight_search_response(
    message: str, trip: dict,
    user_id: Optional[str] = None, chat_id: Optional[str] = None,
    llm_result=None,
) -> Optional[dict]:
    """Busca vuelos con datos extraidos del LLM."""
    try:
        # Datos del LLM result
        origin = ""
        destination_city = ""
        origin_iata = ""
        dest_iata = ""
        limit = 5
        if llm_result:
            origin = llm_result.flight_origin or ""
            destination_city = getattr(llm_result, "flight_destination", "") or ""
            origin_iata = getattr(llm_result, "flight_origin_iata", "") or ""
            dest_iata = getattr(llm_result, "flight_destination_iata", "") or ""
            limit = llm_result.result_count or 5
        logger.info("    [flight_search] origin=%s (%s), dest_city=%s (%s), limit=%s",
                    origin, origin_iata, destination_city, dest_iata, limit)

        flights = search_flights_for_trip(
            trip, origin=origin, destination_city=destination_city,
            origin_iata=origin_iata, dest_iata=dest_iata,
            max_results=limit,
        )
        if not flights:
            if origin:
                dest = trip.get("destination", "tu destino")
                return {
                    "role": "assistant",
                    "type": "text",
                    "content": (
                        f"No encontre vuelos de **{origin.title()}** a **{dest}** para esas fechas. "
                        "Google Flights no tiene resultados para esta ruta. "
                        "Intenta con otra ciudad de origen o fechas diferentes."
                    ),
                }
            return {
                "role": "assistant",
                "type": "text",
                "content": (
                    "Para buscar vuelos necesito saber tu **ciudad de origen**. "
                    "Por ejemplo: _busca vuelos desde Buenos Aires_ o _vuelos desde Montevideo_."
                ),
            }

        cards = format_flights_as_cards(flights)

        dest = trip.get("destination", "tu destino")
        origin_display = origin.title() if origin else "tu origen"
        return {
            "role": "assistant",
            "type": "flight_results",
            "content": {
                "text": (
                    f"Vuelos de **{origin_display}** a **{dest}** "
                    f"({trip.get('start_date', '')} — {trip.get('end_date', '')}):"
                ),
                "flights": cards,
            },
        }
    except Exception as e:
        logger.warning("Error en busqueda de vuelos: %s", e)
        return {
            "role": "assistant",
            "type": "text",
            "content": (
                "Hubo un error al buscar vuelos. "
                "Google Flights puede estar temporalmente no disponible. "
                "Intenta de nuevo en unos segundos."
            ),
        }


def _llm_chat_response(
    message: str, trip: Optional[dict],
    user_id: Optional[str] = None, chat_id: Optional[str] = None,
) -> dict:
    """Envia mensaje al LLM chat para respuesta conversacional."""
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


def _remove_item_response(msg: str, trip: dict, llm_result=None) -> dict:
    """Genera confirmacion de eliminacion de items.

    Con LLM: usa remove_item_ids/remove_all/remove_summary del resultado.
    Sin LLM (fallback): elimina el ultimo item (comportamiento legacy).
    """
    items = trip.get("items", [])
    if not items:
        return {
            "role": "assistant",
            "type": "text",
            "content": "No hay items en el itinerario para eliminar.",
        }

    # ─── Path CON LLM: eliminacion inteligente ───
    if llm_result is not None and hasattr(llm_result, "remove_item_ids"):
        ids_to_remove = llm_result.remove_item_ids
        summary = llm_result.remove_summary or ""

        if not ids_to_remove:
            # El LLM no encontro items que coincidan
            return {
                "role": "assistant",
                "type": "text",
                "content": summary or "No encontre items que coincidan con lo que quieres eliminar.",
            }

        # Construir mapa de items por ID para lookup rapido
        items_by_id = {item["id"]: item for item in items}

        # Filtrar solo IDs que realmente existen
        valid_ids = [rid for rid in ids_to_remove if rid in items_by_id]
        if not valid_ids:
            return {
                "role": "assistant",
                "type": "text",
                "content": "No encontre los items indicados en el itinerario actual.",
            }

        # Caso single item — formato simple
        if len(valid_ids) == 1:
            target = items_by_id[valid_ids[0]]
            return {
                "role": "assistant",
                "type": "confirmation",
                "content": {
                    "action": "remove_item",
                    "summary": summary or f"Eliminar '{target['name']}' del itinerario",
                    "details": {
                        "item_id": target["id"],
                        "item_name": target["name"],
                    },
                },
            }

        # Caso multi item — lista de nombres + IDs en _item_ids
        names = [items_by_id[rid]["name"] for rid in valid_ids]
        names_list = ", ".join(names)
        return {
            "role": "assistant",
            "type": "confirmation",
            "content": {
                "action": "remove_item",
                "summary": summary or f"Eliminar {len(valid_ids)} items del itinerario",
                "details": {
                    "item_names": names_list,
                    "item_count": len(valid_ids),
                    "_item_ids": valid_ids,
                },
            },
        }

    # Sin resultado LLM → no se puede determinar que eliminar
    return {
        "role": "assistant",
        "type": "text",
        "content": "No pude determinar que items quieres eliminar. Indica cuales con mas detalle.",
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
        # Soporte multi-removal: _item_ids (lista) tiene prioridad sobre item_id (single)
        item_ids = details.get("_item_ids") or []
        if not item_ids:
            # Fallback single item (compatibilidad con formato anterior)
            single_id = details.get("item_id")
            if single_id:
                item_ids = [single_id]

        if not item_ids:
            return "No se encontraron items a eliminar."

        removed = []
        for rid in item_ids:
            for i, item in enumerate(trip["items"]):
                if item["id"] == rid:
                    removed.append(item["name"])
                    trip["items"].pop(i)
                    break

        if removed:
            sync_trip_changes(trips, trip)
            if len(removed) == 1:
                return f"Se elimino '{removed[0]}' del itinerario."
            return f"Se eliminaron {len(removed)} items del itinerario: {', '.join(removed)}."
        return "No se encontraron los items a eliminar."

    elif action_type == "add_expense":
        from services.expense_service import add_expense
        name = details.get("name", "Gasto")
        category = details.get("_category_value", "extras")
        amount = details.get("_amount_value", 0.0)
        notes = details.get("_notes", "")
        expense = add_expense(trip, name, category, amount, notes)
        sync_trip_changes(trips, trip)
        return f"Se registró el gasto '{expense['name']}' por USD {expense['amount']:,.2f} en {details.get('category', 'extras')}."

    elif action_type == "modify_expense":
        from services.expense_service import update_expense
        expense_id = details.get("_expense_id")
        changes = details.get("_changes", {})
        if expense_id and changes:
            updated = update_expense(trip, expense_id, changes)
            if updated:
                sync_trip_changes(trips, trip)
                return f"Se actualizó el gasto '{updated['name']}' (USD {updated['amount']:,.2f})."
        return "No se pudo modificar el gasto."

    elif action_type == "remove_expense":
        from services.expense_service import remove_expense
        expense_id = details.get("_expense_id")
        if expense_id:
            removed_name = remove_expense(trip, expense_id)
            if removed_name:
                sync_trip_changes(trips, trip)
                return f"Se eliminó el gasto '{removed_name}' del presupuesto."
        return "No se pudo eliminar el gasto."

    elif action_type == "remove_all_expenses":
        from services.expense_service import remove_expense
        expense_ids = details.get("_expense_ids", [])
        removed = []
        for eid in expense_ids:
            name = remove_expense(trip, eid)
            if name:
                removed.append(name)
        if removed:
            sync_trip_changes(trips, trip)
            return f"Se eliminaron {len(removed)} gastos del presupuesto: {', '.join(removed)}."
        return "No se pudieron eliminar los gastos."

    elif action_type == "create_trip":
        # Esto se maneja de forma especial en el chat
        return "✅ Viaje creado exitosamente."

    return "❌ Acción no reconocida."
