# Documentacion General del Sistema — Trip Planner

**Fecha de generacion:** 2026-03-27
**Version del sistema:** MVP (Minimum Viable Product)

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Estructura de Archivos](#3-estructura-de-archivos)
4. [Modelos de Datos](#4-modelos-de-datos)
5. [Enums y Constantes](#5-enums-y-constantes)
6. [Servicios](#6-servicios)
7. [Componentes UI](#7-componentes-ui)
8. [Paginas](#8-paginas)
9. [Sistema de Chat](#9-sistema-de-chat)
10. [Persistencia](#10-persistencia)
11. [Configuracion](#11-configuracion)
12. [Reglas de Negocio](#12-reglas-de-negocio)
13. [Dependencias y Ejecucion](#13-dependencias-y-ejecucion)

---

## 1. Resumen Ejecutivo

### Que es Trip Planner

Trip Planner es un **MVP de un agente de planificacion de viajes** con interfaz web construida en Streamlit. Es una aplicacion **multi-usuario con Google OAuth** (fallback a modo demo sin autenticacion). Permite planificar viajes completos: itinerarios dia a dia, presupuestos por categoria con gastos directos, cronograma visual global, y un chat conversacional con un agente LLM (OpenAI gpt-5-nano via LangGraph). Incluye busqueda real de hoteles (Booking.com via RapidAPI) y vuelos (SerpAPI Google Flights + fast-flights fallback). La persistencia se realiza en **Supabase (PostgreSQL)**.

### Usuario Objetivo

Multiples viajeros que desean planificar uno o mas viajes con asistencia de un agente conversacional inteligente. El sistema soporta multi-usuario con aislamiento de datos por `user_id`. Autenticacion via Google OAuth (requiere Authlib + credenciales en `.streamlit/secrets.toml`). Sin OAuth, opera en modo demo con `DEMO_USER_ID`.

### Stack Tecnologico

| Tecnologia | Version minima | Proposito |
|---|---|---|
| Python | 3.x | Lenguaje principal |
| Streamlit | >= 1.42.0 | Framework de interfaz web (pages, session_state, login/logout) |
| Authlib | >= 1.3.2 | Google OAuth condicional |
| Plotly | >= 5.18.0 | Graficos de presupuesto (donut, barras) |
| streamlit-calendar | >= 1.2.0 | Vista de calendario interactiva (FullCalendar.js) |
| python-dotenv | >= 1.0.0 | Carga de variables de entorno desde `.env` |
| langchain-openai | >= 0.3.0 | Integracion con OpenAI gpt-5-nano |
| langchain-core | >= 0.3.0 | Primitivas de LangChain (prompts, mensajes, parsers) |
| langgraph | >= 0.2.0 | Pipeline de nodos del chatbot |
| langgraph-checkpoint | >= 2.0.0 | Persistencia de checkpoints de LangGraph |
| langgraph-checkpoint-sqlite | >= 3.0.0 | Checkpointer SQLite para LangGraph |
| langchain-chroma | >= 0.2.0 | Integracion LangChain + ChromaDB |
| chromadb | >= 0.5.0 | Base de datos vectorial para memorias |
| pydantic | >= 2.0.0 | Modelos estructurados (memoria LLM + schema `ItemExtractionResult`) |
| typing_extensions | >= 4.8.0 | Extensiones de tipado para Python |
| httpx | >= 0.25.0 | Cliente HTTP para Booking.com API y SerpAPI |
| fast-flights | >= 2.2.0 | Scraper de Google Flights (fallback de busqueda de vuelos sin API key) |
| airportsdata | >= 20250101 | Base de datos de 7800+ aeropuertos con codigos IATA |
| mcp[cli] | >= 1.2.0 | Servidor MCP standalone (FastMCP) |
| supabase | >= 2.0.0 | Cliente Supabase (persistencia PostgreSQL) |

### Estado Actual

MVP funcional multi-usuario. No hay tests ni linter configurados. El sistema soporta 3 viajes de ejemplo precargados (Tokio, Barcelona, Lima). El agente conversacional opera exclusivamente via LLM (OpenAI gpt-5-nano). Sin `OPENAI_API_KEY`, el chat muestra "IA no disponible" y redirige al usuario a la UI. Integracion con Booking.com para hoteles reales y SerpAPI/fast-flights para vuelos reales.

---

## 2. Arquitectura del Sistema

### Diagrama de Capas

```
┌─────────────────────────────────────────────────────────────────┐
│                        CAPA DE PRESENTACION                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  app.py  (Punto de entrada, config, OAuth guard,          │  │
│  │           session_state, navegacion, sidebar)              │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  pages/                                                    │  │
│  │  1_Dashboard | 2_Chat | 3_Cronograma | 4_Itinerario       │  │
│  │  5_Presupuesto | 6_Perfil | 7_Mis_Viajes                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  components/                                               │  │
│  │  chat_widget | budget_charts | trip_card                   │  │
│  │  itinerary_item | alert_banner                             │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        CAPA DE SERVICIOS                        │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │  trip_service.py         │  │  agent_service.py (LLM-Only)│  │
│  │  budget_service.py       │  │  llm_item_extraction.py     │  │
│  │  expense_service.py      │  │  llm_agent_service.py       │  │
│  │  profile_service.py      │  │  llm_chatbot.py (LangGraph) │  │
│  │  weather_service.py      │  │  memory_manager.py (ChromaDB)│  │
│  │  feedback_service.py     │  │  item_utils.py              │  │
│  │  chat_service.py         │  │  trip_creation_flow.py      │  │
│  │  auth_service.py         │  │  booking_service.py         │  │
│  │  supabase_client.py      │  │  flight_service.py          │  │
│  └─────────────────────────┘  └─────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                     CAPA DE CONFIGURACION                       │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │  config/settings.py │  │  config/llm_config │                │
│  └────────────────────┘  └────────────────────┘                │
├─────────────────────────────────────────────────────────────────┤
│                     CAPA DE PERSISTENCIA                        │
│  ┌──────────────────────────────┐  ┌──────────────────────────┐│
│  │  Supabase (PostgreSQL)        │  │  data/llm_data/          ││
│  │  ┌─────────────────────────┐  │  │   chromadb/ (vectores)   ││
│  │  │ users, profiles, trips  │  │  │   langgraph_memory.db    ││
│  │  │ itinerary_items         │  │  └──────────────────────────┘│
│  │  │ expenses, chats         │  │                              │
│  │  │ chat_messages, feedbacks│  │                              │
│  │  └─────────────────────────┘  │                              │
│  └──────────────────────────────┘                               │
├─────────────────────────────────────────────────────────────────┤
│                     CAPA MCP                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  mcp_servers/booking_server.py (FastMCP standalone, stdio) │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo de Datos Principal

```
st.session_state.trips  (fuente de verdad en runtime)
         │
         ├──> Paginas leen trips y obtienen viaje activo via selectbox propio
         │
         ├──> Usuario interactua (chat, botones, formularios)
         │
         ├──> Servicios mutan trips[] (agregar/eliminar items, cambiar estados)
         │
         ├──> sync_trip_changes() recalcula presupuesto + persiste a Supabase
         │
         └──> st.rerun() refresca la pagina con datos actualizados
```

### Patron de Comunicacion entre Componentes

1. **Paginas** leen `st.session_state.trips` y obtienen el viaje activo via `st.selectbox` propio (Dashboard, Itinerario, Presupuesto) o selector obligatorio (Chat).
2. **Componentes** reciben datos como parametros y retornan acciones como dicts (ej: `{"action": "accept", "item_id": "..."}`).
3. **Paginas** interpretan la accion retornada y llaman al servicio correspondiente.
4. **Servicios** mutan los datos en memoria y persisten a Supabase (write-through).
5. La pagina llama `st.rerun()` para refrescar la UI.

### Puntos de Entrada y Salida

- **Entrada principal:** `app.py` es el unico punto de entrada de la app web. Se ejecuta con `python -m streamlit run app.py`.
- **Entrada MCP:** `mcp_servers/booking_server.py` — servidor MCP standalone ejecutable con `python mcp_servers/booking_server.py` (transporte stdio).
- **Salida de datos:** Supabase (PostgreSQL) para toda la persistencia de negocio; bases de datos locales en `data/llm_data/` para el LLM.

---

## 3. Estructura de Archivos

```
Trip_Planner/
├── .env                              # Variables: SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY, RAPIDAPI_KEY, SERPAPI_KEY
├── .gitignore                        # Excluye: .env, data/llm_data/, venv/, __pycache__/
├── .streamlit/
│   ├── config.toml                   # Tema y configuracion de Streamlit
│   └── secrets.toml                  # Credenciales Google OAuth (no en repo, ver secrets.toml.example)
├── CLAUDE.md                         # Instrucciones para Claude Code
├── DOCUMENTACION_SISTEMA.md          # Este documento
├── app.py                            # Punto de entrada: config, OAuth guard, session_state, navegacion, sidebar
├── requirements.txt                  # Dependencias de Python
├── run.bat                           # Windows: lanza la app con el venv explicitamente
│
├── config/
│   ├── __init__.py                   # Vacio
│   ├── settings.py                   # Enums, colores, iconos, labels, mapeos globales, DEMO_USER_ID
│   └── llm_config.py                 # Modelo OpenAI gpt-5-nano, embeddings, temperatura, memoria
│
├── components/
│   ├── __init__.py                   # Vacio
│   ├── alert_banner.py               # Alertas descartables del viaje
│   ├── budget_charts.py              # Graficos Plotly (donut, barras comparativas)
│   ├── chat_widget.py                # Tarjetas ricas, confirmaciones, resultados de hoteles/vuelos
│   ├── itinerary_item.py             # Item expandible del itinerario + traslados
│   └── trip_card.py                  # Tarjeta de viaje para la lista Mis Viajes
│
├── data/
│   ├── __init__.py                   # Vacio
│   ├── sample_data.py                # 3 viajes demo + perfil ejemplo + chat histories
│   └── llm_data/                     # (gitignored)
│       ├── chromadb/                 # Base vectorial ChromaDB
│       ├── langgraph_memory.db       # Checkpoints de LangGraph (SQLite)
│       ├── langgraph_memory.db-shm   # Shared memory de SQLite
│       └── langgraph_memory.db-wal   # Write-ahead log de SQLite
│
├── models/
│   ├── __init__.py                   # Vacio
│   ├── trip.py                       # Dataclass Trip con to_dict()/from_dict()
│   ├── itinerary_item.py             # Dataclass ItineraryItem
│   ├── budget.py                     # Dataclass BudgetSummary + funcion de calculo
│   ├── user_profile.py               # Dataclass UserProfile
│   └── feedback.py                   # Dataclasses ItemFeedback y TripFeedback
│
├── pages/
│   ├── 1_Dashboard.py                # Panel overview del viaje activo
│   ├── 2_Chat.py                     # Chat multi-conversacion con selector obligatorio de viaje
│   ├── 3_Cronograma.py               # Vista de calendario global (todos los viajes)
│   ├── 4_Itinerario.py               # Itinerario dia por dia
│   ├── 5_Presupuesto.py              # Desglose de presupuesto por categoria + gastos directos
│   ├── 6_Perfil.py                   # Configuracion de preferencias + info OAuth
│   └── 7_Mis_Viajes.py               # Lista de viajes + crear/eliminar + feedback
│
├── services/
│   ├── __init__.py                   # Vacio
│   ├── supabase_client.py            # Cliente Supabase singleton (credenciales de .env o st.secrets)
│   ├── auth_service.py               # OAuth condicional (Authlib + secrets.toml), guard, CRUD usuarios
│   ├── trip_service.py               # CRUD viajes, agrupacion, sync con Supabase, presupuesto
│   ├── agent_service.py              # Dispatcher LLM-Only del chat, sanitizacion, ruteo por intent
│   ├── llm_item_extraction.py        # Extraccion via LLM structured output (ItemExtractionResult, 30 campos)
│   ├── item_utils.py                 # Utilidades puras: validacion, conflictos horarios, drafts
│   ├── trip_creation_flow.py         # Flujo multi-turn de creacion de viajes, regex de fechas
│   ├── llm_agent_service.py          # Wrapper delgado sobre TripChatbot
│   ├── llm_chatbot.py                # TripChatbot (singleton), pipeline LangGraph 4 nodos (OpenAI)
│   ├── memory_manager.py             # TripMemoryManager, ChromaDB para memorias vectoriales
│   ├── chat_service.py               # Multi-conversacion por usuario, CRUD chats en Supabase
│   ├── booking_service.py            # Cliente Booking.com via RapidAPI DataCrawler (cache, retry 429)
│   ├── flight_service.py             # SerpAPI Google Flights + fast-flights fallback, airportsdata
│   ├── budget_service.py             # Calculo de presupuesto por categoria (items + expenses)
│   ├── expense_service.py            # CRUD gastos directos (expenses) en Supabase
│   ├── profile_service.py            # Preferencias de usuario en Supabase
│   ├── weather_service.py            # Datos climaticos mock por destino
│   └── feedback_service.py           # Retroalimentacion post-viaje en Supabase
│
├── mcp_servers/
│   ├── __init__.py                   # Vacio
│   └── booking_server.py             # Servidor MCP standalone (FastMCP, stdio)
│
├── scripts/
│   └── setup_database.sql            # Schema Supabase (transaccional, idempotente)
│
└── Requerimientos/
    └── MVP/
        ├── Chatbot_Login/            # REQ-CL-001 a REQ-CL-005
        ├── Chatbot_Funcionalities/   # REQ-CF-001 a REQ-CF-003
        └── UI/                       # REQ-UI-001 a REQ-UI-012
```

---

## 4. Modelos de Datos

### 4.1. Estructura de un Trip (dict)

En runtime, los viajes son **dicts planos** (no dataclasses). La estructura completa:

| Campo | Tipo | Descripcion | Ejemplo |
|---|---|---|---|
| `id` | `str` | Identificador unico, formato `trip-{hex8}` | `"trip-001"` |
| `user_id` | `str` | ID del usuario propietario | `"user-abc12345"` |
| `name` | `str` | Nombre descriptivo del viaje | `"Aventura en Tokio"` |
| `destination` | `str` | Destino con ciudad y pais | `"Tokio, Japon"` |
| `start_date` | `str` | Fecha de inicio ISO YYYY-MM-DD | `"2026-04-10"` |
| `end_date` | `str` | Fecha de fin ISO YYYY-MM-DD | `"2026-04-16"` |
| `status` | `str` | Estado del viaje (valor de `TripStatus`) | `"en_planificacion"` |
| `budget_total` | `float` | Presupuesto total calculado (excluye sugeridos) | `3200.0` |
| `notes` | `str` | Notas libres del viaje | `"Viaje de primavera..."` |
| `items` | `list[dict]` | Lista de items del itinerario | `[{...}, {...}]` |
| `expenses` | `list[dict]` | Lista de gastos directos | `[{...}, {...}]` |

### 4.2. Estructura de un Item (dict)

Cada item vive anidado dentro de `trip["items"]`:

| Campo | Tipo | Descripcion | Ejemplo |
|---|---|---|---|
| `id` | `str` | Identificador unico, formato `item-{hex8}` | `"item-001"` |
| `trip_id` | `str` | ID del viaje padre | `"trip-001"` |
| `name` | `str` | Nombre de la actividad | `"Vuelo MVD -> Tokio"` |
| `item_type` | `str` | Tipo (valor de `ItemType`) | `"vuelo"` |
| `day` | `int` | Dia del viaje (1-based) | `1` |
| `end_day` | `int\|None` | Dia de fin para items multi-dia (>= day) | `3` |
| `start_time` | `str` | Hora de inicio HH:MM | `"06:00"` |
| `end_time` | `str` | Hora de fin HH:MM | `"22:00"` |
| `status` | `str` | Estado (valor de `ItemStatus`) | `"confirmado"` |
| `location` | `str` | Ubicacion corta | `"Aeropuerto Narita"` |
| `address` | `str` | Direccion completa | `"Narita International Airport, Chiba"` |
| `notes` | `str` | Notas descriptivas | `"ANA NH105 -- Escala en LAX 3h"` |
| `cost_estimated` | `float` | Costo estimado en USD | `850.0` |
| `cost_real` | `float` | Costo real en USD (0 si no aplica) | `820.0` |
| `booking_url` | `str` | URL de reserva (vacio si no hay) | `""` |
| `provider` | `str` | Proveedor del servicio | `"ANA"` |

### 4.3. Estructura de un Expense (gasto directo)

Cada gasto directo vive anidado dentro de `trip["expenses"]`:

| Campo | Tipo | Descripcion | Ejemplo |
|---|---|---|---|
| `id` | `str` | Identificador unico, formato `exp-{hex8}` | `"exp-a1b2c3d4"` |
| `trip_id` | `str` | ID del viaje padre | `"trip-001"` |
| `name` | `str` | Descripcion del gasto | `"Seguro de viaje"` |
| `category` | `str` | Categoria (valor de `BudgetCategory`) | `"extras"` |
| `amount` | `float` | Monto en USD | `120.0` |
| `notes` | `str` | Notas adicionales | `"Cobertura completa"` |

### 4.4. Estructura de un Mensaje de Chat

Los mensajes se almacenan como lista de dicts en cada chat (persistidos en Supabase tabla `chat_messages`).

#### Tipo `text`
```python
{
    "role": "user" | "assistant",
    "type": "text",
    "content": "Texto del mensaje en markdown"
}
```

#### Tipo `card` (tarjeta rica)
```python
{
    "role": "assistant",
    "type": "card",
    "content": {
        "card_type": "flight" | "hotel" | "activity" | "food",
        "name": "Nombre del servicio",
        "provider": "Nombre del proveedor",
        "price": 650.0,
        "location": "Ubicacion",
        "rating": "4.5 ★",          # solo hotel/food
        "departure": "08:00",       # solo flight
        "arrival": "14:30",         # solo flight
        "duration": "6h 30m",       # solo flight/activity
        "notes": "Descripcion adicional"
    }
}
```

#### Tipo `confirmation` (accion pendiente)
```python
{
    "role": "assistant",
    "type": "confirmation",
    "content": {
        "action": "add_item" | "remove_item" | "create_trip" | "calendar_event" | "add_expense" | "modify_expense" | "remove_expense",
        "summary": "Descripcion breve de la accion",
        "details": {
            # Campos especificos segun la accion
            # add_item: name, item_type, day, start_time, end_time, cost_estimated, location
            # remove_item: item_id, item_name o remove_all
            # create_trip: destination, name, start_date, end_date
            # add_expense: name, category, amount
        }
    },
    "processed": True | False,      # Se agrega cuando el usuario responde
    "result": "Texto del resultado"  # Se agrega junto con processed
}
```

#### Tipo `hotel_results` (resultados de Booking.com)
```python
{
    "role": "assistant",
    "type": "hotel_results",
    "content": {
        "hotels": [...],            # Lista de dicts con datos de hotel
        "summary": "Texto resumen"
    }
}
```

#### Tipo `flight_results` (resultados de vuelos)
```python
{
    "role": "assistant",
    "type": "flight_results",
    "content": {
        "flights": [...],           # Lista de dicts con datos de vuelo
        "summary": "Texto resumen"
    }
}
```

### 4.5. Estructura del Perfil de Usuario

Almacenado en `st.session_state.user_profile` y persistido en Supabase (tabla `profiles`):

```python
{
    "accommodation_types": ["Hotel", "Apartamento"],       # list[str]
    "food_restrictions": ["Sin gluten"],                   # list[str]
    "allergies": "Mani",                                   # str
    "travel_styles": ["Cultural", "Gastronomico"],         # list[str]
    "daily_budget": 150.0,                                 # float (USD/dia)
    "preferred_airlines": "LATAM, Iberia",                 # str (libre)
    "preferred_hotel_chains": "Marriott, Ibis"             # str (libre)
}
```

### 4.6. Estructura de Feedback

Persistido en Supabase (tabla `feedbacks`), con clave unica = trip_id:

```python
{
    "trip_id": "trip-003",
    "overall_rating": 4,          # int 1-5
    "comment": "Texto libre",      # str
    "item_feedbacks": [            # list[dict]
        {
            "item_id": "item-201",
            "item_name": "Vuelo MVD -> Lima",
            "rating": 4,           # int 1-5
            "comment": "Nota..."    # str
        }
    ],
    "skipped": False               # bool, True si fue omitido
}
```

### 4.7. Estructura de un Chat

Persistido en Supabase (tablas `chats` + `chat_messages`):

```python
{
    "chat_id": "chat-a1b2c3d4",
    "user_id": "user-abc12345",
    "trip_id": "trip-001",
    "title": "Planificando Tokio",
    "created_at": "2026-03-27T10:00:00",
    "last_activity_at": "2026-03-27T12:30:00",
    "messages": [...]              # Lista de dicts de mensajes
}
```

---

## 5. Enums y Constantes

Todas las constantes viven en `config/settings.py`.

### 5.1. Enums

#### TripStatus
| Valor del Enum | Valor string | Label en espanol |
|---|---|---|
| `PLANNING` | `"en_planificacion"` | En planificacion |
| `CONFIRMED` | `"confirmado"` | Confirmado |
| `IN_PROGRESS` | `"en_curso"` | En curso |
| `COMPLETED` | `"completado"` | Completado |

#### ItemStatus
| Valor del Enum | Valor string | Label |
|---|---|---|
| `CONFIRMED` | `"confirmado"` | Confirmado |
| `PENDING` | `"pendiente"` | Pendiente |
| `SUGGESTED` | `"sugerido"` | Sugerido |

#### ItemType
| Valor del Enum | Valor string | Label |
|---|---|---|
| `ACTIVITY` | `"actividad"` | Actividad |
| `TRANSFER` | `"traslado"` | Traslado |
| `ACCOMMODATION` | `"alojamiento"` | Alojamiento |
| `FOOD` | `"comida"` | Comida |
| `FLIGHT` | `"vuelo"` | Vuelo |
| `EXTRA` | `"extra"` | Extra |

#### BudgetCategory
| Valor del Enum | Valor string | Label |
|---|---|---|
| `FLIGHTS` | `"vuelos"` | Vuelos |
| `ACCOMMODATION` | `"alojamiento"` | Alojamiento |
| `ACTIVITIES` | `"actividades"` | Actividades |
| `FOOD` | `"comidas"` | Comidas |
| `TRANSPORT` | `"transporte_local"` | Transporte local |
| `EXTRAS` | `"extras"` | Extras |

### 5.2. Mapeos

#### Colores por ItemType (`ITEM_TYPE_COLORS`)
| Tipo | Color hex |
|---|---|
| ACTIVITY | `#4CAF50` (verde) |
| TRANSFER | `#9E9E9E` (gris) |
| ACCOMMODATION | `#2196F3` (azul) |
| FOOD | `#FF9800` (naranja) |
| FLIGHT | `#E91E63` (rosa) |
| EXTRA | `#9C27B0` (purpura) |

#### Colores por BudgetCategory (`BUDGET_CATEGORY_COLORS`)
| Categoria | Color hex |
|---|---|
| FLIGHTS | `#E91E63` |
| ACCOMMODATION | `#2196F3` |
| ACTIVITIES | `#4CAF50` |
| FOOD | `#FF9800` |
| TRANSPORT | `#9E9E9E` |
| EXTRAS | `#9C27B0` |

#### Iconos por ItemType (`ITEM_TYPE_ICONS`)
| Tipo | Icono |
|---|---|
| ACTIVITY | 🎯 |
| TRANSFER | 🚕 |
| ACCOMMODATION | 🏨 |
| FOOD | 🍽️ |
| FLIGHT | ✈️ |
| EXTRA | 📦 |

#### Iconos por ItemStatus (`STATUS_ICONS`)
| Estado | Icono |
|---|---|
| CONFIRMED | ✅ |
| PENDING | ⏳ |
| SUGGESTED | 💡 |

#### Mapeo ItemType a BudgetCategory (`ITEM_TYPE_TO_BUDGET`)
| ItemType | BudgetCategory |
|---|---|
| ACTIVITY | ACTIVITIES |
| TRANSFER | TRANSPORT |
| ACCOMMODATION | ACCOMMODATION |
| FOOD | FOOD |
| FLIGHT | FLIGHTS |
| EXTRA | EXTRAS |

### 5.3. Configuracion LLM (`config/llm_config.py`)

| Constante | Valor | Descripcion |
|---|---|---|
| `BASE_DIR` | (calculado) | Raiz del proyecto |
| `LLM_DATA_DIR` | `data/llm_data/` | Directorio de datos del LLM |
| `DEFAULT_MODEL` | `"gpt-5-nano"` | Modelo de OpenAI para chat (configurable via env `LLM_DEFAULT_MODEL`) |
| `DEFAULT_TEMPERATURE` | `0.7` | Temperatura de generacion para chat |
| `EXTRACTION_TEMPERATURE` | `0` | Temperatura para extraccion de items (determinismo) |
| `DEFAULT_EMBEDDING_MODEL` | `"text-embedding-3-small"` | Modelo de embeddings de OpenAI |
| `MAX_VECTOR_RESULTS` | `3` | Memorias vectoriales a recuperar por query |
| `MEMORY_CATEGORIES` | `["viaje", "preferencias", "personal", "hechos_importantes"]` | Categorias de memoria |

---

## 6. Servicios

### 6.1. supabase_client.py

**Archivo:** `services/supabase_client.py`
**Proposito:** Cliente Supabase singleton. Lee credenciales de `.env` (local) o `st.secrets` (Streamlit Cloud).
**Dependencias:** `supabase`

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `get_supabase_client` | `() -> Client` | `Client` | Retorna el cliente Supabase singleton. Requiere `SUPABASE_URL` y `SUPABASE_SERVICE_KEY`. Lanza `RuntimeError` si faltan. |
| `is_supabase_available` | `() -> bool` | `bool` | Verifica si Supabase esta configurado y accesible (test de conectividad). |

### 6.2. auth_service.py

**Archivo:** `services/auth_service.py`
**Proposito:** OAuth condicional (Authlib + secrets.toml). Guard de autenticacion. CRUD de usuarios en Supabase.
**Dependencias:** `streamlit`, `config.settings`, Authlib (condicional)

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `is_auth_enabled` | `() -> bool` | `bool` | Verifica si Authlib esta instalado y las credenciales OAuth estan en `secrets.toml` con formato anidado `[auth.google]`. |
| `require_auth` | `() -> Optional[str]` | `str\|None` | Guard: bloquea usuarios no autenticados con `st.login("google")`. Retorna `user_id` si autenticado, o `DEMO_USER_ID` si OAuth no esta habilitado. |
| `get_or_create_user` | `(user_info: dict) -> str` | `str` | Crea o actualiza el registro del usuario en Supabase tras el callback OAuth. Retorna `user_id`. |

### 6.3. trip_service.py

**Archivo:** `services/trip_service.py`
**Proposito:** Servicio central de gestion de viajes. CRUD de viajes e items, agrupacion, ordenamiento, sincronizacion con Supabase.
**Dependencias:** `config.settings`, `services.supabase_client`

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `load_trips` | `(user_id: str) -> list` | `list[dict]` | Carga viajes del usuario desde Supabase (con items y expenses). Si no hay, carga datos de ejemplo. |
| `get_trip_by_id` | `(trips: list, trip_id: str) -> Optional[dict]` | `dict\|None` | Busca un viaje por ID en la lista. |
| `get_active_trip` | `(trips: list, active_trip_id: Optional[str]) -> Optional[dict]` | `dict\|None` | Obtiene el viaje activo. Prioridad: `active_trip_id` > primer viaje en planificacion > proximo confirmado > en curso. |
| `create_trip` | `(trips: list, name: str, destination: str, start_date: str, end_date: str, user_id: str) -> dict` | `dict` | Crea un viaje nuevo en estado `"en_planificacion"`. Persiste a Supabase. |
| `delete_trip` | `(trips: list, trip_id: str) -> bool` | `bool` | Elimina un viaje (solo si esta en planificacion). Elimina en Supabase incluyendo items, expenses y chats asociados. |
| `update_trip_statuses` | `(trips: list) -> None` | `None` | Actualiza estados automaticamente segun fechas. |
| `sort_trips` | `(trips: list) -> list` | `list[dict]` | Ordena: en curso > en planificacion (asc) > confirmado (asc) > completado (desc). |
| `filter_trips_by_status` | `(trips: list, status: Optional[str]) -> list` | `list[dict]` | Filtra viajes por estado. |
| `group_items_by_day` | `(items: list) -> dict` | `dict[int, list]` | Agrupa items por dia, ordena por `start_time`. |
| `accept_suggestion` | `(trip: dict, item_id: str) -> bool` | `bool` | Cambia item de `"sugerido"` a `"pendiente"`. Actualiza en Supabase. |
| `discard_suggestion` | `(trip: dict, item_id: str) -> bool` | `bool` | Elimina un item sugerido. Elimina en Supabase. |
| `add_item_to_trip` | `(trip: dict, item: dict) -> None` | `None` | Agrega un item y persiste a Supabase. Recalcula presupuesto. |
| `remove_item_from_trip` | `(trip: dict, item_id: str) -> bool` | `bool` | Elimina un item. Elimina en Supabase. Recalcula presupuesto. |
| `recalculate_budget` | `(trip: dict) -> None` | `None` | Recalcula `budget_total` (items no sugeridos + expenses). |
| `sync_trip_changes` | `(trips: list, trip: dict) -> None` | `None` | Recalcula presupuesto, actualiza el trip en la lista, persiste a Supabase. |
| `get_transfer_info` | `(item_a: dict, item_b: dict) -> Optional[dict]` | `dict\|None` | Genera info de traslado entre items consecutivos con ubicaciones diferentes. Datos mock: "Metro / Taxi", 20 min, USD 5. |

### 6.4. agent_service.py

**Archivo:** `services/agent_service.py`
**Proposito:** Dispatcher principal del chat. LLM-Only: una sola llamada al LLM detecta todos los intents y extrae datos. Sin LLM, muestra "IA no disponible".
**Dependencias:** `config.settings`, `services.llm_agent_service` (condicional), `services.llm_item_extraction` (condicional), `services.booking_service` (condicional), `services.flight_service` (condicional), `services.item_utils`, `services.trip_creation_flow`

**Deteccion del modo LLM** (lazy init):
```python
_USE_LLM = None  # None = no inicializado aun
def _check_llm():
    global _USE_LLM, _llm_process_fn, _llm_extract_fn
    _USE_LLM = bool(os.environ.get("OPENAI_API_KEY"))
    # Importa condicionalmente llm_agent_service y llm_item_extraction
```

**Flujo de ruteo secuencial en `process_message()`:**
1. Sanitizar input (`_sanitize_user_input`) — regex contra prompt injection
2. LLM extraction UNICA — si hay LLM, una sola llamada a `_llm_extract_fn()` que retorna `ItemExtractionResult`
3. Flujo multi-turn de creacion de viaje — si hay draft activo
4. Escape de draft de item — si el LLM clasifico como intent distinto de `add_item`
5. Flujo multi-turn de creacion de item — si hay draft activo
6. Sin viaje activo → LLM chat
7. `_dispatch_llm_intent(llm_result)` — rutea por intent

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `is_llm_active` | `() -> bool` | `bool` | Retorna `True` si el LLM esta activo. Inicializa lazy. |
| `is_booking_active` | `() -> bool` | `bool` | Retorna `True` si Booking.com esta disponible. |
| `is_flights_active` | `() -> bool` | `bool` | Retorna `True` si la busqueda de vuelos esta disponible. |
| `process_message` | `(message, trip, user_id, chat_id, trip_creation_draft, item_creation_draft, chat_history) -> dict` | `dict` | Procesa un mensaje del usuario. Retorna `{role, type, content}`. Tipos: `text`, `card`, `confirmation`, `hotel_results`, `flight_results`. |
| `apply_confirmed_action` | `(action: dict, trip: dict, trips: list, user_id: str) -> str` | `str` | Aplica una accion confirmada. Sincroniza con Supabase. Retorna mensaje de resultado. |

**Intents manejados por `_dispatch_llm_intent()`:**
- `add_item` → confirmacion de agregar item
- `create_trip` → confirmacion de crear viaje
- `calendar_event` → confirmacion de evento de calendario
- `remove_item` → confirmacion de eliminar item(s)
- `hotel_search` → busqueda en Booking.com con filtros del LLM
- `flight_search` → busqueda de vuelos con `flight_origin`/IATA del LLM
- `add_expense`, `modify_expense`, `remove_expense` → confirmaciones de gastos
- `informative`, `unknown` → fall-through al LLM chat

### 6.5. llm_item_extraction.py

**Archivo:** `services/llm_item_extraction.py`
**Proposito:** Extraccion inteligente via LLM structured output. Una sola llamada detecta intent y extrae TODOS los datos.
**Dependencias:** `langchain_openai`, `pydantic`, `airportsdata`, `config.llm_config`

**Schema Pydantic `ItemExtractionResult` (30 campos):**

| Grupo | Campos |
|---|---|
| Intent | `intent` |
| Item basico | `name`, `day`, `start_time`, `end_time`, `item_type`, `location`, `cost` |
| Completitud | `is_complete`, `missing_fields`, `follow_up_question` |
| Eliminacion | `remove_item_ids`, `remove_all`, `remove_summary` |
| Creacion de viaje | `trip_destination`, `trip_start_date`, `trip_end_date`, `trip_name` |
| Gastos | `expense_category`, `expense_id`, `expense_amount`, `remove_all_expenses` |
| Hoteles | `hotel_type`, `hotel_location`, `hotel_max_price` |
| Vuelos | `flight_origin`, `flight_destination`, `flight_origin_iata`, `flight_destination_iata` |
| Compartido | `result_count` |

**Funcionalidad clave:**
- Singleton `_extraction_llm` (`ChatOpenAI` con `EXTRACTION_TEMPERATURE=0`)
- `ChatOpenAI.with_structured_output(ItemExtractionResult)` para una sola llamada
- System prompt semantico: describe intenciones por significado, no por keywords
- Post-validacion defensiva (`_post_validate`): valida intent, item_type, rango de dias, formato de horas, IATA (validacion con `airportsdata`), result_count (1-10), fechas ISO
- Base de datos `airportsdata` (7800+ aeropuertos) para validacion y fallback de codigos IATA

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `extract_item_with_llm` | `(message, trip, partial_draft, chat_history) -> Optional[ItemExtractionResult]` | `ItemExtractionResult\|None` | Extrae intent y datos del mensaje. Retorna `None` si falla. |

### 6.6. item_utils.py

**Archivo:** `services/item_utils.py`
**Proposito:** Utilidades puras de validacion y construccion de items. Funciones de negocio sin dependencias externas.
**Dependencias:** Ninguna (modulo puro)

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `calculate_end_time` | `(start_time: str, item_type: str) -> str` | `str` | Calcula end_time sumando duracion por defecto. Trunca a 23:59 si excede medianoche. |
| `get_missing_item_fields` | `(draft: dict) -> list` | `list[str]` | Retorna campos minimos requeridos faltantes (`name`, `day`). |
| `build_item_prompt_for_missing` | `(draft: dict, missing: list) -> str` | `str` | Genera pregunta natural en espanol para datos faltantes. |
| `validate_item_day_range` | `(day: int, trip: dict) -> tuple` | `(bool, str)` | Valida que el dia este dentro del rango del viaje. |
| `detect_time_conflict` | `(item: dict, existing_items: list) -> Optional[dict]` | `dict\|None` | Detecta conflictos de horario con items existentes del mismo dia. |
| `build_item_confirmation_data` | `(draft: dict) -> dict` | `dict` | Construye datos de confirmacion para el chat a partir de un draft. |
| `new_item_draft` | `() -> dict` | `dict` | Crea un nuevo draft vacio de item con step="collecting". |

**Constantes:**
- `_DEFAULT_DURATIONS`: duraciones por tipo en horas (actividad: 2h, comida: 1.5h, vuelo: 3h, etc.)
- `_DEFAULT_TIMES`: horarios por defecto (actividad: 10:00, comida: 12:30, vuelo: 08:00, etc.)

### 6.7. trip_creation_flow.py

**Archivo:** `services/trip_creation_flow.py`
**Proposito:** Flujo multi-turn de creacion de viajes desde el chat. Extraccion de destino y fechas con regex robusto para espanol.
**Dependencias:** Ninguna (modulo puro)

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `detect_cancel_intent` | `(message: str) -> bool` | `bool` | Detecta si el usuario quiere cancelar un flujo multi-turn. |
| `extract_trip_data` | `(message: str, llm_result) -> dict` | `dict` | Extrae destino y fechas. LLM result como fuente primaria, regex como fallback. |
| `get_missing_fields` | `(draft: dict) -> list` | `list[str]` | Retorna campos faltantes (destination, start_date, end_date). |
| `build_prompt_for_missing` | `(draft: dict) -> str` | `str` | Genera pregunta para datos faltantes. |
| `validate_dates` | `(start_date: str, end_date: str) -> tuple` | `(bool, str)` | Valida fechas (end > start). |
| `build_confirmation_data` | `(draft: dict) -> dict` | `dict` | Construye datos de confirmacion de creacion de viaje. |
| `new_draft` | `() -> dict` | `dict` | Crea un nuevo draft de viaje. |

### 6.8. llm_agent_service.py

**Archivo:** `services/llm_agent_service.py`
**Proposito:** Wrapper delgado que conecta `agent_service.py` con `TripChatbot`. Expone `LLM_AVAILABLE`.
**Dependencias:** `services.llm_chatbot`

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `process_message_llm` | `(message: str, trip: Optional[dict], user_profile: Optional[dict]) -> dict` | `dict` | Obtiene la instancia singleton de `TripChatbot`, construye el `chat_id`, delega a `chat()`. |

**Variable global:** `LLM_AVAILABLE: bool` — `True` si `TripChatbot` se pudo importar sin error.

### 6.9. llm_chatbot.py

**Archivo:** `services/llm_chatbot.py`
**Proposito:** Pipeline LangGraph completo con 4 nodos para el chatbot con OpenAI gpt-5-nano. Singleton.
**Dependencias:** `langgraph`, `langchain_core`, `langchain_openai`, `services.memory_manager`, `config.llm_config`

**Clase `TripChatbot`:**

| Metodo | Signature | Retorno | Descripcion |
|---|---|---|---|
| `get_instance` | `(cls) -> TripChatbot` | `TripChatbot` | Patron singleton. |
| `__init__` | `(self)` | - | Inicializa `TripMemoryManager`, `ChatOpenAI(model=gpt-5-nano, temp=0.7)`, system prompt, message trimmer, y compila pipeline LangGraph. |
| `_create_app` | `(self)` | `CompiledGraph` | Crea pipeline con 4 nodos y checkpointer SQLite. |
| `chat` | `(self, message, trip, user_profile, chat_id) -> dict` | `dict` | Envia mensaje al pipeline. Retorna `{role: "assistant", type: "text", content: str}`. |

### 6.10. memory_manager.py

**Archivo:** `services/memory_manager.py`
**Proposito:** Gestion de memoria vectorial con ChromaDB. Extraccion automatica de memorias relevantes.
**Dependencias:** `chromadb`, `langchain_chroma`, `langchain_openai`, `langchain_core`, `pydantic`, `config.llm_config`

**Clase `TripMemoryManager`:**

| Metodo | Signature | Retorno | Descripcion |
|---|---|---|---|
| `__init__` | `(self)` | - | Crea directorio `data/llm_data/`, inicializa ChromaDB con `OpenAIEmbeddings(model="text-embedding-3-small")` y sistema de extraccion. |
| `save_vector_memory` | `(self, text, metadata) -> str` | `str` | Guarda memoria en ChromaDB. Retorna ID o vacio si falla. |
| `search_vector_memory` | `(self, query, k) -> List[str]` | `list[str]` | Busca las k memorias mas similares semanticamente (default k=3). |
| `get_all_vector_memories` | `(self) -> List[Dict]` | `list[dict]` | Retorna todas las memorias como `{id, content, metadata}`. |
| `extract_and_store_memories` | `(self, user_message) -> bool` | `bool` | Extrae memorias con LLM. Si importancia >= 2, guarda. Fallback manual por keywords. |

### 6.11. chat_service.py

**Archivo:** `services/chat_service.py`
**Proposito:** Multi-conversacion por usuario. CRUD de chats con persistencia en Supabase.
**Dependencias:** `services.supabase_client`

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `load_chats` | `(user_id: str) -> list` | `list[dict]` | Carga chats del usuario desde Supabase con mensajes, ordenados por actividad reciente. |
| `create_chat` | `(user_id, trip_id, title) -> dict` | `dict` | Crea un nuevo chat. Persiste en Supabase. ID formato `chat-{hex8}`. |
| `save_message` | `(chat_id, message) -> None` | `None` | Guarda un mensaje individual en Supabase. Actualiza `last_activity_at`. |
| `delete_chat` | `(chat_id: str) -> bool` | `bool` | Elimina un chat y todos sus mensajes de Supabase. |
| `update_chat_title` | `(chat_id, title) -> None` | `None` | Actualiza el titulo de un chat. Auto-genera titulo desde primer mensaje. |

### 6.12. booking_service.py

**Archivo:** `services/booking_service.py`
**Proposito:** Cliente Booking.com via RapidAPI DataCrawler. Cache en memoria (1h TTL). Retry para 429.
**Dependencias:** `httpx`

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `is_booking_available` | `() -> bool` | `bool` | `True` si `RAPIDAPI_KEY` esta configurada. |
| `search_destinations` | `(query: str) -> list` | `list[dict]` | Busca destinos en Booking.com. Retorna lista con `dest_id`, nombre, tipo. |
| `search_hotels` | `(dest_id, checkin, checkout, ...) -> list` | `list[dict]` | Busca hoteles para un destino. Soporta filtros de tipo, precio, ordenamiento. |
| `search_hotels_for_trip` | `(trip: dict) -> list` | `list[dict]` | Busca hoteles usando destino y fechas del viaje activo. |
| `format_hotels_as_cards` | `(hotels: list) -> list` | `list[dict]` | Formatea hoteles para renderizado como tarjetas en el chat. |

**Seguridad:** Whitelist de dominios permitidos, sanitizacion de parametros de query, validacion de `dest_id` y fechas.

### 6.13. flight_service.py

**Archivo:** `services/flight_service.py`
**Proposito:** Busqueda de vuelos. Dual backend: SerpAPI Google Flights (primario, con `deep_search=true`) + fast-flights (fallback scraper). Base de datos airportsdata (7800+ aeropuertos). Cache 30 min.
**Dependencias:** `httpx`, `fast_flights` (condicional), `airportsdata`

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `is_flights_available` | `() -> bool` | `bool` | `True` si SerpAPI o fast-flights estan disponibles. |
| `search_flights` | `(origin, destination, date, ...) -> list` | `list[dict]` | Busca vuelos. Intenta SerpAPI primero, fallback a fast-flights. |
| `search_flights_for_trip` | `(trip, origin_city) -> list` | `list[dict]` | Busca vuelos usando destino y fechas del viaje. Necesita ciudad de origen. |
| `format_flights_as_cards` | `(flights: list) -> list` | `list[dict]` | Formatea vuelos para renderizado en el chat. |
| `get_airport_code` | `(city_name: str) -> Optional[str]` | `str\|None` | Mapea ciudades a codigos IATA usando airportsdata (7800+ aeropuertos). Incluye overrides curados para ciudades ambiguas y nombres en espanol. |

**Indice de aeropuertos:** Construido dinámicamente desde `airportsdata` al importar el modulo. Incluye overrides manuales para ciudades con multiples aeropuertos y aliases en espanol (ej: "manaos" → MAO, "cdmx" → MEX, "londres" → LHR).

### 6.14. budget_service.py

**Archivo:** `services/budget_service.py`
**Proposito:** Calculos de presupuesto por categoria. Acepta `items` y `expenses` (gastos directos).
**Dependencias:** `config.settings`

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `calculate_budget_summary` | `(items: list, expenses: list) -> dict` | `dict` | Presupuesto desglosado por categoria. Items sugeridos NO se contabilizan. Incluye `total_expenses`. Retorna `{total_estimated, total_real, total_expenses, by_category}`. |
| `has_real_costs` | `(items: list) -> bool` | `bool` | `True` si algun item no sugerido tiene `cost_real > 0`. |
| `calculate_planning_progress` | `(items: list) -> float` | `float` | Proporcion de items confirmados (0.0 a 1.0). |

### 6.15. expense_service.py

**Archivo:** `services/expense_service.py`
**Proposito:** CRUD de gastos directos (`expenses`) no asociados a items del itinerario. Persistencia en Supabase.
**Dependencias:** `config.settings`, `services.supabase_client`

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `load_expenses` | `(trip_id: str) -> list` | `list[dict]` | Carga gastos de un viaje desde Supabase. |
| `add_expense` | `(trip_id, name, category, amount, notes) -> dict` | `dict` | Crea un gasto. ID formato `exp-{hex8}`. Persiste en Supabase. |
| `update_expense` | `(expense_id, updates) -> bool` | `bool` | Actualiza un gasto existente en Supabase. |
| `remove_expense` | `(expense_id: str) -> bool` | `bool` | Elimina un gasto de Supabase. |
| `format_existing_expenses` | `(expenses: list) -> str` | `str` | Formatea gastos como texto para contexto del LLM. |

### 6.16. profile_service.py

**Archivo:** `services/profile_service.py`
**Proposito:** Carga y guardado de preferencias de usuario en Supabase.
**Dependencias:** `services.supabase_client`, `data.sample_data`

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `load_profile` | `(user_id: str) -> dict` | `dict` | Carga perfil del usuario desde Supabase. Si no existe, retorna perfil por defecto. |
| `save_profile` | `(user_id: str, profile: dict) -> bool` | `bool` | Guarda/actualiza el perfil en Supabase. |

### 6.17. weather_service.py

**Archivo:** `services/weather_service.py`
**Proposito:** Datos climaticos mock para destinos. No consulta APIs externas.
**Dependencias:** Ninguna

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `get_weather` | `(destination: str) -> dict` | `dict` | Retorna datos climaticos mock: `{temp_min, temp_max, condition, icon, description}`. Default generico si el destino no esta en datos hardcodeados. |

**Destinos con datos:**
| Destino | Temp min-max | Condicion |
|---|---|---|
| Tokio, Japon | 15-22°C | Parcialmente nublado |
| Barcelona, Espana | 18-25°C | Soleado |
| Lima, Peru | 20-28°C | Nublado parcial |

### 6.18. feedback_service.py

**Archivo:** `services/feedback_service.py`
**Proposito:** CRUD de retroalimentacion post-viaje. Persistencia en Supabase.
**Dependencias:** `config.settings`, `services.supabase_client`

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `save_feedback` | `(trip_id: str, feedback: dict) -> bool` | `bool` | Guarda feedback en Supabase. Constraint UNIQUE en trip_id. |
| `has_feedback` | `(trip_id: str) -> bool` | `bool` | `True` si el viaje tiene feedback. |
| `get_feedback` | `(trip_id: str) -> dict` | `dict` | Retorna el feedback del viaje (o dict vacio). |
| `has_pending_feedback` | `(trips: list) -> bool` | `bool` | `True` si hay viajes completados sin feedback. |
| `get_trips_pending_feedback` | `(trips: list) -> list` | `list[dict]` | Retorna viajes completados sin feedback. |

---

## 7. Componentes UI

### 7.1. chat_widget.py

**Archivo:** `components/chat_widget.py`
**Proposito:** Renderiza tarjetas ricas, confirmaciones, resultados de hoteles y resultados de vuelos dentro del chat.

#### `render_rich_card(card_data: dict) -> None`
- **Renderiza:** Contenedor con borde que muestra icono de tipo, nombre, proveedor, ubicacion, duracion, precio, rating, horarios de vuelo y notas.
- **Parametros:** `card_data` — dict con campos: `card_type`, `name`, `provider`, `price`, `location`, `rating`, `duration`, `departure`, `arrival`, `notes`.

#### `render_confirmation(action_data: dict, msg_index: int) -> str`
- **Renderiza:** Contenedor con resumen de la accion, detalles en formato clave-valor (filtra campos internos con prefijo `_`), y botones "Confirmar" / "Cancelar".
- **Retorna:** `"confirm"`, `"cancel"` o `""`.

#### `render_hotel_results(hotel_data: dict) -> None`
- **Renderiza:** Resultados de busqueda de hoteles de Booking.com como tarjetas con nombre, precio, rating, ubicacion y link.

#### `render_flight_results(flight_data: dict) -> None`
- **Renderiza:** Resultados de busqueda de vuelos como tabla compacta HTML.

### 7.2. budget_charts.py

**Archivo:** `components/budget_charts.py`
**Proposito:** Graficos Plotly para la vista de presupuesto. Dark theme.

#### `render_donut_chart(budget_summary: dict) -> None`
- Grafico de dona (Pie con hole=0.4) con distribucion del presupuesto estimado por categoria. Colores de `BUDGET_CATEGORY_COLORS`. Altura: 350px.

#### `render_comparison_bars(budget_summary: dict) -> None`
- Barras agrupadas comparando estimado (azul) vs real (verde) por categoria. Eje Y en USD. Altura: 350px.

### 7.3. trip_card.py

**Archivo:** `components/trip_card.py`
**Proposito:** Tarjeta de viaje para la lista en Mis Viajes.

#### `render_trip_card(trip: dict, index: int) -> dict`
- **Renderiza:** Contenedor con nombre, destino con badge de estado, fechas, presupuesto, boton "Ver viaje", y boton "Eliminar" (solo en planificacion).
- **Retorna:** `{"action": "view", "trip_id": "..."}`, `{"action": "delete", "trip_id": "..."}` o `{}`.

**Badges de estado:**
| Estado | Badge |
|---|---|
| en_planificacion | 🟡 |
| confirmado | 🟢 |
| en_curso | 🔵 |
| completado | ⚪ |

### 7.4. itinerary_item.py

**Archivo:** `components/itinerary_item.py`
**Proposito:** Item expandible del itinerario y bloque visual de traslado.

#### `render_itinerary_item(item: dict, index: int) -> dict`
- **Renderiza:** `st.expander` con icono de tipo + nombre + horario. Al expandir: tipo, ubicacion, costos, proveedor, notas, link de reserva. Items sugeridos: botones "Aceptar" / "Descartar".
- **Retorna:** `{"action": "accept", "item_id": "..."}`, `{"action": "discard", "item_id": "..."}` o `{}`.

#### `render_transfer(transfer_info: dict) -> None`
- Bloque HTML con fondo gris: origen -> destino, transporte, duracion, costo estimado.

### 7.5. alert_banner.py

**Archivo:** `components/alert_banner.py`
**Proposito:** Genera y renderiza alertas descartables del viaje activo.

#### `get_alerts(trip: dict) -> list`
- Items pendientes → `"warning"`, sugeridos → `"info"`, dias sin actividades → `"info"`.

#### `render_alerts(alerts: list) -> None`
- Renderiza con `st.warning()`/`st.error()`/`st.info()`. Boton "X" para descartar. Descartadas en `st.session_state.dismissed_alerts`.

---

## 8. Paginas

### 8.1. Dashboard (`pages/1_Dashboard.py`)

**Requerimientos:** REQ-UI-001 (Panel Overview), REQ-UI-010 (Clima y Alertas)

**Que muestra:**
- **Selector de viaje** propio (`st.selectbox`).
- **Sin viaje activo:** Titulo, mensaje de bienvenida, botones "Ir a Mis Viajes" y "Abrir Chat".
- **Con viaje activo:**
  - Fila 1: 4 metricas — destino, dias restantes, presupuesto total estimado, items confirmados/total.
  - Fila 2: Progreso de planificacion (barra + porcentaje) y clima del destino (datos mock).
  - Fila 3: Alertas descartables (si hay).
  - Fila 4: Accesos rapidos a Chat, Cronograma, Itinerario, Presupuesto.
  - Banner superior si hay viajes completados sin feedback.

### 8.2. Chat (`pages/2_Chat.py`)

**Requerimientos:** REQ-UI-002, REQ-UI-003, REQ-CL-001 a REQ-CL-005

**Que muestra:**
- **Selector obligatorio de viaje.**
- **Multi-conversacion:** Lista de chats por viaje, crear/eliminar chats.
- Indicador de modo: "Asistente IA (OpenAI)" o "IA no disponible".
- Historial de mensajes renderizados segun tipo (`text`, `card`, `confirmation`, `hotel_results`, `flight_results`).
- Campo de entrada `st.chat_input()`.

**Flujo de interaccion:**
1. Usuario escribe un mensaje.
2. El mensaje se agrega al historial y se persiste en Supabase.
3. Se llama `process_message()` con spinner.
4. La respuesta se agrega al historial y se persiste.
5. `st.rerun()` refresca la pagina.

**Confirmaciones:**
- Si `msg["processed"]` es `True`: muestra texto del resultado.
- Si `msg["processed"]` es `False`: renderiza botones Confirmar/Cancelar.
- Confirmar: ejecuta `apply_confirmed_action()`, marca como procesada, agrega mensaje de resultado.
- Cancelar: marca como procesada con "Cancelado por el usuario".

### 8.3. Cronograma (`pages/3_Cronograma.py`)

**Requerimiento:** REQ-UI-004 (Cronograma / Calendario)

**Que muestra:**
- **Vista global:** Muestra items de **todos los viajes** (no solo el activo). Eventos prefijados con destino del viaje.
- Selector de vista (Semana, Dia, Mes) y calendario interactivo via `streamlit-calendar` (FullCalendar.js).
- Items convertidos a eventos con fecha real, color por tipo, 50% opacidad para sugeridos.
- Items multi-dia (`end_day > day`) se renderizan como `allDay: true` con color Blue Grey (`#607D8B`).
- Vista fallback (sin streamlit-calendar): tabs por dia.

### 8.4. Itinerario (`pages/4_Itinerario.py`)

**Requerimientos:** REQ-UI-005, REQ-UI-011

**Que muestra:**
- **Selector de viaje** propio.
- Leyenda de estados, tabs por dia (con fecha), items expandibles, bloques de traslado entre items con ubicaciones diferentes.

**Interacciones:**
- Expandir/colapsar items.
- Aceptar sugerencia → cambia a "pendiente", recalcula, persiste a Supabase.
- Descartar sugerencia → elimina item, recalcula, persiste.

### 8.5. Presupuesto (`pages/5_Presupuesto.py`)

**Requerimiento:** REQ-UI-006

**Que muestra:**
- **Selector de viaje** propio.
- Metricas: presupuesto estimado, gasto real (con delta), gastos directos, items contabilizados.
- Grafico donut + tabla desglose por categoria.
- Barras comparativas estimado vs real (solo si hay costos reales).
- Drill-down por categoria con expanders por item.
- Seccion de gastos directos (expenses) con posibilidad de agregar/editar/eliminar.

### 8.6. Perfil (`pages/6_Perfil.py`)

**Requerimiento:** REQ-UI-007

**Que muestra:**
- **Info OAuth** (read-only): email, nombre, foto (si autenticado via Google).
- Formulario con tabs de preferencias:
  1. **Alojamiento:** Multiselect + cadenas hoteleras.
  2. **Alimentacion:** Multiselect restricciones + alergias.
  3. **Estilo de viaje:** Multiselect estilos.
  4. **Presupuesto:** Number input (USD, 0-10000).
  5. **Transporte:** Textarea aerolineas preferidas.
- Boton "Guardar preferencias" — persiste en Supabase.

### 8.7. Mis Viajes (`pages/7_Mis_Viajes.py`)

**Requerimientos:** REQ-UI-008, REQ-UI-009, REQ-UI-012

**Que muestra:**
- Filtro por estado + boton "Nuevo viaje".
- Formulario de nuevo viaje: nombre, destino, fecha inicio/fin.
- Lista de viajes con tarjetas (`trip_card`).
- Confirmacion de eliminacion.
- Para viajes completados sin feedback: seccion de retroalimentacion.

**Interacciones:**
- Ver viaje → sincroniza `active_trip_id` y `chat_selected_trip_id`, navega a Dashboard.
- Eliminar viaje → confirmacion, solo en planificacion. Elimina en Supabase.
- Crear viaje → validacion, crea en Supabase, redirige al Chat.

---

## 9. Sistema de Chat (Detalle)

### 9.1. Flujo Completo de un Mensaje

```
1. Usuario escribe mensaje en st.chat_input()
         │
2. Se agrega {role:"user", type:"text", content:msg} al historial
   Se persiste en Supabase (chat_messages)
         │
3. Se llama process_message(msg, trip, ...) en agent_service.py
         │
4. agent_service ejecuta flujo LLM-Only:
   ├── Sanitizar input (_sanitize_user_input)
   ├── LLM extraction UNICA → _llm_extract_fn() → ItemExtractionResult
   ├── Flujo multi-turn creacion de viaje (si draft activo)
   ├── Flujo multi-turn creacion de item (si draft activo)
   ├── Sin viaje activo → LLM chat
   └── _dispatch_llm_intent(llm_result) por intent:
       ├── add_item → Confirmacion UI
       ├── create_trip → Confirmacion UI
       ├── calendar_event → Confirmacion UI
       ├── remove_item → Confirmacion UI
       ├── hotel_search → Booking.com (RapidAPI) → hotel_results
       ├── flight_search → SerpAPI/fast-flights → flight_results
       ├── add/modify/remove_expense → Confirmacion UI
       └── informative/unknown → LLM chat (TripChatbot)
                    │
                    └── Pipeline LangGraph (4 nodos)
                              │
                              └── Retorna {role, type, content}
         │
5. Respuesta se agrega al historial y se persiste en Supabase
         │
6. st.rerun() → La pagina se refresca
```

### 9.2. Modo LLM-Only

| Aspecto | Descripcion |
|---|---|
| **Activacion** | `OPENAI_API_KEY` presente en `.env`. Deteccion lazy (`_check_llm()`) |
| **Modelo** | gpt-5-nano (temperatura 0.7 para chat, 0 para extraccion) |
| **Sin OPENAI_API_KEY** | El chat muestra "IA no disponible" y redirige al usuario a la UI. NO hay fallback mock |
| **Respuestas de texto** | Generadas por LLM con contexto de viaje, perfil y memorias |
| **Tarjetas ricas** | Generadas por el dispatcher para resultados de hoteles y vuelos |
| **Confirmaciones** | Generadas por el dispatcher para acciones que modifican datos |
| **Extraccion de intents** | `ItemExtractionResult` (structured output, 30 campos) en una sola llamada LLM |
| **Memoria** | ChromaDB vectorial + extraccion automatica de memorias |
| **Persistencia** | Supabase (chats + chat_messages) + SQLite via LangGraph checkpointer |

### 9.3. Pipeline LangGraph (4 Nodos)

```
START → memory_retrieval → context_optimization → response_generation → memory_extraction → END
```

#### Nodo 1: `memory_retrieval`
- Busca el ultimo `HumanMessage`.
- Llama `memory_manager.search_vector_memory(last_user_message.content)`.
- Retorna `{"vector_memories": [lista de textos relevantes]}`.

#### Nodo 2: `context_optimization`
- Aplica `trim_messages(strategy="last", max_tokens=4000)`.
- Trunca historial para que quepa en el contexto.

#### Nodo 3: `response_generation`
- Construye contexto: memorias vectoriales, datos del viaje, preferencias del usuario.
- Formatea system prompt con los 3 contextos.
- Invoca chain `prompt | llm` (OpenAI gpt-5-nano).

#### Nodo 4: `memory_extraction`
- Extrae memorias del mensaje del usuario.
- Si importancia >= 2, guarda en ChromaDB.
- Evita reprocesar el mismo mensaje.

**Checkpointer:** SQLite en `data/llm_data/langgraph_memory.db`, thread_id `"trip_chat_{chat_id}"`.

### 9.4. Sistema de Memorias Vectoriales (ChromaDB)

**Coleccion:** `"trip_planner_memories"` en `data/llm_data/chromadb/`
**Embeddings:** `OpenAIEmbeddings(model="text-embedding-3-small")`

**Flujo de extraccion de memorias:**
1. El nodo `memory_extraction` recibe el mensaje del usuario.
2. Si hay chain de extraccion LLM: analiza el mensaje, determina categoria y relevancia. Si `category != "none"` y `importance >= 2`, guarda.
3. Fallback manual: busca keywords ("prefiero", "alergia", "me llamo", "viaje a", "presupuesto").

**Flujo de recuperacion:**
1. El nodo `memory_retrieval` busca las 3 memorias mas similares en ChromaDB.
2. Las pasa como contexto al nodo de generacion de respuesta.

### 9.5. Extraccion Inteligente de Items (LLM Structured Output)

**Modulo:** `services/llm_item_extraction.py`

Una sola llamada a `ChatOpenAI.with_structured_output(ItemExtractionResult)` detecta el intent del usuario y extrae TODOS los datos relevantes en una unica invocacion. El schema Pydantic `ItemExtractionResult` tiene 30 campos organizados por grupo funcional.

**Post-validacion defensiva (`_post_validate`):**
- Valida que `intent` sea uno de los valores permitidos
- Valida `item_type` contra valores del enum
- Valida rango de dias dentro del viaje
- Valida formato de horas HH:MM
- Valida `flight_origin` (sin digitos)
- Valida codigos IATA con `airportsdata` (7800+ aeropuertos); fallback a indice de ciudades
- Valida `result_count` en rango 1-10
- Valida fechas ISO para create_trip
- Merge con draft existente si hay flujo multi-turn activo

### 9.6. Tipos de Respuesta

#### Texto (`type: "text"`)
Respuesta en markdown generada por el LLM.

#### Tarjeta Rica (`type: "card"`)
Informacion estructurada de un servicio (vuelos, hoteles, actividades, comidas).

#### Confirmacion (`type: "confirmation"`)
Accion pendiente que requiere aprobacion del usuario con botones UI.

#### Resultados de Hoteles (`type: "hotel_results"`)
Resultados de Booking.com renderizados como tarjetas con precio, rating y link.

#### Resultados de Vuelos (`type: "flight_results"`)
Resultados de SerpAPI/fast-flights renderizados como tabla compacta HTML.

### 9.7. Flujo de Confirmaciones

1. El dispatcher genera un mensaje `type: "confirmation"` con resumen y detalles.
2. `pages/2_Chat.py` renderiza botones "Confirmar" / "Cancelar" via `render_confirmation()`.
3. Si confirma: `apply_confirmed_action()` ejecuta la accion, sincroniza con Supabase, marca como procesada.
4. Si cancela: marca como procesada con "Cancelado".
5. `st.rerun()`.

### 9.8. Busqueda de Hoteles (Booking.com)

- `booking_service.py` — Cliente HTTP (`httpx`) contra RapidAPI DataCrawler.
- Flujo: `search_destinations(query)` → `search_hotels(dest_id, checkin, checkout)` → `format_hotels_as_cards()`.
- Intent `hotel_search`: el LLM extrae `hotel_type`, `hotel_location`, `hotel_max_price`, `result_count`.
- Retry automatico para HTTP 429 (Too Many Requests).
- Cache en memoria con TTL de 1 hora.
- Seguridad: whitelist de dominios, sanitizacion de parametros, validacion de inputs.

### 9.9. Busqueda de Vuelos (SerpAPI + fast-flights)

- `flight_service.py` — Dual backend:
  - **SerpAPI Google Flights** (primario, requiere `SERPAPI_KEY`): API REST estable, `deep_search=true`.
  - **fast-flights** (fallback): scraper directo de Google Flights, sin API key.
- El LLM extrae `flight_origin`, `flight_destination`, `flight_origin_iata`, `flight_destination_iata`, `result_count`.
- `get_airport_code()` usa `airportsdata` (7800+ aeropuertos) con overrides curados e indice de ciudades normalizado.
- Cache en memoria con TTL de 30 minutos.
- Renderizado: `render_flight_results()` como tabla compacta HTML.

### 9.10. Sanitizacion de Input

`_sanitize_user_input()` en `agent_service.py`:
- Detecta y elimina: instrucciones de ignorar/olvidar, cambios de rol/persona, intentos de revelar system prompt, tokens de control (`[INST]`, `<|im_start|>`).
- Soft sanitization: si queda vacio tras limpiar, devuelve el original.

### 9.11. MCP Server

**Archivo:** `mcp_servers/booking_server.py`
- Servidor FastMCP standalone que expone `buscar_destinos` y `buscar_hoteles` como tools.
- Transporte: stdio.
- Ejecutable: `python mcp_servers/booking_server.py`.

---

## 10. Persistencia

### 10.1. Supabase (PostgreSQL)

La persistencia principal del sistema reside en Supabase (PostgreSQL). El schema se define en `scripts/setup_database.sql` (transaccional e idempotente — ejecutar en Supabase SQL Editor).

#### Tablas

| Tabla | Contenido | Clave primaria | Campos clave |
|---|---|---|---|
| `users` | Cuentas de usuario | `user_id` (TEXT UNIQUE) | email, name, avatar_url, created_at |
| `profiles` | Preferencias del usuario | `user_id` (FK a users) | accommodation_types, food_restrictions, travel_styles, daily_budget |
| `trips` | Viajes | `id` (TEXT, `trip-{hex8}`) | user_id, name, destination, start_date, end_date, status, budget_total |
| `itinerary_items` | Items del itinerario | `id` (TEXT, `item-{hex8}`) | trip_id, name, item_type, day, end_day, start_time, end_time, status, cost_estimated, cost_real |
| `expenses` | Gastos directos | `id` (TEXT, `exp-{hex8}`) | trip_id, name, category, amount, notes |
| `chats` | Conversaciones | `chat_id` (TEXT, `chat-{hex8}`) | user_id, trip_id, title, created_at, last_activity_at |
| `chat_messages` | Mensajes de chat | `id` (UUID auto) | chat_id, role, type, content (JSONB), sort_order |
| `feedbacks` | Feedback post-viaje | `trip_id` (FK, UNIQUE) | overall_rating, comment, item_feedbacks (JSONB), skipped |

#### Triggers de Presupuesto

- **`trg_recalc_budget`** — Recalcula `trips.budget_total` al modificar `itinerary_items`. Excluye items con status `'sugerido'`.
- **`trg_recalc_budget_expenses`** — Recalcula `trips.budget_total` al modificar `expenses`.
- **Formula:** `budget_total = SUM(items.cost_estimated WHERE status != 'sugerido') + SUM(expenses.amount)`

#### Seguridad

- RLS (Row Level Security) habilitado en todas las tablas.
- `service_role key` bypasea RLS por defecto (usado por la app).
- Datos aislados por `user_id` (FK en todas las tablas).

#### Patron de Escritura

- **Write-through:** Cualquier mutacion en `st.session_state.trips` se persiste inmediatamente a Supabase via `sync_trip_changes()`.
- Las funciones de servicio (`add_item_to_trip`, `remove_item_from_trip`, `create_trip`, `delete_trip`, etc.) interactuan directamente con Supabase.

### 10.2. Bases de Datos Locales (LLM)

#### ChromaDB (`data/llm_data/chromadb/`)
- **Proposito:** Base de datos vectorial para memorias del chatbot.
- **Coleccion:** `"trip_planner_memories"`
- **Embeddings:** `OpenAIEmbeddings(model="text-embedding-3-small")`
- **Escritura:** `memory_manager.save_vector_memory()` — desde `extract_and_store_memories()`.
- **Lectura:** `memory_manager.search_vector_memory()` — en el nodo `memory_retrieval`.
- **Nota:** Directorio completo en `.gitignore`.

#### SQLite (`data/llm_data/langgraph_memory.db`)
- **Proposito:** Checkpointer de LangGraph para persistir estado del pipeline entre invocaciones.
- **Patron:** Cada conversacion tiene thread_id `"trip_chat_{chat_id}"` para reanudar historial.
- **Nota:** Directorio completo en `.gitignore`.

### 10.3. Datos de Ejemplo

Definidos en `data/sample_data.py`. Se cargan automaticamente si el usuario no tiene viajes en Supabase:

- **3 viajes:** Tokio (7 dias, en planificacion), Barcelona (5 dias, confirmado), Lima (3 dias, completado).
- **Items variados** con diferentes tipos, estados y costos.
- **1 perfil de ejemplo** con preferencias de alojamiento, restricciones y estilos.
- **Historiales de chat** con mensajes de ejemplo.

---

## 11. Configuracion

### 11.1. `.streamlit/config.toml`

```toml
[theme]
primaryColor = "#1E88E5"               # Azul principal
backgroundColor = "#FFFFFF"             # Fondo blanco
secondaryBackgroundColor = "#F5F7FA"    # Fondo secundario gris claro
textColor = "#212121"                   # Texto casi negro
font = "sans serif"                     # Fuente sans serif

[server]
headless = true                         # Sin navegador automatico

[browser]
gatherUsageStats = false                # No recolectar estadisticas
```

### 11.2. `.streamlit/secrets.toml` (OAuth)

Credenciales de Google OAuth. No incluido en el repositorio. Formato requerido:

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"

[auth.google]
client_id = "..."
client_secret = "..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

Sin este archivo (o sin Authlib instalado), la app funciona en modo demo con `DEMO_USER_ID`.

### 11.3. `.env`

```
SUPABASE_URL=<URL del proyecto Supabase>
SUPABASE_SERVICE_KEY=<Service role key de Supabase>
OPENAI_API_KEY=<Clave de API de OpenAI>
OPENAI_PROJECT=<Project ID de OpenAI (opcional)>
RAPIDAPI_KEY=<Clave de RapidAPI para Booking.com>
RAPIDAPI_BOOKING_HOST=booking-com15.p.rapidapi.com
SERPAPI_KEY=<Clave de SerpAPI para Google Flights>
```

| Variable | Requerida | Descripcion |
|---|---|---|
| `SUPABASE_URL` | **Si** | URL del proyecto Supabase |
| `SUPABASE_SERVICE_KEY` | **Si** | Service role key de Supabase (bypasea RLS) |
| `OPENAI_API_KEY` | No | Habilita OpenAI gpt-5-nano LLM. Sin ella, el chat muestra "IA no disponible" |
| `OPENAI_PROJECT` | No | Project ID de OpenAI (usado automaticamente por el SDK) |
| `RAPIDAPI_KEY` | No | Habilita busqueda de hoteles reales via Booking.com (DataCrawler) |
| `RAPIDAPI_BOOKING_HOST` | No | Host de la API (default: `booking-com15.p.rapidapi.com`) |
| `SERPAPI_KEY` | No | Habilita busqueda de vuelos via SerpAPI Google Flights. Sin ella, usa fast-flights (scraper) como fallback |

Las variables se cargan desde `.env` con `load_dotenv(override=True)` al inicio de `app.py`. El flag `override=True` es necesario porque la maquina puede tener variables de entorno de sistema que colisionan.

### 11.4. `config/settings.py`

Contiene todos los enums, colores, iconos, labels, mapeos globales y `DEMO_USER_ID`. Documentado en detalle en la seccion 5.

### 11.5. `config/llm_config.py`

Contiene la configuracion del modelo LLM (OpenAI gpt-5-nano), modelo de embeddings, temperaturas y parametros de memoria. Documentado en la seccion 5.3. Todos los valores son configurables via variables de entorno (`LLM_DEFAULT_MODEL`, `LLM_DEFAULT_TEMPERATURE`, `LLM_EXTRACTION_TEMPERATURE`, `LLM_EMBEDDING_MODEL`, `LLM_MAX_VECTOR_RESULTS`).

### 11.6. CSS Global

Definido inline en `app.py`:
- `.status-badge` — Badges de estado con colores por tipo.
- `.status-planning` — Fondo amarillo claro, texto ambar.
- `.status-confirmed` — Fondo verde claro, texto verde oscuro.
- `.status-in-progress` — Fondo azul claro, texto azul oscuro.
- `.status-completed` — Fondo gris claro, texto gris.
- `.suggested-item` — Borde punteado naranja con opacidad 85%.
- `.active-trip-box` — Caja azul con borde izquierdo azul para sidebar.
- `.transfer-block` — Bloque gris con borde izquierdo gris para traslados.

---

## 12. Reglas de Negocio

### 12.1. Regla Critica: Items Sugeridos y Presupuesto

> Los items con `status = "sugerido"` **NO se contabilizan en el presupuesto**. Solo se suman los costos estimados de items `"pendiente"` y `"confirmado"`, mas los gastos directos (expenses).

Esta regla se aplica consistentemente en:
- `recalculate_budget()` en trip_service.py
- `calculate_budget_summary()` en budget_service.py
- Triggers de Supabase (`trg_recalc_budget`)

### 12.2. Transiciones de Estado de Viajes

```
en_planificacion ──(usuario confirma)──> confirmado
        │                                     │
        └──(hoy >= start_date)──> en_curso <──┘
                                     │
                                     └──(hoy > end_date)──> completado
```

**Reglas automaticas (en `update_trip_statuses()`):**
- Si `hoy > end_date` y no esta completado → `completado`
- Si `start_date <= hoy <= end_date` y esta en `confirmado` o `en_planificacion` → `en_curso`
- Los viajes ya `completado` nunca se modifican automaticamente.

### 12.3. Prioridad de Viaje Activo

El viaje activo se selecciona con la siguiente prioridad:
1. El `active_trip_id` explicito (si existe y es valido).
2. El primer viaje en estado `"en_planificacion"`.
3. El proximo viaje confirmado (por fecha de inicio ascendente).
4. El primer viaje en curso.
5. `None` si no hay viajes.

### 12.4. Seleccion de Viaje por Pagina

Cada pagina (excepto Cronograma que es global) tiene un `st.selectbox` propio para elegir viaje. Al seleccionar en cualquier pagina, se actualiza `st.session_state.active_trip_id` para sincronizar las demas. `app.py` sincroniza `chat_selected_trip_id` → `active_trip_id` en cada rerun.

### 12.5. Eliminacion de Viajes

Solo se pueden eliminar viajes en estado `"en_planificacion"`. Los viajes confirmados, en curso o completados no pueden eliminarse. La eliminacion en Supabase es cascada (items, expenses, chats).

### 12.6. Ordenamiento de Viajes en Lista

Orden: en curso > en planificacion (fecha asc) > confirmado (fecha asc) > completado (fecha desc).

### 12.7. Items Multi-dia

Items con `end_day > day` se renderizan como `allDay: true` en FullCalendar con color Blue Grey (`#607D8B`).

### 12.8. Traslados entre Items

Se genera un bloque de traslado entre dos items consecutivos si ambos tienen ubicacion definida y son diferentes. En el MVP, datos mock: "Metro / Taxi", 20 min, USD 5.

### 12.9. Acciones desde el Chat que Requieren Confirmacion

Todas las acciones que modifican datos requieren confirmacion UI:
- Agregar item (`add_item`)
- Eliminar item (`remove_item`)
- Crear viaje (`create_trip`)
- Agregar evento de calendario (`calendar_event`)
- Agregar gasto (`add_expense`)
- Modificar gasto (`modify_expense`)
- Eliminar gasto (`remove_expense`)

### 12.10. Multi-conversacion

Cada usuario tiene multiples chats. Cada chat esta asociado a un viaje (`trip_id`) y tiene titulo auto-generado. Persistido en Supabase (tablas `chats` + `chat_messages`). Al cambiar de viaje, se muestran los chats de ese viaje.

### 12.11. Feedback Post-Viaje

- Solo disponible para viajes completados.
- Opcional; el usuario puede omitirla (`skipped: True`).
- Incluye valoracion general (1-5), comentarios, y valoracion por item.
- Banner de feedback pendiente en el Dashboard.

### 12.12. Autenticacion y Multi-usuario

- OAuth condicional por Authlib + secrets.toml.
- Sin OAuth: modo demo con `DEMO_USER_ID`.
- Todos los servicios aceptan `user_id`.
- Supabase aisla datos por `user_id` con FK en todas las tablas + RLS.
- `st.logout()` es una accion inmediata, no un boton — siempre envolverlo en `if st.button(): st.logout()`.

---

## 13. Dependencias y Ejecucion

### 13.1. Instalacion

```bash
python -m venv venv

# Activar entorno virtual
# Windows (PowerShell): .\venv\Scripts\Activate.ps1
# Windows (CMD): .\venv\Scripts\activate.bat
# Linux/macOS: source venv/bin/activate

pip install -r requirements.txt
```

### 13.2. Ejecucion

```bash
python -m streamlit run app.py         # App principal (localhost:8501)
.\run.bat                              # Windows: lanza con el venv explicitamente
python mcp_servers/booking_server.py   # Servidor MCP standalone (stdio)
```

Siempre usar `python -m streamlit run app.py` (no `streamlit run app.py`) para asegurar que se use el Python del venv.

### 13.3. Variables de Entorno

| Variable | Requerida | Descripcion |
|---|---|---|
| `SUPABASE_URL` | **Si** | URL del proyecto Supabase |
| `SUPABASE_SERVICE_KEY` | **Si** | Service role key de Supabase (bypasea RLS) |
| `OPENAI_API_KEY` | No | Habilita OpenAI gpt-5-nano. Sin ella, "IA no disponible" |
| `OPENAI_PROJECT` | No | Project ID de OpenAI |
| `RAPIDAPI_KEY` | No | Habilita hoteles reales (Booking.com) |
| `RAPIDAPI_BOOKING_HOST` | No | Host de la API (default: `booking-com15.p.rapidapi.com`) |
| `SERPAPI_KEY` | No | Habilita vuelos via SerpAPI. Sin ella, usa fast-flights como fallback |

Las variables se cargan desde `.env` con `load_dotenv(override=True)` en `app.py`. OAuth requiere adicionalmente `.streamlit/secrets.toml`.

### 13.4. Base de Datos

Ejecutar `scripts/setup_database.sql` en el Supabase SQL Editor para crear el schema. El script es transaccional e idempotente.
