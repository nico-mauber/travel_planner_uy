# Plan de Implementacion — Chatbot Funcionalities (REQ-CF-001/002/003)

## 1. Contexto

Este documento describe el plan de implementacion para 3 nuevos requerimientos funcionales del chatbot del **Trip Planner**: selector obligatorio de viaje (CF-001), eventos multi-dia en cronograma (CF-002), y extraccion inteligente de items (CF-003). Los cambios extienden la funcionalidad existente del chat, cronograma y modelo de datos, manteniendo retrocompatibilidad total con el comportamiento actual.

**Alcance:** 3 requerimientos (REQ-CF-001 a REQ-CF-003)
**Prerequisitos:** Todos los requerimientos REQ-UI y REQ-CL deben estar implementados.
**Fecha de planificacion:** 2026-03-16

---

## 2. Hallazgos de Validacion Incorporados

Los siguientes hallazgos del proceso de validacion se incorporan en este plan:

| ID | Tipo | Descripcion | Resolucion |
|----|------|-------------|------------|
| CRIT-01 | Critico | CF-002 CA-002 usaba `status="pendiente"` para eventos creados | Corregido: items creados por confirmacion explicita del usuario usan `status="planificado"` (consistente con el flujo de confirmacion existente) |
| CRIT-02 | Critico | CF-003 no definia `end_time` para items creados | Resuelto: duraciones por defecto segun tipo: actividad=2h, comida=1.5h, vuelo=3h, traslado=1h, alojamiento=check-in(1h), extra=1h |
| MAY-01 | Mayor | CF-001 RN-005 (eliminar auto-deteccion) no tiene CA directo | Se verifica en CA-001/CA-006: si el selector es obligatorio y el agente rechaza preguntas de otro viaje, la auto-deteccion esta implicitamente eliminada |
| MAY-02 | Mayor | CF-001 contradice REQ-CL-004 RN-005/CA-007/CA-008 | CF-001 supersede CL-004 en la mecanica de asociacion viaje-chat. Documentar en notas de implementacion |
| MAY-03 | Mayor | CF-001 contradice REQ-UI-002 CA-010 | CF-001 supersede UI-002 CA-010. La asociacion viaje-chat pasa de implicita a explicita via selector |
| MAY-04 | Mayor | CF-002 no define visualizacion en Itinerario Detallado | Decidido: item multi-dia se muestra en Dia 1 con etiqueta "(Dias 1-N)" indicando duracion |
| MAY-05 | Mayor | CF-003 RN-007 no tiene CA de costos | Decidido: costo por defecto = 0 cuando el usuario no lo menciona. Solo se registra costo explicitamente mencionado |
| MAY-06 | Mayor | CF-002 CA-001/002 no verifican start_time/end_time | Eventos multi-dia usan `allDay: true`, los campos start_time/end_time se setean a "00:00"/"23:59" como valores nominales |

---

## 3. Hallazgos del Analisis de Codebase

| ID | Hallazgo | Impacto |
|----|----------|---------|
| COD-01 | `_find_trip_by_destination()` esta en `pages/2_Chat.py` (lineas 16-30), no en `agent_service.py` como indica el req | La eliminacion debe hacerse en `pages/2_Chat.py`, no en `agent_service.py` |
| COD-02 | `streamlit-calendar` no usa `allDay` actualmente | Verificar soporte de `allDay: true` antes de implementar CF-002 |
| COD-03 | Migracion SQL `ALTER TABLE` requiere ejecucion manual en Supabase | Crear script de migracion separado |
| COD-04 | Dos drafts multi-turn coexistirian en session_state | Disenar para que sean mutuamente excluyentes |
| COD-05 | `create_chat()` tiene `trip_id` como `Optional[str]` | Cambio de firma afecta todos los callers |
| COD-06 | Regex mock para CF-003 es significativamente mas complejo que el de `trip_creation_flow.py` | Seguir patron de `trip_creation_flow.py` pero con scope expandido |

---

## 4. Decisiones de Diseno

