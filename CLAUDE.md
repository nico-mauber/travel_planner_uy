# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proyecto

Trip Planner — MVP de un agente de planificación de viajes con interfaz Streamlit. Multi-usuario con Google OAuth (fallback a modo demo sin auth). Persistencia en Supabase (PostgreSQL). Agente conversacional dual: LLM (OpenAI gpt-4.1-nano via LangGraph) cuando `OPENAI_API_KEY` está presente, o mock por pattern matching. Integración opcional con Booking.com (RapidAPI) para búsqueda de hoteles reales. Servidor MCP standalone para exponer herramientas de búsqueda de hoteles.

## Comandos

```bash
pip install -r requirements.txt        # Instalar dependencias
python -m streamlit run app.py         # Ejecutar la app (localhost:8501)
.\run.bat                              # Windows: lanza con el venv explícitamente
python mcp_servers/booking_server.py   # Servidor MCP standalone (stdio)
```

Siempre usar `python -m streamlit run app.py` (no `streamlit run app.py`) para asegurar que se use el Python del venv. El proyecto tiene múltiples instalaciones de Python en la máquina; `run.bat` fuerza el uso de `venv\Scripts\python.exe`.

No hay tests ni linter configurados actualmente.

## Variables de entorno

En `.env` (cargado con `load_dotenv(override=True)` al inicio de `app.py` — `override=True` porque la máquina tiene variables de entorno de sistema que pueden colisionar):

| Variable | Requerida | Efecto |
|---|---|---|
| `SUPABASE_URL` | **Sí** | URL del proyecto Supabase |
| `SUPABASE_SERVICE_KEY` | **Sí** | Service role key de Supabase (bypasea RLS) |
| `OPENAI_API_KEY` | No | Habilita OpenAI gpt-4.1-nano LLM. Sin ella, el chat usa mock por pattern matching |
| `OPENAI_PROJECT` | No | Project ID de OpenAI (usado automáticamente por el SDK) |
| `RAPIDAPI_KEY` | No | Habilita búsqueda de hoteles reales via Booking.com (DataCrawler) |
| `RAPIDAPI_BOOKING_HOST` | No | Host de la API (default: `booking-com15.p.rapidapi.com`) |

OAuth requiere adicionalmente `.streamlit/secrets.toml` con credenciales de Google (ver `secrets.toml.example`).

## Arquitectura

**Flujo de datos:** `st.session_state.trips` (lista de dicts) es la fuente de verdad durante la sesión. Las páginas leen/mutan esta lista. Tras cualquier mutación, llamar `sync_trip_changes()` para recalcular presupuesto y persistir a Supabase. La base de datos Supabase es la fuente de verdad persistente.

### Capas

- **`app.py`** — Punto de entrada. Configura `st.set_page_config(layout="wide")`, inyecta CSS global, ejecuta guard de autenticación, inicializa `session_state` (trips, active_trip_id, user_chats, active_chat_id, dismissed_alerts, user_profile, current_user), configura `st.navigation()` con 7 páginas, renderiza sidebar con viaje activo. Carga `.env` con `load_dotenv()` al inicio.
- **`services/`** — Lógica de negocio pura (sin Streamlit). 12 servicios (ver sección Servicios).
- **`pages/`** — 7 páginas Streamlit. Cada una lee `st.session_state.trips`, obtiene el viaje activo vía `get_active_trip()`, y renderiza su sección. Páginas que requieren viaje activo redirigen a Mis Viajes si no hay uno.
- **`components/`** — 5 widgets reutilizables que reciben datos y retornan acciones del usuario como dicts (ej: `{"action": "accept", "item_id": "..."}`).
- **`config/`** — `settings.py` (Enums, paletas de colores, iconos, labels en español, `DEMO_USER_ID`) y `llm_config.py` (modelo OpenAI `gpt-4.1-nano`, temperatura, embeddings, reasoning effort).
- **`models/`** — Dataclasses con `to_dict()`/`from_dict()` (Trip, ItineraryItem, Budget, UserProfile, Feedback). No se usan en runtime — los services operan directo sobre dicts.
- **`data/`** — Archivos JSON de persistencia + `sample_data.py` (3 viajes demo: Tokio, Barcelona, Lima, ~32 items).
- **`mcp_servers/`** — Servidor MCP standalone (`booking_server.py`) que expone `buscar_destinos` y `buscar_hoteles` como tools via FastMCP (transporte stdio).

