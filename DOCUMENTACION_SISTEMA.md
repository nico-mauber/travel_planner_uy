# Documentacion General del Sistema — Trip Planner

**Fecha de generacion:** 2026-03-14
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

Trip Planner es un **MVP de un agente de planificacion de viajes** con interfaz web construida en Streamlit. Permite a un usuario unico planificar viajes completos: itinerarios dia a dia, presupuestos por categoria, cronograma visual, y un chat conversacional con un agente que puede operar en dos modos (LLM con Google Gemini o mock con pattern matching).

### Usuario Objetivo

Un viajero individual que desea planificar uno o mas viajes con asistencia de un agente conversacional. No hay autenticacion ni multiusuario; el sistema opera con persistencia local en archivos JSON.

### Stack Tecnologico

| Tecnologia | Version minima | Proposito |
|---|---|---|
| Python | 3.x | Lenguaje principal |
| Streamlit | >= 1.40.0 | Framework de interfaz web |
| Plotly | >= 5.18.0 | Graficos de presupuesto (donut, barras) |
| streamlit-calendar | >= 1.2.0 | Vista de calendario interactiva |
| python-dotenv | >= 1.0.0 | Carga de variables de entorno desde `.env` |
| langchain-google-genai | >= 2.1.0 | Integracion con Google Gemini |
| langchain-core | >= 0.3.0 | Primitivas de LangChain (prompts, mensajes, parsers) |
| langgraph | >= 0.2.0 | Pipeline de nodos del chatbot |
| langgraph-checkpoint | >= 2.0.0 | Persistencia de checkpoints de LangGraph |
| langgraph-checkpoint-sqlite | >= 3.0.0 | Checkpointer SQLite para LangGraph |
| langchain-chroma | >= 0.2.0 | Integracion LangChain + ChromaDB |
| chromadb | >= 0.5.0 | Base de datos vectorial para memorias |
| pydantic | >= 2.0.0 | Validacion de modelos de datos estructurados |
| typing_extensions | >= 4.8.0 | Extensiones de tipado para Python |

### Estado Actual

MVP funcional. No hay tests ni linter configurados. El sistema soporta 3 viajes de ejemplo precargados (Tokio, Barcelona, Lima) con ~32 items totales. El agente conversacional opera en modo mock (pattern matching) o modo LLM (Google Gemini) dependiendo de la disponibilidad de la API key.

---

## 2. Arquitectura del Sistema

### Diagrama de Capas

```
┌─────────────────────────────────────────────────────────────────┐
│                        CAPA DE PRESENTACION                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  app.py  (Punto de entrada, config, session_state, nav)   │  │
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
│  ┌────────────────────┐  ┌────────────────────────────────┐    │
│  │  trip_service.py    │  │  agent_service.py (selector)   │    │
│  │  budget_service.py  │  │  llm_agent_service.py          │    │
│  │  profile_service.py │  │  llm_chatbot.py (LangGraph)    │    │
│  │  weather_service.py │  │  memory_manager.py (ChromaDB)  │    │
│  │  feedback_service.py│  │                                │    │
│  └────────────────────┘  └────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                     CAPA DE CONFIGURACION                       │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │  config/settings.py │  │  config/llm_config │                │
│  └────────────────────┘  └────────────────────┘                │
├─────────────────────────────────────────────────────────────────┤
│                     CAPA DE PERSISTENCIA                        │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│  │ trips.json   │ │profiles.json │ │ data/llm_data/           │ │
│  │              │ │              │ │  chromadb/ (vectores)    │ │
│  │              │ │              │ │  langgraph_memory.db     │ │
│  └─────────────┘ └──────────────┘ └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo de Datos Principal

```
st.session_state.trips  (fuente unica de verdad en runtime)
         │
         ├──> Paginas leen trips y obtienen viaje activo via get_active_trip()
         │
         ├──> Usuario interactua (chat, botones, formularios)
         │
         ├──> Servicios mutan trips[] (agregar/eliminar items, cambiar estados)
         │
         ├──> sync_trip_changes() recalcula presupuesto + persiste a JSON
         │
         └──> st.rerun() refresca la pagina con datos actualizados
```

### Patron de Comunicacion entre Componentes

1. **Paginas** leen `st.session_state.trips` y obtienen el viaje activo.
2. **Componentes** reciben datos como parametros y retornan acciones como dicts (ej: `{"action": "accept", "item_id": "..."}`).
3. **Paginas** interpretan la accion retornada y llaman al servicio correspondiente.
4. **Servicios** mutan los datos en memoria y persisten a JSON.
5. La pagina llama `st.rerun()` para refrescar la UI.

### Puntos de Entrada y Salida

- **Entrada:** `app.py` es el unico punto de entrada. Se ejecuta con `python -m streamlit run app.py`.
- **Salida de datos:** Archivos JSON en `data/` (trips.json, profiles.json, feedbacks.json) y bases de datos en `data/llm_data/`.

---

## 3. Estructura de Archivos

```
Trip_Planner/
├── .env                              # Variable GOOGLE_API_KEY
├── .gitignore                        # Excluye: .env, data/llm_data/, feedbacks.json, venv/, __pycache__/
├── .streamlit/
│   └── config.toml                   # Tema y configuracion de Streamlit
├── CLAUDE.md                         # Instrucciones para Claude Code
├── app.py                            # Punto de entrada: config, session_state, navegacion, sidebar
├── requirements.txt                  # Dependencias de Python
│
├── config/
│   ├── __init__.py                   # Vacio
│   ├── settings.py                   # Enums, colores, iconos, labels, mapeos globales
│   └── llm_config.py                 # Modelo LLM, embedding, memoria vectorial
│
├── components/
│   ├── __init__.py                   # Vacio
│   ├── alert_banner.py               # Alertas descartables del viaje
│   ├── budget_charts.py              # Graficos Plotly (donut, barras comparativas)
│   ├── chat_widget.py                # Tarjetas ricas y confirmaciones del chat
│   ├── itinerary_item.py             # Item expandible del itinerario + traslados
│   └── trip_card.py                  # Tarjeta de viaje para la lista Mis Viajes
│
├── data/
│   ├── __init__.py                   # Vacio
│   ├── sample_data.py                # 3 viajes demo + perfil ejemplo + chat histories
│   ├── trips.json                    # Persistencia de viajes
│   ├── profiles.json                 # Persistencia del perfil de usuario
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
│   ├── 2_Chat.py                     # Chat conversacional con el agente
│   ├── 3_Cronograma.py               # Vista de calendario
│   ├── 4_Itinerario.py               # Itinerario dia por dia
│   ├── 5_Presupuesto.py              # Desglose de presupuesto por categoria
│   ├── 6_Perfil.py                   # Configuracion de preferencias
│   └── 7_Mis_Viajes.py               # Lista de viajes + crear/eliminar + feedback
│
├── services/
│   ├── __init__.py                   # Vacio
│   ├── trip_service.py               # CRUD viajes, agrupacion, sync, presupuesto
│   ├── agent_service.py              # Selector LLM/mock, pattern matching, confirmaciones
│   ├── llm_agent_service.py          # Wrapper que instancia TripChatbot
│   ├── llm_chatbot.py                # Pipeline LangGraph con 4 nodos (Gemini)
│   ├── memory_manager.py             # ChromaDB, extraccion automatica de memorias
│   ├── budget_service.py             # Calculo de presupuesto por categoria
│   ├── profile_service.py            # Carga/guardado de perfil (JSON)
│   ├── weather_service.py            # Datos climaticos mock por destino
│   └── feedback_service.py           # CRUD de retroalimentacion post-viaje
│
└── Requerimientos/
    └── MVP/
        └── UI/
            ├── resumen-requerimientos.md
            ├── REQ-UI-001.md a REQ-UI-012.md
            └── PLAN_IMPLEMENTACION_UI.md