| # | Decision | Justificacion |
|---|----------|---------------|
| 1 | **Orden: CF-001 → CF-003 → CF-002** | CF-001 es prerequisito (selector obligatorio). CF-003 es prioridad Alta y no requiere cambios de schema. CF-002 es prioridad Media y requiere ALTER TABLE + extension del modelo |
| 2 | **Nuevo modulo `services/item_extraction.py`** | Encapsula logica de extraccion (regex/LLM), validacion, conflictos horarios y flujo multi-turn. Sigue patron de `trip_creation_flow.py`: logica pura sin Streamlit |
| 3 | **Drafts mutuamente excluyentes** | Si `_trip_creation_draft` esta activo, `_item_creation_draft` no puede iniciarse (y viceversa). El usuario debe completar o cancelar un flujo antes de iniciar otro |
| 4 | **`trip_id` sigue Optional en `create_chat()`** | En lugar de hacer `trip_id` obligatorio en la firma (breaking change), se agrega validacion en `pages/2_Chat.py` que garantiza que siempre se pasa. La firma se mantiene flexible para el flujo de "Crear nuevo viaje" |
| 5 | **Eventos multi-dia como `allDay` en FullCalendar** | Eventos con `end_day` usan `allDay: true`, `start = fecha_dia`, `end = fecha_end_day + 1 dia` (end exclusivo en FullCalendar) |
| 6 | **Color de eventos multi-dia: `#607D8B` (Blue Grey)** | Color neutro distinto de todos los tipos de item existentes, con 50% opacity para borde punteado en el calendario |
| 7 | **`end_time` calculado por duracion por defecto** | actividad=2h, comida=1.5h, vuelo=3h, traslado=1h, alojamiento=1h, extra=1h. Si `start_time + duracion > 23:59`, se trunca a "23:59" |
| 8 | **Costo por defecto = 0** | El agente solo registra costo cuando el usuario lo menciona explicitamente ("cena por 50 dolares"). Sin mencion, `cost_estimated = 0` |

---

## 5. Fases de Implementacion

### Fase 1 — REQ-CF-001: Selector Obligatorio de Viaje

**Complejidad: Alta**
**Archivos a modificar: 4 | Funciones nuevas: 2 | Funciones eliminadas: 1**

#### Paso 1.1 — Agregar `get_latest_chat_for_trip()` en `services/chat_service.py`

**Archivo:** `services/chat_service.py`
**Tipo:** Agregar funcion nueva (despues de linea 64)

```python
def get_latest_chat_for_trip(user_id: str, trip_id: str) -> Optional[dict]:
    """Obtiene el chat mas reciente para un viaje especifico."""
    from services.supabase_client import get_supabase_client

    sb = get_supabase_client()
    result = sb.table("chats").select("*").eq("user_id", user_id).eq(
        "trip_id", trip_id
    ).order("last_activity_at", desc=True).limit(1).execute()

    if not result.data:
        return None

    chat = _row_to_chat(result.data[0])
    # Cargar mensajes
    msgs_result = sb.table("chat_messages").select("*").eq(
        "chat_id", chat["chat_id"]
    ).order("sort_order").execute()
    chat["messages"] = [_row_to_message(m) for m in (msgs_result.data or [])]
    return chat
```

**Riesgo:** Bajo. Funcion nueva aditiva, no modifica logica existente.

#### Paso 1.2 — Reescribir `pages/2_Chat.py` con selector de viaje

**Archivo:** `pages/2_Chat.py`
**Tipo:** Modificacion mayor

**Cambios especificos:**

1. **Eliminar `_find_trip_by_destination()` (lineas 16-30)** — Funcion completa se elimina.

2. **Eliminar uso de `_find_trip_by_destination` en procesamiento de mensajes (lineas 277-282)** — El bloque:
   ```python
   detected = _find_trip_by_destination(user_input.lower(), trips)
   if detected and detected["id"] != (chat_trip or {}).get("id"):
       chat_trip = detected
       active_chat["trip_id"] = detected["id"]
       st.session_state.active_trip_id = detected["id"]
   ```
   Se elimina completamente.

