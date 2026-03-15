# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proyecto

Trip Planner — MVP de un agente de planificación de viajes con interfaz Streamlit. Multi-usuario con Google OAuth (fallback a modo demo sin auth). Persistencia local en JSON. Agente conversacional dual: LLM (Gemini via LangGraph) cuando `GOOGLE_API_KEY` está presente, o mock por pattern matching.

## Comandos

```bash
pip install -r requirements.txt        # Instalar dependencias
python -m streamlit run app.py         # Ejecutar la app (localhost:8501)
.\run.bat                              # Windows: lanza con el venv explícitamente
```

Siempre usar `python -m streamlit run app.py` (no `streamlit run app.py`) para asegurar que se use el Python del venv. El proyecto tiene múltiples instalaciones de Python en la máquina; `run.bat` fuerza el uso de `venv\Scripts\python.exe`.

No hay tests ni linter configurados actualmente.

## Arquitectura

**Flujo de datos:** `st.session_state.trips` (lista de dicts) es la fuente única de verdad durante la sesión. Las páginas leen/mutan esta lista. Tras cualquier mutación, llamar `sync_trip_changes()` para recalcular presupuesto y persistir a JSON.

**Capas:**
- **`app.py`** — Punto de entrada. Configura `st.set_page_config(layout="wide")`, inyecta CSS global, ejecuta guard de autenticación, inicializa `session_state` (trips, active_trip_id, user_chats, active_chat_id, dismissed_alerts, user_profile, current_user), configura `st.navigation()` con 7 páginas, renderiza sidebar con viaje activo. Carga `.env` con `load_dotenv()` al inicio.
- **`services/`** — Lógica de negocio pura (sin Streamlit). `trip_service.py` es el servicio central: CRUD de viajes, agrupación de items por día, aceptar/descartar sugerencias, sincronización con JSON. `agent_service.py` procesa mensajes con LLM o mock. `auth_service.py` gestiona OAuth y usuarios. `chat_service.py` gestiona multi-conversación.
- **`pages/`** — Cada página lee `st.session_state.trips`, obtiene el viaje activo vía `get_active_trip()`, y renderiza su sección. Páginas que requieren viaje activo redirigen a Mis Viajes si no hay uno.
- **`components/`** — Widgets reutilizables que reciben datos y retornan acciones del usuario como dicts (ej: `{"action": "accept", "item_id": "..."}`).
- **`config/settings.py`** — Enums (`TripStatus`, `ItemStatus`, `ItemType`, `BudgetCategory`), paletas de colores, iconos y labels en español. `DEMO_USER_ID = "user-demo0001"`.
- **`config/llm_config.py`** — Configuración del LLM: modelo Gemini (`gemini-2.5-flash`), temperatura, embeddings (`models/embedding-001`), categorías de memoria vectorial.
- **`data/sample_data.py`** — 3 viajes demo hardcodeados (Tokio, Barcelona, Lima) con ~32 items. Se cargan automáticamente si no hay datos para el usuario.

**Modelos de datos:** Los viajes e items son dicts planos (no dataclasses en runtime). Los modelos en `models/` tienen `to_dict()`/`from_dict()` pero no se usan actualmente — los services operan directo sobre dicts. Un item se anida dentro de `trip["items"]` (lista de dicts).

## Autenticación (OAuth)

**Condicional por Authlib + secrets.toml:**
- `auth_service.py` verifica al importar si `authlib` está instalado (`_AUTHLIB_AVAILABLE`). Si no está o faltan credenciales OAuth en `.streamlit/secrets.toml`, la app funciona en modo demo (`DEMO_USER_ID`).
- Si OAuth está habilitado: `require_auth()` en app.py bloquea usuarios no autenticados con `st.login("google")`. Tras el callback, `get_or_create_user()` crea el registro en `data/users.json`.
- **`st.logout()` es una acción inmediata, NO un botón.** Siempre envolverlo en `if st.button(): st.logout()`. Llamarlo directamente desloguea al usuario en cada rerun.

**Multi-usuario:** Todos los servicios aceptan `user_id`. `save_trips_for_user()` lee el JSON completo, reemplaza solo los viajes del usuario, y fusiona. Esto previene sobreescritura entre usuarios.

## Chat — Dual mode (LLM / Mock)

- `agent_service.py` detecta `GOOGLE_API_KEY` en el entorno. Si presente, delega consultas informativas a `llm_agent_service.py` → `llm_chatbot.py` (LangGraph + Gemini). Si ausente, usa pattern matching mock.
- Las **acciones que modifican datos** (crear viaje, agregar/eliminar items) **siempre** pasan por el mock para generar confirmaciones con botones UI, nunca por el LLM.
- Los mensajes son dicts con `{role, type, content}`. `type` puede ser `"text"`, `"card"` (tarjeta rica) o `"confirmation"` (acción pendiente con botones Confirmar/Cancelar). Las confirmaciones procesadas se marcan con `msg["processed"] = True`.

**Multi-conversación:** `chat_service.py` gestiona múltiples chats por usuario. Cada chat tiene `{chat_id, user_id, trip_id, title, messages}`. Auto-genera título desde el primer mensaje. Persistido en `data/chats.json`.

**LLM Backend (LangGraph + Gemini):**
- `services/llm_chatbot.py` — `TripChatbot` (singleton). Pipeline LangGraph de 4 nodos secuenciales: memory_retrieval → context_optimization → response_generation → memory_extraction.
- `services/memory_manager.py` — `TripMemoryManager`. ChromaDB para memorias vectoriales (importancia >= 2), SQLite para checkpoints LangGraph. Datos en `data/llm_data/`.
- El system prompt inyecta: memorias vectoriales del usuario, contexto del viaje activo (destino, fechas, presupuesto, items), y perfil del usuario.

## Reglas de negocio críticas

1. **Items con `status="sugerido"` NO se contabilizan en presupuesto** (REQ-UI-006 RN-002). Filtrar por `ItemStatus.SUGGESTED` antes de cualquier cálculo financiero.
2. **Auto-update de estado por fecha** (en cada carga): `today > end_date` → "completado"; `start_date <= today <= end_date` → "en_curso".
3. **Prioridad de viaje activo:** ID explícito > primer viaje "en_planificacion" > "confirmado" (por fecha) > "en_curso".

## Convenciones

- Viajes y items son **dicts**, no objetos tipados, a lo largo de toda la app
- IDs usan formato `trip-{hex8}` / `item-{hex8}` / `chat-{hex8}` / `user-{hex8}` generados con `uuid.uuid4().hex[:8]`
- Fechas como strings ISO `"YYYY-MM-DD"`, horas como `"HH:MM"`
- Items usan `day` (int, 1-based) para posición temporal relativa al inicio del viaje
- Enums en `config/settings.py` usan valores en español (`"en_planificacion"`, `"confirmado"`, `"sugerido"`, etc.)
- Persistencia: write-through a `data/trips.json`, `data/chats.json`, `data/profiles.json`, `data/users.json`
- Cada página envuelve su contenido en `try/except` con botón "Reintentar"
- `GOOGLE_API_KEY` en `.env` habilita el LLM; sin ella, la app funciona idénticamente en modo mock

## Idioma

- Todas las respuestas y comunicaciones deben ser en español.
- Términos técnicos y nombres de código se mantienen en su forma original (inglés).
