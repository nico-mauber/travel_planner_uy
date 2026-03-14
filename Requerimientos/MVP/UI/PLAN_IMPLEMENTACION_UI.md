# Plan de Implementacion — Trip Planner MVP (Interfaz Streamlit)

## 1. Contexto

Este documento describe el plan de implementacion completo del frontend MVP del **Trip Planner**, un agente de planificacion de viajes con interfaz construida en Streamlit. La aplicacion cubre 12 requerimientos funcionales (REQ-UI-001 a REQ-UI-012) organizados en secciones de Dashboard, Chat, Cronograma, Itinerario, Presupuesto, Perfil y Mis Viajes.

El agente opera como un mock basado en pattern matching, sin LLM real, orientado a validar la experiencia de usuario antes de integrar un modelo de lenguaje en produccion.

---

## 2. Concesiones del MVP

| # | Concesion | Justificacion |
|---|-----------|---------------|
| 1 | Chat como pagina dedicada, no panel lateral persistente | Streamlit no soporta paneles laterales personalizados con chat embebido. Se mitiga con boton "Abrir Chat" siempre visible en el sidebar. |
| 2 | Drag & drop limitado en el calendario | `streamlit-calendar` soporta click en eventos pero el drag & drop nativo es limitado. Se incluye fallback por tabs si el componente no esta instalado. |
| 3 | Sin autenticacion — usuario unico | El MVP no implementa login/registro. Se asume un unico usuario por instancia. |
| 4 | Agente mock — pattern matching basico | Las respuestas del agente se generan por coincidencia de palabras clave (vuelo, hotel, actividad, etc.), sin modelo de lenguaje. |
| 5 | Persistencia en JSON | Los datos se almacenan en archivos JSON locales (`data/trips.json`, `data/profiles.json`, `data/feedbacks.json`) en lugar de una base de datos. |
| 6 | Responsive limitado | Streamlit ofrece layout responsive basico pero no permite control CSS granular. La app funciona en desktop; en movil la experiencia es aceptable pero no optimizada. |

---

## 3. Stack Tecnico

| Componente | Version | Proposito |
|------------|---------|-----------|
| Python | 3.10+ | Lenguaje base |
| Streamlit | >= 1.40.0 | Framework de interfaz web |
| Plotly | >= 5.18.0 | Graficos de presupuesto (donut, barras agrupadas) |
| streamlit-calendar | >= 1.2.0 | Componente de calendario interactivo (FullCalendar) |

Archivo de dependencias: `requirements.txt`

```
streamlit>=1.40.0
plotly>=5.18.0
streamlit-calendar>=1.2.0
```

---

## 4. Estructura de Archivos

```
Trip_Planner/
|
|-- app.py                          # Punto de entrada, configuracion global, navegacion
|-- requirements.txt                # Dependencias del proyecto
|
|-- .streamlit/
|   |-- config.toml                 # Tema visual y configuracion del servidor
|
|-- config/
|   |-- __init__.py
|   |-- settings.py                 # Enums, constantes, colores, iconos, labels
|
|-- models/
|   |-- __init__.py
|   |-- trip.py                     # Dataclass Trip (viaje)
|   |-- itinerary_item.py          # Dataclass ItineraryItem (item del itinerario)
|   |-- user_profile.py            # Dataclass UserProfile (perfil de usuario)
|   |-- budget.py                  # Dataclass BudgetSummary + calculo desde items
|   |-- feedback.py                # Dataclasses ItemFeedback y TripFeedback
|
|-- pages/
|   |-- 1_Dashboard.py             # Panel Overview del viaje activo
|   |-- 2_Chat.py                  # Chat con el agente (interfaz conversacional)
|   |-- 3_Cronograma.py            # Calendario interactivo con items
|   |-- 4_Itinerario.py            # Vista dia por dia detallada
|   |-- 5_Presupuesto.py           # Desglose presupuestario con graficos
|   |-- 6_Perfil.py                # Formulario de preferencias del viajero
|   |-- 7_Mis_Viajes.py            # Listado, creacion, eliminacion y feedback
|
|-- components/
|   |-- __init__.py
|   |-- chat_widget.py             # Tarjetas ricas y confirmaciones del chat
|   |-- budget_charts.py           # Graficos Plotly (donut y barras comparativas)
|   |-- trip_card.py               # Tarjeta de viaje para la lista
|   |-- itinerary_item.py          # Item expandible del itinerario + traslados
|   |-- alert_banner.py            # Sistema de alertas descartables
|
|-- services/
|   |-- __init__.py
|   |-- agent_service.py           # Agente mock (pattern matching + acciones)
|   |-- trip_service.py            # CRUD de viajes, sincronizacion, persistencia JSON
|   |-- budget_service.py          # Calculos de presupuesto por categoria
|   |-- profile_service.py         # Carga y guardado del perfil de usuario
|   |-- weather_service.py         # Datos climaticos mock por destino
|   |-- feedback_service.py        # CRUD de retroalimentacion post-viaje
|
|-- data/
|   |-- __init__.py
|   |-- sample_data.py             # Datos de ejemplo: 3 viajes, ~30 items, perfil, chats
|   |-- trips.json                 # Persistencia de viajes (generado en runtime)
|   |-- profiles.json              # Persistencia del perfil (generado en runtime)
```