3. **Reemplazar inicializacion de trip (lineas 34-36)** — De:
   ```python
   active_trip_id = st.session_state.get("active_trip_id")
   trip = get_active_trip(trips, active_trip_id)
   ```
   A: selector explicitamente construido (ver paso 4).

4. **Agregar selector de viaje despues del titulo (despues de linea 39)** — Nuevo bloque:
   ```python
   # Filtrar viajes activos
   from config.settings import TripStatus
   active_statuses = [TripStatus.PLANNING.value, TripStatus.CONFIRMED.value, TripStatus.IN_PROGRESS.value]
   available_trips = [t for t in trips if t["status"] in active_statuses]

   # Construir opciones del selector
   CREAR_NUEVO = "__crear_nuevo__"
   options = {t["id"]: f"{t['name']} — {t['destination']} ({t['status']})" for t in available_trips}
   options[CREAR_NUEVO] = "Crear nuevo viaje"

   # Selector
   selected_key = st.selectbox(
       "Selecciona un viaje",
       options=list(options.keys()),
       format_func=lambda k: options[k],
       index=None if not st.session_state.get("chat_selected_trip_id") else ...,
       key="trip_selector",
   )
   ```

5. **Logica de seleccion y carga de chat:**
   - Si `selected_key == CREAR_NUEVO`: habilitar chat sin trip_id, iniciar flujo de creacion
   - Si `selected_key` es un trip_id valido: cargar `get_latest_chat_for_trip()` o crear nuevo chat. Persistir en `st.session_state.chat_selected_trip_id`
   - Si `selected_key is None`: deshabilitar chat_input, mostrar mensaje

6. **Eliminar fallback de `chat_trip` (lineas 137-142)** — De:
   ```python
   chat_trip = None
   if active_chat.get("trip_id"):
       chat_trip = get_trip_by_id(trips, active_chat["trip_id"])
   if not chat_trip:
       chat_trip = trip  # fallback eliminado
   ```
   A: `chat_trip` viene directamente del selector, sin fallback.

7. **Deshabilitar chat_input sin seleccion (linea 261)** — Agregar `disabled=True` al `st.chat_input()` cuando no hay viaje seleccionado (excepto modo "Crear nuevo viaje").

**Riesgo:** Alto. Cambio fundamental en el flujo del chat. Probar exhaustivamente: seleccion, cambio de viaje, creacion, navegacion entre paginas.

#### Paso 1.3 — Actualizar system prompt del LLM

**Archivo:** `services/llm_chatbot.py`
**Tipo:** Modificacion menor (lineas 40-78 del system_template)

**Agregar al final de las REGLAS DE SEGURIDAD:**
```
- SOLO responde sobre el viaje activo cuyo contexto se proporciona abajo. Si el usuario pregunta sobre un viaje diferente (otro destino, otras fechas), responde amablemente que actualmente estas ayudando con el viaje a {destino} y sugiere cambiar la seleccion de viaje en el selector para interactuar con otro viaje. NUNCA proporciones informacion ni ejecutes acciones sobre un viaje distinto al activo.
```

**Riesgo:** Bajo. Solo agrega una instruccion al prompt, no cambia la logica del pipeline.

#### Paso 1.4 — Agregar labels de confirmacion para items

**Archivo:** `components/chat_widget.py`
**Tipo:** Modificacion menor (agregar despues de linea 77)

```python
_ADD_ITEM_LABELS = {
    "name": "Actividad",
    "day": "Dia",
    "start_time": "Hora inicio",
    "end_time": "Hora fin",
    "item_type": "Tipo",
    "location": "Ubicacion",
    "cost_estimated": "Costo estimado",
    "end_day": "Hasta dia",
}
```

Y modificar `render_confirmation()` (linea 91) para usar labels segun el tipo de accion:
```python
if is_create_trip:
    label = _CREATE_TRIP_LABELS.get(key, key)
elif action_data.get("action") == "add_item":
    label = _ADD_ITEM_LABELS.get(key, key)
else:
    label = key
```

**Riesgo:** Bajo. Cambio aditivo en renderizado.

---

