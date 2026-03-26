"""Utilidades de validacion y fallback de extraccion de items para el itinerario.

Cuando OPENAI_API_KEY esta disponible, la extraccion principal la hace
services/llm_item_extraction.py (LLM structured output). Este modulo provee:
- Funciones de validacion pura (validate_item_day_range, detect_time_conflict)
- Funciones de confirmacion (build_item_confirmation_data)
- Utilidades (calculate_end_time, new_item_draft, get_missing_item_fields, etc.)
- Fallback basico de extraccion por keywords (sin LLM)
"""

import re
from datetime import date, timedelta
from typing import Optional

from services.trip_creation_flow import _CANCEL_KEYWORDS

# ─── Duraciones por defecto por tipo en horas ───
_DEFAULT_DURATIONS = {
    "actividad": 2.0, "comida": 1.5, "vuelo": 3.0,
    "traslado": 1.0, "alojamiento": 1.0, "extra": 1.0,
}

# ─── Horarios por defecto segun tipo ───
_DEFAULT_TIMES = {
    "actividad": "10:00", "comida": "12:30", "vuelo": "08:00",
    "traslado": "09:00", "alojamiento": "15:00", "extra": "10:00",
}

# ─── Keywords de tipo de item (fallback sin LLM) ───
_ITEM_TYPE_KEYWORDS = {
    "comida": [
        "restaurante", "cena", "almuerzo", "desayuno", "comer",
        "comida", "brunch", "cenar", "almorzar", "desayunar",
    ],
    "alojamiento": [
        "hotel", "hospedaje", "airbnb", "hostel", "alojamiento",
        "check-in", "check-out", "checkin", "checkout",
    ],
    "vuelo": ["vuelo", "avion", "aeropuerto", "volar"],
    "traslado": [
        "taxi", "uber", "bus", "traslado", "transfer",
        "metro", "tren", "colectivo",
    ],
    "extra": ["extra", "seguro", "equipaje", "compras", "souvenir"],
}

# ─── Keywords de agregar item (fallback sin LLM) ───
_ADD_KEYWORDS = ["agregar", "añadir", "agrega", "añade", "anadir", "anade"]

# ─── Keywords que excluyen add_item (son intenciones de cronograma) ───
_CALENDAR_EXCLUSION_KEYWORDS = [
    "cronograma", "calendario", "al cronograma", "al calendario",
]

# ─── Keywords de cronograma (fallback sin LLM, REQ-CF-002) ───
_CALENDAR_KEYWORDS = [
    "cronograma", "calendario", "agregar al calendario",
    "crear evento", "bloque de viaje", "fechas del viaje al cronograma",
    "agregar al cronograma", "evento de calendario",
    "agregar mi viaje al cronograma", "crear evento del viaje",
]

# ─── Keywords de busqueda de hoteles (fallback sin LLM) ───
_HOTEL_KEYWORDS = [
    "hotel", "hoteles", "alojamiento", "hospedaje", "hostel",
    "donde dormir", "donde alojar", "donde quedar",
    "habitacion", "habitación", "reservar hotel",
    "booking", "alojarnos", "hospedarnos",
]

# ─── Keywords de busqueda de vuelos (fallback sin LLM) ───
_FLIGHT_KEYWORDS = [
    "vuelo", "vuelos", "pasaje", "pasajes", "avion", "avión",
    "aerolinea", "aerolínea", "volar", "buscar vuelo",
    "boleto aereo", "boleto aéreo", "ticket aereo",
    "precio de vuelo", "precios de vuelos",
]

# ─── Keywords de eliminar item (fallback sin LLM) ───
_REMOVE_KEYWORDS = ["eliminar", "quitar", "elimina", "quita", "borrar"]

# ─── Mapeo de ordinales en español (usado por agent_service._is_informative_question) ───
_ORDINALS = {
    "primero": 1, "primer": 1, "primera": 1,
    "segundo": 2, "segunda": 2,
    "tercero": 3, "tercer": 3, "tercera": 3,
    "cuarto": 4, "cuarta": 4,
    "quinto": 5, "quinta": 5,
    "sexto": 6, "sexta": 6,
    "septimo": 7, "séptimo": 7, "septima": 7, "séptima": 7,
    "octavo": 8, "octava": 8,
    "noveno": 9, "novena": 9,
    "decimo": 10, "décimo": 10, "decima": 10, "décima": 10,
}

