# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proyecto

Trip Planner — MVP de un agente de planificacion de viajes con interfaz Streamlit. Multi-usuario con Google OAuth (fallback a modo demo sin auth). Persistencia en Supabase (PostgreSQL). Agente conversacional dual: LLM (OpenAI gpt-4.1-nano via LangGraph) cuando `OPENAI_API_KEY` esta presente, o fallback basico. Extraccion inteligente de items via LLM structured output (ChatOpenAI.with_structured_output + Pydantic) con fallback a keywords. Integracion opcional con Booking.com (RapidAPI) para busqueda de hoteles. Servidor MCP standalone para exponer herramientas de busqueda de hoteles.

## Comandos

### Setup inicial (crear y activar entorno virtual)

```bash
python -m venv venv

# Activar el entorno virtual
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
.\venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### Ejecutar la app

```bash
python -m streamlit run app.py         # Ejecutar la app (localhost:8501)
.\run.bat                              # Windows: lanza con el venv explicitamente
python mcp_servers/booking_server.py   # Servidor MCP standalone (stdio)
```

Siempre usar `python -m streamlit run app.py` (no `streamlit run app.py`) para asegurar que se use el Python del venv. El proyecto tiene multiples instalaciones de Python en la maquina; `run.bat` fuerza el uso de `venv\Scripts\python.exe`.

No hay tests ni linter configurados actualmente.

## Variables de entorno

En `.env` (cargado con `load_dotenv(override=True)` al inicio de `app.py` — `override=True` porque la maquina tiene variables de entorno de sistema que pueden colisionar):

| Variable | Requerida | Efecto |
|---|---|---|
| `SUPABASE_URL` | **Si** | URL del proyecto Supabase |
| `SUPABASE_SERVICE_KEY` | **Si** | Service role key de Supabase (bypasea RLS) |
| `OPENAI_API_KEY` | No | Habilita OpenAI gpt-4.1-nano LLM. Sin ella, solo funciona pattern matching para acciones |
| `OPENAI_PROJECT` | No | Project ID de OpenAI (usado automaticamente por el SDK) |
| `RAPIDAPI_KEY` | No | Habilita busqueda de hoteles reales via Booking.com (DataCrawler) |
| `RAPIDAPI_BOOKING_HOST` | No | Host de la API (default: `booking-com15.p.rapidapi.com`) |
| `SERPAPI_KEY` | No | Habilita busqueda de vuelos via SerpAPI Google Flights (backend primario estable). Sin ella, usa fast-flights (scraper directo) como fallback |

OAuth requiere adicionalmente `.streamlit/secrets.toml` con credenciales de Google (ver `secrets.toml.example`).

## Arquitectura

**Flujo de datos:** `st.session_state.trips` (lista de dicts) es la fuente de verdad durante la sesion. Las paginas leen/mutan esta lista. Tras cualquier mutacion, llamar `sync_trip_changes()` para recalcular presupuesto y persistir a Supabase. La base de datos Supabase es la fuente de verdad persistente.

**Seleccion de viaje por pagina:** Dashboard, Itinerario y Presupuesto tienen un `st.selectbox` propio para elegir viaje. Cronograma es global (muestra todos los viajes). Chat tiene su propio selector obligatorio. Al seleccionar en cualquier pagina, se actualiza `st.session_state.active_trip_id` para sincronizar las demas.

### Capas

- **`app.py`** — Punto de entrada. Configura `st.set_page_config(layout="wide")`, inyecta CSS global, ejecuta guard de autenticacion, inicializa `session_state`, sincroniza `active_trip_id` desde `chat_selected_trip_id`, configura `st.navigation()` con 7 paginas, renderiza sidebar con viaje activo. Carga `.env` con `load_dotenv()` al inicio.
- **`services/`** — Logica de negocio pura (sin Streamlit). 16 servicios (ver seccion Servicios).
- **`pages/`** — 7 paginas Streamlit. Dashboard, Itinerario y Presupuesto tienen selector de viaje propio. Cronograma muestra todos los viajes. Chat tiene selector obligatorio.
- **`components/`** — 5 widgets reutilizables que reciben datos y retornan acciones del usuario como dicts (ej: `{"action": "accept", "item_id": "..."}`).
- **`config/`** — `settings.py` (Enums, paletas de colores, iconos, labels en espanol, `DEMO_USER_ID`) y `llm_config.py` (modelo OpenAI `gpt-4.1-nano`, temperaturas para chat y extraccion, embeddings).
- **`models/`** — Dataclasses con `to_dict()`/`from_dict()` (Trip, ItineraryItem, Budget, UserProfile, Feedback). No se usan en runtime — los services operan directo sobre dicts.
- **`data/`** — `sample_data.py` (viajes demo) + `llm_data/` (ChromaDB + checkpoints, local).
- **`mcp_servers/`** — Servidor MCP standalone (`booking_server.py`) que expone `buscar_destinos` y `buscar_hoteles` como tools via FastMCP (transporte stdio).

### Servicios (`services/`)

| Servicio | Responsabilidad |
|---|---|
| `supabase_client.py` | Cliente Supabase singleton. Lee `SUPABASE_URL` y `SUPABASE_SERVICE_KEY` de `.env` |
| `trip_service.py` | CRUD de viajes, agrupacion de items por dia, aceptar/descartar sugerencias, recalculo de presupuesto, sincronizacion con Supabase. Servicio central |
| `agent_service.py` | Dispatcher principal del chat. 2 paths: CON LLM (el LLM detecta ALL intents semanticamente, sin keywords) y SIN LLM (keywords centralizadas en item_extraction). Deteccion lazy (`_check_llm()`). Sanitizacion de input. Funciones extraidas: `_hotel_search_response()`, `_llm_chat_response()` |
| `item_extraction.py` | Utilidades de validacion, confirmacion y fallback basico. ALL keywords de fallback centralizadas aqui (`_CALENDAR_KEYWORDS`, `_HOTEL_KEYWORDS`, `_REMOVE_KEYWORDS`, `_ADD_KEYWORDS`). Funciones `detect_*_intent()` solo para path sin LLM |
| `llm_item_extraction.py` | Extraccion inteligente de items via LLM structured output (`ChatOpenAI.with_structured_output` + schema Pydantic `ItemExtractionResult`). Detecta intent + extrae datos en una sola llamada. Post-validacion defensiva |
| `trip_creation_flow.py` | Flujo multi-turn de creacion de viajes desde el chat. Deteccion de intencion (strong/weak keywords), extraccion de destino y fechas con regex, validacion. Logica pura sin Streamlit |
| `auth_service.py` | OAuth condicional (Authlib + secrets.toml). Guard `require_auth()`. CRUD de usuarios en Supabase |
| `chat_service.py` | Multi-conversacion por usuario. CRUD de chats, auto-titulo, persistencia en Supabase |
| `llm_agent_service.py` | Wrapper delgado sobre `TripChatbot`. Importa condicionalmente |
| `llm_chatbot.py` | `TripChatbot` (singleton). Pipeline LangGraph de 4 nodos: memory_retrieval -> context_optimization -> response_generation -> memory_extraction |
| `memory_manager.py` | `TripMemoryManager`. ChromaDB para memorias vectoriales (importancia >= 2), SQLite para checkpoints LangGraph. Datos en `data/llm_data/` |
| `booking_service.py` | Cliente Booking.com via RapidAPI (DataCrawler). Cache en memoria (1h TTL) |
| `flight_service.py` | Busqueda de vuelos. Dual backend: SerpAPI Google Flights (primario, requiere `SERPAPI_KEY`) + fast-flights (fallback scraper, sin API key). Cache en memoria (30 min TTL). Funciones: `search_flights()`, `search_flights_for_trip()`, `format_flights_as_cards()`, `get_airport_code()`, `is_flights_available()` |
| `expense_service.py` | CRUD de gastos directos (`expenses`) no asociados a items del itinerario. Funciones: `load_expenses()`, `add_expense()`, `update_expense()`, `remove_expense()`, `format_existing_expenses()`. IDs con formato `exp-{hex8}` |
| `budget_service.py` | Calculo de resumen de presupuesto por categoria. Acepta `items` y `expenses` (gastos directos). Excluye items sugeridos. Retorna `total_estimated`, `total_real`, `total_expenses`, `by_category` |
| `profile_service.py` | Preferencias de usuario. Persistencia en Supabase |
| `feedback_service.py` | Retroalimentacion post-viaje. Rating general + por item. Persistencia en Supabase |
| `weather_service.py` | Clima mock hardcodeado para algunos destinos. Default generico |

### Paginas (`pages/`)

| Pagina | Funcionalidad |
|---|---|
| `1_Dashboard.py` | Selector de viaje + metricas, progreso, clima, alertas, quick links |
| `2_Chat.py` | Chat multi-conversacion con selector obligatorio de viaje. Renderiza text/cards/confirmaciones/hotel_results. Maneja acciones create_trip, add_item, remove_item, calendar_event |
| `3_Cronograma.py` | Vista calendario **global** (todos los viajes). FullCalendar.js via `streamlit-calendar`. Eventos prefijados con destino del viaje. Fallback a tabs por fecha |
| `4_Itinerario.py` | Selector de viaje + itinerario dia a dia con items expandibles, bloques de traslado, aceptar/descartar sugerencias |
| `5_Presupuesto.py` | Selector de viaje + desglose por categoria, donut chart + barras comparativas (Plotly), drill-down |
| `6_Perfil.py` | Editor de preferencias del usuario. Info OAuth (read-only) + tabs de preferencias |
| `7_Mis_Viajes.py` | Gestion de viajes (crear/ver/eliminar). "Ver viaje" sincroniza `active_trip_id` y `chat_selected_trip_id`, navega a Dashboard |

### Componentes (`components/`)

| Componente | Funcionalidad |
|---|---|
| `chat_widget.py` | `render_rich_card()` (vuelos, hoteles, actividades, comidas), `render_hotel_results()` (Booking.com), `render_confirmation()` (Confirmar/Cancelar, filtra campos internos con prefijo `_`) |
| `itinerary_item.py` | `render_itinerary_item()` (expandible con detalles), `render_transfer()` (bloque de traslado) |
| `budget_charts.py` | `render_donut_chart()` (pie por categoria), `render_comparison_bars()` (estimado vs real). Plotly dark theme |
| `trip_card.py` | `render_trip_card()` — card con nombre, destino, fechas, presupuesto, badge de estado, botones Ver/Eliminar |
| `alert_banner.py` | `get_alerts()` (items pendientes, sugerencias, dias vacios), `render_alerts()` (banners descartables) |

### Modelos de datos

Los viajes e items son **dicts planos** a lo largo de toda la app. Un item se anida dentro de `trip["items"]` (lista de dicts). Los gastos directos en `trip["expenses"]` (lista de dicts). Items multi-dia tienen campo `end_day` (opcional, >= `day`). Los dataclasses en `models/` existen como referencia pero no se instancian en runtime.

### Persistencia (Supabase)

Tablas en Supabase (PostgreSQL):

| Tabla | Contenido | Clave primaria |
|---|---|---|
| `users` | Cuentas de usuario | `user_id` (TEXT UNIQUE) |
| `profiles` | Preferencias del usuario | `user_id` (FK a users) |
| `trips` | Viajes | `id` (TEXT, formato `trip-{hex8}`) |
| `itinerary_items` | Items del itinerario (incluye `end_day` para multi-dia) | `id` (TEXT, formato `item-{hex8}`) |
| `expenses` | Gastos directos no asociados a items | `id` (TEXT, formato `exp-{hex8}`) |
| `chats` | Conversaciones | `chat_id` (TEXT) |
| `chat_messages` | Mensajes de chat | `id` (UUID auto) |
| `feedbacks` | Feedback post-viaje | `trip_id` (FK a trips, UNIQUE) |

- Schema unificado en `scripts/setup_database.sql` (transaccional e idempotente — ejecutar en Supabase SQL Editor)
- Trigger `trg_recalc_budget` recalcula `trips.budget_total` al modificar `itinerary_items` (excluye sugeridos)
- Trigger `trg_recalc_budget_expenses` recalcula `trips.budget_total` al modificar `expenses`
- `budget_total` = SUM(items.cost_estimated donde status != 'sugerido') + SUM(expenses.amount)
- RLS habilitado; service_role key bypasea RLS por defecto
- Datos LLM (ChromaDB + checkpoints) en `data/llm_data/` (local)

## Autenticacion (OAuth)

**Condicional por Authlib + secrets.toml:**
- `auth_service.py` verifica al importar si `authlib` esta instalado (`_AUTHLIB_AVAILABLE`). Si no esta o faltan credenciales OAuth en `.streamlit/secrets.toml`, la app funciona en modo demo (`DEMO_USER_ID`).
- Si OAuth esta habilitado: `require_auth()` en app.py bloquea usuarios no autenticados con `st.login("google")`. Tras el callback, `get_or_create_user()` crea el registro en Supabase.
- **`st.logout()` es una accion inmediata, NO un boton.** Siempre envolverlo en `if st.button(): st.logout()`. Llamarlo directamente desloguea al usuario en cada rerun.

**Multi-usuario:** Todos los servicios aceptan `user_id`. Supabase aisla datos por `user_id` (FK en todas las tablas). RLS habilitado para seguridad adicional.

## Chat — Dual mode (LLM / Fallback)

- `agent_service.py` detecta `OPENAI_API_KEY` de forma **lazy** (`_check_llm()`). La deteccion se ejecuta la primera vez que se procesa un mensaje, no al importar el modulo. Esto evita problemas con el hot-reload de Streamlit que puede re-importar modulos antes de que `load_dotenv()` haya corrido. Carga tanto el chatbot LLM (`_llm_process_fn`) como el extractor de items (`_llm_extract_fn` desde `llm_item_extraction.py`).
- Las **acciones que modifican datos** (crear viaje, agregar/eliminar items, eventos de cronograma) **siempre** pasan por pattern matching para generar confirmaciones con botones UI, nunca por el LLM.
- Los mensajes son dicts con `{role, type, content}`. `type` puede ser `"text"`, `"card"`, `"confirmation"` o `"hotel_results"`. Las confirmaciones procesadas se marcan con `msg["processed"] = True`.

**Prioridad de ruteo en `agent_service.py`** — 2 paths mutuamente excluyentes:

*CON LLM* (orden estricto):
1. **Flujo multi-turn de creacion de viaje** (`trip_creation_flow.py`) — si hay draft activo
2. **Flujo multi-turn de creacion de item** (`item_extraction.py`) — si hay draft activo. Preguntas informativas escapan al LLM sin consumir turno
3. **Deteccion unificada via LLM** (`_handle_llm_extraction`) — UNA sola llamada detecta intent (`add_item`, `calendar_event`, `remove_item`, `hotel_search`, `informative`, `unknown`) y extrae datos. **Sin keywords, sin guards previos** — el LLM entiende la intencion semanticamente sin importar idioma o palabras exactas
4. **LLM chat** (`_llm_chat_response`) — fall-through para informative/unknown

*SIN LLM* (fallback por keywords):
1. **Flujo multi-turn de creacion de viaje** — si hay draft activo
2. **Flujo multi-turn de creacion de item** — si hay draft activo
3. **Keywords**: calendario → agregar item → eliminar → hotel (funciones `detect_*_intent()` centralizadas en `item_extraction.py`)
4. **"IA no disponible"** — mensaje de fallback final

**Extraccion inteligente de items — Dual mode (LLM / Fallback):**

*Con LLM* (`llm_item_extraction.py`):
- `ChatOpenAI.with_structured_output(ItemExtractionResult)` — una sola llamada detecta intent y extrae datos estructurados
- Schema Pydantic `ItemExtractionResult`: intent (incluye `hotel_search`), name, day, start_time, end_time, item_type, location, cost, is_complete, missing_fields, follow_up_question
- System prompt semantico: describe intenciones por significado, NO por keywords. El LLM entiende cualquier idioma/fraseo
- Post-validacion defensiva (`_post_validate`): valida intent, item_type, rango de dias, formato de horas, merge con draft existente
- Singleton `_extraction_llm` (ChatOpenAI con `EXTRACTION_TEMPERATURE=0` para determinismo)
- Interpreta ordinales ("tercer dia" -> 3), referencias relativas ("ultimo dia", "manana"), y periodos ("por la tarde" -> 15:00)

*Sin LLM — fallback* (`item_extraction.py`):
- Extraccion basica por regex y keywords: dia (`dia N`), hora (`HH:MM`), tipo por keywords
- **ALL keywords de fallback centralizadas** en este modulo: `_ADD_KEYWORDS`, `_CALENDAR_KEYWORDS`, `_HOTEL_KEYWORDS`, `_REMOVE_KEYWORDS`, `_ITEM_TYPE_KEYWORDS`
- Funciones de deteccion de intent: `detect_add_item_intent()`, `detect_calendar_intent()`, `detect_hotel_intent()`, `detect_remove_item_intent()`

*Comun a ambos modos:*
- Flujo multi-turn (max 3 turnos) si faltan datos minimos (nombre + dia)
- Calcula `end_time` por duraciones default segun tipo (`_DEFAULT_DURATIONS`)
- Detecta conflictos horarios con items existentes (`detect_time_conflict`)
- Genera confirmacion con tarjeta rica (`build_item_confirmation_data`)

**Deteccion de intencion de creacion de viaje** (`trip_creation_flow.py`):
- Keywords **fuertes** ("quiero ir", "crear viaje", "me gustaria ir") -> siempre disparan creacion
- Keywords **debiles** ("viaje", "vacaciones", "visitar") -> NO disparan si el mensaje es una pregunta o refiere a un viaje existente
- Proteccion anti-duplicado: si hay viaje activo al mismo destino, no inicia creacion

**Multi-conversacion:** `chat_service.py` gestiona multiples chats por usuario. Cada chat tiene `{chat_id, user_id, trip_id, title, messages}`. Auto-genera titulo desde el primer mensaje. Persistido en Supabase (tablas `chats` + `chat_messages`).

**LLM Backend (LangGraph + OpenAI):**
- `services/llm_chatbot.py` — `TripChatbot` (singleton). Pipeline LangGraph de 4 nodos secuenciales: memory_retrieval -> context_optimization -> response_generation -> memory_extraction.
- `services/memory_manager.py` — `TripMemoryManager`. ChromaDB para memorias vectoriales (importancia >= 2), SQLite para checkpoints LangGraph. Datos en `data/llm_data/`.

**Busqueda de hoteles (Booking.com):**
- `booking_service.py` — Cliente HTTP (httpx) contra RapidAPI DataCrawler.
- Flujo: `search_destinations(query)` -> `search_hotels(dest_id, checkin, checkout)` -> `format_hotels_as_cards()`.

**Busqueda de vuelos (SerpAPI + Google Flights fallback):**
- `flight_service.py` — Dual backend: SerpAPI Google Flights (primario, requiere `SERPAPI_KEY`) + fast-flights (fallback scraper, sin API key).
- Flujo: `search_flights(origin, destination, date)` -> `format_flights_as_cards()`.
- `search_flights_for_trip(trip)` usa destino y fechas del viaje activo. Necesita ciudad de origen del usuario.
- `get_airport_code(city_name)` mapea ciudades a codigos IATA (169 ciudades de Latam, Europa, NA, Asia, Africa).
- Intent `flight_search` en el dispatcher: detectado por LLM semanticamente o por keywords (`_FLIGHT_KEYWORDS`).
- Renderizado: `render_flight_results()` en chat_widget.py como tabla compacta HTML.
- Cache en memoria con TTL de 1 hora. Si `RAPIDAPI_KEY` no esta configurada, retorna listas vacias.

**MCP Server:**
- `mcp_servers/booking_server.py` — Servidor FastMCP standalone que expone `buscar_destinos` y `buscar_hoteles` como tools.
- Transporte: stdio. Ejecutable con `python mcp_servers/booking_server.py`.

**Sanitizacion de input:**
- `_sanitize_user_input()` en `agent_service.py` limpia patrones de prompt injection antes de procesar mensajes
- Detecta y elimina: instrucciones de ignorar/olvidar, cambios de rol/persona, intentos de revelar system prompt, tokens de control (`[INST]`, `<|im_start|>`)
- No bloquea el mensaje (soft sanitization): si queda vacio tras limpiar, devuelve el original

## Reglas de negocio criticas

1. **Items con `status="sugerido"` NO se contabilizan en presupuesto**. Filtrar por `ItemStatus.SUGGESTED` antes de cualquier calculo financiero.
2. **Auto-update de estado por fecha** (en cada carga): `today > end_date` -> "completado"; `start_date <= today <= end_date` -> "en_curso".
3. **Seleccion de viaje por pagina:** Cada pagina (excepto Cronograma que es global) tiene un `st.selectbox` que actualiza `active_trip_id`. `app.py` sincroniza `chat_selected_trip_id` -> `active_trip_id` en cada rerun.
4. **Solo se pueden eliminar viajes en estado "en_planificacion".**
5. **Feedback solo disponible para viajes completados.**
6. **Items multi-dia** tienen `end_day > day` y se renderizan como `allDay: true` en FullCalendar con color Blue Grey (`#607D8B`).

