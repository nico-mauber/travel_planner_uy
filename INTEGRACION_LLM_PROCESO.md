# Proceso de Integración del Backend LLM en Trip Planner

**Fecha:** 2026-03-14
**Metodología:** Agent Team (4 agentes especializados trabajando en paralelo y secuencia)

---

## Equipo de Agentes

Se creó un equipo de 4 agentes con roles diferenciados para analizar e implementar la integración del backend del `multiuser_chat_system` (sistema de chat con LangGraph + Gemini + ChromaDB) como backend del chatbot del Trip Planner.

| Agente | Rol | Enfoque |
|--------|-----|---------|
| **Agent 1: Analista multiuser_chat_system** | Exploración profunda del sistema origen | Arquitectura, modelos de datos, pipeline LangGraph, persistencia, APIs |
| **Agent 2: Analista Trip Planner** | Exploración profunda del chatbot existente | agent_service.py, 2_Chat.py, chat_widget.py, flujo de datos, limitaciones |
| **Agent 3: Integrador** | Diseño del plan de integración | Estrategia, archivos a crear/modificar, adaptaciones, riesgos |
| **Agent 4: Evaluador** | Verificación de calidad post-integración | Compatibilidad, errores, seguridad, puntuación |

---

## Fase 1: Análisis Paralelo (Agentes 1 y 2)

Los agentes 1 y 2 se lanzaron **en paralelo** para maximizar eficiencia.

### Agent 1 — Hallazgos clave del multiuser_chat_system

- **No es un sistema cliente-servidor:** Es una app Streamlit monolítica sin APIs REST ni WebSockets.
- **Pipeline LangGraph de 4 nodos secuenciales:** memory_retrieval → context_optimization → response_generation → memory_extraction.
- **Persistencia en 3 capas:** SQLite (checkpoints LangGraph), ChromaDB (memorias vectoriales), JSON (metadatos de chats).
- **LLM:** Google Gemini 2.5 Flash con embeddings via `models/embedding-001`.
- **Extracción de memorias inteligente:** LLM analiza cada mensaje y extrae memorias con categoría e importancia (0-5). Solo guarda si importancia >= 2.
- **Clases reutilizables:** `ModernChatbot` (orquestación), `ModernMemoryManager` (ChromaDB + chats), `ChatbotManager` (singleton por usuario).
- **Bugs encontrados:** Typo en `update_at` vs `updated_at`, `delete_chat_from_langgraph()` siempre retorna False.
- **Seguridad mínima:** Sin autenticación, sin sanitización de prompts, API key en `.env`.

### Agent 2 — Hallazgos clave del chatbot Trip Planner

- **Agente 100% mock:** Pattern matching por keywords, sin LLM, sin memoria, sin contexto histórico.
- **3 tipos de respuesta:** `text` (markdown), `card` (tarjeta rica), `confirmation` (acción pendiente con botones).
- **Contrato limpio:** `process_message(message, trip) → {role, type, content}` — agnóstico a implementación.
- **Integración sólida:** `apply_confirmed_action()` + `sync_trip_changes()` garantizan consistencia de datos.
- **Historial solo en session_state:** Se pierde al reiniciar.
- **Limitaciones principales:** Precios fijos, sin NLP, sin contexto entre mensajes, keywords rígidas.
- **Punto de extensión claro:** Reemplazar `process_message()` manteniendo el formato de retorno.

---

## Fase 2: Diseño de Integración (Agente 3)

El agente integrador leyó todos los archivos de ambos proyectos y produjo un plan detallado de 12 secciones.

### Estrategia elegida: Adaptar y Wrappear

- **NO copiar directamente** — los sistemas son incompatibles en formato.
- **Copiar y adaptar** `memory_manager.py` y `chatbot.py` al dominio de viajes.
- **Crear wrapper** que conecte el LLM con el formato `{role, type, content}` existente.
- **Mantener mock como fallback** — sin API key, la app funciona idénticamente.

### Decisiones arquitectónicas clave