### Fase 2 — REQ-CF-003: Extraccion Inteligente de Items

**Complejidad: Alta**
**Archivos nuevos: 1 | Archivos a modificar: 2**

#### Paso 2.1 — Crear `services/item_extraction.py` (NUEVO)

**Archivo:** `services/item_extraction.py` (crear)
**Tipo:** Modulo nuevo — logica pura sin Streamlit

**Estructura del modulo (siguiendo patron de `trip_creation_flow.py`):**

```python
"""Flujo de extraccion inteligente de items para el itinerario.

Logica pura — sin Streamlit, sin imports pesados. Solo re, datetime.
Patron de referencia: services/trip_creation_flow.py
"""

import re
from datetime import date, datetime, timedelta
from typing import Optional

# Reutilizar mapeo de meses de trip_creation_flow
from services.trip_creation_flow import _MESES, _CANCEL_KEYWORDS

# Keywords de tipo de item (RN-005)
_ITEM_TYPE_KEYWORDS = {
    "comida": ["restaurante", "cena", "almuerzo", "desayuno", "comer", "comida", "brunch"],
    "alojamiento": ["hotel", "hospedaje", "airbnb", "hostel", "alojamiento", "check-in", "check-out"],
    "vuelo": ["vuelo", "avion", "aeropuerto", "volar"],
    "traslado": ["taxi", "uber", "bus", "traslado", "transfer", "metro", "tren"],
    "extra": ["extra", "seguro", "equipaje", "compras", "souvenir"],
}

# Franjas horarias genericas (RN-004)
_TIME_SLOTS = {
    "manana": "09:00",
    "mediodia": "12:00",
    "tarde": "15:00",
    "noche": "20:00",
}

# Duraciones por defecto por tipo (CRIT-02)
_DEFAULT_DURATIONS = {
    "actividad": 2.0,    # 2 horas
    "comida": 1.5,       # 1.5 horas
    "vuelo": 3.0,        # 3 horas
    "traslado": 1.0,     # 1 hora
    "alojamiento": 1.0,  # 1 hora (check-in)
    "extra": 1.0,        # 1 hora
}

# Horarios por defecto segun tipo (RN-004)
_DEFAULT_TIMES = {
    "actividad": "10:00",
    "comida": "12:30",      # almuerzo por defecto
    "vuelo": "08:00",
    "traslado": "09:00",
    "alojamiento": "15:00", # check-in
    "extra": "10:00",
}
```

**Funciones principales:**
- `detect_add_item_intent(msg: str) -> bool`
- `extract_item_data(msg: str, trip: dict, current_draft: dict = None) -> dict`
- `infer_item_type(msg: str) -> str`
- `extract_time(msg: str) -> Optional[str]`
- `extract_day_from_message(msg: str, trip: dict) -> Optional[int]`
- `calculate_end_time(start_time: str, item_type: str) -> str`
- `get_missing_item_fields(draft: dict) -> list`
- `build_item_prompt_for_missing(draft: dict, missing: list) -> str`
- `validate_item_day_range(day: int, trip: dict) -> tuple[bool, str]`
- `detect_time_conflict(day: int, start_time: str, end_time: str, items: list) -> Optional[str]`
- `build_item_confirmation_data(draft: dict, trip: dict) -> dict`
- `new_item_draft() -> dict`
- `detect_cancel_intent(msg: str) -> bool`

**Funciones clave detalladas:**

1. **`extract_item_data(msg, trip, draft)`**: Extrae name, day, start_time, item_type, location, cost del mensaje. Combina con draft existente. Usa regex para modo mock.

2. **`extract_day_from_message(msg, trip)`**: Convierte referencias temporales a dia relativo:
   - "el 15 de abril" → calcula `(date(2026,4,15) - start_date).days + 1`
   - "el dia 3" / "dia 5" → valor directo
   - "manana" → `(date.today() + 1 - start_date).days + 1`
   - Reutiliza `_MESES` y patrones de fecha de `trip_creation_flow.py`

3. **`calculate_end_time(start_time, item_type)`**: Calcula end_time sumando duracion por defecto al start_time. Trunca a "23:59" si excede medianoche.

