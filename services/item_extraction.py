"""Flujo de extraccion inteligente de items para el itinerario.

Logica pura — sin Streamlit, sin imports pesados. Solo re, datetime.
Patron de referencia: services/trip_creation_flow.py
"""

import re
from datetime import date, timedelta
from typing import Optional

# Reutilizar mapeo de meses y keywords de cancelacion de trip_creation_flow
from services.trip_creation_flow import _MESES, _CANCEL_KEYWORDS

_MESES_PATTERN = "|".join(_MESES.keys())

# ─── Keywords de tipo de item (RN-005) ───
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

# ─── Franjas horarias genericas (RN-004) ───
_TIME_SLOTS = {
    "manana": "09:00",
    "mañana": "09:00",
    "mediodia": "12:00",
    "medio dia": "12:00",
    "tarde": "15:00",
    "noche": "20:00",
}

# ─── Duraciones por defecto por tipo en horas (CRIT-02) ───
_DEFAULT_DURATIONS = {
    "actividad": 2.0,
    "comida": 1.5,
    "vuelo": 3.0,
    "traslado": 1.0,
    "alojamiento": 1.0,
    "extra": 1.0,
}

# ─── Horarios por defecto segun tipo (RN-004) ───
_DEFAULT_TIMES = {
    "actividad": "10:00",
    "comida": "12:30",
    "vuelo": "08:00",
    "traslado": "09:00",
    "alojamiento": "15:00",
    "extra": "10:00",
}

# ─── Subtipos de comida con horarios especificos ───
_MEAL_TIMES = {
    "desayuno": "08:00",
    "desayunar": "08:00",
    "brunch": "10:30",
    "almuerzo": "12:30",
    "almorzar": "12:30",
    "comida": "12:30",
    "comer": "12:30",
    "cena": "20:00",
    "cenar": "20:00",
}

# ─── Keywords de agregar item ───
_ADD_KEYWORDS = ["agregar", "añadir", "agrega", "añade", "anadir", "anade"]

# ─── Keywords que excluyen add_item (son intenciones de cronograma) ───
_CALENDAR_EXCLUSION_KEYWORDS = [
    "cronograma", "calendario", "al cronograma", "al calendario",
]

# ─── Regex para hora explicita ───
_TIME_EXPLICIT = re.compile(
    r"(?:a\s+las?\s+)?(\d{1,2})[:\.](\d{2})",
    re.IGNORECASE,
)

_TIME_AM_PM = re.compile(
    r"(\d{1,2})\s+de\s+la\s+(manana|mañana|tarde|noche)",
    re.IGNORECASE,
)

# ─── Regex para rango horario ("16:30 a 19:30", "de las 16:30 a las 19:30") ───
_TIME_RANGE = re.compile(
    r"(?:de\s+(?:las?\s+)?|para\s+(?:las?\s+)?|a\s+las?\s+)?(\d{1,2})[:\.](\d{2})\s*(?:a|[-–])\s*(?:las?\s+)?(\d{1,2})[:\.](\d{2})",
    re.IGNORECASE,
)

# ─── Regex para dia relativo explicito ───
_DAY_RELATIVE = re.compile(
    r"(?:el\s+)?dia\s+(\d{1,2})",
    re.IGNORECASE,
)

# ─── Mapeo de ordinales en español ───
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

# ─── Regex para dia ordinal en español ───
# "el quinto dia", "en el tercer dia", "quinto dia de mi viaje"
_DAY_ORDINAL = re.compile(
    rf"(?:en\s+)?(?:el\s+)?({_ORDINAL_NAMES})\s+dia",
    re.IGNORECASE,
)

# "dia quinto", "el dia tercero"
_DAY_ORDINAL_INVERTED = re.compile(
    rf"(?:el\s+)?dia\s+({_ORDINAL_NAMES})",
    re.IGNORECASE,
)

# "ultimo dia", "penultimo dia"
_DAY_RELATIVE_NAMED = re.compile(
    r"(?:el\s+)?(ultimo|último|penultimo|penúltimo)\s+dia",
    re.IGNORECASE,
)

# ─── Regex para fecha con nombre de mes ───
_DATE_WITH_MONTH = re.compile(
    rf"(?:el\s+)?(\d{{1,2}})\s+de\s+({_MESES_PATTERN})",
    re.IGNORECASE,
)

# ─── Regex para costo ───
_COST_PATTERN = re.compile(
    r"(?:por|cuesta|costo|precio|usd|dolares|\$)\s*(\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)

_COST_PATTERN_2 = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:dolares|usd|pesos|\$)",
    re.IGNORECASE,
)


