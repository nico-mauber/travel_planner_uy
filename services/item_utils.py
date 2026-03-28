"""Utilidades de validacion y construccion de items para el itinerario.

Funciones de negocio puras: validacion de rangos, conflictos horarios,
calculo de duraciones, confirmaciones, y gestion de borradores.
"""

from datetime import date, timedelta
from typing import Optional

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