4. **`detect_time_conflict(day, start_time, end_time, items)`**: Busca items existentes en el mismo dia con solapamiento horario. Retorna descripcion del conflicto o None.

5. **`build_item_confirmation_data(draft, trip)`**: Construye dict de confirmacion tipo `{"action": "add_item", "summary": "Agregar ...", "details": {...}}` con todos los campos extraidos.

**Riesgo:** Medio-Alto. La complejidad principal esta en la robustez de los regex para extraer datos del lenguaje natural en modo mock. Mitigacion: usar tests manuales con frases de ejemplo del req.

#### Paso 2.2 — Reescribir `_add_item_response()` y agregar manejo de draft en `services/agent_service.py`

**Archivo:** `services/agent_service.py`
**Tipo:** Modificacion mayor

**Cambios especificos:**

1. **Agregar import del nuevo modulo (despues de linea 14):**
   ```python
   from services.item_extraction import (
       extract_item_data, get_missing_item_fields,
       build_item_prompt_for_missing, validate_item_day_range,
       detect_time_conflict, build_item_confirmation_data,
       new_item_draft, calculate_end_time,
   )
   ```

2. **Agregar manejo del draft de item en `process_message()` (despues de linea 110):**
   ```python
   # Flujo multi-turn de creacion de item
   result = _handle_item_creation_flow(msg, message, trip, item_creation_draft)
   if result is not None:
       return result
   ```

3. **Agregar parametro `item_creation_draft` a `process_message()` (linea 91):**
   ```python
   def process_message(message: str, trip: Optional[dict] = None,
                       user_id: Optional[str] = None,
                       chat_id: Optional[str] = None,
                       trip_creation_draft: Optional[dict] = None,
                       item_creation_draft: Optional[dict] = None) -> dict:
   ```

4. **Nueva funcion `_handle_item_creation_flow()`** (patron similar a `_handle_trip_creation_flow`):
   - Si hay draft activo con `step="collecting"`: procesar respuesta del usuario, actualizar draft
   - Si no hay draft pero se detecta intencion de agregar: iniciar extraccion
   - Verificar datos minimos (name + day). Si faltan, preguntar (max 3 turnos)
   - Si hay datos completos: validar rango de fechas, detectar conflictos, construir confirmacion
   - Retornar `_item_creation_draft` en la respuesta para persistir en session_state

5. **Reescribir `_add_item_response()` (lineas 298-315):**
   ```python
   def _add_item_response(msg: str, trip: dict) -> dict:
       """Extrae datos del mensaje y genera confirmacion o inicia flujo multi-turn."""
       draft = new_item_draft()
       draft = extract_item_data(msg, trip, draft)
       draft["step"] = "collecting"

       missing = get_missing_item_fields(draft)

       if not missing:
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
           # Detectar conflictos horarios
           conflict = detect_time_conflict(
               draft["day"], draft["start_time"],
               draft.get("end_time") or calculate_end_time(draft["start_time"], draft["item_type"]),
               trip.get("items", []),
           )
           if conflict:
               return {
                   "role": "assistant",
                   "type": "text",
                   "content": f"{conflict}\n\nDeseas agregarlo de todas formas o prefieres cambiar el horario?",
                   "_item_creation_draft": draft,
               }
           # Todo listo — confirmacion
           confirmation = build_item_confirmation_data(draft, trip)
           confirmation["_item_creation_draft"] = None
           return confirmation

       # Faltan datos — multi-turn
       prompt = build_item_prompt_for_missing(draft, missing)
       return {
           "role": "assistant",
           "type": "text",
           "content": prompt,
           "_item_creation_draft": draft,
       }
   ```

6. **Actualizar `apply_confirmed_action()` (lineas 348-368)** — El bloque `add_item` debe aceptar campos enriquecidos del draft.

**Riesgo:** Alto. Cambio central en la logica del agente.

#### Paso 2.3 — Agregar manejo de `_item_creation_draft` en `pages/2_Chat.py`