def detect_add_item_intent(msg: str) -> bool:
    """Detecta si el mensaje tiene intencion de agregar un item al itinerario."""
    lower = msg.lower().strip()
    # Si refiere a cronograma/calendario, no es add_item
    if any(kw in lower for kw in _CALENDAR_EXCLUSION_KEYWORDS):
        return False
    return any(kw in lower for kw in _ADD_KEYWORDS)


def detect_cancel_intent(msg: str) -> bool:
    """Detecta si el usuario quiere cancelar el flujo."""
    lower = msg.lower().strip()
    return any(kw in lower for kw in _CANCEL_KEYWORDS)


def infer_item_type(msg: str) -> str:
    """Infiere el tipo de item a partir de keywords en el mensaje (RN-005)."""
    lower = msg.lower()
    for item_type, keywords in _ITEM_TYPE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return item_type
    return "actividad"


def extract_time(msg: str) -> Optional[str]:
    """Extrae hora de inicio del mensaje (RN-004). Retorna formato HH:MM o None."""
    lower = msg.lower()

    # 1. Hora explicita: "a las 10:00", "10:30", "6.30"
    m = _TIME_EXPLICIT.search(lower)
    if m:
        h, mins = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mins <= 59:
            return f"{h:02d}:{mins:02d}"

    # 2. Hora con AM/PM coloquial: "10 de la manana", "8 de la noche"
    m = _TIME_AM_PM.search(lower)
    if m:
        h = int(m.group(1))
        period = m.group(2).lower()
        if period in ("tarde",) and h < 12:
            h += 12
        elif period in ("noche",) and h < 12:
            h += 12
        if 0 <= h <= 23:
            return f"{h:02d}:00"

    # 3. Franja horaria generica: "por la manana", "al mediodia", "por la tarde"
    for slot_name, slot_time in _TIME_SLOTS.items():
        if slot_name in lower:
            return slot_time

    return None


def extract_time_range(msg: str) -> tuple:
    """Extrae rango horario del mensaje. Retorna (start_time, end_time) o (None, None).

    Soporta: "HH:MM a HH:MM", "HH:MM - HH:MM", "de HH:MM a HH:MM",
    "de las HH:MM a las HH:MM", "para las HH:MM a las HH:MM".
    Si solo hay un tiempo individual, retorna (start, None).
    """
    lower = msg.lower()

    # 1. Rango explicito: "16:30 a 19:30", "de las 16:30 a las 19:30"
    m = _TIME_RANGE.search(lower)
    if m:
        h1, m1 = int(m.group(1)), int(m.group(2))
        h2, m2 = int(m.group(3)), int(m.group(4))
        if 0 <= h1 <= 23 and 0 <= m1 <= 59 and 0 <= h2 <= 23 and 0 <= m2 <= 59:
            return (f"{h1:02d}:{m1:02d}", f"{h2:02d}:{m2:02d}")

    # 2. Tiempo individual (fallback a extract_time)
    single = extract_time(msg)
    if single:
        return (single, None)

    return (None, None)


def extract_day_from_message(msg: str, trip: dict) -> Optional[int]:
    """Extrae dia relativo del viaje desde el mensaje (RN-002).

    Convierte referencias temporales a dia 1-based relativo a trip["start_date"].
    """
    lower = msg.lower().strip()
    start_date_str = trip.get("start_date", "")
    if not start_date_str:
        return None

    try:
        start_date = date.fromisoformat(start_date_str)
    except ValueError:
        return None

    # 1. Ordinal en español: "el quinto dia", "en el tercer dia"
    m = _DAY_ORDINAL.search(lower)
    if m:
        day_num = _ORDINALS.get(m.group(1).lower())
        if day_num:
            return day_num

    # 2. Ordinal invertido: "dia quinto", "el dia tercero"
    m = _DAY_ORDINAL_INVERTED.search(lower)
    if m:
        day_num = _ORDINALS.get(m.group(1).lower())
        if day_num:
            return day_num

    # 3. "ultimo dia", "penultimo dia" (requiere end_date)
    m = _DAY_RELATIVE_NAMED.search(lower)
    if m:
        end_date_str = trip.get("end_date", "")
        if end_date_str:
            try:
                end_date = date.fromisoformat(end_date_str)
                total_days = (end_date - start_date).days + 1
                word = m.group(1).lower()
                if word in ("ultimo", "último"):
                    return total_days
                if word in ("penultimo", "penúltimo"):
                    return max(1, total_days - 1)
            except ValueError:
                pass

    # 4. Dia relativo explicito: "el dia 3", "dia 5"
    m = _DAY_RELATIVE.search(lower)
    if m:
        return int(m.group(1))

    # 5. Fecha con nombre de mes: "el 15 de abril"
    m = _DATE_WITH_MONTH.search(lower)
    if m:
        day_num = int(m.group(1))
        month_name = m.group(2).lower()
        month = _MESES.get(month_name)
        if month:
            # Inferir ano
            year = start_date.year
            try:
                target = date(year, month, day_num)
            except ValueError:
                return None
            if target < start_date:
                target = date(year + 1, month, day_num)
            delta = (target - start_date).days + 1
            if delta >= 1:
                return delta

    # 6. "manana" (referencia relativa a hoy, NO franja horaria)
    if re.search(r"\bmanana\b", lower) or re.search(r"\bmañana\b", lower):
        # Solo si NO esta precedido por "por la" o "de la" (franja horaria)
        if not re.search(r"(?:por|de)\s+la\s+ma[nñ]ana", lower):
            tomorrow = date.today() + timedelta(days=1)
            delta = (tomorrow - start_date).days + 1
            if delta >= 1:
                return delta

    # 7. "pasado manana"
    if "pasado" in lower and ("manana" in lower or "mañana" in lower):
        day_after = date.today() + timedelta(days=2)
        delta = (day_after - start_date).days + 1
        if delta >= 1:
            return delta

    return None


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