---

## 5. Fases de Implementacion

### Fase 0 (F0) — Estructura Base y Configuracion

**Archivos creados:**
- `app.py`
- `requirements.txt`
- `.streamlit/config.toml`
- `config/__init__.py`
- `config/settings.py`

**Funcionalidades clave:**
- Configuracion de `st.set_page_config()` con layout `wide` y sidebar expandido.
- Tema visual personalizado en `config.toml`: color primario azul (#1E88E5), fondo blanco, fuente sans-serif.
- Definicion de enums centrales: `TripStatus`, `ItemStatus`, `ItemType`, `BudgetCategory`.
- Paleta de colores por tipo de item y por categoria de presupuesto.
- Iconos y labels en espanol para todos los enums.
- Mapeo `ITEM_TYPE_TO_BUDGET` para vincular tipos de item a categorias presupuestarias.
- CSS global inyectado en `app.py`: badges de estado, items sugeridos (borde punteado), caja de viaje activo en sidebar, bloques de traslado.

---

### Fase 1 (F1) — Modelos de Datos

**Archivos creados:**
- `models/__init__.py`
- `models/trip.py`
- `models/itinerary_item.py`
- `models/user_profile.py`
- `models/budget.py`
- `models/feedback.py`

**Funcionalidades clave:**
- **Trip**: dataclass con id, nombre, destino, fechas ISO, estado, presupuesto total, items (lista de dicts) y notas. Properties para calcular duracion, dias restantes y conversion a/desde dict.
- **ItineraryItem**: dataclass con 15 campos incluyendo dia del viaje (1-based), horarios start/end, estado (confirmado/pendiente/sugerido), ubicacion, costos estimado y real, URL de reserva y proveedor.
- **UserProfile**: dataclass con preferencias de alojamiento, restricciones alimentarias, alergias, estilos de viaje, presupuesto diario, aerolineas y cadenas hoteleras preferidas.
- **BudgetSummary**: dataclass con totales estimado/real y desglose por categoria. Incluye funcion `calculate_budget_from_items()` que excluye items sugeridos del calculo (regla de negocio RN-002).
- **TripFeedback / ItemFeedback**: dataclasses para retroalimentacion post-viaje con valoracion general (1-5), comentario, y valoraciones individuales por item.

---

### Fase 2 (F2) — Servicios de Persistencia y Datos de Ejemplo

**Archivos creados:**
- `services/__init__.py`
- `services/trip_service.py`
- `services/profile_service.py`
- `data/__init__.py`
- `data/sample_data.py`

**Funcionalidades clave:**
- **trip_service**: carga de viajes desde JSON con fallback a datos de ejemplo, guardado automatico, obtencion de viaje por ID, deteccion de viaje activo (prioridad: seleccion manual > en planificacion > proximo confirmado > en curso).
- **profile_service**: carga y guardado de perfil en `profiles.json` con fallback a perfil de ejemplo.
- **sample_data**: 3 viajes de ejemplo con ~30 items totales:
  - "Aventura en Tokio" (7 dias, en planificacion, 15 items incluyendo sugeridos).
  - "Barcelona Cultural" (5 dias, confirmado, 10 items).
  - "Escapada a Lima" (3 dias, completado, 7 items con costos reales).
- Historiales de chat pre-cargados para cada viaje de ejemplo.
- Perfil de usuario de ejemplo con preferencias configuradas.

---

### Fase 3 (F3) — Navegacion y Sidebar Global

**Archivos modificados:**
- `app.py`

**Funcionalidades clave:**
- Navegacion multi-pagina con `st.navigation()` y 7 paginas (Dashboard, Chat, Cronograma, Itinerario, Presupuesto, Perfil, Mis Viajes).
- Sidebar persistente con:
  - Logo y titulo "Trip Planner".
  - Caja visual del viaje activo mostrando nombre, destino, fechas y badge de estado con color semantico.
  - Boton "Abrir Chat" siempre visible para compensar la concesion de chat como pagina dedicada.
- Inicializacion de `session_state`: viajes, viaje activo, historiales de chat, alertas descartadas, perfil de usuario.
- Actualizacion automatica de estados de viaje por fecha (completado si fecha fin < hoy, en curso si entre fechas).

---

### Fase 4 (F4) — Dashboard (Panel Overview)

**Archivos creados:**
- `pages/1_Dashboard.py`
- `components/alert_banner.py`

**Archivos utilizados:**
- `services/weather_service.py`
- `services/budget_service.py`
- `services/feedback_service.py`

**Funcionalidades clave:**
- Estado vacio con bienvenida y accesos directos a "Mis Viajes" y "Chat" cuando no hay viaje activo.
- Fila de metricas: destino, dias restantes (con variantes "Hoy empieza" y "En curso"), presupuesto total, items confirmados vs. total.
- Barra de progreso de planificacion (% de items confirmados sobre no-sugeridos).
- Bloque de clima en destino con icono, rango de temperatura y descripcion.
- Sistema de alertas inteligentes:
  - Items pendientes de confirmacion.
  - Sugerencias del agente sin revisar.
  - Dias sin actividades planificadas.
- Alertas descartables con boton de cierre y persistencia en session_state.
- Banner de feedback pendiente para viajes completados.
- Botones de acceso rapido a Chat, Cronograma, Itinerario y Presupuesto.

---

### Fase 5 (F5) — Servicio de Clima Mock

**Archivos creados:**
- `services/weather_service.py`

**Funcionalidades clave:**
- Datos climaticos mock predefinidos para los 3 destinos de ejemplo (Tokio, Barcelona, Lima).
- Datos por defecto ("Variable") para destinos no reconocidos.
- Cada entrada incluye: temperatura minima/maxima, condicion, icono, descripcion contextual.

---

### Fase 6 (F6) — Chat con el Agente

**Archivos creados:**
- `pages/2_Chat.py`
- `services/agent_service.py`
- `components/chat_widget.py`

**Funcionalidades clave:**
- Interfaz conversacional con `st.chat_message()` y `st.chat_input()`.
- Historial de chat por viaje almacenado en session_state.
- Mensaje de bienvenida contextual (con o sin viaje activo).
- **Agente mock** con pattern matching para 9 categorias de mensajes:
  - Creacion de viaje ("viajar a X").
  - Busqueda de vuelos, hoteles, actividades, restaurantes.
  - Agregar / eliminar items del itinerario.
  - Consulta de presupuesto y clima.
  - Saludo y respuesta generica con menu de opciones.
- **Tres tipos de respuesta**:
  - `text`: mensaje de texto simple renderizado con markdown.
  - `card`: tarjeta rica con datos del item (vuelo, hotel, actividad, comida) mostrando proveedor, precio, ubicacion, duracion, rating.
  - `confirmation`: solicitud de confirmacion con botones "Confirmar" / "Cancelar" para acciones que modifican el itinerario.
- Flujo de confirmacion: el agente propone, el usuario confirma, se aplica la accion via `apply_confirmed_action()`, se sincroniza con la lista de viajes y se persiste en JSON.
- Creacion de viaje desde el chat: detecta destino, solicita confirmacion, crea el viaje, redirige el historial de chat.

---

### Fase 7 (F7) — Cronograma / Calendario

**Archivos creados:**
- `pages/3_Cronograma.py`

**Funcionalidades clave:**
- Selector de vista: Dia, Semana, Mes (radio buttons horizontales).
- **Vista principal** con `streamlit-calendar` (FullCalendar):
  - Items convertidos a eventos con fecha calculada a partir del dia del viaje + fecha de inicio.
  - Color por tipo de item (actividad verde, vuelo rosa, alojamiento azul, comida naranja, traslado gris, extra morado).
  - Opacidad reducida (50%) para items sugeridos.
  - Rango valido limitado a las fechas del viaje.
  - Franja horaria de 05:00 a 24:00, locale en espanol.
  - Click en evento muestra popover con detalle (nombre, ubicacion, costo, estado).
- **Vista fallback** cuando `streamlit-calendar` no esta instalado:
  - Tabs por dia con items renderizados como bloques con borde de color por tipo.
  - Icono de tipo, icono de estado, nombre, horario y ubicacion.

---

### Fase 8 (F8) — Itinerario Detallado

**Archivos creados:**
- `pages/4_Itinerario.py`
- `components/itinerary_item.py`

**Funcionalidades clave:**
- Tabs por dia con label "Dia N — Lun 10 Abr".
- Leyenda de estados: confirmado, pendiente, sugerido.
- Items renderizados como expanders con informacion completa:
  - Tipo, ubicacion, direccion, costo estimado, costo real, proveedor, notas.
  - Enlace de reserva (si existe) con `st.link_button()`.
- Diferenciacion visual para items sugeridos: caption indicando que no son parte del plan + botones de accion.
- **Aceptar / Descartar sugerencias**: cambia estado de "sugerido" a "pendiente" o elimina el item, sincroniza y persiste.
- **Traslados entre items** (REQ-UI-011): cuando dos items consecutivos tienen ubicaciones diferentes, se muestra un bloque visual de traslado con: origen, destino, medio de transporte (Metro / Taxi), duracion estimada (20 min) y costo aproximado (USD 5).
- Agrupacion y ordenamiento cronologico de items dentro de cada dia.

---

### Fase 9 (F9) — Presupuesto

**Archivos creados:**
- `pages/5_Presupuesto.py`
- `services/budget_service.py`
- `components/budget_charts.py`

**Funcionalidades clave:**
- Metricas principales: presupuesto estimado total, gasto real (con delta), items contabilizados.
- **Grafico donut** (Plotly) con distribucion por categoria de presupuesto.
- **Tabla de desglose** por categoria: estimado, real, diferencia.
- **Grafico de barras agrupadas** (Plotly) comparando estimado vs. real por categoria — solo se muestra si hay costos reales registrados.
- **Drill-down por categoria**: expanders con detalle de cada item (nombre, costo estimado, costo real).
- Regla de negocio: items con estado "sugerido" se excluyen de todos los calculos presupuestarios.

---

### Fase 10 (F10) — Perfil y Preferencias

**Archivos creados:**
- `pages/6_Perfil.py`

**Funcionalidades clave:**
- Formulario completo con 5 tabs tematicas:
  - **Alojamiento**: multiselect de tipos (Hotel, Hostel, Apartamento, Resort, Camping, Casa rural) + cadenas hoteleras preferidas.
  - **Alimentacion**: multiselect de restricciones (Sin gluten, Vegetariano, Vegano, Sin lactosa, Kosher, Halal, Sin mariscos) + alergias en texto libre.
  - **Estilo de viaje**: multiselect (Aventura, Relax, Cultural, Gastronomico, Familiar, Romantico, Mochilero, Lujo).
  - **Presupuesto**: presupuesto diario habitual en USD (number_input, 0-10000, step 10).
  - **Transporte**: aerolineas preferidas en texto libre.
- Validacion: presupuesto diario no puede ser negativo.
- Guardado en JSON con feedback visual de exito o error.
- Carga automatica de datos existentes en los campos del formulario.

---

### Fase 11 (F11) — Mis Viajes + Retroalimentacion Post-Viaje

**Archivos creados:**
- `pages/7_Mis_Viajes.py`
- `services/feedback_service.py`
- `components/trip_card.py`

**Funcionalidades clave:**
- **Listado de viajes** con tarjetas que muestran: nombre, destino, badge de estado con color semantico, fechas, presupuesto.
- **Filtrado por estado** via selectbox: Todos, En planificacion, Confirmado, En curso, Completado.
- **Ordenamiento automatico**: en curso primero, luego proximos (ascendente por fecha), luego completados (descendente).
- **Creacion de nuevo viaje**: formulario con nombre, destino, fecha inicio, fecha fin. Validacion de campos obligatorios y coherencia de fechas. Redireccion automatica al Chat tras crear.
- **Acceso rapido**: boton "Ver viaje" que establece el viaje como activo y navega al Dashboard.
- **Eliminacion**: solo para viajes en planificacion, con dialogo de confirmacion.
- **Retroalimentacion post-viaje** (REQ-UI-012):
  - Deteccion automatica de viajes completados sin feedback.
  - Seccion expandible con formulario de valoracion general (slider 1-5), comentario, y valoracion individual por item (hasta 10 items).
  - Opcion de omitir feedback.
  - Persistencia en `data/feedbacks.json`.

---

## 6. Cobertura de Requerimientos

| Requerimiento | Titulo | Archivos Principales | Cobertura |
|---------------|--------|---------------------|-----------|
| **REQ-UI-001** | Panel Overview — Vista general del viaje activo | `pages/1_Dashboard.py`, `components/alert_banner.py` | Metricas del viaje, progreso de planificacion, accesos rapidos. |
| **REQ-UI-002** | Chat — Interfaz conversacional | `pages/2_Chat.py`, `components/chat_widget.py`, `services/agent_service.py` | Historial por viaje, mensajes de texto, tarjetas ricas (vuelos, hoteles, actividades, comida), spinner de "pensando". |
| **REQ-UI-003** | Chat — Solicitud de cambios al itinerario | `pages/2_Chat.py`, `services/agent_service.py` | Agregar/eliminar items via confirmacion, creacion de viaje desde chat, sincronizacion con todas las secciones. |
| **REQ-UI-004** | Cronograma / Calendario | `pages/3_Cronograma.py` | Vistas dia/semana/mes, bloques coloreados por tipo, opacidad para sugeridos, click en evento, fallback sin libreria. |
| **REQ-UI-005** | Itinerario Detallado | `pages/4_Itinerario.py`, `components/itinerary_item.py` | Vista dia por dia con tabs, informacion completa de cada item, aceptar/descartar sugerencias. |
| **REQ-UI-006** | Presupuesto | `pages/5_Presupuesto.py`, `services/budget_service.py`, `components/budget_charts.py`, `models/budget.py` | Donut por categoria, barras estimado vs. real, tabla de desglose, drill-down, exclusion de sugeridos. |
| **REQ-UI-007** | Perfil y Preferencias del Viajero | `pages/6_Perfil.py`, `services/profile_service.py`, `models/user_profile.py` | Formulario con 5 tabs tematicas, persistencia en JSON, carga de datos existentes. |
| **REQ-UI-008** | Mis Viajes — Historial y gestion | `pages/7_Mis_Viajes.py`, `components/trip_card.py`, `services/trip_service.py` | Listado con tarjetas, filtrado por estado, ordenamiento, creacion, eliminacion con confirmacion. |
| **REQ-UI-009** | Navegacion General | `app.py`, `config/settings.py`, `.streamlit/config.toml` | Menu lateral con st.navigation(), sidebar con viaje activo, boton de chat global, tema visual, CSS global. |
| **REQ-UI-010** | Dashboard — Clima y alertas | `pages/1_Dashboard.py`, `services/weather_service.py`, `components/alert_banner.py` | Bloque de clima mock, alertas por items pendientes/sugeridos/dias vacios, alertas descartables. |
| **REQ-UI-011** | Itinerario — Traslados y logistica | `pages/4_Itinerario.py`, `components/itinerary_item.py`, `services/trip_service.py` | Bloque visual de traslado entre items con ubicaciones diferentes, medio de transporte, duracion y costo. |
| **REQ-UI-012** | Perfil — Retroalimentacion post-viaje | `pages/7_Mis_Viajes.py`, `services/feedback_service.py`, `models/feedback.py` | Valoracion general y por item, opcion de omitir, deteccion de feedback pendiente, banner en Dashboard. |

---

## 7. Patrones y Decisiones de Arquitectura

### 7.1 Estado global via `st.session_state`
Toda la informacion compartida entre paginas se gestiona a traves de `st.session_state`:
- `trips`: lista de viajes (fuente de verdad en memoria).
- `active_trip_id`: ID del viaje activo seleccionado.
- `chat_histories`: diccionario de historiales de chat indexado por trip_id.
- `dismissed_alerts`: conjunto de IDs de alertas descartadas.
- `user_profile`: diccionario con las preferencias del usuario.

### 7.2 Persistencia JSON transparente
Los servicios (`trip_service`, `profile_service`, `feedback_service`) encapsulan la lectura y escritura de archivos JSON. Al iniciar, si el archivo no existe o esta vacio, se cargan datos de ejemplo automaticamente.

### 7.3 Sincronizacion tras cambios
La funcion `sync_trip_changes()` se invoca despues de cualquier modificacion al itinerario (agregar, eliminar, aceptar sugerencia). Recalcula el presupuesto total y persiste en JSON.

### 7.4 Separacion componentes / servicios / paginas
- **Paginas** (`pages/`): logica de presentacion y flujo de usuario.
- **Componentes** (`components/`): widgets reutilizables con interfaz clara (reciben datos, retornan acciones).
- **Servicios** (`services/`): logica de negocio, calculos y persistencia, sin dependencia de Streamlit.
- **Modelos** (`models/`): dataclasses para tipar los datos (referencia, no se usan como unica forma de transporte — los datos fluyen como dicts para compatibilidad con JSON y session_state).

### 7.5 Manejo de errores
Todas las paginas envuelven su logica en bloques `try/except` con `st.error()` y un boton "Reintentar" que ejecuta `st.rerun()`.

---

## 8. Como Ejecutar

### Requisitos previos
- Python 3.10 o superior instalado.
- pip disponible en el PATH.

### Instalacion y ejecucion

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar la aplicacion
streamlit run app.py
```

La aplicacion se abrira en el navegador en `http://localhost:8501`.

### Datos de ejemplo
Al ejecutar por primera vez, la aplicacion carga automaticamente 3 viajes de ejemplo con items, un perfil de usuario pre-configurado e historiales de chat. Los datos se persisten en la carpeta `data/` como archivos JSON que se pueden editar manualmente si es necesario.

---

## 9. Proximos Pasos (Post-MVP)

1. **Integracion con LLM real** para reemplazar el agente mock (OpenAI, Anthropic, etc.).
2. **Autenticacion** con soporte multi-usuario.
3. **Base de datos** (SQLite o PostgreSQL) en lugar de JSON.
4. **API de clima real** (OpenWeatherMap, WeatherAPI).
5. **Integraciones de reservas** (Booking, Skyscanner, GetYourGuide).
6. **Notificaciones push** para alertas criticas.
7. **Modo oscuro** y soporte de internacionalizacion.
8. **Tests automatizados** (unitarios + integracion).