_ORDINAL_NAMES = "|".join(_ORDINALS.keys())

# ─── Regex basico para fallback (sin LLM) ───
_BASIC_DAY = re.compile(r"dia\s+(\d{1,2})", re.IGNORECASE)
_BASIC_TIME = re.compile(r"(\d{1,2})[:\.](\d{2})", re.IGNORECASE)


def detect_add_item_intent(msg: str) -> bool:
    """Detecta si el mensaje tiene intencion de agregar un item al itinerario."""
    lower = msg.lower().strip()
    if any(kw in lower for kw in _CALENDAR_EXCLUSION_KEYWORDS):
        return False
    return any(kw in lower for kw in _ADD_KEYWORDS)


def detect_calendar_intent(msg: str) -> bool:
    """Detecta si el mensaje tiene intencion de crear evento de cronograma (fallback sin LLM)."""
    lower = msg.lower().strip()
    return any(kw in lower for kw in _CALENDAR_KEYWORDS)


def detect_hotel_intent(msg: str) -> bool:
    """Detecta si el mensaje tiene intencion de buscar hoteles (fallback sin LLM)."""
    lower = msg.lower().strip()
    return any(kw in lower for kw in _HOTEL_KEYWORDS)


def detect_flight_intent(msg: str) -> bool:
    """Detecta si el mensaje pide buscar vuelos."""
    lower = msg.lower()
    return any(kw in lower for kw in _FLIGHT_KEYWORDS)


def detect_remove_item_intent(msg: str) -> bool:
    """Detecta si el mensaje tiene intencion de eliminar un item (fallback sin LLM)."""
    lower = msg.lower().strip()
    return any(kw in lower for kw in _REMOVE_KEYWORDS)


def detect_cancel_intent(msg: str) -> bool:
    """Detecta si el usuario quiere cancelar el flujo."""
    lower = msg.lower().strip()
    return any(kw in lower for kw in _CANCEL_KEYWORDS)


def infer_item_type(msg: str) -> str:
    """Infiere el tipo de item a partir de keywords en el mensaje."""
    lower = msg.lower()
    for item_type, keywords in _ITEM_TYPE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return item_type
    return "actividad"


def calculate_end_time(start_time: str, item_type: str) -> str:
    """Calcula end_time sumando duracion por defecto al start_time.

    Trunca a 23:59 si excede medianoche.
    """
    duration = _DEFAULT_DURATIONS.get(item_type, 1.0)
    try:
        h, m = map(int, start_time.split(":"))
    except (ValueError, AttributeError):
        return "23:59"

    total_minutes = h * 60 + m + int(duration * 60)
    if total_minutes >= 24 * 60:
        return "23:59"

    end_h = total_minutes // 60
    end_m = total_minutes % 60
    return f"{end_h:02d}:{end_m:02d}"


def get_missing_item_fields(draft: dict) -> list:
    """Retorna lista de campos minimos requeridos faltantes."""
    missing = []
    if not draft.get("name"):
        missing.append("name")
    if not draft.get("day"):
        missing.append("day")
    return missing


def build_item_prompt_for_missing(draft: dict, missing: list) -> str:
    """Genera mensaje para pedir datos faltantes al usuario."""
    if "name" in missing and "day" in missing:
        return "Que actividad quieres agregar y en que dia de tu viaje?"

    if "name" in missing:
        day = draft.get("day", "?")
        time = draft.get("start_time", "")
        time_str = f" a las {time}" if time else ""
        return f"Que actividad quieres agregar para el dia {day}{time_str}?"

    if "day" in missing:
        name = draft.get("name", "esta actividad")
        return f"En que dia de tu viaje quieres programar '{name}'?"

    return ""


def validate_item_day_range(day: int, trip: dict) -> tuple:
    """Valida que el dia este dentro del rango del viaje.

    Retorna (is_valid, error_message).
    """
    start_str = trip.get("start_date", "")
    end_str = trip.get("end_date", "")

    if not start_str or not end_str:
        return True, ""

    try:
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
    except ValueError:
        return True, ""

    total_days = (end - start).days + 1

    if day < 1:
        return False, f"El dia debe ser al menos 1. Tu viaje tiene {total_days} dias (del {start_str} al {end_str})."

    if day > total_days:
        return False, (
            f"Esa fecha esta fuera de tu viaje, que va del {start_str} al {end_str} "
            f"({total_days} dias). Indica un dia entre 1 y {total_days}."
        )

    return True, ""