def extract_item_name(msg: str) -> Optional[str]:
    """Extrae el nombre/descripcion de la actividad del mensaje (RN-001).

    Intenta limpiar keywords de agregar y datos temporales para obtener el nombre.
    """
    lower = msg.lower().strip()

    # Remover keywords de agregar al inicio
    for kw in _ADD_KEYWORDS:
        if lower.startswith(kw):
            lower = lower[len(kw):].strip()
            break

    # Remover datos temporales y de costo del final/medio
    # Remover "el dia X", "el 15 de abril", "a las 10:00", "por la manana", etc.
    patterns_to_remove = [
        rf"(?:en\s+)?(?:el\s+)?(?:{_ORDINAL_NAMES})\s+dia(?:\s+de\s+mi\s+viaje)?",
        rf"(?:el\s+)?dia\s+(?:{_ORDINAL_NAMES})",
        r"(?:el\s+)?(?:ultimo|último|penultimo|penúltimo)\s+dia(?:\s+de\s+mi\s+viaje)?",
        r"\bde\s+mi\s+viaje\b",
        rf"(?:el\s+)?dia\s+\d+",
        rf"(?:el\s+)?\d{{1,2}}\s+de\s+(?:{_MESES_PATTERN})",
        r"(?:a\s+las?\s+)?\d{1,2}[:.]\d{2}",
        r"\d{1,2}\s+de\s+la\s+(?:manana|mañana|tarde|noche)",
        r"por\s+la\s+(?:manana|mañana|tarde|noche)",
        r"al\s+mediodia",
        r"(?:por|cuesta|costo|precio|usd|dolares|\$)\s*\d+(?:[.,]\d+)?",
        r"\d+(?:[.,]\d+)?\s*(?:dolares|usd|pesos|\$)",
        r"(?:manana|mañana|pasado\s+manana|pasado\s+mañana)\b",
    ]

    cleaned = lower
    for pat in patterns_to_remove:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)

    # Limpiar espacios multiples y puntuacion residual
    cleaned = re.sub(r"\s+", " ", cleaned).strip().strip(".,;:!?")

    if not cleaned or len(cleaned) < 2:
        return None

    # Capitalizar primera letra
    return cleaned[0].upper() + cleaned[1:]


def extract_cost(msg: str) -> Optional[float]:
    """Extrae costo mencionado en el mensaje. Retorna None si no se menciona."""
    m = _COST_PATTERN.search(msg)
    if m:
        val = m.group(1).replace(",", ".")
        try:
            return float(val)
        except ValueError:
            pass

    m = _COST_PATTERN_2.search(msg)
    if m:
        val = m.group(1).replace(",", ".")
        try:
            return float(val)
        except ValueError:
            pass

    return None


