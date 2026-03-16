"""Extraccion inteligente de items usando LLM structured output (OpenAI gpt-4.1-nano).

Reemplaza la logica regex de item_extraction.py cuando OPENAI_API_KEY esta disponible.
Usa ChatOpenAI.with_structured_output() con schema Pydantic para obtener datos
estructurados del mensaje del usuario en una sola llamada.
"""

import re
import logging
from datetime import date, timedelta
from typing import Optional, List

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from config.llm_config import DEFAULT_MODEL, EXTRACTION_TEMPERATURE

logger = logging.getLogger(__name__)


# ─── Schema Pydantic para structured output ───

class ItemExtractionResult(BaseModel):
    """Resultado de la extraccion LLM de un item del itinerario."""
    intent: str = Field(
        description=(
            "Intencion detectada: 'add_item' (agregar actividad/item al itinerario), "
            "'calendar_event' (agregar viaje completo al cronograma/calendario), "
            "'remove_item' (eliminar item existente), "
            "'hotel_search' (buscar hoteles/hospedaje — NO es agregar item tipo alojamiento), "
            "'informative' (pregunta informativa, no modifica itinerario), "
            "'unknown' (no se puede determinar)"
        )
    )
    name: Optional[str] = Field(
        default=None,
        description="Nombre descriptivo de la actividad/item (limpio, sin datos temporales ni de costo)",
    )
    day: Optional[int] = Field(
        default=None,
        description="Dia relativo del viaje (1-based). Ej: dia 1 = primer dia del viaje",
    )
    start_time: Optional[str] = Field(
        default=None,
        description="Hora de inicio en formato HH:MM (24 horas)",
    )
    end_time: Optional[str] = Field(
        default=None,
        description="Hora de fin en formato HH:MM (24 horas). Solo si se menciona explicitamente",
    )
    item_type: Optional[str] = Field(
        default=None,
        description="Tipo de item: 'actividad', 'comida', 'vuelo', 'traslado', 'alojamiento', 'extra'",
    )
    location: Optional[str] = Field(
        default=None,
        description="Ubicacion o lugar especifico mencionado",
    )
    cost: Optional[float] = Field(
        default=None,
        description="Costo estimado en USD si se menciona",
    )
    is_complete: bool = Field(
        default=False,
        description="True si se tienen los datos minimos requeridos (nombre Y dia)",
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="Campos minimos faltantes: 'name', 'day'",
    )
    follow_up_question: Optional[str] = Field(
        default=None,
        description="Pregunta al usuario para obtener datos faltantes (en español, natural)",
    )


# ─── Singleton ChatOpenAI para extraccion ───

_extraction_llm: Optional[ChatOpenAI] = None


def _get_extraction_llm() -> ChatOpenAI:
    """Obtiene o crea el singleton de ChatOpenAI para extraccion."""
    global _extraction_llm
    if _extraction_llm is None:
        _extraction_llm = ChatOpenAI(
            model=DEFAULT_MODEL,
            temperature=EXTRACTION_TEMPERATURE,
        )
    return _extraction_llm


# ─── System prompt para extraccion ───

