---
name: Trip Planner MVP - Contexto del proyecto
description: Proyecto Trip Planner, agente de planificacion de viajes con interfaz web agentica. MVP incluye 7 secciones principales. Requerimientos generados en 3 areas (UI, Chatbot/Login, Chatbot_Funcionalities).
type: project
---

Trip Planner es un sistema de planificacion de viajes basado en un agente conversacional. El MVP cubre solo la interfaz web.

**Secciones del MVP:** Dashboard, Chat con Agente, Cronograma/Calendario, Itinerario Detallado, Presupuesto, Perfil y Preferencias, Mis Viajes.

**Estados de viaje:** En planificacion, Confirmado, En curso, Completado.

**Estados de items del itinerario:** Confirmado, Pendiente, Sugerido.

**Categorias de presupuesto:** Vuelos, Alojamiento, Actividades, Comidas, Transporte local, Extras.

**Chat dual mode:** Modo LLM (OpenAI gpt-4.1-nano via LangGraph) si OPENAI_API_KEY esta configurada; modo mock (pattern matching) si no. Acciones que modifican datos siempre pasan por mock con confirmaciones UI.

**Persistencia actual:** Supabase (PostgreSQL) como fuente de verdad persistente. Tablas: users, profiles, trips, itinerary_items, chats, chat_messages, feedbacks. ChromaDB (memorias vectoriales) y SQLite (checkpoints LangGraph) en data/llm_data/ (local).

**Requerimientos generados:**
- REQ-UI-001 a REQ-UI-012 (2026-03-14) — almacenados en `Requerimientos/MVP/UI/`
- REQ-CL-001 a REQ-CL-005 (2026-03-14) — almacenados en `Requerimientos/MVP/Chatbot_Login/`
- REQ-CF-001 (2026-03-16) — almacenado en `Requerimientos/MVP/Chatbot_Funcionalities/` — Selector Obligatorio de Viaje antes del Chat
- REQ-CF-002 (2026-03-16) — almacenado en `Requerimientos/MVP/Chatbot_Funcionalities/` — Creacion de Eventos en el Cronograma desde el Chatbot (multi-dia, campo end_day)
- REQ-CF-003 (2026-03-16) — almacenado en `Requerimientos/MVP/Chatbot_Funcionalities/` — Creacion de Items en el Itinerario desde el Chatbot con Extraccion Inteligente de Datos (extraccion NLP/regex de nombre, fecha, hora, tipo, ubicacion; flujo multi-turn; confirmacion con tarjeta rica; deteccion de conflictos horarios; dual-mode LLM/mock)

**Area Chatbot_Funcionalities:** Requerimientos funcionales del chatbot que modifican su comportamiento y logica de interaccion. Diferente de Chatbot_Login (autenticacion y estructura multi-chat) y UI (interfaz visual).

**Why:** El usuario es analista/PO trabajando en la documentacion funcional del MVP de Trip Planner.

**How to apply:** Usar estas entidades, estados y categorias como vocabulario establecido del dominio en futuras conversaciones sobre este proyecto.