def detect_time_conflict(day: int, start_time: str, end_time: str, items: list) -> Optional[str]:
    """Detecta conflictos horarios con items existentes en el mismo dia.

    Retorna descripcion del conflicto o None si no hay.
    """
    for item in items:
        if item.get("day") != day:
            continue
        if item.get("end_day") and item["end_day"] > item["day"]:
            continue

        existing_start = item.get("start_time", "00:00")
        existing_end = item.get("end_time", "23:59")

        if start_time < existing_end and end_time > existing_start:
            return (
                f"Ya tienes '{item['name']}' de {existing_start} a {existing_end} "
                f"en el dia {day}."
            )

    return None


def build_item_confirmation_data(draft: dict, trip: dict) -> dict:
    """Construye dict de confirmacion con datos del item extraido."""
    item_type = draft.get("item_type", "actividad")
    start_time = draft.get("start_time") or _DEFAULT_TIMES.get(item_type, "10:00")
    end_time = draft.get("end_time") or calculate_end_time(start_time, item_type)
    day = draft.get("day", 1)
    name = draft.get("name", "Nueva actividad")
    cost = draft.get("cost_estimated", 0.0)

    date_label = f"Dia {day}"
    start_str = trip.get("start_date", "")
    if start_str:
        try:
            start_date = date.fromisoformat(start_str)
            abs_date = start_date + timedelta(days=day - 1)
            date_label = f"Dia {day} ({abs_date.isoformat()})"
        except ValueError:
            pass

    return {
        "role": "assistant",
        "type": "confirmation",
        "content": {
            "action": "add_item",
            "summary": f"Agregar '{name}' al itinerario",
            "details": {
                "name": name,
                "item_type": item_type,
                "day": date_label,
                "start_time": start_time,
                "end_time": end_time,
                "location": draft.get("location", ""),
                "cost_estimated": cost,
                "_day_int": day,
            },
        },
    }


def new_item_draft() -> dict:
    """Crea un nuevo borrador de item."""
    return {
        "name": None,
        "item_type": None,
        "day": None,
        "start_time": None,
        "end_time": None,
        "location": "",
        "cost_estimated": 0.0,
        "step": "collecting",
        "turns": 0,
    }


def extract_item_data(msg: str, trip: dict, current_draft: Optional[dict] = None) -> dict:
    """Extraccion basica de datos del item (fallback sin LLM).

    Solo extrae datos simples por keywords y patrones basicos.
    Para extraccion completa, usar services/llm_item_extraction.py.
    """
    draft = dict(current_draft) if current_draft else new_item_draft()
    lower = msg.lower().strip()

    # Extraer dia basico: "dia 3", "dia 10"
    if not draft.get("day"):
        m = _BASIC_DAY.search(lower)
        if m:
            draft["day"] = int(m.group(1))

    # Extraer hora basica: "10:00", "15.30"
    if not draft.get("start_time"):
        m = _BASIC_TIME.search(lower)
        if m:
            h, mins = int(m.group(1)), int(m.group(2))
            if 0 <= h <= 23 and 0 <= mins <= 59:
                draft["start_time"] = f"{h:02d}:{mins:02d}"

    # Inferir tipo por keywords
    if not draft.get("item_type") or draft["item_type"] == "actividad":
        inferred = infer_item_type(msg)
        if inferred != "actividad" or not draft.get("item_type"):
            draft["item_type"] = inferred

    # Extraer nombre: limpiar keywords de agregar y datos temporales
    if not draft.get("name"):
        name = lower
        for kw in _ADD_KEYWORDS:
            if name.startswith(kw):
                name = name[len(kw):].strip()
                break
        name = _BASIC_DAY.sub("", name)
        name = _BASIC_TIME.sub("", name)
        name = re.sub(r"\s+", " ", name).strip().strip(".,;:!?")
        if name and len(name) >= 2:
            draft["name"] = name[0].upper() + name[1:]

    return draft
