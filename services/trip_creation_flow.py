"""Flujo multi-turn de creación de viajes desde el chat.

Lógica pura — sin Streamlit, sin imports pesados. Solo re, datetime.
"""

import re
from datetime import date, datetime, timedelta

# ─── Mapeo de meses en español ───
_MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

_MESES_PATTERN = "|".join(_MESES.keys())

_CANCEL_KEYWORDS = [
    "cancelar", "cancelo", "no quiero", "olvidalo", "olvídalo",
    "dejalo", "déjalo", "mejor no", "no importa", "nada",
]

# ─── Preprocesamiento para destino ───
_SKIP_PHRASES = re.compile(
    r"\bpara\s+(?:mi|mí|nosotros|nosotras|él|ella|ellos|ellas|ti)\b",
    re.IGNORECASE,
)


def _preprocess_for_dest(msg: str) -> str:
    """Remueve frases como 'para mi/nosotros' para simplificar extracción."""
    result = _SKIP_PHRASES.sub("", msg)
    return re.sub(r"\s+", " ", result).strip()


# ─── Regex para destino ───
_DEST_PATTERNS = [
    # "viajar a París", "ir para Roma", "escapada a Barcelona", "viaje a/para X"
    r"(?:viajar|ir|escapada|vacaciones|visitar|conocer|viaje)\s+(?:a|para|hacia)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?)(?:\s+(?:del|en|desde|entre|el|para|por|con)\s+|\s*$)",
    # "planear viaje a X", "crear viaje a/para X", "armar viaje a X"
    r"(?:planear|planificar|organizar|crear|crea|armar|hacer|haz)\s+(?:un\s+)?(?:viaje|vacaciones|escapada|plan)\s+(?:a|para|hacia)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?)(?:\s+(?:del|en|desde|entre|el|para|por|con)\s+|\s*$)",
    # Fallback: keyword + "a/para" + destino al final
    r"(?:viajar|ir|escapada|vacaciones|viaje|visitar|conocer)\s+(?:a|para|hacia)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+?)$",
]

# ─── Regex para fechas ───

# Rangos cruzados (mes diferente) — unifica del/desde/entre + al/hasta/y
# "del 12 de abril al 5 de mayo", "desde el 12 de abril al 5 de mayo",
# "desde el 12 de abril hasta el 5 de mayo", "entre el 12 de abril y el 5 de mayo"
_DATE_RANGE_CROSS_MONTH = re.compile(
    rf"(?:del|desde(?:\s+el)?|entre(?:\s+el)?)\s+"
    rf"(\d{{1,2}})\s+de\s+({_MESES_PATTERN})\s+"
    rf"(?:al|hasta(?:\s+el)?|y(?:\s+el)?)\s+"
    rf"(\d{{1,2}})\s+de\s+({_MESES_PATTERN})"
    rf"(?:\s+(?:de\s+|del\s+)?(\d{{4}}))?",
    re.IGNORECASE,
)

# Rangos mismo mes — unifica del/desde/entre + al/hasta/y
# "del 15 al 22 de junio", "desde el 15 al 22 de junio", "entre el 15 y el 22 de junio"
_DATE_RANGE_SAME_MONTH = re.compile(
    rf"(?:del|desde(?:\s+el)?|entre(?:\s+el)?)\s+"
    rf"(\d{{1,2}})\s+"
    rf"(?:al|hasta(?:\s+el)?|y(?:\s+el)?)\s+"
    rf"(\d{{1,2}})\s+de\s+({_MESES_PATTERN})"
    rf"(?:\s+(?:de\s+|del\s+)?(\d{{4}}))?",
    re.IGNORECASE,
)

# "en junio" → semana por defecto (1-7 del mes)
_DATE_MONTH_ONLY = re.compile(
    rf"\ben\s+({_MESES_PATTERN})(?:\s+(?:de\s+|del\s+)?(\d{{4}}))?",
    re.IGNORECASE,
)

# Formato ISO: YYYY-MM-DD
_DATE_ISO = re.compile(
    r"(\d{4})-(\d{1,2})-(\d{1,2})"
)

# Formato numérico: "15/06/2026" o "15-06-2026" (DD/MM/YYYY)
_DATE_NUMERIC = re.compile(
    r"(\d{1,2})[/](\d{1,2})[/](\d{4})"
)

