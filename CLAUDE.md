# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proyecto

Trip Planner — MVP de un agente de planificación de viajes con interfaz Streamlit. Usuario único, persistencia local en JSON, agente conversacional mock (pattern matching, sin LLM).

## Comandos

```bash
pip install -r requirements.txt        # Instalar dependencias
python -m streamlit run app.py         # Ejecutar la app (localhost:8501)
```

No hay tests ni linter configurados actualmente.

## Arquitectura

**Flujo de datos:** `st.session_state.trips` (lista de dicts) es la fuente única de verdad. Las páginas leen/mutan esta lista. Tras cualquier mutación, llamar `sync_trip_changes()` para recalcular presupuesto y persistir a JSON.

**Capas:**
- **`app.py`** — Punto de entrada. Configura `st.set_page_config(layout="wide")`, inyecta CSS global, inicializa `session_state` (trips, active_trip_id, chat_histories, dismissed_alerts, user_profile), configura `st.navigation()` con 7 páginas, renderiza sidebar con viaje activo. Carga `.env` con `load_dotenv()` al inicio.
- **`services/`** — Lógica de negocio pura (sin Streamlit). `trip_service.py` es el servicio central: CRUD de viajes, agrupación de items por día, aceptar/descartar sugerencias, sincronización con JSON. `agent_service.py` procesa mensajes con LLM (Gemini) si `GOOGLE_API_KEY` está configurada, o fallback a pattern matching por keywords. Retorna dicts con `type: "text"|"card"|"confirmation"`.
- **`pages/`** — Cada página lee `st.session_state.trips`, obtiene el viaje activo vía `get_active_trip()`, y renderiza su sección. Páginas que requieren viaje activo redirigen a Mis Viajes si no hay uno.
- **`components/`** — Widgets reutilizables que reciben datos y retornan acciones del usuario como dicts (ej: `{"action": "accept", "item_id": "..."}`).
- **`config/settings.py`** — Enums (`TripStatus`, `ItemStatus`, `ItemType`, `BudgetCategory`), paletas de colores, iconos y labels en español. Todos los mapeos globales viven aquí.
- **`config/llm_config.py`** — Configuración del LLM: modelo Gemini, temperatura, embeddings, categorías de memoria vectorial.
- **`data/sample_data.py`** — 3 viajes demo hardcodeados (Tokio, Barcelona, Lima) con ~32 items. Se cargan automáticamente si `trips.json` está vacío.

**Modelos de datos:** Los viajes e items son dicts planos (no dataclasses en runtime). Los modelos en `models/` tienen `to_dict()`/`from_dict()` pero no se usan actualmente — los services operan directo sobre dicts. Un item se anida dentro de `trip["items"]` (lista de dicts).

**Chat — Dual mode (LLM / Mock):**
- `agent_service.py` detecta `GOOGLE_API_KEY` en el entorno. Si presente, delega consultas informativas a `llm_agent_service.py` → `llm_chatbot.py` (LangGraph + Gemini). Si ausente, usa pattern matching mock.
- Las **acciones que modifican datos** (crear viaje, agregar/eliminar items) **siempre** pasan por el mock para generar confirmaciones con botones UI, nunca por el LLM.
- Los mensajes son dicts con `{role, type, content}`. `type` puede ser `"text"`, `"card"` (tarjeta rica) o `"confirmation"` (acción pendiente con botones Confirmar/Cancelar). Las confirmaciones procesadas se marcan con `msg["processed"] = True`.
- Los historiales se guardan en `st.session_state.chat_histories[trip_id]`.

**LLM Backend (LangGraph + Gemini):**
- `services/llm_chatbot.py` — `TripChatbot` (singleton). Pipeline LangGraph de 4 nodos secuenciales: memory_retrieval → context_optimization → response_generation → memory_extraction.
- `services/memory_manager.py` — `TripMemoryManager`. ChromaDB para memorias vectoriales, SQLite para checkpoints LangGraph. Datos en `data/llm_data/`.
- El system prompt inyecta: memorias vectoriales del usuario, contexto del viaje activo (destino, fechas, presupuesto, items), y perfil del usuario.
- Memorias se extraen automáticamente de mensajes del usuario (importancia >= 2) y se guardan en ChromaDB para enriquecer futuras respuestas.

**Regla de negocio crítica:** Items con `status="sugerido"` NO se contabilizan en presupuesto (REQ-UI-006 RN-002). Filtrar por `ItemStatus.SUGGESTED` antes de cualquier cálculo financiero.

## Convenciones

- Viajes y items son **dicts**, no objetos tipados, a lo largo de toda la app
- IDs usan formato `trip-{hex8}` / `item-{hex8}` generados con `uuid.uuid4().hex[:8]`
- Fechas como strings ISO `"YYYY-MM-DD"`, horas como `"HH:MM"`
- Items usan `day` (int, 1-based) para posición temporal relativa al inicio del viaje
- Enums en `config/settings.py` usan valores en español (`"en_planificacion"`, `"confirmado"`, etc.)
- Persistencia: write-through a `data/trips.json` y `data/profiles.json`
- Cada página envuelve su contenido en `try/except` con botón "Reintentar"
- `GOOGLE_API_KEY` en `.env` habilita el LLM; sin ella, la app funciona idénticamente en modo mock

## Idioma

- Todas las respuestas y comunicaciones deben ser en español.
- Términos técnicos y nombres de código se mantienen en su forma original (inglés).