```

---

## 4. Modelos de Datos

### 4.1. Estructura de un Trip (dict)

En runtime, los viajes son **dicts planos** (no dataclasses). La estructura completa, verificada en `data/sample_data.py` (lineas 9-281) y `services/trip_service.py` (lineas 72-87):

| Campo | Tipo | Descripcion | Ejemplo |
|---|---|---|---|
| `id` | `str` | Identificador unico, formato `trip-{hex8}` | `"trip-001"` |
| `name` | `str` | Nombre descriptivo del viaje | `"Aventura en Tokio"` |
| `destination` | `str` | Destino con ciudad y pais | `"Tokio, Japon"` |
| `start_date` | `str` | Fecha de inicio ISO YYYY-MM-DD | `"2026-04-10"` |
| `end_date` | `str` | Fecha de fin ISO YYYY-MM-DD | `"2026-04-16"` |
| `status` | `str` | Estado del viaje (valor de `TripStatus`) | `"en_planificacion"` |
| `budget_total` | `float` | Presupuesto total calculado (excluye sugeridos) | `3200.0` |
| `notes` | `str` | Notas libres del viaje | `"Viaje de primavera..."` |
| `items` | `list[dict]` | Lista de items del itinerario | `[{...}, {...}]` |

### 4.2. Estructura de un Item (dict)

Cada item vive anidado dentro de `trip["items"]`. Estructura verificada en `data/sample_data.py` (lineas 21-36) y `models/itinerary_item.py`:

| Campo | Tipo | Descripcion | Ejemplo |
|---|---|---|---|
| `id` | `str` | Identificador unico, formato `item-{hex8}` | `"item-001"` |
| `trip_id` | `str` | ID del viaje padre | `"trip-001"` |
| `name` | `str` | Nombre de la actividad | `"Vuelo MVD -> Tokio"` |
| `item_type` | `str` | Tipo (valor de `ItemType`) | `"vuelo"` |
| `day` | `int` | Dia del viaje (1-based) | `1` |
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

### 4.3. Estructura de un Mensaje de Chat

Los mensajes se almacenan en `st.session_state.chat_histories[trip_id]` como lista de dicts. Verificado en `data/sample_data.py` (lineas 622-674) y `pages/2_Chat.py`.

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
        "action": "add_item" | "remove_item" | "create_trip",
        "summary": "Descripcion breve de la accion",
        "details": {
            # Campos especificos segun la accion
            # add_item: name, item_type, day, start_time, end_time, cost_estimated, location
            # remove_item: item_id, item_name
            # create_trip: destination, name
        }
    },
    "processed": True | False,      # Se agrega cuando el usuario responde
    "result": "Texto del resultado"  # Se agrega junto con processed
}
```

### 4.4. Estructura del Perfil de Usuario

Almacenado en `st.session_state.user_profile` y persistido en `data/profiles.json`. Verificado en `data/sample_data.py` (lineas 607-617):

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

### 4.5. Estructura de Feedback

Almacenado en `data/feedbacks.json` con clave = trip_id. Verificado en `pages/7_Mis_Viajes.py` (lineas 201-221):

```python
{
    "trip-003": {
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
}
```

---

## 5. Enums y Constantes

Todas las constantes viven en `config/settings.py` (109 lineas).

### 5.1. Enums

#### TripStatus (linea 6)
| Valor del Enum | Valor string | Label en espanol |
|---|---|---|
| `PLANNING` | `"en_planificacion"` | En planificacion |
| `CONFIRMED` | `"confirmado"` | Confirmado |
| `IN_PROGRESS` | `"en_curso"` | En curso |
| `COMPLETED` | `"completado"` | Completado |

#### ItemStatus (linea 13)
| Valor del Enum | Valor string | Label |
|---|---|---|
| `CONFIRMED` | `"confirmado"` | Confirmado |
| `PENDING` | `"pendiente"` | Pendiente |
| `SUGGESTED` | `"sugerido"` | Sugerido |

#### ItemType (linea 19)
| Valor del Enum | Valor string | Label |
|---|---|---|
| `ACTIVITY` | `"actividad"` | Actividad |
| `TRANSFER` | `"traslado"` | Traslado |
| `ACCOMMODATION` | `"alojamiento"` | Alojamiento |
| `FOOD` | `"comida"` | Comida |
| `FLIGHT` | `"vuelo"` | Vuelo |
| `EXTRA` | `"extra"` | Extra |

#### BudgetCategory (linea 28)
| Valor del Enum | Valor string | Label |
|---|---|---|
| `FLIGHTS` | `"vuelos"` | Vuelos |
| `ACCOMMODATION` | `"alojamiento"` | Alojamiento |
| `ACTIVITIES` | `"actividades"` | Actividades |
| `FOOD` | `"comidas"` | Comidas |
| `TRANSPORT` | `"transporte_local"` | Transporte local |
| `EXTRAS` | `"extras"` | Extras |

### 5.2. Mapeos

#### Colores por ItemType (`ITEM_TYPE_COLORS`, linea 38)
| Tipo | Color hex |
|---|---|
| ACTIVITY | `#4CAF50` (verde) |
| TRANSFER | `#9E9E9E` (gris) |
| ACCOMMODATION | `#2196F3` (azul) |
| FOOD | `#FF9800` (naranja) |
| FLIGHT | `#E91E63` (rosa) |
| EXTRA | `#9C27B0` (purpura) |

#### Colores por BudgetCategory (`BUDGET_CATEGORY_COLORS`, linea 48)
| Categoria | Color hex |
|---|---|
| FLIGHTS | `#E91E63` |
| ACCOMMODATION | `#2196F3` |
| ACTIVITIES | `#4CAF50` |
| FOOD | `#FF9800` |
| TRANSPORT | `#9E9E9E` |
| EXTRAS | `#9C27B0` |

#### Iconos por ItemType (`ITEM_TYPE_ICONS`, linea 58)
| Tipo | Icono |
|---|---|
| ACTIVITY | 🎯 |
| TRANSFER | 🚕 |
| ACCOMMODATION | 🏨 |
| FOOD | 🍽️ |
| FLIGHT | ✈️ |
| EXTRA | 📦 |

#### Iconos por ItemStatus (`STATUS_ICONS`, linea 68)
| Estado | Icono |
|---|---|
| CONFIRMED | ✅ |
| PENDING | ⏳ |
| SUGGESTED | 💡 |

#### Mapeo ItemType a BudgetCategory (`ITEM_TYPE_TO_BUDGET`, linea 101)
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
| `DEFAULT_MODEL` | `"gemini-2.5-flash"` | Modelo de Gemini para chat |
| `DEFAULT_TEMPERATURE` | `0.7` | Temperatura de generacion |
| `DEFAULT_EMBEDDING_MODEL` | `"models/embedding-001"` | Modelo de embeddings de Google |
| `MAX_VECTOR_RESULTS` | `3` | Memorias vectoriales a recuperar por query |
| `MEMORY_CATEGORIES` | `["viaje", "preferencias", "personal", "hechos_importantes"]` | Categorias de memoria |