### Servicios (`services/`)

| Servicio | Responsabilidad |
|---|---|
| `supabase_client.py` | Cliente Supabase singleton. Lee `SUPABASE_URL` y `SUPABASE_SERVICE_KEY` de `.env` |
| `trip_service.py` | CRUD de viajes, agrupación de items por día, aceptar/descartar sugerencias, recálculo de presupuesto, sincronización con Supabase. Servicio central |
| `agent_service.py` | Dispatcher principal del chat. Detecta `OPENAI_API_KEY` y `RAPIDAPI_KEY`. Rutea a LLM, mock o Booking.com según contexto. Acciones de datos siempre por mock |
| `auth_service.py` | OAuth condicional (Authlib + secrets.toml). Guard `require_auth()`. CRUD de usuarios en Supabase |
| `chat_service.py` | Multi-conversación por usuario. CRUD de chats, auto-título, persistencia en Supabase |
| `llm_agent_service.py` | Wrapper delgado sobre `TripChatbot`. Importa condicionalmente |
| `llm_chatbot.py` | `TripChatbot` (singleton). Pipeline LangGraph de 4 nodos: memory_retrieval → context_optimization → response_generation → memory_extraction |
| `memory_manager.py` | `TripMemoryManager`. ChromaDB para memorias vectoriales (importancia >= 2), SQLite para checkpoints LangGraph. Datos en `data/llm_data/` |
| `booking_service.py` | Cliente Booking.com via RapidAPI (DataCrawler). Cache en memoria (1h TTL). `search_destinations()`, `search_hotels()`, `search_hotels_for_trip()`, `format_hotels_as_cards()` |
| `budget_service.py` | Cálculo de resumen de presupuesto por categoría. Excluye items sugeridos. Calcula progreso de planificación |
| `profile_service.py` | Preferencias de usuario (alojamiento, alimentación, estilo, presupuesto, transporte). Persistencia en Supabase |
| `feedback_service.py` | Retroalimentación post-viaje. Rating general + por item. Persistencia en Supabase |
| `trip_creation_flow.py` | Flujo multi-turn de creación de viajes desde el chat. Detección de intención (strong/weak keywords), extracción de destino y fechas con regex, validación. Lógica pura sin Streamlit |
| `weather_service.py` | Clima mock hardcodeado para Tokio, Barcelona, Lima. Default genérico para otros destinos |

### Páginas (`pages/`)

| Página | Funcionalidad |
|---|---|
| `1_Dashboard.py` | Métricas del viaje activo, progreso, clima, alertas, quick links |
| `2_Chat.py` | Chat multi-conversación. Renderiza text/cards/confirmaciones/hotel_results. Maneja acciones create_trip, add_item, remove_item |
| `3_Cronograma.py` | Vista calendario (FullCalendar.js via `streamlit-calendar`). Fallback a tabs por día |
| `4_Itinerario.py` | Itinerario día a día con items expandibles, bloques de traslado, aceptar/descartar sugerencias |
| `5_Presupuesto.py` | Desglose por categoría, donut chart + barras comparativas (Plotly), drill-down por categoría |
| `6_Perfil.py` | Editor de preferencias del usuario. Info OAuth (read-only) + tabs de preferencias |
| `7_Mis_Viajes.py` | Gestión de viajes (crear/ver/eliminar). Filtro por estado. Sección de feedback para viajes completados |

### Componentes (`components/`)

| Componente | Funcionalidad |
|---|---|
| `chat_widget.py` | `render_rich_card()` (vuelos, hoteles, actividades, comidas), `render_hotel_results()` (Booking.com), `render_confirmation()` (Confirmar/Cancelar) |
| `itinerary_item.py` | `render_itinerary_item()` (expandible con detalles), `render_transfer()` (bloque de traslado) |
| `budget_charts.py` | `render_donut_chart()` (pie por categoría), `render_comparison_bars()` (estimado vs real). Plotly dark theme |
| `trip_card.py` | `render_trip_card()` — card con nombre, destino, fechas, presupuesto, badge de estado, botones Ver/Eliminar |
| `alert_banner.py` | `get_alerts()` (items pendientes, sugerencias, días vacíos), `render_alerts()` (banners descartables) |

### Modelos de datos