**Archivo:** `pages/2_Chat.py`
**Tipo:** Modificacion menor (en el bloque de procesamiento de mensajes, ~linea 285)

```python
item_creation_draft = st.session_state.get("_item_creation_draft")
response = process_message(
    user_input, chat_trip,
    user_id=user_id,
    chat_id=active_chat["chat_id"],
    trip_creation_draft=trip_creation_draft,
    item_creation_draft=item_creation_draft,
)

# Manejar draft de item en la respuesta
if "_item_creation_draft" in response:
    draft_value = response.pop("_item_creation_draft")
    if draft_value is None:
        st.session_state.pop("_item_creation_draft", None)
    else:
        st.session_state["_item_creation_draft"] = draft_value
```

**Riesgo:** Bajo. Patron ya existente para trip_creation_draft.

---

### Fase 3 — REQ-CF-002: Eventos Multi-dia en Cronograma

**Complejidad: Media**
**Archivos a modificar: 5 | Archivos nuevos: 1 (migracion SQL)**

#### Paso 3.1 — Migracion SQL

**Archivo:** `scripts/migration_cf002_end_day.sql` (crear)

```sql
-- Migracion REQ-CF-002: Soporte para items multi-dia
-- Ejecutar en Supabase SQL Editor ANTES de desplegar el codigo

ALTER TABLE public.itinerary_items
ADD COLUMN end_day INTEGER NULL;

ALTER TABLE public.itinerary_items
ADD CONSTRAINT chk_end_day CHECK (end_day IS NULL OR end_day >= day);

-- Verificar
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'itinerary_items' AND column_name = 'end_day';
```

**Tambien actualizar `scripts/schema.sql`** para incluir `end_day` en la definicion de la tabla (para nuevas instalaciones).

**Riesgo:** Medio. Requiere ejecucion manual en Supabase.

#### Paso 3.2 — Actualizar modelo de item

**Archivo:** `models/itinerary_item.py`
**Tipo:** Modificacion menor

- Despues de `day: int`: Agregar `end_day: int = None`
- En `to_dict()`: Agregar `"end_day": self.end_day,`
- En `from_dict()`: Agregar `end_day=data.get("end_day"),`

**Riesgo:** Bajo. Campo opcional con default None, retrocompatibilidad total.

#### Paso 3.3 — Actualizar servicio de viajes

**Archivo:** `services/trip_service.py`
**Tipo:** Modificacion menor

1. **`_row_to_item()`:** Agregar `"end_day": row.get("end_day"),`
2. **`_item_to_row()`:** Agregar `"end_day": item.get("end_day"),`
3. **`group_items_by_day()`:** Modificar para que items con `end_day` aparezcan en todos los dias que abarcan:
   ```python
   def group_items_by_day(items: list) -> dict:
       groups = {}
       for item in items:
           start_day = item["day"]
           end_day = item.get("end_day") or start_day
           for d in range(start_day, end_day + 1):
               if d not in groups:
                   groups[d] = []
               groups[d].append(item)
       for day in groups:
           groups[day].sort(key=lambda x: x["start_time"])
       return dict(sorted(groups.items()))
   ```

**Riesgo:** Medio. El cambio en `group_items_by_day()` afecta el itinerario detallado.

#### Paso 3.4 — Agregar deteccion de intencion de cronograma en `services/agent_service.py`

**Archivo:** `services/agent_service.py`
**Tipo:** Modificacion media

1. **Agregar keywords de cronograma:**
   ```python
   _CALENDAR_KEYWORDS = [
       "cronograma", "calendario", "agregar al calendario",
       "crear evento", "bloque de viaje", "fechas del viaje al cronograma",
       "agregar al cronograma", "evento de calendario",
   ]
   ```

2. **Agregar funcion de deteccion:**
   ```python
   def _detect_calendar_intent(msg: str) -> bool:
       return any(kw in msg for kw in _CALENDAR_KEYWORDS)
   ```

3. **Agregar bloque de ruteo en `process_message()` (entre agregar/eliminar item y hotel search):**
   ```python
   if trip and _detect_calendar_intent(msg):
       return _calendar_event_response(trip)
   ```