## Convenciones

- Viajes y items son **dicts**, no objetos tipados, a lo largo de toda la app
- IDs usan formato `trip-{hex8}` / `item-{hex8}` / `exp-{hex8}` / `chat-{hex8}` / `user-{hex8}` generados con `uuid.uuid4().hex[:8]`
- Fechas como strings ISO `"YYYY-MM-DD"`, horas como `"HH:MM"`
- Items usan `day` (int, 1-based) para posicion temporal relativa al inicio del viaje. `end_day` (int, opcional) para items multi-dia
- Enums en `config/settings.py` usan valores en espanol (`"en_planificacion"`, `"confirmado"`, `"sugerido"`, etc.)
- Persistencia: write-through a Supabase (tablas: users, profiles, trips, itinerary_items, chats, chat_messages, feedbacks)
- Cada pagina envuelve su contenido en `try/except` con boton "Reintentar"
- `OPENAI_API_KEY` en `.env` habilita el LLM; sin ella, solo funcionan acciones por pattern matching
- Servicios que dependen de APIs externas (OpenAI, Booking.com) degradan graciosamente
- Singletons para `TripChatbot`, `TripMemoryManager` y `_extraction_llm` (ChatOpenAI para extraccion) — una instancia por proceso

## Dependencias principales

| Paquete | Uso |
|---|---|
| `streamlit>=1.42.0` | Framework UI (pages, session_state, login/logout) |
| `Authlib>=1.3.2` | Google OAuth (condicional) |
| `plotly>=5.18.0` | Charts de presupuesto (donut, barras) |
| `streamlit-calendar>=1.2.0` | Vista calendario FullCalendar.js |
| `python-dotenv>=1.0.0` | Carga de `.env` |
| `langchain-openai`, `langgraph`, `langgraph-checkpoint-sqlite` | Pipeline LLM con OpenAI gpt-4.1-nano |
| `langchain-chroma`, `chromadb` | Memoria vectorial |
| `httpx>=0.25.0` | Cliente HTTP para Booking.com API y SerpAPI fallback |
| `fast-flights>=2.2.0` | Scraper de Google Flights (fallback de busqueda de vuelos sin API key) |
| `mcp[cli]>=1.2.0` | Servidor MCP (FastMCP) |
| `supabase>=2.0.0` | Cliente Supabase (persistencia PostgreSQL) |
| `pydantic>=2.0.0` | Modelos estructurados (memoria LLM + schema `ItemExtractionResult` para structured output) |

## Documentacion de requerimientos

En `Requerimientos/MVP/` hay especificaciones detalladas:
- **`Chatbot_Login/`** — REQ-CL-001 a REQ-CL-005: login, chatbot, integracion LLM, multi-conversacion
- **`Chatbot_Funcionalities/`** — REQ-CF-001 a REQ-CF-003: selector obligatorio, eventos cronograma, extraccion inteligente de items
- **`UI/`** — REQ-UI-001 a REQ-UI-012: dashboard, itinerario, cronograma, presupuesto, perfil, mis viajes, feedback, alertas

## Idioma

- Todas las respuestas y comunicaciones deben ser en espanol.
- Terminos tecnicos y nombres de codigo se mantienen en su forma original (ingles).