Los viajes e items son **dicts planos** a lo largo de toda la app. Un item se anida dentro de `trip["items"]` (lista de dicts). Los dataclasses en `models/` (Trip, ItineraryItem, BudgetSummary, UserProfile, TripFeedback/ItemFeedback) existen como referencia pero no se instancian en runtime.

### Persistencia (Supabase)

Tablas en Supabase (PostgreSQL):

| Tabla | Contenido | Clave primaria |
|---|---|---|
| `users` | Cuentas de usuario | `user_id` (TEXT UNIQUE) |
| `profiles` | Preferencias del usuario | `user_id` (FK a users) |
| `trips` | Viajes | `id` (TEXT, formato `trip-{hex8}`) |
| `itinerary_items` | Items del itinerario | `id` (TEXT, formato `item-{hex8}`) |
| `chats` | Conversaciones | `chat_id` (TEXT) |
| `chat_messages` | Mensajes de chat | `id` (UUID auto) |
| `feedbacks` | Feedback post-viaje | `trip_id` (FK a trips, UNIQUE) |

- Schema en `scripts/schema.sql` (ejecutar en Supabase SQL Editor)
- Script de migración JSON a Supabase: `scripts/migrate_to_supabase.py`
- Trigger `trg_recalc_budget` recalcula `trips.budget_total` automáticamente al modificar items
- RLS habilitado; service_role key bypasea RLS por defecto
- Datos LLM (ChromaDB + checkpoints) siguen en `data/llm_data/` (local)

## Autenticación (OAuth)

**Condicional por Authlib + secrets.toml:**
- `auth_service.py` verifica al importar si `authlib` está instalado (`_AUTHLIB_AVAILABLE`). Si no está o faltan credenciales OAuth en `.streamlit/secrets.toml`, la app funciona en modo demo (`DEMO_USER_ID`).
- Si OAuth está habilitado: `require_auth()` en app.py bloquea usuarios no autenticados con `st.login("google")`. Tras el callback, `get_or_create_user()` crea el registro en Supabase.
- **`st.logout()` es una acción inmediata, NO un botón.** Siempre envolverlo en `if st.button(): st.logout()`. Llamarlo directamente desloguea al usuario en cada rerun.

**Multi-usuario:** Todos los servicios aceptan `user_id`. Supabase aísla datos por `user_id` (FK en todas las tablas). RLS habilitado para seguridad adicional.

## Chat — Dual mode (LLM / Mock)

- `agent_service.py` detecta `OPENAI_API_KEY` en el entorno. Si presente, delega consultas informativas a `llm_agent_service.py` → `llm_chatbot.py` (LangGraph + OpenAI gpt-4.1-nano). Si ausente, usa pattern matching mock.
- Las **acciones que modifican datos** (crear viaje, agregar/eliminar items) **siempre** pasan por el mock para generar confirmaciones con botones UI, nunca por el LLM.
- Los mensajes son dicts con `{role, type, content}`. `type` puede ser `"text"`, `"card"` (tarjeta rica), `"confirmation"` (acción pendiente con botones Confirmar/Cancelar) o `"hotel_results"` (resultados de Booking.com). Las confirmaciones procesadas se marcan con `msg["processed"] = True`.

**Prioridad de ruteo en `agent_service.py`** (orden estricto):
1. **Flujo de creación de viaje** (`trip_creation_flow.py`) — detecta intención de crear viaje, maneja multi-turn
2. **Agregar/eliminar item** — pattern matching simple ("agregar", "eliminar") → confirmación UI
3. **Búsqueda de hoteles** — si Booking.com activo y keywords de hotel detectados
4. **LLM** — consultas informativas van a OpenAI gpt-4.1-nano
5. **Fallback** — mensaje de "IA no disponible" si no hay API key

**Detección de intención de creación de viaje** (`trip_creation_flow.py`):
- Keywords **fuertes** ("quiero ir", "crear viaje", "me gustaría ir") → siempre disparan creación
- Keywords **débiles** ("viaje", "vacaciones", "visitar") → NO disparan si el mensaje es una pregunta (`?`, `¿`) o refiere a un viaje existente ("mi viaje", "el viaje", "del viaje")
- Protección anti-duplicado: si hay viaje activo al mismo destino, no inicia creación

**Multi-conversación:** `chat_service.py` gestiona múltiples chats por usuario. Cada chat tiene `{chat_id, user_id, trip_id, title, messages}`. Auto-genera título desde el primer mensaje. Persistido en Supabase (tablas `chats` + `chat_messages`).