1. **Confirmaciones siempre por mock:** Las acciones `create_trip`, `add_item`, `remove_item` requieren botones UI, no texto LLM.
2. **LLM solo para consultas informativas:** Preguntas sobre destinos, hoteles, clima, presupuesto → respuesta inteligente del LLM.
3. **System prompt adaptado a viajes:** Inyecta contexto del viaje activo (destino, fechas, presupuesto, items) y perfil del usuario.
4. **Memorias vectoriales con categorías de viaje:** viaje, preferencias, personal, hechos_importantes.
5. **Persistencia aislada:** Datos del LLM en `data/llm_data/`, sin conflicto con `trips.json`.
6. **Fase 1 = solo text responses:** El LLM retorna `type: "text"`. Tarjetas ricas y confirmaciones siguen por mock.

### Archivos del plan

| Acción | Archivo |
|--------|---------|
| CREAR | `.env`, `.gitignore`, `config/llm_config.py` |
| CREAR | `services/memory_manager.py`, `services/llm_chatbot.py`, `services/llm_agent_service.py` |
| MODIFICAR | `app.py` (load_dotenv), `requirements.txt` (deps LLM) |
| MODIFICAR | `services/agent_service.py` (selector LLM/mock) |
| MODIFICAR | `pages/2_Chat.py` (indicador de modo) |
| SIN CAMBIOS | Todas las demás páginas, components, trip_service, budget_service |

---

## Fase 3: Implementación

Se implementó el plan del Agente 3 paso a paso:

1. Creación de `.env` con API key de Google.
2. Creación de `.gitignore` protegiendo `.env` y `data/llm_data/`.
3. Creación de `config/llm_config.py` con configuración del modelo.
4. Creación de `services/memory_manager.py` — gestor de memoria vectorial adaptado a viajes.
5. Creación de `services/llm_chatbot.py` — pipeline LangGraph con system prompt de viajes.
6. Creación de `services/llm_agent_service.py` — wrapper simple.
7. Modificación de `app.py` — `load_dotenv()` al inicio.
8. Modificación de `requirements.txt` — 8 dependencias LLM agregadas.
9. Modificación de `services/agent_service.py` — selector `_USE_LLM` con fallback.
10. Modificación de `pages/2_Chat.py` — indicador visual de modo LLM/básico.

### Verificaciones realizadas

- Sintaxis de todos los archivos Python: OK (0 errores).
- Fallback mock sin API key: OK (confirmaciones, tarjetas, respuestas mock funcionan).
- Health check de Streamlit: OK (app inicia correctamente).

---

## Fase 4: Evaluación (Agente 4)

El agente evaluador leyó todos los archivos integrados y produjo un informe de 12 secciones.

### Puntuación final

| Aspecto | Puntuación | Notas |
|--------|-----------|-------|
| Completitud de la integración | **9/10** | Todos los archivos presentes y funcionales |
| Calidad del código | **7.5/10** | Limpio, pero usa print() en vez de logging |
| Compatibilidad hacia atrás | **10/10** | 100% compatible sin API key |
| Manejo de errores | **7/10** | Try/catch exhaustivo, faltaba validación en result["messages"] |
| Documentación implícita | **8/10** | Código claro con docstrings adecuados |
| Persistencia | **9/10** | ChromaDB y SQLite aislados correctamente |
| Arquitectura | **8/10** | Pipeline LangGraph correcto |

### Problemas identificados y resueltos

| Problema | Severidad | Estado |
|---------|-----------|--------|
| Falta validación en `result["messages"][-1]` | IMPORTANTE | **CORREGIDO** — Agregada validación de lista vacía |
| Import sin usar (`AIMessage`) | MENOR | **CORREGIDO** — Eliminado |
| API key expuesta en .env | CRÍTICO | Documentado (requiere rotación por el usuario) |

### Problemas documentados (no bloqueantes)

- Print vs logging estructurado (mejora futura).
- Sin retry logic en LLM (mejora futura).
- Singleton sin reset por viaje (bajo impacto, threads separados).
- Disclaimer de estimaciones de precios (mejora futura).

---

## Fase 5: Evolución Post-Integración

**Periodo:** 2026-03-14 a 2026-03-27

Después de la integración original (Fases 1-4), el sistema evolucionó significativamente. Esta sección documenta todos los cambios mayores que transformaron el MVP desde un prototipo con Gemini y JSON a un sistema de producción con OpenAI, Supabase y múltiples integraciones externas.