# Fecha individual con nombre de mes: "el 15 de junio", "5 de mayo", "para el 15 de junio"
_DATE_SINGLE = re.compile(
    rf"(?:para\s+)?(?:el\s+)?(\d{{1,2}})\s+de\s+({_MESES_PATTERN})"
    rf"(?:\s+(?:de\s+|del\s+)?(\d{{4}}))?",
    re.IGNORECASE,
)


def _infer_year(month: int) -> int:
    """Infiere el año: si el mes ya pasó, usa el año siguiente."""
    today = date.today()
    if month < today.month:
        return today.year + 1
    if month == today.month and today.day > 15:
        return today.year + 1
    return today.year


def _parse_date(day: int, month_name: str, year_str: str = None) -> str:
    """Convierte día, nombre de mes y año opcional a ISO string."""
    month = _MESES.get(month_name.lower())
    if not month:
        return None
    year = int(year_str) if year_str else _infer_year(month)
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def detect_cancel_intent(msg: str) -> bool:
    """Detecta si el usuario quiere cancelar el flujo de creación."""
    lower = msg.lower().strip()
    return any(kw in lower for kw in _CANCEL_KEYWORDS)


def extract_trip_data(msg: str, current_draft: dict = None) -> dict:
    """Extrae destino y fechas del mensaje. Combina con draft existente.

    Retorna dict con los campos encontrados (destination, start_date, end_date).
    """
    draft = dict(current_draft) if current_draft else {}
    lower = msg.lower().strip()

    # ─── Extraer destino ───
    if not draft.get("destination"):
        # Preprocesar: remover "para mi/nosotros" para simplificar
        preprocessed = _preprocess_for_dest(lower)

        for pattern in _DEST_PATTERNS:
            m = re.search(pattern, preprocessed)
            if m:
                draft["destination"] = m.group(1).strip().title()
                break

        # Fallback: si hay draft activo (step=collecting) y no se encontró patrón,
        # el mensaje podría ser solo el nombre del destino (ej: "Barcelona")
        if not draft.get("destination") and current_draft and current_draft.get("step") == "collecting":
            clean = lower.strip().strip(".,!?¿")
            # Solo aceptar si es corto (<=4 palabras), sin números ni meses
            if clean and len(clean.split()) <= 4 and not re.search(r"\d", clean) and not any(
                m in clean for m in _MESES.keys()
            ):
                draft["destination"] = clean.title()

    # ─── Extraer fechas ───
    dates_found = _extract_dates(lower)

    if dates_found.get("start_date") and dates_found.get("end_date"):
        # Rango completo extraído
        if not draft.get("start_date"):
            draft["start_date"] = dates_found["start_date"]
        if not draft.get("end_date"):
            draft["end_date"] = dates_found["end_date"]
    elif dates_found.get("start_date"):
        # Fecha individual extraída
        if not draft.get("start_date"):
            draft["start_date"] = dates_found["start_date"]
        elif not draft.get("end_date"):
            # start_date ya existe → tratar la nueva fecha como end_date
            draft["end_date"] = dates_found["start_date"]

    return draft