4. **Nueva funcion `_calendar_event_response(trip)`:**
   ```python
   def _calendar_event_response(trip: dict) -> dict:
       start = trip.get("start_date", "")
       end = trip.get("end_date", "")
       if not start or not end:
           return {
               "role": "assistant", "type": "text",
               "content": "No puedo crear el evento porque el viaje no tiene fechas definidas.",
           }
       from datetime import date
       total_days = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
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
                   "day": 1,
                   "end_day": total_days,
                   "start_time": "00:00",
                   "end_time": "23:59",
                   "cost_estimated": 0.0,
                   "location": dest,
               },
           },
       }
   ```

5. **Actualizar `apply_confirmed_action()` para soportar `end_day`:**
   Agregar `"end_day": details.get("end_day"),` al dict `new_item`.

**Riesgo:** Bajo. Logica aditiva, no modifica flujos existentes.

#### Paso 3.5 — Renderizar eventos multi-dia en FullCalendar

**Archivo:** `pages/3_Cronograma.py`
**Tipo:** Modificacion media

**Modificar el loop de conversion items a eventos (lineas 52-78):**

```python
for item in items:
    day_offset = item["day"] - 1
    event_date = start_date + timedelta(days=day_offset)

    item_type = item.get("item_type", "extra")
    try:
        color = ITEM_TYPE_COLORS.get(ItemType(item_type), "#9E9E9E")
    except ValueError:
        color = "#9E9E9E"

    if item["status"] == ItemStatus.SUGGESTED.value:
        color = color + "80"

    end_day = item.get("end_day")
    if end_day and end_day > item["day"]:
        # Evento multi-dia (allDay)
        event_end_date = start_date + timedelta(days=end_day)  # exclusivo
        events.append({
            "title": item["name"],
            "start": str(event_date),
            "end": str(event_end_date),
            "allDay": True,
            "color": "#607D8B",  # Blue Grey para eventos multi-dia
            "extendedProps": {
                "id": item["id"],
                "type": item["item_type"],
                "status": item["status"],
                "location": item.get("location", ""),
                "cost": item.get("cost_estimated", 0),
                "multiday": True,
            },
        })
    else:
        # Evento de dia unico (comportamiento actual sin cambios)
        events.append({
            "title": item["name"],
            "start": f"{event_date}T{item['start_time']}:00",
            "end": f"{event_date}T{item['end_time']}:00",
            "color": color,
            "extendedProps": {
                "id": item["id"],
                "type": item["item_type"],
                "status": item["status"],
                "location": item.get("location", ""),
                "cost": item.get("cost_estimated", 0),
            },
        })
```

**Riesgo:** Medio. Depende de que `streamlit-calendar` soporte `allDay: true`.
**Mitigacion:** Si `allDay` no funciona, usar `start/end` con fechas sin hora como fallback.

#### Paso 3.6 — Actualizar fallback calendar

**Archivo:** `pages/3_Cronograma.py`, funcion `_render_fallback_calendar()`
**Tipo:** Modificacion menor

Items multi-dia ya apareceran en cada tab gracias al cambio en `group_items_by_day()`. Solo agregar etiqueta visual:

```python
is_multiday = item.get("end_day") and item["end_day"] > item["day"]
duration_label = f" (Dias {item['day']}-{item['end_day']})" if is_multiday else ""
```

**Riesgo:** Bajo.

---

## 6. Resumen de Archivos Afectados

| Archivo | CF-001 | CF-002 | CF-003 | Tipo de cambio |
|---------|--------|--------|--------|----------------|
| `pages/2_Chat.py` | **Mayor** | — | Menor | Reescritura parcial (selector) |
| `services/agent_service.py` | — | Medio | **Mayor** | Nuevas funciones + reescritura |
| `services/chat_service.py` | Menor | — | — | Nueva funcion |
| `services/llm_chatbot.py` | Menor | — | — | Actualizacion de prompt |
| `components/chat_widget.py` | Menor | — | — | Labels adicionales |
| `services/item_extraction.py` | — | — | **Nuevo** | Modulo completo |
| `services/trip_service.py` | — | Medio | — | end_day en CRUD + group_items |
| `models/itinerary_item.py` | — | Menor | — | Campo end_day |
| `pages/3_Cronograma.py` | — | **Mayor** | — | allDay + fallback |
| `scripts/schema.sql` | — | Menor | — | Definicion end_day |
| `scripts/migration_cf002_end_day.sql` | — | **Nuevo** | — | ALTER TABLE |
| `config/settings.py` | — | Posible | — | Color multi-dia (opcional) |