def extract_location(msg: str) -> str:
    """Extrae ubicacion del mensaje si se menciona un lugar especifico (RN-006).

    Busca patrones como "en [lugar]" despues de remover datos temporales.
    """
    lower = msg.lower()

    # Buscar "en [lugar]" — excluir "en abril", "en el dia 3", etc.
    m = re.search(
        rf"en\s+(?!(?:{_MESES_PATTERN})\b)(?!el\s+dia\b)(?!la\s+(?:manana|mañana|tarde|noche)\b)"
        rf"(?!(?:el\s+)?(?:{_ORDINAL_NAMES})\s+dia)"
        r"([A-Za-záéíóúñÁÉÍÓÚÑ\s]+?)(?:\s+(?:el|a\s+las?|por|del|dia)\s+|$)",
        lower,
    )
    if m:
        loc = m.group(1).strip().strip(".,;:!?")
        # Limpiar referencias ordinales/temporales residuales del final
        loc = re.sub(
            rf"\s*(?:en\s+)?(?:el\s+)?(?:{_ORDINAL_NAMES})\s+dia.*", "",
            loc, flags=re.IGNORECASE,
        ).strip()
        loc = re.sub(
            r"\s*(?:el\s+)?(?:ultimo|último|penultimo|penúltimo)\s+dia.*", "",
            loc, flags=re.IGNORECASE,
        ).strip()
        loc = re.sub(r"\s*(?:el\s+)?dia\s+\d+.*", "", loc, flags=re.IGNORECASE).strip()
        if len(loc) >= 2:
            return loc[0].upper() + loc[1:]

    return ""


def extract_item_data(msg: str, trip: dict, current_draft: Optional[dict] = None) -> dict:
    """Extrae todos los campos del item desde el mensaje. Combina con draft existente.

    Retorna dict con los campos encontrados.
    """
    draft = dict(current_draft) if current_draft else new_item_draft()

    # Extraer nombre si no existe en draft
    if not draft.get("name"):
        name = extract_item_name(msg)
        if name:
            draft["name"] = name

    # Extraer tipo si no esta definido
    if not draft.get("item_type") or draft["item_type"] == "actividad":
        inferred = infer_item_type(msg)
        if inferred != "actividad" or not draft.get("item_type"):
            draft["item_type"] = inferred

    # Extraer dia si no existe
    if not draft.get("day"):
        day = extract_day_from_message(msg, trip)
        if day:
            draft["day"] = day

    # Extraer hora — siempre intentar override si el usuario la especifica
    time_range = extract_time_range(msg)
    if time_range[0]:
        draft["start_time"] = time_range[0]
        if time_range[1]:
            draft["end_time"] = time_range[1]
    # Si no hay tiempo en el mensaje y no hay tiempo previo → queda None

    # Si no se extrajo hora, usar default segun tipo y subtipo
    if not draft.get("start_time") and draft.get("item_type"):
        # Para comidas, buscar subtipo especifico
        if draft["item_type"] == "comida":
            lower = msg.lower()
            for meal, meal_time in _MEAL_TIMES.items():
                if meal in lower:
                    draft["start_time"] = meal_time
                    break

    # Extraer ubicacion si no existe
    if not draft.get("location"):
        loc = extract_location(msg)
        if loc:
            draft["location"] = loc

    # Extraer costo si no existe
    if draft.get("cost_estimated") is None or draft["cost_estimated"] == 0:
        cost = extract_cost(msg)
        if cost is not None:
            draft["cost_estimated"] = cost

    return draft


def get_missing_item_fields(draft: dict) -> list:
    """Retorna lista de campos minimos requeridos faltantes (RN-008)."""
    missing = []
    if not draft.get("name"):
        missing.append("name")
    if not draft.get("day"):
        missing.append("day")
    return missing


def build_item_prompt_for_missing(draft: dict, missing: list) -> str:
    """Genera mensaje para pedir datos faltantes al usuario (RN-009)."""
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
    """Valida que el dia este dentro del rango del viaje (RN-003).

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
    """Detecta conflictos horarios con items existentes en el mismo dia (RN-011).

    Retorna descripcion del conflicto o None si no hay.
    """
    for item in items:
        if item.get("day") != day:
            continue
        # Ignorar items multi-dia (allDay) que no tienen horario real
        if item.get("end_day") and item["end_day"] > item["day"]:
            continue

        existing_start = item.get("start_time", "00:00")
        existing_end = item.get("end_time", "23:59")

        # Solapamiento: nuevo_start < existente_end AND nuevo_end > existente_start
        if start_time < existing_end and end_time > existing_start:
            return (
                f"Ya tienes '{item['name']}' de {existing_start} a {existing_end} "
                f"en el dia {day}."
            )

    return None


def build_item_confirmation_data(draft: dict, trip: dict) -> dict:
    """Construye dict de confirmacion con datos del item extraido (RN-010)."""
    item_type = draft.get("item_type", "actividad")
    start_time = draft.get("start_time") or _DEFAULT_TIMES.get(item_type, "10:00")
    end_time = draft.get("end_time") or calculate_end_time(start_time, item_type)
    day = draft.get("day", 1)
    name = draft.get("name", "Nueva actividad")
    cost = draft.get("cost_estimated", 0.0)

    # Calcular fecha absoluta para mostrar en la confirmacion
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
                # Datos internos para apply_confirmed_action
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