def _extract_dates(msg: str) -> dict:
    """Extrae start_date y end_date del mensaje."""
    result = {}

    # 1. Rango cruzado (más específico): "del 12 de abril al 5 de mayo"
    m = _DATE_RANGE_CROSS_MONTH.search(msg)
    if m:
        day1, month1, day2, month2 = int(m.group(1)), m.group(2), int(m.group(3)), m.group(4)
        year_str = m.group(5)
        result["start_date"] = _parse_date(day1, month1, year_str)
        result["end_date"] = _parse_date(day2, month2, year_str)
        return result

    # 2. Rango mismo mes: "del 15 al 22 de junio"
    m = _DATE_RANGE_SAME_MONTH.search(msg)
    if m:
        day1, day2, month_name = int(m.group(1)), int(m.group(2)), m.group(3)
        year_str = m.group(4)
        result["start_date"] = _parse_date(day1, month_name, year_str)
        result["end_date"] = _parse_date(day2, month_name, year_str)
        return result

    # 3. Solo mes: "en junio" → 1-7 del mes
    m = _DATE_MONTH_ONLY.search(msg)
    if m:
        month_name = m.group(1)
        year_str = m.group(2)
        result["start_date"] = _parse_date(1, month_name, year_str)
        result["end_date"] = _parse_date(7, month_name, year_str)
        return result

    # 4. Fechas ISO: YYYY-MM-DD
    iso_dates = _DATE_ISO.findall(msg)
    if len(iso_dates) >= 2:
        y1, m1, d1 = iso_dates[0]
        y2, m2, d2 = iso_dates[1]
        try:
            result["start_date"] = date(int(y1), int(m1), int(d1)).isoformat()
            result["end_date"] = date(int(y2), int(m2), int(d2)).isoformat()
        except ValueError:
            pass
        return result
    elif len(iso_dates) == 1:
        y1, m1, d1 = iso_dates[0]
        try:
            result["start_date"] = date(int(y1), int(m1), int(d1)).isoformat()
        except ValueError:
            pass
        return result

    # 5. Fechas numéricas DD/MM/YYYY
    numeric_dates = _DATE_NUMERIC.findall(msg)
    if len(numeric_dates) >= 2:
        d1, m1, y1 = numeric_dates[0]
        d2, m2, y2 = numeric_dates[1]
        try:
            result["start_date"] = date(int(y1), int(m1), int(d1)).isoformat()
            result["end_date"] = date(int(y2), int(m2), int(d2)).isoformat()
        except ValueError:
            pass
        return result
    elif len(numeric_dates) == 1:
        d1, m1, y1 = numeric_dates[0]
        try:
            result["start_date"] = date(int(y1), int(m1), int(d1)).isoformat()
        except ValueError:
            pass
        return result

    # 6. Fechas individuales con nombre de mes (findall para captar varias)
    single_matches = _DATE_SINGLE.findall(msg)
    if len(single_matches) >= 2:
        d1, m1, y1 = single_matches[0]
        d2, m2, y2 = single_matches[1]
        result["start_date"] = _parse_date(int(d1), m1, y1 or None)
        result["end_date"] = _parse_date(int(d2), m2, y2 or None)
        return result
    elif len(single_matches) == 1:
        d1, m1, y1 = single_matches[0]
        result["start_date"] = _parse_date(int(d1), m1, y1 or None)
        return result

    return result


def get_missing_fields(draft: dict) -> list:
    """Retorna lista de campos requeridos faltantes."""
    missing = []
    if not draft.get("destination"):
        missing.append("destination")
    if not draft.get("start_date"):
        missing.append("start_date")
    if not draft.get("end_date"):
        missing.append("end_date")
    return missing


def build_prompt_for_missing(draft: dict, missing: list) -> str:
    """Genera mensaje para pedir datos faltantes al usuario."""
    if "destination" in missing:
        return "¿A dónde te gustaría viajar?"

    dest = draft.get("destination", "")

    if "start_date" in missing and "end_date" in missing:
        return f"Genial, viaje a **{dest}**. ¿En qué fechas te gustaría ir?"

    if "start_date" in missing:
        return f"¿Desde qué fecha te gustaría viajar a **{dest}**?"

    if "end_date" in missing:
        start = draft.get("start_date", "")
        return f"Tienes el inicio el **{start}**. ¿Hasta qué fecha sería el viaje a **{dest}**?"

    return ""


def validate_dates(start_str: str, end_str: str) -> tuple:
    """Valida que las fechas sean coherentes.

    Retorna (is_valid, error_message).
    """
    try:
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
    except (ValueError, TypeError):
        return False, "Las fechas no tienen un formato válido. Usa formato DD/MM/AAAA o 'del X al Y de mes'."

    if end <= start:
        return False, "La fecha de fin debe ser posterior a la de inicio. ¿Podrías corregir las fechas?"

    if start < date.today():
        return False, "La fecha de inicio ya pasó. ¿Podrías indicar fechas futuras?"

    return True, ""


def build_confirmation_data(draft: dict) -> dict:
    """Construye el dict de confirmación con datos completos del viaje."""
    dest = draft.get("destination", "Sin destino")
    name = draft.get("name") or f"Viaje a {dest}"
    start = draft.get("start_date", "")
    end = draft.get("end_date", "")

    return {
        "role": "assistant",
        "type": "confirmation",
        "content": {
            "action": "create_trip",
            "summary": f"Crear nuevo viaje a {dest}",
            "details": {
                "destination": dest,
                "name": name,
                "start_date": start,
                "end_date": end,
            },
        },
    }


def new_draft(destination=None, start_date=None, end_date=None) -> dict:
    """Crea un nuevo borrador de viaje."""
    return {
        "destination": destination,
        "name": None,
        "start_date": start_date,
        "end_date": end_date,
        "step": "collecting",
    }