**LLM Backend (LangGraph + OpenAI):**
- `services/llm_chatbot.py` — `TripChatbot` (singleton). Pipeline LangGraph de 4 nodos secuenciales: memory_retrieval → context_optimization → response_generation → memory_extraction.
- `services/memory_manager.py` — `TripMemoryManager`. ChromaDB para memorias vectoriales (importancia >= 2), SQLite para checkpoints LangGraph. Datos en `data/llm_data/`.
- El system prompt inyecta: memorias vectoriales del usuario, contexto del viaje activo (destino, fechas, presupuesto, items), y perfil del usuario.

**Búsqueda de hoteles (Booking.com):**
- `booking_service.py` — Cliente HTTP (httpx) contra RapidAPI DataCrawler (`booking-com15.p.rapidapi.com`).
- Flujo: `search_destinations(query)` → obtener `dest_id` → `search_hotels(dest_id, checkin, checkout)` → `format_hotels_as_cards()`.
- `search_hotels_for_trip(trip)` — Wrapper que extrae destino y fechas del viaje activo automáticamente.
- Cache en memoria con TTL de 1 hora. Si `RAPIDAPI_KEY` no está configurada, retorna listas vacías.
- `agent_service.py` detecta intención de buscar hoteles en el chat y rutea a este servicio.

**MCP Server:**
- `mcp_servers/booking_server.py` — Servidor FastMCP standalone que expone `buscar_destinos` y `buscar_hoteles` como tools.
- Transporte: stdio. Ejecutable con `python mcp_servers/booking_server.py`.
- Reutiliza `services/booking_service.py` internamente.

## Reglas de negocio críticas

1. **Items con `status="sugerido"` NO se contabilizan en presupuesto** (REQ-UI-006 RN-002). Filtrar por `ItemStatus.SUGGESTED` antes de cualquier cálculo financiero.
2. **Auto-update de estado por fecha** (en cada carga): `today > end_date` → "completado"; `start_date <= today <= end_date` → "en_curso".
3. **Prioridad de viaje activo:** ID explícito > primer viaje "en_planificacion" > "confirmado" (por fecha) > "en_curso".
4. **Solo se pueden eliminar viajes en estado "en_planificacion".**
5. **Feedback solo disponible para viajes completados** — `feedback_service.py` filtra por `TripStatus.COMPLETED`.

## Convenciones

- Viajes y items son **dicts**, no objetos tipados, a lo largo de toda la app
- IDs usan formato `trip-{hex8}` / `item-{hex8}` / `chat-{hex8}` / `user-{hex8}` generados con `uuid.uuid4().hex[:8]`
- Fechas como strings ISO `"YYYY-MM-DD"`, horas como `"HH:MM"`
- Items usan `day` (int, 1-based) para posición temporal relativa al inicio del viaje
- Enums en `config/settings.py` usan valores en español (`"en_planificacion"`, `"confirmado"`, `"sugerido"`, etc.)
- Persistencia: write-through a Supabase (tablas: users, profiles, trips, itinerary_items, chats, chat_messages, feedbacks)
- Cada página envuelve su contenido en `try/except` con botón "Reintentar"
- `OPENAI_API_KEY` en `.env` habilita el LLM; sin ella, la app funciona idénticamente en modo mock
- Servicios que dependen de APIs externas (OpenAI, Booking.com) degradan graciosamente: retornan vacío o usan fallback mock
- Singletons para `TripChatbot` y `TripMemoryManager` — una instancia por proceso

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
| `httpx>=0.25.0` | Cliente HTTP para Booking.com API |
| `mcp[cli]>=1.2.0` | Servidor MCP (FastMCP) |
| `supabase>=2.0.0` | Cliente Supabase (persistencia PostgreSQL) |
| `pydantic>=2.0.0` | Modelos estructurados (memoria LLM) |

## Documentación de requerimientos

En `Requerimientos/MVP/` hay especificaciones detalladas:
- **`Chatbot_Login/`** — REQ-CL-001 a REQ-CL-005: login, chatbot, integración LLM, multi-conversación
- **`UI/`** — REQ-UI-001 a REQ-UI-012: dashboard, itinerario, cronograma, presupuesto, perfil, mis viajes, feedback, alertas

## Idioma

- Todas las respuestas y comunicaciones deben ser en español.
- Términos técnicos y nombres de código se mantienen en su forma original (inglés).