---

## 6. Servicios

### 6.1. trip_service.py

**Archivo:** `services/trip_service.py` (226 lineas)
**Proposito:** Servicio central de gestion de viajes. CRUD de viajes e items, agrupacion, ordenamiento, sincronizacion con JSON.
**Dependencias:** `config.settings`, `data.sample_data`

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `load_trips` | `() -> list` | `list[dict]` | Carga viajes desde `trips.json`. Si esta vacio, carga datos de ejemplo y los persiste. |
| `save_trips` | `(trips: list) -> None` | `None` | Persiste la lista de viajes en `trips.json`. Crea el directorio `data/` si no existe. |
| `get_trip_by_id` | `(trips: list, trip_id: str) -> Optional[dict]` | `dict` o `None` | Busca un viaje por ID. |
| `get_active_trip` | `(trips: list, active_trip_id: Optional[str]) -> Optional[dict]` | `dict` o `None` | Obtiene el viaje activo. Prioridad: `active_trip_id` > primer viaje en planificacion > proximo confirmado > en curso. |
| `create_trip` | `(trips: list, name: str, destination: str, start_date: str, end_date: str) -> dict` | `dict` | Crea un viaje nuevo en estado `"en_planificacion"` con ID generado via `uuid.uuid4().hex[:8]`. Persiste a JSON. |
| `delete_trip` | `(trips: list, trip_id: str) -> bool` | `bool` | Elimina un viaje (solo si esta en planificacion). Retorna `True` si lo elimino. |
| `update_trip_statuses` | `(trips: list) -> None` | `None` | Actualiza estados automaticamente segun fechas. Confirmado/Planning -> En curso si hoy esta entre start y end. Cualquier estado -> Completado si hoy > end. No modifica viajes ya completados. |
| `sort_trips` | `(trips: list) -> list` | `list[dict]` | Ordena: en curso > en planificacion (asc) > confirmado (asc) > completado (desc). |
| `filter_trips_by_status` | `(trips: list, status: Optional[str]) -> list` | `list[dict]` | Filtra viajes por estado. `None` o `"Todos"` retorna todos. |
| `group_items_by_day` | `(items: list) -> dict` | `dict[int, list]` | Agrupa items por dia y ordena cronologicamente por `start_time` dentro de cada dia. |
| `accept_suggestion` | `(trip: dict, item_id: str) -> bool` | `bool` | Cambia un item de `"sugerido"` a `"pendiente"`. |
| `discard_suggestion` | `(trip: dict, item_id: str) -> bool` | `bool` | Elimina un item en estado `"sugerido"`. |
| `add_item_to_trip` | `(trip: dict, item: dict) -> None` | `None` | Agrega un item y recalcula presupuesto. |
| `remove_item_from_trip` | `(trip: dict, item_id: str) -> bool` | `bool` | Elimina un item por ID y recalcula presupuesto. |
| `recalculate_budget` | `(trip: dict) -> None` | `None` | Recalcula `budget_total` sumando `cost_estimated` de items no sugeridos. **Efecto:** Muta `trip["budget_total"]`. |
| `sync_trip_changes` | `(trips: list, trip: dict) -> None` | `None` | Recalcula presupuesto, actualiza el trip en la lista, y persiste a JSON. **Efecto:** Escritura a disco. |
| `get_transfer_info` | `(item_a: dict, item_b: dict) -> Optional[dict]` | `dict` o `None` | Genera info de traslado entre dos items con ubicaciones diferentes. Retorna `None` si la ubicacion es la misma o esta vacia. Datos mock fijos: transporte "Metro / Taxi", duracion "20 min", costo 5.0. |

### 6.2. agent_service.py

**Archivo:** `services/agent_service.py` (278 lineas)
**Proposito:** Selector LLM/mock y procesamiento de mensajes del usuario. Las acciones que modifican el itinerario (agregar, eliminar, crear viaje) siempre pasan por el mock para generar confirmaciones UI, independientemente del modo.
**Dependencias:** `config.settings`, `services.llm_agent_service` (condicional)

**Deteccion del modo LLM** (lineas 11-18):
```python
_USE_LLM = bool(os.environ.get("GOOGLE_API_KEY"))
if _USE_LLM:
    try:
        from services.llm_agent_service import process_message_llm, LLM_AVAILABLE
        _USE_LLM = LLM_AVAILABLE
    except ImportError:
        _USE_LLM = False
```

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `is_llm_active` | `() -> bool` | `bool` | Retorna `True` si el LLM esta activo. |
| `process_message` | `(message: str, trip: Optional[dict]) -> dict` | `dict` | Procesa un mensaje. Las acciones de modificacion (agregar, eliminar, crear) siempre usan mock con confirmaciones. Para todo lo demas, usa LLM si disponible, sino fallback a mock. Retorna `{role, type, content}`. |
| `apply_confirmed_action` | `(action: dict, trip: dict, trips: list) -> str` | `str` | Aplica una accion confirmada (add_item, remove_item, create_trip). Crea items con ID generado, sincroniza cambios. Retorna mensaje de resultado. |

**Funciones mock privadas:**
- `_mock_process_message(msg, trip)` — Pattern matching por keywords: vuelo, hotel, actividad, comida, presupuesto, clima, saludo. Retorna `text` o `card`.
- `_flight_response(trip)` / `_hotel_response(trip)` / `_activity_response(trip)` / `_food_response(trip)` — Generan tarjetas ricas mock.
- `_add_item_response(msg, trip)` — Genera confirmacion de agregar item.
- `_remove_item_response(msg, trip)` — Genera confirmacion de eliminar el ultimo item.
- `_budget_response(trip)` — Calcula y muestra presupuesto total (excluye sugeridos).
- `_weather_response(trip)` — Obtiene datos climaticos mock via `weather_service`.

### 6.3. llm_agent_service.py

**Archivo:** `services/llm_agent_service.py` (29 lineas)
**Proposito:** Wrapper delgado que conecta `agent_service.py` con `TripChatbot`. Expone la variable `LLM_AVAILABLE` para que el selector sepa si puede usar LLM.
**Dependencias:** `services.llm_chatbot`

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `process_message_llm` | `(message: str, trip: Optional[dict], user_profile: Optional[dict]) -> dict` | `dict` | Obtiene la instancia singleton de `TripChatbot`, construye el `chat_id` a partir del trip ID, y delega al metodo `chat()`. |

**Variable global:**
- `LLM_AVAILABLE: bool` — `True` si `TripChatbot` se pudo importar sin error. Se evalua al importar el modulo.

### 6.4. llm_chatbot.py

**Archivo:** `services/llm_chatbot.py` (227 lineas)
**Proposito:** Pipeline LangGraph completo con 4 nodos para el chatbot con Google Gemini. Implementa el patron singleton.
**Dependencias:** `langgraph`, `langchain_core`, `langchain_google_genai`, `services.memory_manager`, `config.llm_config`

**Clase `TripChatbot`:**