### 5.1 Migración de LLM: Google Gemini → OpenAI gpt-5-nano

El modelo se cambió de **Google Gemini 2.5 Flash** a **OpenAI gpt-5-nano** (modelo mas barato y rapido para MVP).

| Aspecto | Antes (Fase 3) | Después (actual) |
|---------|----------------|-------------------|
| Modelo | `gemini-2.5-flash` | `gpt-5-nano` |
| Embeddings | `models/embedding-001` (Google) | `text-embedding-3-small` (OpenAI) |
| SDK | `langchain-google-genai` | `langchain-openai` |
| Variable de entorno | `GOOGLE_API_KEY` | `OPENAI_API_KEY` |
| Temperatura chat | 0.7 | 0.7 (sin cambio) |
| Temperatura extraccion | N/A | 0 (determinismo) |

La configuracion reside en `config/llm_config.py` con defaults configurables via variables de entorno (`LLM_DEFAULT_MODEL`, `LLM_EXTRACTION_TEMPERATURE`, `LLM_EMBEDDING_MODEL`).

### 5.2 Migración de persistencia: JSON → Supabase (PostgreSQL)

Se reemplazó completamente la persistencia en archivos JSON por **Supabase (PostgreSQL)** con 8 tablas:

| Tabla | Contenido | Clave primaria |
|-------|-----------|----------------|
| `users` | Cuentas de usuario | `user_id` (TEXT UNIQUE) |
| `profiles` | Preferencias del usuario | `user_id` (FK a users) |
| `trips` | Viajes | `id` (TEXT, formato `trip-{hex8}`) |
| `itinerary_items` | Items del itinerario (incluye `end_day` para multi-dia) | `id` (TEXT, formato `item-{hex8}`) |
| `expenses` | Gastos directos no asociados a items | `id` (TEXT, formato `exp-{hex8}`) |
| `chats` | Conversaciones | `chat_id` (TEXT) |
| `chat_messages` | Mensajes de chat | `id` (UUID auto) |
| `feedbacks` | Feedback post-viaje | `trip_id` (FK a trips, UNIQUE) |

- Schema unificado en `scripts/setup_database.sql` (transaccional e idempotente).
- Triggers de base de datos (`trg_recalc_budget`, `trg_recalc_budget_expenses`) recalculan `trips.budget_total` automaticamente.
- RLS habilitado; `service_role key` bypasea RLS por defecto.
- Cliente singleton en `services/supabase_client.py`.
- Datos LLM (ChromaDB + checkpoints LangGraph) permanecen en `data/llm_data/` (local).

### 5.3 Multi-usuario con Google OAuth

Se agregó autenticación condicional con **Authlib + secrets.toml**:

- `services/auth_service.py` verifica si Authlib esta instalado y si `.streamlit/secrets.toml` tiene credenciales OAuth.
- Si OAuth esta habilitado: `require_auth()` en `app.py` bloquea usuarios no autenticados con `st.login("google")`.
- Si no esta habilitado: modo demo con `DEMO_USER_ID`.
- Todos los servicios aceptan `user_id` para aislamiento de datos.

### 5.4 Eliminación del fallback mock — Sistema LLM-only

Se eliminó completamente el pattern matching por keywords. El sistema ahora es **LLM-only**:

- `agent_service.py` ya no tiene logica de keywords/regex para detectar intents.
- Sin `OPENAI_API_KEY`: el chat muestra "IA no disponible" y redirige al usuario a la UI.
- La deteccion de LLM es **lazy** (`_check_llm()`) para evitar problemas con el hot-reload de Streamlit.

### 5.5 Eliminación de `item_extraction.py` — Reemplazo por `item_utils.py`

Se eliminó `services/item_extraction.py` (~349 lineas de codigo muerto): funciones de deteccion por keywords (`detect_add_intent`, `detect_remove_intent`, etc.), regex, y pattern matching.

En su lugar:
- **`services/item_utils.py`** — Funciones de negocio puras: `calculate_end_time()`, `validate_item_day_range()`, `detect_time_conflict()`, `build_item_confirmation_data()`, `new_item_draft()`. Constantes: `_DEFAULT_DURATIONS` (horas por tipo), `_DEFAULT_TIMES` (horario default por tipo).
- Toda la logica de deteccion de intents y extraccion de datos se movio al LLM structured output (ver 5.6).