EXTRACTION_SYSTEM_PROMPT = """Eres un extractor de datos para items de itinerario de viaje. Tu trabajo es analizar el mensaje del usuario y extraer informacion estructurada.

CONTEXTO DEL VIAJE:
- Destino: {destination}
- Fechas: {start_date} a {end_date} ({total_days} dias)
- Fecha de hoy: {today}

{existing_items_context}

{partial_draft_context}

INSTRUCCIONES:

1. DETECTA LA INTENCION del mensaje analizando el significado semantico (NO busques keywords especificas — entiende la intencion del usuario sin importar el idioma o las palabras exactas que use):
   - "add_item": el usuario quiere agregar una actividad, comida, vuelo, traslado u otro item concreto al itinerario (tiene o puede completar datos como nombre, dia, hora)
   - "calendar_event": el usuario quiere agregar el viaje completo como bloque al cronograma o calendario (no un item individual, sino el viaje entero como evento)
   - "remove_item": el usuario quiere eliminar o quitar un item existente del itinerario
   - "hotel_search": el usuario quiere explorar opciones de hospedaje — buscar hoteles, ver donde dormir. Esto NO es agregar un item tipo alojamiento con datos concretos
   - "informative": el usuario hace una pregunta informativa o conversacional, NO quiere modificar el itinerario
   - "unknown": no se puede determinar la intencion

IMPORTANTE sobre hotel_search vs add_item:
- Quiere explorar opciones de hospedaje sin datos concretos → hotel_search
- Quiere agregar un alojamiento especifico con datos concretos (nombre, dia, hora) → add_item

2. Si la intencion es "add_item", EXTRAE estos campos:
   - name: nombre descriptivo de la actividad (limpio, sin datos temporales ni de costo). Ej: "Cena en restaurante italiano", "Tour por el centro historico"
   - day: dia relativo del viaje (1 = primer dia). Convierte referencias a dia relativo:
     * "dia 3" → 3
     * "el tercer dia" → 3
     * "ultimo dia" → {total_days}
     * "penultimo dia" → {total_days} - 1
     * Fecha absoluta "15 de abril": calcula diferencia con start_date + 1
     * "mañana": calcula (fecha_de_mañana - start_date).days + 1
   - start_time: hora de inicio en HH:MM (24h). Interpreta:
     * "por la mañana" → 09:00, "mediodia" → 12:00, "por la tarde" → 15:00, "por la noche" → 20:00
     * "8 de la noche" → 20:00, "3 de la tarde" → 15:00
   - end_time: hora de fin en HH:MM SOLO si se menciona explicitamente (ej: "de 16:30 a 19:30"). NO inventes end_time
   - item_type: infiere del contexto:
     * restaurante/cena/almuerzo/desayuno/brunch → "comida"
     * hotel/hospedaje/airbnb/hostel/check-in → "alojamiento"
     * vuelo/avion/aeropuerto → "vuelo"
     * taxi/uber/bus/traslado/transfer/metro/tren → "traslado"
     * seguro/equipaje/compras/souvenir → "extra"
     * cualquier otra actividad → "actividad"
   - location: lugar especifico si se menciona (ej: "en el centro", "en la Torre Eiffel")
   - cost: costo en USD si se menciona (busca "$", "dolares", "usd", "cuesta", "por X dolares")

3. EVALUA COMPLETITUD:
   - is_complete = True si tienes al menos name Y day
   - missing_fields: lista de campos faltantes entre "name" y "day"
   - follow_up_question: pregunta natural en español para pedir lo que falta. Ejemplos:
     * Falta name y day: "¿Que actividad quieres agregar y en que dia de tu viaje?"
     * Falta name: "¿Que actividad quieres agregar para el dia X?"
     * Falta day: "¿En que dia de tu viaje quieres programar 'nombre'?"

REGLAS CRITICAS:
- Responde SOLO con datos presentes en el mensaje o inferibles con certeza
- NO inventes datos que no estan en el mensaje
- Los dias deben ser entre 1 y {total_days}
- Las horas en formato HH:MM (24 horas, dos digitos cada campo)
- item_type debe ser exactamente uno de: actividad, comida, vuelo, traslado, alojamiento, extra
- Si el usuario da un rango horario ("de 16:30 a 19:30"), extrae AMBOS start_time Y end_time
- Si hay un BORRADOR PARCIAL, el usuario esta en medio de agregar un item. Interpreta su mensaje como datos para completar el borrador. El intent deberia ser "add_item" a menos que el usuario explicitamente cancele o pregunte algo diferente.
- No sobreescribas datos del borrador que el usuario no menciona en este mensaje.
"""


# ─── Helpers de formato ───

def _format_existing_items(trip: dict) -> str:
    """Formatea los items existentes del viaje para contexto del LLM."""
    items = trip.get("items", [])
    if not items:
        return "ITEMS EXISTENTES: ninguno"

    lines = ["ITEMS EXISTENTES:"]
    for item in items:
        end_day = item.get("end_day")
        day_str = f"Dia {item.get('day', '?')}"
        if end_day and end_day > item.get("day", 0):
            day_str = f"Dias {item.get('day')}-{end_day}"
        lines.append(
            f"- {item.get('name', '?')} ({item.get('item_type', '?')}) | "
            f"{day_str} | {item.get('start_time', '?')}-{item.get('end_time', '?')}"
        )
    return "\n".join(lines)


def _format_partial_draft(draft: Optional[dict]) -> str:
    """Formatea el borrador parcial para contexto del LLM."""
    if not draft:
        return ""

    parts = ["BORRADOR PARCIAL (datos ya recopilados):"]
    if draft.get("name"):
        parts.append(f"- Nombre: {draft['name']}")
    if draft.get("day"):
        parts.append(f"- Dia: {draft['day']}")
    if draft.get("start_time"):
        parts.append(f"- Hora inicio: {draft['start_time']}")
    if draft.get("end_time"):
        parts.append(f"- Hora fin: {draft['end_time']}")
    if draft.get("item_type"):
        parts.append(f"- Tipo: {draft['item_type']}")
    if draft.get("location"):
        parts.append(f"- Ubicacion: {draft['location']}")
    if draft.get("cost_estimated") and draft["cost_estimated"] > 0:
        parts.append(f"- Costo: ${draft['cost_estimated']}")

    if len(parts) == 1:
        return ""

    parts.append(
        "\nCOMPLEMENTA este borrador con los datos nuevos del mensaje. "
        "No sobreescribas datos existentes a menos que el usuario los corrija explicitamente."
    )
    return "\n".join(parts)


