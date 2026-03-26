"""Extraccion inteligente de items usando LLM structured output (OpenAI).

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
            "'create_trip' (crear un viaje NUEVO a un destino — sin datos de dia/hora concretos), "
            "'calendar_event' (agregar viaje completo al cronograma/calendario), "
            "'remove_item' (eliminar item existente), "
            "'hotel_search' (buscar hoteles/hospedaje — NO es agregar item tipo alojamiento), "
            "'flight_search' (buscar vuelos/pasajes/avion — NO es agregar item tipo vuelo con datos concretos), "
            "'informative' (pregunta informativa, no modifica itinerario), "
            "'unknown' (no se puede determinar)"
        )
    )
    name: Optional[str] = Field(
        default=None,
        description="Nombre descriptivo de la actividad, item o gasto (limpio, sin datos temporales ni de costo). Tambien se usa para identificar gastos en modify_expense y remove_expense.",
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
    # ─── Campos para intent remove_item ───
    remove_item_ids: List[str] = Field(
        default_factory=list,
        description=(
            "IDs de items a eliminar (solo para intent 'remove_item'). "
            "Usa los IDs exactos del listado de ITEMS EXISTENTES."
        ),
    )
    remove_all: bool = Field(
        default=False,
        description=(
            "True si el usuario quiere eliminar TODOS los items del itinerario "
            "(solo para intent 'remove_item')"
        ),
    )
    remove_summary: Optional[str] = Field(
        default=None,
        description=(
            "Resumen legible de lo que se va a eliminar, en español. "
            "Ej: 'Todas las actividades del dia 2', 'La cena del dia 3'. "
            "(solo para intent 'remove_item')"
        ),
    )
    # ─── Campo para intent create_trip ───
    trip_destination: Optional[str] = Field(
        default=None,
        description=(
            "Destino del nuevo viaje (solo para intent 'create_trip'). "
            "Ej: 'Japon', 'Roma', 'Cancun'"
        ),
    )
    # ─── Campos para intents de gastos (expenses) ───
    expense_category: Optional[str] = Field(
        default=None,
        description=(
            "Categoria del gasto para presupuesto (solo para intents de expense). "
            "Valores: 'vuelos', 'alojamiento', 'actividades', 'comidas', 'transporte_local', 'extras'"
        ),
    )
    expense_id: Optional[str] = Field(
        default=None,
        description=(
            "ID del gasto a modificar o eliminar (solo para 'modify_expense' y 'remove_expense'). "
            "Usa los IDs exactos del listado de GASTOS EXISTENTES."
        ),
    )
    expense_amount: Optional[float] = Field(
        default=None,
        description="Monto del gasto en USD (solo para intents de expense)",
    )
    remove_all_expenses: bool = Field(
        default=False,
        description=(
            "True si el usuario quiere eliminar TODOS los gastos del presupuesto "
            "(solo para intent 'remove_expense'). Ej: 'elimina todos los gastos', 'borra los gastos del viaje'"
        ),
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

{existing_expenses_context}

{partial_draft_context}

INSTRUCCIONES:

1. DETECTA LA INTENCION del mensaje analizando el significado semantico (NO busques keywords especificas — entiende la intencion del usuario sin importar el idioma o las palabras exactas que use):
   - "add_item": el usuario quiere agregar una actividad, comida, vuelo, traslado u otro item concreto al itinerario (tiene o puede completar datos como nombre, dia, hora)
   - "create_trip": el usuario quiere crear un VIAJE NUEVO a un destino. Habla de un destino/lugar sin datos concretos de itinerario (sin dia, sin hora). Ej: "quiero ir a Japon", "planifiquemos un viaje a Roma"
   - "calendar_event": el usuario quiere agregar el viaje completo como bloque al cronograma o calendario (no un item individual, sino el viaje entero como evento)
   - "remove_item": el usuario quiere eliminar o quitar uno, varios o TODOS los items existentes del itinerario. Analiza cuales items matchean con lo que pide el usuario
   - "hotel_search": el usuario quiere explorar opciones de hospedaje — buscar hoteles, ver donde dormir. Esto NO es agregar un item tipo alojamiento con datos concretos
   - "flight_search": el usuario quiere buscar vuelos, pasajes de avion, comparar precios de vuelos, ver opciones de aerolineas. Esto NO es agregar un item tipo vuelo con datos concretos de dia y hora
   - "add_expense": el usuario quiere registrar un gasto/costo al presupuesto del viaje que NO es un item del itinerario. Ej: "me compré los pasajes por 500 dólares", "pagué el seguro de viaje", "gasté 200 en souvenirs"
   - "modify_expense": el usuario quiere cambiar el monto, nombre o categoría de un gasto ya registrado
   - "remove_expense": el usuario quiere eliminar un gasto registrado del presupuesto
   - "informative": el usuario hace una pregunta informativa o conversacional, NO quiere modificar el itinerario
   - "unknown": no se puede determinar la intencion

REGLA DE PRIORIDAD (aplicar ANTES de cualquier otra):
- Si el mensaje contiene CUALQUIER indicador temporal concreto (dia, hora, "primer dia", "manana", "por la tarde", "a las 7am", etc.) junto con una actividad o lugar → SIEMPRE es add_item, sin importar que empiece con "quiero ir a"
- Ejemplo: "quiero ir a pasear por la rambla el primer dia a las 7am" → add_item (tiene dia + hora + actividad concreta)
- Solo es create_trip si habla UNICAMENTE de un destino de viaje (pais/ciudad) sin NINGUN dato temporal

REGLA CRITICA — CLASIFICACION INDEPENDIENTE:
- Clasifica SIEMPRE el intent basandote UNICAMENTE en el ULTIMO mensaje del usuario (el mensaje actual)
- El historial de chat sirve SOLO para recuperar datos concretos (nombres, dias, horas) si el usuario hace referencia ("lo que te dije", "el paseo que mencionamos")
- NUNCA dejes que el tema de mensajes anteriores influya en la clasificacion del intent actual
- Si el historial habla de vuelos pero el usuario ahora pregunta por hoteles → hotel_search (NO flight_search)
- Si el historial habla de hoteles pero el usuario ahora quiere agregar una cena → add_item (NO hotel_search)
- Cada mensaje se clasifica POR SU PROPIO CONTENIDO SEMANTICO, independientemente del contexto previo

IMPORTANTE sobre create_trip vs add_item:
- Si el mensaje contiene indicadores de dia/hora/posicion en itinerario → add_item (es un item concreto para el viaje actual)
- "agrega viaje a Cristo Redentor el dia 1 a las 7am" → add_item (tiene dia y hora, es un item del itinerario)
- "quiero ir a Japon" → create_trip (habla de destino sin datos de itinerario)
- "planifiquemos vacaciones en Cancun" → create_trip
- Si habla de destino sin datos de itinerario → create_trip
- Si hay un viaje activo y el mensaje parece referirse a una actividad del viaje actual → add_item

IMPORTANTE sobre hotel_search vs add_item:
- Quiere explorar opciones de hospedaje sin datos concretos → hotel_search
- Quiere agregar un alojamiento especifico con datos concretos (nombre, dia, hora) → add_item

IMPORTANTE sobre flight_search vs add_item:
- Quiere buscar/explorar/comparar vuelos sin datos concretos de dia/hora en el itinerario → flight_search
- Quiere agregar un vuelo especifico con dia, hora, aerolinea concretos al itinerario → add_item

IMPORTANTE sobre add_expense vs add_item:
- Si el usuario habla de un GASTO o COSTO sin datos de itinerario (dia, hora) → add_expense (es un costo para el presupuesto)
- "me compré los pasajes por 500 dolares" → add_expense (gasto sin dia/hora concretos)
- "pagué 200 del hotel" → add_expense
- "agrega un vuelo el dia 1 a las 8am por 500 dolares" → add_item (tiene dia + hora, es item del itinerario)
- Si tiene indicadores temporales concretos (dia, hora) → add_item
- Si solo habla de dinero/costo sin posicionarlo en el itinerario → add_expense

IMPORTANTE sobre remove_item vs remove_expense:
- Si el usuario menciona "gasto", "gastos", "presupuesto", "costo" → remove_expense (quiere eliminar del presupuesto)
- Si el nombre coincide con un GASTO EXISTENTE (por nombre o categoria) → remove_expense
- Si el nombre coincide con un ITEM EXISTENTE del itinerario → remove_item
- "elimina el gasto de comida" → remove_expense
- "elimina todos los gastos" / "borra los gastos del viaje" → remove_expense con remove_all_expenses=True
- "elimina la cena del dia 2" → remove_item (es un item del itinerario)
- "elimina el transporte local" → remove_expense SI hay un gasto con categoria transporte_local o nombre similar en GASTOS EXISTENTES
- En caso de duda, revisa si lo que pide el usuario existe en GASTOS EXISTENTES o en ITEMS EXISTENTES para decidir

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

3. Si la intencion es "remove_item", IDENTIFICA los items a eliminar:
   - Revisa la lista de ITEMS EXISTENTES con sus IDs entre corchetes [item-XXXXXXXX]
   - remove_item_ids: lista de IDs exactos de los items que el usuario quiere eliminar
   - remove_all: True SOLO si el usuario explicitamente quiere eliminar TODOS los items (ej: "elimina todo", "borra todos los items", "limpia el itinerario")
   - remove_summary: descripcion legible de lo que se eliminara (ej: "Cena en restaurante italiano del dia 2", "Todos los items del dia 3", "Todos los items del itinerario")
   - Si remove_all es True, pon TODOS los IDs de items existentes en remove_item_ids
   - Interpreta semanticamente: "elimina las comidas" → todos los items tipo comida. "elimina todo del dia 2" → todos los items del dia 2. "elimina la cena" → el item de comida que sea una cena
   - Si NO encuentras items que coincidan con lo que pide el usuario, deja remove_item_ids vacio y pon en remove_summary una explicacion (ej: "No se encontraron items que coincidan")

4. Si la intencion es "add_expense", "modify_expense" o "remove_expense":
   - expense_category: infiere la categoria del contexto:
     * pasajes/vuelos/avion → "vuelos"
     * hotel/hospedaje/airbnb → "alojamiento"
     * tour/entrada/actividad/excursion → "actividades"
     * comida/restaurante/cena → "comidas"
     * taxi/uber/transporte/bus → "transporte_local"
     * seguro/equipaje/compras/souvenir/otro → "extras"
   - Para add_expense: extrae name (nombre DESCRIPTIVO del gasto, NO la categoria — ej: "Pasajes aereos", "Seguro de viaje", "Comida en el aeropuerto". Si el usuario no da un nombre concreto, genera uno descriptivo basado en el contexto) y expense_amount (monto en USD)
   - Para modify_expense: identifica el gasto por expense_id de la lista de GASTOS EXISTENTES. SIEMPRE incluye tambien el name del gasto como fallback. Extrae los campos a cambiar (name, expense_amount, expense_category)
   - Para remove_expense: identifica el gasto por expense_id de la lista de GASTOS EXISTENTES. SIEMPRE incluye tambien el name del gasto como fallback para identificarlo. Si el usuario dice "el gasto de comida", pon name="Gasto en comida" o similar basandote en los GASTOS EXISTENTES. Si el usuario quiere eliminar TODOS los gastos ("elimina los gastos", "borra todos los gastos"), pon remove_all_expenses=True

5. EVALUA COMPLETITUD:
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
    """Formatea los items existentes del viaje para contexto del LLM.

    Incluye el ID de cada item para que el LLM pueda referenciarlos
    en operaciones de eliminacion (remove_item_ids).
    """
    items = trip.get("items", [])
    if not items:
        return "ITEMS EXISTENTES: ninguno"

    lines = ["ITEMS EXISTENTES (formato: [ID] Nombre (tipo) | Dia | Horario):"]
    for item in items:
        item_id = item.get("id", "?")
        end_day = item.get("end_day")
        day_str = f"Dia {item.get('day', '?')}"
        if end_day and end_day > item.get("day", 0):
            day_str = f"Dias {item.get('day')}-{end_day}"
        lines.append(
            f"- [{item_id}] {item.get('name', '?')} ({item.get('item_type', '?')}) | "
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
_VALID_INTENTS = {"add_item", "create_trip", "calendar_event", "remove_item", "hotel_search", "flight_search", "add_expense", "modify_expense", "remove_expense", "informative", "unknown"}
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

    # Validar campos de remove_item
    if result.intent == "remove_item":
        existing_ids = {item.get("id") for item in trip.get("items", [])}
        # Filtrar IDs que no existen en el viaje
        result.remove_item_ids = [
            rid for rid in result.remove_item_ids if rid in existing_ids
        ]
        # Si remove_all, asegurar que incluya todos los IDs
        if result.remove_all and existing_ids:
            result.remove_item_ids = list(existing_ids)
    else:
        # Limpiar campos de remove si el intent no es remove_item
        result.remove_item_ids = []
        result.remove_all = False
        result.remove_summary = None

    # Limpiar trip_destination si el intent no es create_trip
    if result.intent != "create_trip":
        result.trip_destination = None

    # Validar expense_category
    _VALID_EXPENSE_CATEGORIES = {"vuelos", "alojamiento", "actividades", "comidas", "transporte_local", "extras"}
    if result.expense_category and result.expense_category not in _VALID_EXPENSE_CATEGORIES:
        result.expense_category = "extras"

    # Limpiar campos de expense si el intent no es de expense
    if result.intent not in ("add_expense", "modify_expense", "remove_expense"):
        result.expense_category = None
        result.expense_id = None
        result.expense_amount = None
        result.remove_all_expenses = False

    # Validar expense_amount no negativo
    if result.expense_amount is not None and result.expense_amount < 0:
        result.expense_amount = None

    # Validar expense_id existe (para modify/remove)
    if result.intent in ("modify_expense", "remove_expense") and result.expense_id:
        existing_expense_ids = {exp.get("id") for exp in trip.get("expenses", [])}
        if result.expense_id not in existing_expense_ids:
            result.expense_id = None

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


# ─── Helper para formatear historial de chat ───

def _format_chat_history(messages: Optional[list], max_messages: int = 6) -> list:
    """Formatea mensajes recientes del chat como historial para el LLM.

    Solo incluye mensajes type=="text" con content string (excluye cards,
    confirmaciones, hotel_results cuyos content son dicts).
    Retorna los ultimos max_messages (~3 pares user/assistant).
    """
    if not messages:
        return []
    text_msgs = [
        m for m in messages
        if m.get("type") == "text" and isinstance(m.get("content"), str)
    ]
    recent = text_msgs[-max_messages:]
    return [{"role": m["role"], "content": m["content"]} for m in recent]


# ─── Funcion principal de extraccion ───

def extract_item_with_llm(
    message: str,
    trip: dict,
    partial_draft: Optional[dict] = None,
    chat_history: Optional[list] = None,
) -> Optional[ItemExtractionResult]:
    """Extrae datos de item usando LLM structured output.

    Args:
        message: Mensaje del usuario
        trip: Dict del viaje activo (con items, fechas, destino)
        partial_draft: Borrador parcial de item (flujo multi-turn)
        chat_history: Lista de mensajes previos del chat (sin el mensaje actual)

    Returns:
        ItemExtractionResult con datos extraidos, o None si hay error.
    """
    try:
        llm = _get_extraction_llm()
        structured_llm = llm.with_structured_output(ItemExtractionResult)

        total_days = _calculate_total_days(trip)

        try:
            from services.expense_service import format_existing_expenses
            expenses_context = format_existing_expenses(trip)
        except ImportError:
            expenses_context = "GASTOS EXISTENTES: ninguno"

        system_prompt = EXTRACTION_SYSTEM_PROMPT.format(
            destination=trip.get("destination", "No definido"),
            start_date=trip.get("start_date", "No definida"),
            end_date=trip.get("end_date", "No definida"),
            total_days=total_days,
            today=date.today().isoformat(),
            existing_items_context=_format_existing_items(trip),
            existing_expenses_context=expenses_context,
            partial_draft_context=_format_partial_draft(partial_draft),
        )

        history_msgs = _format_chat_history(chat_history)
        messages = [
            {"role": "system", "content": system_prompt},
            *history_msgs,
            {"role": "user", "content": message},
        ]

        result = structured_llm.invoke(messages)

        # Post-validacion defensiva
        result = _post_validate(result, trip, partial_draft)

        logger.info(
            "[llm_extraction] intent=%s, name=%s, day=%s, type=%s, complete=%s, "
            "remove_ids=%s, remove_all=%s",
            result.intent, result.name, result.day, result.item_type, result.is_complete,
            result.remove_item_ids, result.remove_all,
        )

        return result

    except Exception as e:
        logger.warning("Error en extraccion LLM: %s", e)
        return None