### 5.6 Extracción unificada via LLM structured output

`services/llm_item_extraction.py` reemplazó toda la logica de extraccion regex/keywords con una sola llamada LLM usando `ChatOpenAI.with_structured_output()` + schema Pydantic.

**Schema `ItemExtractionResult`** (30 campos):

| Grupo | Campos |
|-------|--------|
| Intent | `intent` (add_item, create_trip, calendar_event, remove_item, hotel_search, flight_search, add_expense, modify_expense, remove_expense, informative, unknown) |
| Item basico | `name`, `day`, `start_time`, `end_time`, `item_type`, `location`, `cost` |
| Completitud | `is_complete`, `missing_fields`, `follow_up_question` |
| Eliminacion | `remove_item_ids`, `remove_all`, `remove_summary` |
| Viaje | `trip_destination`, `trip_start_date`, `trip_end_date`, `trip_name` |
| Gastos | `expense_category`, `expense_id`, `expense_amount`, `remove_all_expenses` |
| Hoteles | `hotel_type`, `hotel_location`, `hotel_max_price` |
| Vuelos | `flight_origin`, `flight_destination`, `flight_origin_iata`, `flight_destination_iata` |
| Compartido | `result_count` |

- Singleton `_extraction_llm` (ChatOpenAI con temperatura 0 para determinismo).
- System prompt semantico: describe intenciones por significado, no por keywords.
- Post-validacion defensiva (`_post_validate`): valida intent, item_type, rango de dias, formato de horas, codigos IATA (con `airportsdata`), result_count (1-10), fechas ISO, merge con draft existente.

### 5.7 Búsqueda de hoteles — Booking.com via RapidAPI

`services/booking_service.py` — Cliente HTTP (httpx) contra RapidAPI DataCrawler:

- Flujo: `search_destinations(query)` → `search_hotels(dest_id, checkin, checkout)` → `format_hotels_as_cards()`.
- Cache en memoria con TTL de 1 hora.
- Intent `hotel_search` detectado semanticamente por el LLM. Extrae `hotel_type`, `hotel_location`, `hotel_max_price`.
- Renderizado: `render_hotel_results()` en `components/chat_widget.py`.
- Variable: `RAPIDAPI_KEY` (sin ella, busqueda de hoteles no disponible).

### 5.8 Búsqueda de vuelos — SerpAPI + fast-flights fallback

`services/flight_service.py` — Dual backend:

| Backend | Tipo | Requisito |
|---------|------|-----------|
| SerpAPI Google Flights | API REST estable (primario) | `SERPAPI_KEY` |
| fast-flights | Scraper directo de Google Flights (fallback) | Ninguno (sin API key) |

- Flujo: `search_flights(origin, destination, date)` → `format_flights_as_cards()`.
- `search_flights_for_trip(trip)` usa destino y fechas del viaje activo.
- **El LLM extrae codigos IATA directamente** (`flight_origin_iata`, `flight_destination_iata`) en el schema de extraccion.
- Cache en memoria con TTL de 30 minutos.
- Renderizado: `render_flight_results()` en `components/chat_widget.py` como tabla compacta HTML.

### 5.9 airportsdata — Base de datos de aeropuertos

Se reemplazó el diccionario hardcodeado de ~170 ciudades (`get_airport_code()`) por la libreria **`airportsdata`** (7800+ aeropuertos mundiales):

- Singleton `_IATA_DB` en `llm_item_extraction.py` carga la base una sola vez.
- Valida codigos IATA extraidos por el LLM contra la base real.
- Eliminó la necesidad de mantener un mapeo manual de ciudades a codigos.

### 5.10 Multi-conversación

`services/chat_service.py` gestiona multiples chats por usuario:

- Cada chat tiene `{chat_id, user_id, trip_id, title, messages}`.
- Auto-genera titulo desde el primer mensaje del usuario.
- Persistido en Supabase (tablas `chats` + `chat_messages`).
- CRUD completo: crear, listar, obtener, eliminar conversaciones.

### 5.11 Gastos directos

`services/expense_service.py` para gastos no asociados a items del itinerario:

- CRUD: `load_expenses()`, `add_expense()`, `update_expense()`, `remove_expense()`.
- IDs con formato `exp-{hex8}`.
- Intents LLM: `add_expense`, `modify_expense`, `remove_expense`.
- Incluidos en el calculo de presupuesto via `budget_service.py`.
- Trigger de base de datos `trg_recalc_budget_expenses` mantiene `trips.budget_total` sincronizado.

### 5.12 Servidor MCP standalone

`mcp_servers/booking_server.py` — Servidor FastMCP que expone herramientas de busqueda de hoteles:

- Tools: `buscar_destinos`, `buscar_hoteles`.
- Transporte: stdio.
- Ejecutable con `python mcp_servers/booking_server.py`.

### 5.13 Sanitización de input

`_sanitize_user_input()` en `agent_service.py` limpia patrones de prompt injection:

- Detecta y elimina: instrucciones de ignorar/olvidar, cambios de rol/persona, intentos de revelar system prompt, tokens de control (`[INST]`, `<|im_start|>`).
- Soft sanitization: no bloquea el mensaje, solo limpia patrones peligrosos.

### 5.14 Resumen de servicios actuales (19 servicios)

| Servicio | Responsabilidad |
|----------|----------------|
| `supabase_client.py` | Cliente Supabase singleton |
| `trip_service.py` | CRUD de viajes, items, presupuesto, sync con Supabase |
| `agent_service.py` | Dispatcher LLM-only del chat, ruteo por intent |
| `item_utils.py` | Validacion y construccion de items (funciones puras) |
| `llm_item_extraction.py` | Extraccion via LLM structured output (30 campos) |
| `trip_creation_flow.py` | Flujo multi-turn de creacion de viajes |
| `auth_service.py` | OAuth condicional (Authlib + secrets.toml) |
| `chat_service.py` | Multi-conversacion por usuario con persistencia |
| `llm_agent_service.py` | Wrapper sobre TripChatbot |
| `llm_chatbot.py` | Pipeline LangGraph de 4 nodos (singleton) |
| `memory_manager.py` | ChromaDB + SQLite checkpoints |
| `booking_service.py` | Cliente Booking.com via RapidAPI |
| `flight_service.py` | SerpAPI + fast-flights fallback |
| `expense_service.py` | CRUD de gastos directos |
| `budget_service.py` | Calculo de presupuesto por categoria |
| `profile_service.py` | Preferencias de usuario |
| `feedback_service.py` | Feedback post-viaje |
| `weather_service.py` | Clima mock hardcodeado |
| `__init__.py` | Modulo init |

---

## Resumen de la Integración

### Antes (pre-integración, 2026-03-14)
- Agente mock con pattern matching (keywords fijas).
- Sin memoria entre sesiones.
- Precios y datos hardcodeados.
- No entiende variantes de lenguaje natural.
- Persistencia en JSON local.
- Sin autenticación. Usuario unico.

### Después (estado actual, 2026-03-27)
- **LLM-only:** OpenAI gpt-5-nano con extraccion structured output (30 campos). Sin fallback mock.
- **Memoria vectorial** persistente entre sesiones (ChromaDB).
- **Persistencia en Supabase** (PostgreSQL, 8 tablas) con triggers de recalculo automatico.
- **Multi-usuario** con Google OAuth (Authlib) y fallback a modo demo.
- **Multi-conversación** con persistencia en Supabase.
- **Búsqueda de hoteles reales** via Booking.com (RapidAPI DataCrawler).
- **Búsqueda de vuelos reales** via SerpAPI Google Flights + fast-flights fallback.
- **Base de datos de aeropuertos** (airportsdata, 7800+ aeropuertos) para validacion de codigos IATA.
- **Gastos directos** no asociados a items del itinerario.
- **Sanitización de prompts** contra injection.
- **Servidor MCP** standalone para herramientas de busqueda.
- Confirmaciones con botones UI siguen funcionando para acciones que modifican datos.
- Historial de conversación persistente (LangGraph SQLite + Supabase).

### Archivos nuevos respecto a la integración original (Fase 3)