def _calculate_total_days(trip: dict) -> int:
    """Calcula el total de dias del viaje."""
    start_str = trip.get("start_date", "")
    end_str = trip.get("end_date", "")
    if not start_str or not end_str:
        return 7  # default razonable
    try:
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
        return max(1, (end - start).days + 1)
    except ValueError:
        return 7


# ─── Post-validacion defensiva ───

_TIME_FORMAT = re.compile(r"^\d{2}:\d{2}$")
_VALID_INTENTS = {"add_item", "calendar_event", "remove_item", "hotel_search", "informative", "unknown"}
_VALID_ITEM_TYPES = {"actividad", "comida", "vuelo", "traslado", "alojamiento", "extra"}


def _post_validate(
    result: ItemExtractionResult,
    trip: dict,
    draft: Optional[dict],
) -> ItemExtractionResult:
    """Validacion defensiva del resultado del LLM. No confiar ciegamente."""
    # Validar intent
    if result.intent not in _VALID_INTENTS:
        result.intent = "unknown"

    # Validar item_type
    if result.item_type and result.item_type not in _VALID_ITEM_TYPES:
        result.item_type = "actividad"

    # Validar day range
    total_days = _calculate_total_days(trip)
    if result.day is not None:
        if result.day < 1:
            result.day = 1
        elif result.day > total_days:
            result.day = total_days

    # Validar formato y rango de horas
    for attr in ("start_time", "end_time"):
        val = getattr(result, attr)
        if val:
            if not _TIME_FORMAT.match(val):
                setattr(result, attr, None)
                continue
            try:
                h, m = map(int, val.split(":"))
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    setattr(result, attr, None)
            except (ValueError, AttributeError):
                setattr(result, attr, None)

    # Validar cost no negativo
    if result.cost is not None and result.cost < 0:
        result.cost = None

    # Merge con draft existente (el LLM puede no repetir datos del draft)
    if draft:
        if not result.name and draft.get("name"):
            result.name = draft["name"]
        if not result.day and draft.get("day"):
            result.day = draft["day"]
        if not result.start_time and draft.get("start_time"):
            result.start_time = draft["start_time"]
        if not result.end_time and draft.get("end_time"):
            result.end_time = draft["end_time"]
        if not result.item_type and draft.get("item_type"):
            result.item_type = draft["item_type"]
        if not result.location and draft.get("location"):
            result.location = draft["location"]
        if result.cost is None and draft.get("cost_estimated") and draft["cost_estimated"] > 0:
            result.cost = draft["cost_estimated"]

    # Re-evaluar completitud despues del merge
    result.missing_fields = []
    if not result.name:
        result.missing_fields.append("name")
    if not result.day:
        result.missing_fields.append("day")
    result.is_complete = len(result.missing_fields) == 0

    # Default item_type
    if not result.item_type:
        result.item_type = "actividad"

    return result


# ─── Funcion principal de extraccion ───

def extract_item_with_llm(
    message: str,
    trip: dict,
    partial_draft: Optional[dict] = None,
) -> Optional[ItemExtractionResult]:
    """Extrae datos de item usando LLM structured output.

    Args:
        message: Mensaje del usuario
        trip: Dict del viaje activo (con items, fechas, destino)
        partial_draft: Borrador parcial de item (flujo multi-turn)

    Returns:
        ItemExtractionResult con datos extraidos, o None si hay error.
    """
    try:
        llm = _get_extraction_llm()
        structured_llm = llm.with_structured_output(ItemExtractionResult)

        total_days = _calculate_total_days(trip)

        system_prompt = EXTRACTION_SYSTEM_PROMPT.format(
            destination=trip.get("destination", "No definido"),
            start_date=trip.get("start_date", "No definida"),
            end_date=trip.get("end_date", "No definida"),
            total_days=total_days,
            today=date.today().isoformat(),
            existing_items_context=_format_existing_items(trip),
            partial_draft_context=_format_partial_draft(partial_draft),
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ]

        result = structured_llm.invoke(messages)

        # Post-validacion defensiva
        result = _post_validate(result, trip, partial_draft)

        logger.info(
            "[llm_extraction] intent=%s, name=%s, day=%s, type=%s, complete=%s",
            result.intent, result.name, result.day, result.item_type, result.is_complete,
        )

        return result

    except Exception as e:
        logger.warning("Error en extraccion LLM: %s", e)
        return None