---

## 7. Cambios de Schema SQL

### Migracion requerida (CF-002):
```sql
ALTER TABLE public.itinerary_items ADD COLUMN end_day INTEGER NULL;
ALTER TABLE public.itinerary_items ADD CONSTRAINT chk_end_day CHECK (end_day IS NULL OR end_day >= day);
```

### Impacto en trigger existente:
El trigger `trg_recalc_budget` **NO se ve afectado**. Ya filtra por `status != 'sugerido'` y suma `cost_estimated`. Items multi-dia con `cost_estimated = 0` no alteran el calculo.

### Impacto en RLS:
Sin cambios. Las politicas RLS existentes filtran por `trip_id` → `user_id`.

---

## 8. Riesgos y Mitigaciones

| # | Riesgo | Probabilidad | Impacto | Mitigacion |
|---|--------|-------------|---------|------------|
| 1 | Selector de viaje rompe flujo de chat existente | Media | Alto | Probar exhaustivamente: seleccion, cambio, creacion, navegacion. Mantener fallback temporario durante desarrollo |
| 2 | `allDay` no soportado por version de `streamlit-calendar` | Baja | Medio | Fallback: usar fechas sin hora (FullCalendar trata como all-day). Verificar version >= 1.2.0 |
| 3 | Migracion SQL no ejecutada | Media | Alto | Documentar en README como paso obligatorio. Codigo maneja `end_day` None graciosamente |
| 4 | Conflicto entre drafts multi-turn | Baja | Medio | Hacerlos mutuamente excluyentes: si uno esta activo, el otro no puede iniciarse |
| 5 | Regex de extraccion mock insuficientes | Media | Medio | Empezar con patrones basicos, iterar. LLM mode es mas robusto |
| 6 | Callers de `create_chat()` pasan `trip_id=None` | Baja | Bajo | Mantener firma flexible, validar en UI |
| 7 | `group_items_by_day()` duplica items multi-dia en itinerario | Baja | Bajo | El item se muestra en cada dia con etiqueta de duracion. Comportamiento intencional |

---

## 9. Dependencias entre Fases

```
Fase 1 (CF-001: Selector) <-- prerequisito de todo
    |
    +-- Fase 2 (CF-003: Extraccion Inteligente)
    |       Requiere: selector activo para tener viaje con fechas
    |
    +-- Fase 3 (CF-002: Eventos Multi-dia)
            Requiere: selector activo + migracion SQL
            Puede hacerse en paralelo con Fase 2
```

---

## 10. Documentacion de Supersedencia

Los siguientes requerimientos anteriores quedan parcialmente supersedidos por CF-001:

| Req Original | Clausula | Supersedido por | Motivo |
|-------------|----------|-----------------|--------|
| REQ-CL-004 | RN-005, CA-007, CA-008 | REQ-CF-001 RN-006, RN-007 | La asociacion viaje-chat pasa de implicita (via active_trip_id) a explicita (via selector) |
| REQ-UI-002 | CA-010 | REQ-CF-001 RN-005 | La auto-deteccion de viaje por destino se elimina |

---

## 11. Checklist Pre-Implementacion

- [ ] Ejecutar migracion SQL `migration_cf002_end_day.sql` en Supabase
- [ ] Verificar version de `streamlit-calendar` >= 1.2.0
- [ ] Verificar que `OPENAI_API_KEY` esta configurada para probar modo LLM (opcional para CF-003)
- [ ] Verificar que hay al menos 2 viajes en estados activos para probar selector
- [ ] Backup de la base de datos antes de la migracion