| Metodo | Signature | Retorno | Descripcion |
|---|---|---|---|
| `get_instance` | `(cls) -> TripChatbot` | `TripChatbot` | Patron singleton. Crea la instancia unica si no existe. |
| `__init__` | `(self)` | - | Inicializa: `TripMemoryManager`, `ChatGoogleGenerativeAI(model=gemini-2.5-flash, temp=0.7)`, system prompt en espanol, message trimmer (4000 tokens), y compila el pipeline LangGraph. |
| `_create_app` | `(self)` | `CompiledGraph` | Crea el pipeline LangGraph con 4 nodos y checkpointer SQLite. Ver seccion 9 para detalle de nodos. |
| `chat` | `(self, message: str, trip: Optional[dict], user_profile: Optional[dict], chat_id: str) -> dict` | `dict` | Envia un mensaje al pipeline. Serializa el contexto del viaje (destino, fechas, stats de items), invoca el grafo con `thread_id = "trip_chat_{chat_id}"`, extrae la respuesta del ultimo mensaje. Siempre retorna `{role: "assistant", type: "text", content: str}`. En caso de error, retorna mensaje de error. |

**System prompt** (lineas 35-56): Define la personalidad del asistente como experto en viajes, conciso, en espanol, que recuerda preferencias y da sugerencias con precios. Incluye placeholders para: `{memory_context}`, `{trip_context}`, `{user_profile_context}`.

### 6.5. memory_manager.py

**Archivo:** `services/memory_manager.py` (213 lineas)
**Proposito:** Gestion de memoria vectorial con ChromaDB para el chatbot LLM. Extraccion automatica de memorias relevantes de los mensajes del usuario.
**Dependencias:** `chromadb`, `langchain_chroma`, `langchain_google_genai`, `langchain_core`, `pydantic`, `config.llm_config`

**Clases auxiliares:**

- `MemoryState(TypedDict)` (linea 17) — Estado del pipeline LangGraph con campos: `messages`, `vector_memories`, `user_profile`, `last_memory_extraction`, `trip_context`.
- `ExtractedMemory(BaseModel)` (linea 26) — Modelo Pydantic con campos: `category` (str), `content` (str), `importance` (int 0-5).

**Clase `TripMemoryManager`:**

| Metodo | Signature | Retorno | Descripcion |
|---|---|---|---|
| `__init__` | `(self)` | - | Crea directorio `data/llm_data/`, inicializa ChromaDB con coleccion `"trip_planner_memories"` y embeddings de Google, inicializa sistema de extraccion. |
| `_init_vector_db` | `(self)` | - | Inicializa ChromaDB persistente con `GoogleGenerativeAIEmbeddings(model="models/embedding-001")`. Crea o recupera la coleccion. Si falla, establece `vectorstore = None`. |
| `_init_extraction_system` | `(self)` | - | Configura un chain de LangChain: `PromptTemplate | ChatGoogleGenerativeAI(temp=0) | PydanticOutputParser(ExtractedMemory)`. El prompt analiza mensajes y extrae memorias categorizadas. |
| `save_vector_memory` | `(self, text: str, metadata: Optional[Dict]) -> str` | `str` | Guarda una memoria en ChromaDB con UUID como ID. Agrega timestamp e ID al metadata. Retorna el ID o string vacio si falla. |
| `search_vector_memory` | `(self, query: str, k: int) -> List[str]` | `list[str]` | Busca las k memorias mas similares semanticamente. Default k=3. Retorna lista de textos. |
| `get_all_vector_memories` | `(self) -> List[Dict]` | `list[dict]` | Retorna todas las memorias almacenadas como lista de `{id, content, metadata}`. |
| `extract_and_store_memories` | `(self, user_message: str) -> bool` | `bool` | Intenta extraer memorias con el LLM. Si la categoria no es "none" y la importancia >= 2, la guarda. Fallback a extraccion manual si falla. |
| `_extract_memories_manual` | `(self, user_message: str) -> bool` | `bool` | Fallback basado en keywords. Reglas: preferencias (prefiero, me gusta...), restricciones (alergia, vegetariano...), personal (me llamo, vivo en...), viaje (viaje a, visite...), presupuesto (presupuesto, gastar...). |

### 6.6. budget_service.py

**Archivo:** `services/budget_service.py` (67 lineas)
**Proposito:** Calculos de presupuesto por categoria, progreso de planificacion.
**Dependencias:** `config.settings`

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `calculate_budget_summary` | `(items: list) -> dict` | `dict` | Calcula presupuesto desglosado por categoria. Items `"sugerido"` NO se contabilizan (RN-002 REQ-UI-006). Retorna `{total_estimated, total_real, by_category: {cat: {label, estimated, real, items}}}`. |
| `has_real_costs` | `(items: list) -> bool` | `bool` | `True` si algun item no sugerido tiene `cost_real > 0`. |
| `calculate_planning_progress` | `(items: list) -> float` | `float` | Proporcion de items confirmados sobre total de items no sugeridos (0.0 a 1.0). |

### 6.7. profile_service.py

**Archivo:** `services/profile_service.py` (35 lineas)
**Proposito:** Carga y guardado del perfil de usuario en JSON.
**Dependencias:** `data.sample_data`

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `load_profile` | `() -> dict` | `dict` | Carga perfil desde `profiles.json`. Si no existe o esta vacio, carga el perfil de ejemplo y lo persiste. |
| `save_profile` | `(profile: dict) -> bool` | `bool` | Guarda el perfil en `profiles.json`. Retorna `True` si exitoso. |

**Archivos afectados:** `data/profiles.json`

### 6.8. weather_service.py

**Archivo:** `services/weather_service.py` (39 lineas)
**Proposito:** Datos climaticos mock para los destinos de ejemplo. No consulta APIs externas.
**Dependencias:** Ninguna

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `get_weather` | `(destination: str) -> dict` | `dict` | Retorna datos climaticos mock: `{temp_min, temp_max, condition, icon, description}`. Si el destino no esta en los datos hardcodeados, retorna datos por defecto ("Variable", 15-25°C). |

**Destinos con datos:**
| Destino | Temp min-max | Condicion |
|---|---|---|
| Tokio, Japon | 15-22°C | Parcialmente nublado |
| Barcelona, Espana | 18-25°C | Soleado |
| Lima, Peru | 20-28°C | Nublado parcial |

### 6.9. feedback_service.py

**Archivo:** `services/feedback_service.py` (62 lineas)
**Proposito:** CRUD de retroalimentacion post-viaje.
**Dependencias:** `config.settings`

| Funcion | Signature | Retorno | Descripcion |
|---|---|---|---|
| `load_feedbacks` | `() -> dict` | `dict` | Carga feedbacks desde `feedbacks.json`. Clave = trip_id. |
| `save_feedback` | `(trip_id: str, feedback: dict) -> bool` | `bool` | Guarda feedback para un viaje. Carga existentes, agrega/sobreescribe, y persiste. |
| `has_feedback` | `(trip_id: str) -> bool` | `bool` | `True` si el viaje tiene feedback. |
| `get_feedback` | `(trip_id: str) -> dict` | `dict` | Retorna el feedback del viaje (o dict vacio). |
| `has_pending_feedback` | `(trips: list) -> bool` | `bool` | `True` si hay viajes completados sin feedback. |
| `get_trips_pending_feedback` | `(trips: list) -> list` | `list[dict]` | Retorna viajes completados sin feedback. |

**Archivo afectado:** `data/feedbacks.json`

---

## 7. Componentes UI

### 7.1. chat_widget.py

**Archivo:** `components/chat_widget.py` (72 lineas)
**Proposito:** Renderiza tarjetas ricas y solicitudes de confirmacion dentro del flujo del chat.

