# Trip Planner

MVP de un agente de planificacion de viajes con interfaz Streamlit.

## Caracteristicas

- **Chat conversacional** con agente dual: LLM (OpenAI gpt-4.1-nano via LangGraph) o fallback basico por pattern matching
- **Multi-usuario** con Google OAuth (fallback a modo demo sin auth)
- **Persistencia** en Supabase (PostgreSQL)
- **Busqueda de hoteles** via Booking.com (RapidAPI) — opcional
- **Servidor MCP** standalone para exponer herramientas de busqueda de hoteles
- **Selector de viaje por pagina** — Dashboard, Itinerario y Presupuesto permiten elegir viaje. Cronograma muestra todos los viajes

## Setup

```bash
# Crear entorno virtual (solo la primera vez)
python -m venv venv

# Activar
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
.\venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## Configuracion

Crear archivo `.env` en la raiz del proyecto:

```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_KEY=tu-service-role-key
OPENAI_API_KEY=sk-...            # Opcional: habilita LLM
OPENAI_PROJECT=proj_...          # Opcional: project ID de OpenAI
RAPIDAPI_KEY=tu-rapidapi-key     # Opcional: habilita Booking.com
RAPIDAPI_BOOKING_HOST=booking-com15.p.rapidapi.com
```

Para Google OAuth, crear `.streamlit/secrets.toml` (ver `secrets.toml.example`).

### Base de datos

Ejecutar `scripts/schema.sql` en el Supabase SQL Editor para crear las tablas.

## Ejecutar

```bash
python -m streamlit run app.py         # App principal (localhost:8501)
.\run.bat                              # Windows: lanza con el venv explicitamente
python mcp_servers/booking_server.py   # Servidor MCP standalone (stdio)
```

Usar siempre `python -m streamlit run app.py` (no `streamlit run app.py`) para asegurar que se use el Python del venv.

## Estructura del proyecto

```
Trip_Planner/
  app.py                    # Punto de entrada Streamlit
  run.bat                   # Launcher Windows
  requirements.txt          # Dependencias Python
  .env                      # Variables de entorno (no versionado)
  pages/
    1_Dashboard.py           # Metricas del viaje (con selector)
    2_Chat.py                # Chat con agente (selector obligatorio)
    3_Cronograma.py          # Calendario global — todos los viajes
    4_Itinerario.py          # Itinerario por viaje (con selector)
    5_Presupuesto.py         # Presupuesto por viaje (con selector)
    6_Perfil.py              # Preferencias del usuario
    7_Mis_Viajes.py          # Gestion de viajes (CRUD)
  services/
    agent_service.py         # Dispatcher del chat (ruteo, LLM, acciones)
    item_extraction.py       # Extraccion inteligente de items (regex)
    trip_creation_flow.py    # Flujo multi-turn de creacion de viajes
    trip_service.py          # CRUD viajes + sync Supabase
    chat_service.py          # Multi-conversacion + persistencia
    llm_agent_service.py     # Wrapper sobre TripChatbot
    llm_chatbot.py           # Pipeline LangGraph (4 nodos)
    memory_manager.py        # ChromaDB + checkpoints LangGraph
    booking_service.py       # Cliente Booking.com (RapidAPI)
    budget_service.py        # Calculo de presupuesto por categoria
    auth_service.py          # OAuth Google (condicional)
    profile_service.py       # Preferencias de usuario
    feedback_service.py      # Feedback post-viaje
    supabase_client.py       # Cliente Supabase singleton
    weather_service.py       # Clima mock
  components/
    chat_widget.py           # Cards, confirmaciones, hotel results
    itinerary_item.py        # Item expandible + traslados
    budget_charts.py         # Donut chart + barras (Plotly)
    trip_card.py             # Card de viaje (Ver/Eliminar)
    alert_banner.py          # Alertas descartables
  config/
    settings.py              # Enums, colores, iconos, labels
    llm_config.py            # Config OpenAI (modelo, temperatura)
  models/                    # Dataclasses de referencia (no usadas en runtime)
  data/                      # sample_data.py + llm_data/ (ChromaDB local)
  mcp_servers/
    booking_server.py        # Servidor MCP (FastMCP, stdio)
  scripts/
    schema.sql               # Schema Supabase (tablas + triggers + RLS)
    migration_cf002_end_day.sql  # Migracion: campo end_day en items
  Requerimientos/            # Especificaciones funcionales
```

## Dependencias principales

| Paquete | Uso |
|---|---|
| `streamlit>=1.42.0` | Framework UI |
| `supabase>=2.0.0` | Persistencia PostgreSQL |
| `python-dotenv>=1.0.0` | Carga de `.env` |
| `plotly>=5.18.0` | Charts de presupuesto |
| `streamlit-calendar>=1.2.0` | Vista calendario FullCalendar.js |
| `langchain-openai`, `langgraph` | Pipeline LLM (opcional) |
| `langchain-chroma`, `chromadb` | Memoria vectorial (opcional) |
| `httpx>=0.25.0` | Cliente HTTP para Booking.com (opcional) |
| `mcp[cli]>=1.2.0` | Servidor MCP (opcional) |
| `Authlib>=1.3.2` | Google OAuth (opcional) |
| `pydantic>=2.0.0` | Modelos estructurados (memoria LLM) |