```
services/item_utils.py
services/booking_service.py
services/flight_service.py
services/chat_service.py
services/expense_service.py
services/auth_service.py
services/supabase_client.py
services/llm_item_extraction.py
services/budget_service.py
services/feedback_service.py
services/profile_service.py
services/weather_service.py
services/trip_creation_flow.py
mcp_servers/booking_server.py
scripts/setup_database.sql
```

### Archivos eliminados

```
services/item_extraction.py  (~349 lineas de keywords/regex — reemplazado por llm_item_extraction.py + item_utils.py)
```

### Archivos modificados desde la integración original

```
app.py                          — OAuth guard, sync active_trip_id, load_dotenv(override=True)
config/llm_config.py            — Gemini → OpenAI, nuevos parametros (EXTRACTION_TEMPERATURE, embedding model)
services/agent_service.py       — LLM-only (sin fallback mock), dispatch por 11 intents, sanitizacion
services/llm_chatbot.py         — Adaptado a OpenAI
services/memory_manager.py      — Adaptado a OpenAI embeddings
services/llm_agent_service.py   — Wrapper actualizado
services/trip_service.py        — Persistencia Supabase, gastos, multi-usuario
requirements.txt                — 19 dependencias (de 9 originales)
pages/2_Chat.py                 — Multi-conversacion, selector obligatorio de viaje
pages/*.py                      — Selector de viaje por pagina, try/except con reintentar
components/chat_widget.py       — render_hotel_results(), render_flight_results()
```

---

## Cómo ejecutar

```bash
# 1. Crear y activar entorno virtual
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
.\venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
# Crear .env con:
#   SUPABASE_URL=...          (requerida)
#   SUPABASE_SERVICE_KEY=...  (requerida)
#   OPENAI_API_KEY=...        (habilita LLM — sin ella, chat no disponible)
#   RAPIDAPI_KEY=...          (habilita busqueda de hoteles)
#   SERPAPI_KEY=...            (habilita busqueda de vuelos via SerpAPI)

# 4. Inicializar base de datos
# Ejecutar scripts/setup_database.sql en el SQL Editor de Supabase

# 5. Ejecutar la app
python -m streamlit run app.py

# Alternativa Windows (usa venv explicitamente):
.\run.bat

# 6. Servidor MCP standalone (opcional)
python mcp_servers/booking_server.py
```

**Nota:** Siempre usar `python -m streamlit run app.py` (no `streamlit run app.py`) para asegurar que se use el Python del venv.

---

## Dependencias actuales

```
streamlit>=1.42.0
Authlib>=1.3.2
plotly>=5.18.0
streamlit-calendar>=1.2.0
python-dotenv>=1.0.0
langchain-openai>=0.3.0
langchain-core>=0.3.0
langgraph>=0.2.0
langgraph-checkpoint>=2.0.0
langgraph-checkpoint-sqlite>=3.0.0
langchain-chroma>=0.2.0
chromadb>=0.5.0
pydantic>=2.0.0
typing_extensions>=4.8.0
httpx>=0.25.0
fast-flights>=2.2.0
airportsdata>=20250101
mcp[cli]>=1.2.0
supabase>=2.0.0
```

### Cambios respecto a las dependencias originales (Fase 3)

| Cambio | Paquete | Motivo |
|--------|---------|--------|
| REEMPLAZADO | `langchain-google-genai` → `langchain-openai` | Migracion Gemini → OpenAI |
| AGREGADO | `langgraph-checkpoint-sqlite>=3.0.0` | Checkpoints LangGraph |
| AGREGADO | `Authlib>=1.3.2` | Google OAuth |
| AGREGADO | `plotly>=5.18.0` | Charts de presupuesto |
| AGREGADO | `streamlit-calendar>=1.2.0` | Vista calendario FullCalendar.js |
| AGREGADO | `httpx>=0.25.0` | Cliente HTTP para Booking.com y SerpAPI |
| AGREGADO | `fast-flights>=2.2.0` | Scraper de Google Flights (fallback) |
| AGREGADO | `airportsdata>=20250101` | Base de datos de 7800+ aeropuertos |
| AGREGADO | `mcp[cli]>=1.2.0` | Servidor MCP (FastMCP) |
| AGREGADO | `supabase>=2.0.0` | Cliente Supabase (PostgreSQL) |