#### `render_rich_card(card_data: dict) -> None`
- **Renderiza:** Un contenedor con borde que muestra un icono de tipo, nombre, proveedor, ubicacion, duracion, precio, rating, horarios de vuelo y notas.
- **Parametros:** `card_data` — dict con campos: `card_type`, `name`, `provider`, `price`, `location`, `rating`, `duration`, `departure`, `arrival`, `notes`.
- **Acciones:** Ninguna (solo lectura).

#### `render_confirmation(action_data: dict, msg_index: int) -> str`
- **Renderiza:** Un contenedor con el resumen de la accion pendiente, detalles en formato clave-valor, y botones "Confirmar" / "Cancelar".
- **Parametros:** `action_data` — dict con `summary` y `details`; `msg_index` — indice para generar keys unicos de botones.
- **Retorna:** `"confirm"`, `"cancel"` o `""` (sin interaccion).

### 7.2. budget_charts.py

**Archivo:** `components/budget_charts.py` (89 lineas)
**Proposito:** Graficos Plotly para la vista de presupuesto.

#### `render_donut_chart(budget_summary: dict) -> None`
- **Renderiza:** Grafico de dona (Pie con hole=0.4) mostrando la distribucion del presupuesto estimado por categoria. Usa los colores de `BUDGET_CATEGORY_COLORS`. Muestra label + porcentaje fuera del grafico. Altura: 350px.
- **Parametros:** `budget_summary` — resultado de `calculate_budget_summary()`.

#### `render_comparison_bars(budget_summary: dict) -> None`
- **Renderiza:** Barras agrupadas comparando estimado (azul `#1E88E5`) vs real (verde `#43A047`) por categoria. Eje Y en USD. Leyenda horizontal arriba. Altura: 350px.
- **Parametros:** `budget_summary` — resultado de `calculate_budget_summary()`.

### 7.3. trip_card.py

**Archivo:** `components/trip_card.py` (49 lineas)
**Proposito:** Tarjeta de viaje para la lista en Mis Viajes.

#### `render_trip_card(trip: dict, index: int) -> dict`
- **Renderiza:** Contenedor con nombre del viaje, destino con badge de estado (emoji color), fechas, presupuesto, boton "Ver viaje" (siempre visible), y boton "Eliminar" (solo si esta en planificacion).
- **Parametros:** `trip` — dict del viaje; `index` — indice para keys unicos.
- **Retorna:** `{"action": "view", "trip_id": "..."}`, `{"action": "delete", "trip_id": "..."}` o `{}`.

**Badges de estado:**
| Estado | Badge |
|---|---|
| en_planificacion | 🟡 |
| confirmado | 🟢 |
| en_curso | 🔵 |
| completado | ⚪ |

### 7.4. itinerary_item.py

**Archivo:** `components/itinerary_item.py` (78 lineas)
**Proposito:** Item expandible del itinerario y bloque visual de traslado.

#### `render_itinerary_item(item: dict, index: int) -> dict`
- **Renderiza:** Un `st.expander` con: icono de tipo + nombre + horario en el titulo, icono de estado, y al expandir: tipo, ubicacion, direccion, costos estimado/real, proveedor, notas, link de reserva. Para items sugeridos: caption explicativa y botones "Aceptar" / "Descartar".
- **Parametros:** `item` — dict del item; `index` — para keys unicos.
- **Retorna:** `{"action": "accept", "item_id": "..."}`, `{"action": "discard", "item_id": "..."}` o `{}`.

#### `render_transfer(transfer_info: dict) -> None`
- **Renderiza:** Bloque HTML con fondo gris, borde izquierdo gris, mostrando: origen -> destino, transporte, duracion, costo estimado.
- **Parametros:** `transfer_info` — dict con `from`, `to`, `transport`, `duration`, `cost_estimated`.

### 7.5. alert_banner.py

**Archivo:** `components/alert_banner.py` (78 lineas)
**Proposito:** Genera y renderiza alertas descartables del viaje activo.

#### `get_alerts(trip: dict) -> list`
- **Genera alertas basandose en:**
  1. Items pendientes de confirmacion → tipo `"warning"`
  2. Items sugeridos sin aceptar → tipo `"info"`
  3. Dias del viaje sin actividades planificadas → tipo `"info"`
- **Retorna:** Lista de dicts `{id, type, message, icon}`.

#### `render_alerts(alerts: list) -> None`
- **Renderiza:** Cada alerta con `st.warning()`, `st.error()` o `st.info()` segun el tipo. Boton "X" para descartar. Las alertas descartadas se guardan en `st.session_state.dismissed_alerts` (set). Al descartar, llama `st.rerun()`.

---

## 8. Paginas

### 8.1. Dashboard (`pages/1_Dashboard.py`)

**Archivo:** `pages/1_Dashboard.py` (122 lineas)
**Requerimientos:** REQ-UI-001 (Panel Overview), REQ-UI-010 (Clima y Alertas)

**Que muestra:**
- **Sin viaje activo:** Titulo, mensaje de bienvenida, botones "Ir a Mis Viajes" y "Abrir Chat".
- **Con viaje activo:**
  - Fila 1: 4 metricas — destino, dias restantes, presupuesto total estimado, items confirmados/total.
  - Fila 2: Progreso de planificacion (barra + porcentaje) y clima del destino (datos mock).
  - Fila 3: Alertas descartables (si hay).
  - Fila 4: Accesos rapidos a Chat, Cronograma, Itinerario, Presupuesto.
  - Banner superior si hay viajes completados sin feedback.

**Dependencias de session_state:** `trips`, `active_trip_id`
**Interacciones:** Navegacion a otras paginas via botones. Descarte de alertas.

### 8.2. Chat (`pages/2_Chat.py`)

**Archivo:** `pages/2_Chat.py` (146 lineas)
**Requerimientos:** REQ-UI-002 (Interfaz conversacional), REQ-UI-003 (Acciones sobre itinerario)

**Que muestra:**
- Indicador de modo: "Asistente IA (Gemini)" o "Asistente basico (sin LLM)".
- Nombre del viaje activo o "Sin viaje activo".
- Historial de mensajes renderizados segun tipo (text, card, confirmation).
- Campo de entrada `st.chat_input()`.

**Flujo de interaccion:**
1. Usuario escribe un mensaje.
2. El mensaje se agrega al historial del viaje.
3. Se llama `process_message()` con spinner "El asistente esta procesando...".
4. La respuesta se agrega al historial.
5. `st.rerun()` refresca la pagina.

**Confirmaciones:**
- Si `msg["processed"]` es `True`: muestra texto del resultado.
- Si `msg["processed"]` es `False`: renderiza botones Confirmar/Cancelar.
- Confirmar: ejecuta `apply_confirmed_action()` o `create_trip()`, marca como procesada, agrega mensaje de resultado.
- Cancelar: marca como procesada con "Cancelado por el usuario".

**Dependencias de session_state:** `trips`, `active_trip_id`, `chat_histories`

### 8.3. Cronograma (`pages/3_Cronograma.py`)

**Archivo:** `pages/3_Cronograma.py` (167 lineas)
**Requerimiento:** REQ-UI-004 (Cronograma / Calendario)

**Que muestra:**
- **Sin viaje activo:** Mensaje informativo + boton "Ir a Mis Viajes".
- **Sin items:** Advertencia + boton "Abrir Chat".
- **Con items:** Selector de vista (Semana, Dia, Mes) y calendario interactivo via `streamlit-calendar`.

