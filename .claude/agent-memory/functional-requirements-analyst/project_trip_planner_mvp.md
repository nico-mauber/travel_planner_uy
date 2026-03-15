---
name: Trip Planner MVP - Contexto del proyecto
description: Proyecto Trip Planner, agente de planificacion de viajes con interfaz web agentica. MVP incluye 7 secciones principales. 14 requerimientos generados en 2 areas (UI y Chatbot/Login).
type: project
---

Trip Planner es un sistema de planificacion de viajes basado en un agente conversacional. El MVP cubre solo la interfaz web.

**Secciones del MVP:** Dashboard, Chat con Agente, Cronograma/Calendario, Itinerario Detallado, Presupuesto, Perfil y Preferencias, Mis Viajes.

**Estados de viaje:** En planificacion, Confirmado, En curso, Completado.

**Estados de items del itinerario:** Confirmado, Pendiente, Sugerido.

**Categorias de presupuesto:** Vuelos, Alojamiento, Actividades, Comidas, Transporte local, Extras.

**Chat dual mode:** Modo LLM (Gemini via LangGraph) si GOOGLE_API_KEY esta configurada; modo mock (pattern matching) si no. Acciones que modifican datos siempre pasan por mock con confirmaciones UI.

**Persistencia actual:** trips.json (viajes), profiles.json (perfil unico), session_state.chat_histories (volatil), ChromaDB (memorias vectoriales), SQLite (checkpoints LangGraph). Todo en data/ y data/llm_data/.

**Requerimientos generados:**
- REQ-UI-001 a REQ-UI-012 (2026-03-14) — almacenados en `Requerimientos/MVP/UI/`
- REQ-CHAT-LOGIN-001 y REQ-CHAT-LOGIN-002 (2026-03-14) — almacenados en `Requerimientos/MVP/Chatbot&Login/`

**Why:** El usuario es analista/PO trabajando en la documentacion funcional del MVP de Trip Planner.

**How to apply:** Usar estas entidades, estados y categorias como vocabulario establecido del dominio en futuras conversaciones sobre este proyecto.