**Vista principal (con streamlit-calendar):**
- Items convertidos a eventos de calendario con fecha real (start_date + day offset), color por tipo, y 50% de opacidad para items sugeridos.
- Click en evento muestra popover con nombre, ubicacion, costo y estado.
- El calendario se limita al rango de fechas del viaje.
- Opciones: slot 05:00-24:00, locale espanol, altura 600px.

**Vista fallback (sin streamlit-calendar):**
- Tabs por dia con items como bloques HTML con borde de color por tipo.

**Dependencias de session_state:** `trips`, `active_trip_id`

### 8.4. Itinerario (`pages/4_Itinerario.py`)

**Archivo:** `pages/4_Itinerario.py` (95 lineas)
**Requerimientos:** REQ-UI-005 (Itinerario detallado), REQ-UI-011 (Traslados)

**Que muestra:**
- **Sin viaje activo:** Mensaje + boton "Ir a Mis Viajes".
- **Sin items:** Advertencia + boton "Abrir Chat".
- **Con items:** Leyenda de estados, tabs por dia (con fecha), items expandibles con detalle completo, bloques de traslado entre items con ubicaciones diferentes.

**Interacciones del usuario:**
- Expandir/colapsar items para ver detalle.
- Aceptar sugerencia: cambia estado a "pendiente", recalcula presupuesto, persiste y refresca.
- Descartar sugerencia: elimina el item, recalcula presupuesto, persiste y refresca.

**Dependencias de session_state:** `trips`, `active_trip_id`

### 8.5. Presupuesto (`pages/5_Presupuesto.py`)

**Archivo:** `pages/5_Presupuesto.py` (129 lineas)
**Requerimiento:** REQ-UI-006 (Presupuesto)

**Que muestra:**
- **Sin viaje activo:** Mensaje + boton "Ir a Mis Viajes".
- **Sin costos:** Mensaje informativo.
- **Con costos:**
  - Fila 1: 3 metricas — presupuesto estimado total, gasto real (con delta), items contabilizados.
  - Fila 2: Grafico donut de distribucion + tabla de desglose por categoria con columnas Estimado/Real/Diferencia.
  - Fila 3: Barras comparativas estimado vs real (solo si hay costos reales).
  - Fila 4: Drill-down por categoria con expanders mostrando cada item, su costo estimado y real.

**Dependencias de session_state:** `trips`, `active_trip_id`

### 8.6. Perfil (`pages/6_Perfil.py`)

**Archivo:** `pages/6_Perfil.py` (104 lineas)
**Requerimiento:** REQ-UI-007 (Perfil y Preferencias)

**Que muestra:**
- Formulario con 5 tabs:
  1. **Alojamiento:** Multiselect (Hotel, Hostel, Apartamento, Resort, Camping, Casa rural) + textarea cadenas hoteleras.
  2. **Alimentacion:** Multiselect restricciones (Sin gluten, Vegetariano, Vegano, Sin lactosa, Kosher, Halal, Sin mariscos) + input alergias.
  3. **Estilo de viaje:** Multiselect (Aventura, Relax, Cultural, Gastronomico, Familiar, Romantico, Mochilero, Lujo).
  4. **Presupuesto:** Number input (USD, 0-10000, step 10).
  5. **Transporte:** Textarea aerolineas preferidas.
- Boton "Guardar preferencias" — valida presupuesto no negativo, guarda en JSON y actualiza session_state.

**Dependencias de session_state:** `user_profile`

### 8.7. Mis Viajes (`pages/7_Mis_Viajes.py`)

**Archivo:** `pages/7_Mis_Viajes.py` (223 lineas)
**Requerimientos:** REQ-UI-008 (Historial de viajes), REQ-UI-009 (Navegacion), REQ-UI-012 (Retroalimentacion)

**Que muestra:**
- Barra superior: filtro por estado (selectbox) + boton "Nuevo viaje".
- Formulario de nuevo viaje (condicional): nombre, destino, fecha inicio/fin, botones Crear/Cancelar.
- Lista de viajes filtrada y ordenada con tarjetas (`trip_card`).
- Confirmacion de eliminacion con botones "Si, eliminar" / "Cancelar".
- Para viajes completados sin feedback: seccion expandible de retroalimentacion.

**Retroalimentacion post-viaje:**
- Slider de valoracion general (1-5).
- Textarea de comentarios.
- Valoracion individual por item (hasta 10 items): slider rating + input nota.
- Botones "Enviar feedback" y "Omitir" (guarda feedback con `skipped: True`).

**Interacciones del usuario:**
- Ver viaje → establece como activo y navega al Dashboard.
- Eliminar viaje → confirmacion previa, solo viajes en planificacion.
- Crear viaje → formulario con validacion (nombre/destino obligatorios, end > start), crea viaje y redirige al Chat.

**Dependencias de session_state:** `trips`, `active_trip_id`, `chat_histories`, `_show_new_trip_form`, `_confirm_delete`

---

## 9. Sistema de Chat (Detalle)

### 9.1. Flujo Completo de un Mensaje

```
1. Usuario escribe mensaje en st.chat_input()
         │
2. Se agrega {role:"user", type:"text", content:msg} al historial
         │
3. Se llama process_message(msg, trip) en agent_service.py
         │
4. agent_service decide el flujo:
   ├── Es accion de crear viaje (sin trip, "viajar a X")? → Confirmacion mock
   ├── Es accion de agregar ("agregar", "anadir")? → Confirmacion mock
   ├── Es accion de eliminar ("eliminar", "quitar")? → Confirmacion mock
   ├── LLM disponible? → Delega a process_message_llm()
   │         │
   │         └── llm_agent_service.py → TripChatbot.chat()
   │                    │
   │                    └── Pipeline LangGraph (4 nodos)
   │                              │
   │                              └── Retorna {role, type:"text", content}
   └── Fallback mock → Pattern matching por keywords
         │
5. Respuesta se agrega al historial
         │
6. st.rerun() → La pagina se refresca y renderiza todos los mensajes
```

### 9.2. Modo LLM vs Modo Mock

| Aspecto | Modo LLM (Gemini) | Modo Mock (Pattern Matching) |
|---|---|---|
| **Activacion** | `GOOGLE_API_KEY` presente en `.env` y `TripChatbot` importable | Default sin API key o si falla importar |
| **Modelo** | gemini-2.5-flash (temperatura 0.7) | N/A |
| **Respuestas de texto** | Generadas por LLM con contexto de viaje, perfil y memorias | Hardcodeadas por keywords |
| **Tarjetas ricas** | No genera (el LLM solo produce texto) | Generadas por keywords (vuelo, hotel, actividad, comida) |
| **Confirmaciones** | Siempre via mock (add_item, remove_item, create_trip) | Siempre via mock |
| **Memoria** | ChromaDB vectorial + extraccion automatica de memorias | No hay memoria |
| **Persistencia de conversacion** | SQLite via LangGraph checkpointer | Solo session_state (se pierde al reiniciar) |

**Regla importante:** Las acciones que modifican el itinerario (agregar, eliminar, crear viaje) **siempre** pasan por el mock, incluso con LLM activo, porque requieren confirmaciones UI con botones.

### 9.3. Pipeline LangGraph (4 Nodos)

Definido en `services/llm_chatbot.py`, metodo `_create_app()` (lineas 68-166):

```
START → memory_retrieval → context_optimization → response_generation → memory_extraction → END
```

#### Nodo 1: `memory_retrieval` (linea 72)
- Busca el ultimo `HumanMessage` en el estado.
- Llama `memory_manager.search_vector_memory(last_user_message.content)`.
- Retorna `{"vector_memories": [lista de textos relevantes]}`.

#### Nodo 2: `context_optimization` (linea 86)
- Aplica `trim_messages(strategy="last", max_tokens=4000)` sobre los mensajes.
- Trunca el historial para que quepa en el contexto del modelo.
- Retorna `{"messages": trimmed_messages}`.

#### Nodo 3: `response_generation` (linea 91)
- Construye el contexto:
  - `memory_context` — memorias vectoriales formateadas como lista.
  - `trip_context` — datos del viaje activo (destino, fechas, stats de items).
  - `profile_context` — preferencias del usuario.
- Formatea el system prompt con los 3 contextos.
- Crea `ChatPromptTemplate` con system + `MessagesPlaceholder`.
- Invoca el chain `prompt | llm`.
- Retorna `{"messages": response}`.

#### Nodo 4: `memory_extraction` (linea 136)
- Busca el ultimo `HumanMessage`.
- Si es diferente al ultimo procesado (`last_memory_extraction`), extrae memorias.
- Llama `memory_manager.extract_and_store_memories(user_message)`.
- Retorna `{"last_memory_extraction": user_message}` para evitar reprocesar.

**Checkpointer:** SQLite en `data/llm_data/langgraph_memory.db`, con thread_id `"trip_chat_{chat_id}"`.

### 9.4. Sistema de Memorias Vectoriales (ChromaDB)

**Coleccion:** `"trip_planner_memories"` en `data/llm_data/chromadb/`
**Embeddings:** `GoogleGenerativeAIEmbeddings(model="models/embedding-001")`

**Flujo de extraccion de memorias:**
1. El nodo `memory_extraction` recibe el mensaje del usuario.
2. Si hay chain de extraccion LLM disponible:
   - El LLM analiza el mensaje con un prompt especializado.
   - Determina si contiene info relevante y su categoria (viaje, preferencias, personal, hechos_importantes).
   - Si `category != "none"` y `importance >= 2`, guarda la memoria.
3. Fallback manual (si el LLM no esta disponible):
   - Busca keywords en el mensaje: "prefiero", "alergia", "me llamo", "viaje a", "presupuesto".
   - Si matchea, guarda una memoria con la categoria correspondiente.

**Flujo de recuperacion:**
1. El nodo `memory_retrieval` recibe el ultimo mensaje del usuario.
2. Busca las 3 memorias mas similares semanticamente en ChromaDB.
3. Las pasa como contexto al nodo de generacion de respuesta.

### 9.5. Tipos de Respuesta

#### Texto (`type: "text"`)
Respuesta en markdown plano. Generada tanto por LLM como por mock.
```
Ejemplo: "El presupuesto estimado total de tu viaje a Tokio, Japon es de USD 2,095."
```

#### Tarjeta Rica (`type: "card"`)
Informacion estructurada de un servicio. Solo generada por el mock.
```
Ejemplo: {card_type: "flight", name: "Vuelo directo a Tokio", provider: "LATAM Airlines",
          price: 650.0, departure: "08:00", arrival: "14:30", duration: "6h 30m"}
```

#### Confirmacion (`type: "confirmation"`)
Accion pendiente que requiere aprobacion del usuario. Solo generada por el mock.
```
Ejemplo: {action: "add_item", summary: "Agregar actividad al itinerario",
          details: {name: "Nueva actividad", day: 1, cost_estimated: 25.0}}
```

### 9.6. Flujo de Confirmaciones

1. El mock genera un mensaje `type: "confirmation"` con el resumen de la accion.
2. `pages/2_Chat.py` renderiza los botones "Confirmar" / "Cancelar" via `render_confirmation()`.
3. Si el usuario confirma:
   - `apply_confirmed_action()` ejecuta la accion (agrega item, elimina item, crea viaje).
   - Se marca `msg["processed"] = True` y `msg["result"] = "texto resultado"`.
   - Se agrega un mensaje de texto con el resultado al historial.
   - `st.rerun()`.
4. Si el usuario cancela:
   - Se marca `msg["processed"] = True` y `msg["result"] = "Cancelado"`.
   - Se agrega mensaje "Entendido, he cancelado la accion".
   - `st.rerun()`.

### 9.7. Integracion con trip_service

Despues de cada accion confirmada (agregar/eliminar item), `apply_confirmed_action()` llama `sync_trip_changes(trips, trip)` que:
1. Recalcula `budget_total` del viaje (excluye sugeridos).
2. Actualiza el trip en la lista de viajes.
3. Persiste todo a `trips.json`.

---

## 10. Persistencia

### 10.1. Archivos JSON

#### `data/trips.json`
- **Contenido:** Lista de dicts con todos los viajes e items anidados.
- **Escritura:** `trip_service.save_trips()` — llamado por `sync_trip_changes()`, `create_trip()`, `delete_trip()`, y al inicializar.
- **Lectura:** `trip_service.load_trips()` — llamado una vez en `app.py` al inicializar `session_state`.
- **Patron:** Write-through. Cualquier mutacion persiste inmediatamente.

#### `data/profiles.json`
- **Contenido:** Dict unico con las preferencias del usuario.
- **Escritura:** `profile_service.save_profile()` — llamado al guardar preferencias desde la pagina de Perfil.
- **Lectura:** `profile_service.load_profile()` — llamado una vez en `app.py` al inicializar `session_state`.

#### `data/feedbacks.json`
- **Contenido:** Dict con clave = trip_id, valor = feedback dict.
- **Escritura:** `feedback_service.save_feedback()` — llamado desde la pagina Mis Viajes al enviar u omitir feedback.
- **Lectura:** `feedback_service.load_feedbacks()` — llamado por `has_feedback()`, `get_feedback()`, `has_pending_feedback()`, `get_trips_pending_feedback()`.
- **Nota:** Este archivo esta en `.gitignore`.

### 10.2. Bases de Datos

#### ChromaDB (`data/llm_data/chromadb/`)
- **Proposito:** Base de datos vectorial para memorias del chatbot.
- **Coleccion:** `"trip_planner_memories"`
- **Contenido:** Textos de memorias extraidas de las conversaciones con embeddings de Google (`models/embedding-001`).
- **Escritura:** `memory_manager.save_vector_memory()` — desde `extract_and_store_memories()`.
- **Lectura:** `memory_manager.search_vector_memory()` — en el nodo `memory_retrieval` del pipeline.
- **Nota:** Directorio completo en `.gitignore`.

#### SQLite (`data/llm_data/langgraph_memory.db`)
- **Proposito:** Checkpointer de LangGraph para persistir el estado del pipeline entre invocaciones.
- **Patron:** Cada conversacion tiene un thread_id `"trip_chat_{chat_id}"` que permite reanudar el historial de mensajes.
- **Nota:** Directorio completo en `.gitignore`.

### 10.3. Datos de Ejemplo

Definidos en `data/sample_data.py`. Se cargan automaticamente si los archivos JSON estan vacios:

- **3 viajes:** Tokio (7 dias, 15 items, en planificacion), Barcelona (5 dias, 10 items, confirmado), Lima (3 dias, 7 items, completado).
- **32 items totales** con variedad de tipos, estados y costos.
- **1 perfil de ejemplo** con preferencias de alojamiento, restricciones y estilos.
- **Historiales de chat** con mensajes de ejemplo para cada viaje.
- **Feedbacks:** Se retorna un dict vacio (el usuario debe probar la funcionalidad).

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

### 11.2. `.env`

```
GOOGLE_API_KEY=<clave de API de Google>
```

Esta variable habilita el modo LLM (Google Gemini). Si esta vacia o no existe, el sistema opera en modo mock.

### 11.3. `config/settings.py`

Contiene todos los enums, colores, iconos, labels y mapeos globales. Documentado en detalle en la seccion 5.

### 11.4. `config/llm_config.py`

Contiene la configuracion del modelo LLM, modelo de embeddings, directorio de datos y parametros de memoria. Documentado en la seccion 5.3.

### 11.5. CSS Global

Definido inline en `app.py` (lineas 22-61):
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

**Fuente:** REQ-UI-006 RN-002, implementada en `services/budget_service.py` (linea 27), `services/trip_service.py` (linea 195), `services/agent_service.py` (linea 251).

> Los items con `status = "sugerido"` **NO se contabilizan en el presupuesto**. Solo se suman los costos estimados de items `"pendiente"` y `"confirmado"`.

Esta regla se aplica consistentemente en:
- `recalculate_budget()` en trip_service.py
- `calculate_budget_summary()` en budget_service.py
- `_budget_response()` en agent_service.py (mock)
- `calculate_budget_from_items()` en models/budget.py

### 12.2. Transiciones de Estado de Viajes

**Fuente:** REQ-UI-008 RN-001/RN-004, implementada en `trip_service.update_trip_statuses()` (lineas 102-118).

```
en_planificacion ──(usuario confirma)──> confirmado
        │                                     │
        └──(hoy >= start_date)──> en_curso <──┘
                                     │
                                     └──(hoy > end_date)──> completado
```

**Reglas automaticas:**
- Si `hoy > end_date` y no esta completado → `completado`
- Si `start_date <= hoy <= end_date` y esta en `confirmado` o `en_planificacion` → `en_curso`
- Los viajes ya `completado` nunca se modifican automaticamente.

**Nota:** La transicion de `en_planificacion` a `confirmado` no esta implementada automaticamente; depende del estado de los items o de una futura accion del usuario.

### 12.3. Prioridad de Viaje Activo

**Fuente:** REQ-UI-001 RN-001, implementada en `trip_service.get_active_trip()` (lineas 46-69).

El viaje activo se selecciona con la siguiente prioridad:
1. El `active_trip_id` explicito (si existe y es valido).
2. El primer viaje en estado `"en_planificacion"`.
3. El proximo viaje confirmado (por fecha de inicio ascendente).
4. El primer viaje en curso.
5. `None` si no hay viajes.

### 12.4. Eliminacion de Viajes

**Fuente:** REQ-UI-008 CA-012, implementada en `trip_service.delete_trip()` (lineas 91-99).

Solo se pueden eliminar viajes en estado `"en_planificacion"`. Los viajes confirmados, en curso o completados no pueden eliminarse.

### 12.5. Ordenamiento de Viajes en Lista

**Fuente:** REQ-UI-008 RN-002, implementada en `trip_service.sort_trips()` (lineas 121-132).

Orden: en curso > en planificacion (fecha asc) > confirmado (fecha asc) > completado (fecha desc).

### 12.6. Traslados entre Items

**Fuente:** REQ-UI-011, implementada en `trip_service.get_transfer_info()` (lineas 211-225).

Se genera un bloque de traslado entre dos items consecutivos si:
- Ambos tienen ubicacion definida (no vacia).
- Las ubicaciones son diferentes.

En el MVP, los datos de traslado son mock fijos: "Metro / Taxi", 20 min, USD 5.

### 12.7. Acciones desde el Chat que Requieren Confirmacion

**Fuente:** REQ-UI-002 RN-004, REQ-UI-003 RN-001.

Todas las acciones que modifican el itinerario requieren confirmacion UI:
- Agregar item (`add_item`)
- Eliminar item (`remove_item`)
- Crear viaje (`create_trip`)

### 12.8. Historial de Chat por Viaje

**Fuente:** REQ-UI-002 RN-002.

Los historiales de chat se almacenan indexados por trip_id en `st.session_state.chat_histories`. Al cambiar de viaje activo, el chat muestra el historial correspondiente.

### 12.9. Feedback Post-Viaje

**Fuente:** REQ-UI-012.

- La retroalimentacion se habilita para viajes completados.
- Es opcional; el usuario puede omitirla (se guarda con `skipped: True`).
- Incluye valoracion general (1-5), comentarios, y valoracion individual por item (hasta 10 items).
- El banner de feedback pendiente aparece en el Dashboard.

---

## 13. Dependencias y Ejecucion

### 13.1. Instalacion

```bash
pip install -r requirements.txt
```

### 13.2. Ejecucion

```bash
python -m streamlit run app.py
```

El servidor se inicia en `http://localhost:8501` por defecto.

### 13.3. Variables de Entorno

| Variable | Requerida | Descripcion |
|---|---|---|
| `GOOGLE_API_KEY` | No | Clave de API de Google Generative AI. Si esta presente y es valida, habilita el modo LLM con Gemini. Si no existe, el sistema opera en modo mock. |

La variable se carga desde el archivo `.env` en la raiz del proyecto via `python-dotenv` (lineas 3-4 de `app.py`).

### 13.4. Modo con LLM vs sin LLM

| Funcionalidad | Con LLM | Sin LLM |
|---|---|---|
| Respuestas del chat | Generadas por Gemini 2.5 Flash con contexto de viaje, perfil y memorias | Hardcodeadas por pattern matching de keywords |
| Tarjetas ricas | No (LLM solo genera texto) | Si (vuelo, hotel, actividad, comida) |
| Confirmaciones | Si (agregar, eliminar, crear) | Si (agregar, eliminar, crear) |
| Memorias vectoriales | Si (ChromaDB + extraccion automatica) | No |
| Persistencia de conversacion LLM | Si (SQLite checkpointer) | No (solo session_state) |
| Indicador visual | "Asistente IA (Gemini)" | "Asistente basico (sin LLM)" |

### 13.5. Dependencias Opcionales

- **streamlit-calendar** — Requerida para la vista de calendario interactiva en la pagina Cronograma. Si no esta instalada, se muestra una vista alternativa basada en tabs.
- **chromadb, langchain-google-genai, langgraph** — Requeridas solo para el modo LLM. Si no estan disponibles, el sistema opera en modo mock sin errores.

### 13.6. Inicializacion del Session State

Al ejecutar `app.py`, se inicializan las siguientes claves en `st.session_state`:

| Clave | Valor Inicial | Descripcion |
|---|---|---|
| `trips` | `load_trips()` | Lista de viajes (desde JSON o datos de ejemplo) |
| `active_trip_id` | `None` | ID del viaje activo seleccionado |
| `chat_histories` | `get_sample_chat_histories()` | Dict de historiales de chat por trip_id |
| `dismissed_alerts` | `set()` | IDs de alertas descartadas |
| `user_profile` | `load_profile()` | Dict con preferencias del usuario |

Despues de la inicializacion, se ejecuta `update_trip_statuses()` para actualizar estados por fecha, y `save_trips()` para persistir los cambios.
