# ROADMAP: De MVP a Agente de Viajes Completo

> Documento generado el 2026-03-26 mediante análisis exhaustivo del sistema actual,
> investigación de mercado (30+ fuentes), comparación con plataformas líderes
> (Kayak, Expedia, Google Travel, Booking.com, Skyscanner, Rome2Rio),
> y relevamiento de APIs disponibles.

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Lo que hace un agente de viajes real](#2-lo-que-hace-un-agente-de-viajes-real)
3. [Estado actual del sistema](#3-estado-actual-del-sistema)
4. [Gap Analysis completo](#4-gap-analysis-completo)
5. [PRIORIDAD 1 — Funcionalidades Críticas](#5-prioridad-1--funcionalidades-críticas)
6. [PRIORIDAD 2 — Funcionalidades Importantes](#6-prioridad-2--funcionalidades-importantes)
7. [PRIORIDAD 3 — Funcionalidades de Valor Agregado](#7-prioridad-3--funcionalidades-de-valor-agregado)
8. [PRIORIDAD 4 — Funcionalidades Avanzadas](#8-prioridad-4--funcionalidades-avanzadas)
9. [APIs recomendadas por funcionalidad](#9-apis-recomendadas-por-funcionalidad)
10. [Impacto arquitectónico](#10-impacto-arquitectónico)
11. [Matriz de dependencias](#11-matriz-de-dependencias)

---

## 1. Resumen Ejecutivo

El sistema Trip Planner actual es un **MVP funcional de planificación de viajes** con chat inteligente (LLM), gestión de itinerarios, presupuesto y búsqueda de hoteles. Sin embargo, comparado con lo que hace un agente de viajes profesional real, **le falta aproximadamente el 60% de las funcionalidades esperadas**.

### Lo que el sistema PUEDE hacer hoy (40%)

- Crear y gestionar viajes (CRUD completo con estados automáticos)
- Chat inteligente dual (LLM con OpenAI gpt-4.1-nano / fallback keywords)
- Agregar/eliminar items al itinerario via chat (extracción estructurada)
- Buscar hoteles en Booking.com (via RapidAPI)
- Gestión de gastos directos (CRUD por categoría)
- Presupuesto con gráficos (donut + barras comparativas estimado vs real)
- Calendario visual (FullCalendar.js con vistas día/semana/mes)
- Memoria vectorial del usuario (ChromaDB)
- Multi-usuario con OAuth Google + RLS en Supabase
- Multi-conversación con historial persistente

### Lo que FALTA para ser un agente de viajes completo (60%)

- Búsqueda y comparación de vuelos
- Búsqueda de actividades, tours y experiencias
- Transporte entre puntos (rutas, tiempos, opciones)
- Clima real por destino y fecha
- Requisitos de viaje (visas, vacunas, documentos)
- Cambio de moneda y presupuesto multi-divisa
- Mapas interactivos con ubicaciones del itinerario
- Checklist de viaje (equipaje, documentos, preparativos)
- Compartir itinerario con compañeros de viaje
- Recomendaciones personalizadas basadas en historial
- Información de emergencia local (embajadas, hospitales)
- Seguros de viaje
- Exportación del itinerario (PDF, calendario, email)
- Notificaciones y alertas inteligentes
- Reservas reales (no solo búsqueda)

---

## 2. Lo que hace un agente de viajes real

Un agente de viajes profesional cubre **3 fases** del ciclo de viaje. Cada sub-punto es algo que un viajero espera de su agente:

### FASE PRE-VIAJE (Planificación)

| # | Servicio | Descripción |
|---|----------|-------------|
| 1 | **Consultoría personalizada** | Entender preferencias, estilo de viaje, presupuesto, restricciones médicas/alimentarias, composición del grupo |
| 2 | **Búsqueda de vuelos** | Comparar precios entre aerolíneas, escalas, horarios, clases, equipaje incluido. Alertas de baja de precio |
| 3 | **Búsqueda de alojamiento** | Hoteles, hostels, apartamentos, resorts. Filtros por precio, ubicación, amenities, rating |
| 4 | **Búsqueda de actividades** | Tours guiados, excursiones, entradas a museos/atracciones, experiencias gastronómicas, aventura |
| 5 | **Transporte terrestre** | Transfers aeropuerto, alquiler de autos, trenes, buses, ferries. Rutas y tiempos |
| 6 | **Armado de itinerario** | Itinerario día a día con tiempos, traslados, reservas. Optimización de rutas y horarios |
| 7 | **Presupuesto detallado** | Desglose por categoría, multi-moneda, comparación de opciones, alertas de sobrecosto |
| 8 | **Documentación** | Verificar pasaporte (vigencia), visa requerida, vacunas obligatorias, seguros obligatorios, requisitos de entrada |
| 9 | **Seguro de viaje** | Cotizar y contratar seguro médico, de equipaje, de cancelación |
| 10 | **Información del destino** | Clima esperado, huso horario, moneda local, costumbres, propinas, enchufes eléctricos |
| 11 | **Packing list** | Lista de equipaje personalizada según destino, clima, duración, actividades planificadas |
| 12 | **Reservas** | Reservar vuelos, hoteles, tours, restaurantes, transporte. Gestionar confirmaciones |
| 13 | **Paquetes** | Bundles vuelo+hotel+actividad con descuento. Comparación de paquetes |
| 14 | **Briefing pre-salida** | Revisión final del itinerario con el viajero. Entrega de documentos y confirmaciones |

### FASE DURANTE EL VIAJE

| # | Servicio | Descripción |
|---|----------|-------------|
| 15 | **Soporte 24/7** | Asistencia ante problemas: cancelaciones, retrasos, pérdida de equipaje, emergencias médicas |
| 16 | **Rebooking de emergencia** | Cambiar vuelos/hoteles en tiempo real ante imprevistos |
| 17 | **Concierge en destino** | Reservas de último momento, recomendaciones locales basadas en ubicación actual |
| 18 | **Tracking de vuelos** | Estado en tiempo real, cambios de gate, retrasos, cancelaciones |
| 19 | **Información de emergencia** | Embajadas/consulados, hospitales, policía, bomberos, números locales |
| 20 | **Registro de gastos** | Tracking de gastos reales durante el viaje, comparación con presupuesto |

### FASE POST-VIAJE

| # | Servicio | Descripción |
|---|----------|-------------|
| 21 | **Feedback y valoración** | Encuesta de satisfacción general y por servicio/actividad |
| 22 | **Gestión de reclamos** | Asistencia con reclamos a aerolíneas, hoteles, seguros |
| 23 | **Análisis financiero** | Reporte final: presupuesto vs gasto real, por categoría y por día |
| 24 | **Aprendizaje** | Usar feedback para mejorar futuras recomendaciones. Detectar patrones |
| 25 | **Fidelización** | Programa de puntos, descuentos por viajes anteriores, recordatorios de aniversarios |

---

## 3. Estado actual del sistema

### Inventario de capacidades implementadas

```
SERVICIO                          │ ESTADO           │ DETALLE
──────────────────────────────────┼──────────────────┼─────────────────────────────────
Crear/gestionar viajes            │ ✅ Completo       │ CRUD + estados auto + sync Supabase
Chat inteligente (LLM)            │ ✅ Completo       │ LangGraph 4 nodos + fallback keywords
Extracción de items via chat      │ ✅ Completo       │ 9 intents, structured output, multi-turn
Búsqueda de hoteles               │ ✅ Funcional      │ Booking.com via RapidAPI (solo búsqueda)
Gestión de gastos                 │ ✅ Completo       │ CRUD gastos directos por categoría
Presupuesto con gráficos          │ ✅ Funcional      │ Donut + barras, estimado vs real
Calendario visual                 │ ✅ Funcional      │ FullCalendar.js, 3 vistas, multi-viaje
Perfil de preferencias            │ ✅ Guardado       │ Se guarda pero NO se usa en recomendaciones
Memoria del usuario               │ ✅ Funcional      │ ChromaDB vectorial + checkpoints SQLite
Multi-usuario OAuth               │ ✅ Funcional      │ Google OAuth + fallback demo + RLS
Multi-conversación                │ ✅ Completo       │ Múltiples chats por viaje, persistidos
Feedback post-viaje               │ ✅ Guardado       │ Rating + comentarios, pero nunca se analiza
Clima                             │ ⚠️ Mock          │ 3 destinos hardcodeados, fallback genérico
Traslados entre items             │ ⚠️ Mock          │ Siempre "Metro/Taxi, 20 min, $5"
──────────────────────────────────┼──────────────────┼─────────────────────────────────
Búsqueda de vuelos                │ ❌ No existe      │
Búsqueda de actividades/tours     │ ❌ No existe      │
Transporte real (rutas/tiempos)   │ ❌ No existe      │
Requisitos de viaje (visas)       │ ❌ No existe      │
Cambio de moneda                  │ ❌ No existe      │
Mapas interactivos                │ ❌ No existe      │
Checklist de viaje                │ ❌ No existe      │
Compartir itinerario              │ ❌ No existe      │
Recomendaciones personalizadas    │ ❌ No existe      │ Infraestructura OK, lógica falta
Info emergencia local             │ ❌ No existe      │
Seguros de viaje                  │ ❌ No existe      │
Exportar itinerario               │ ❌ No existe      │
Notificaciones push/email         │ ❌ No existe      │
Reservas reales                   │ ❌ No existe      │ Solo búsqueda, no booking
```

### Lo que funciona pero está incompleto

| Componente | Problema | Impacto |
|------------|---------|---------|
| `weather_service.py` | Datos mock para 3 ciudades. El resto retorna "15-25°C, Variable" | El usuario recibe info climática inútil para el 99% de destinos |
| `trip_service.get_transfer_info()` | Siempre retorna "Metro/Taxi, 20 min, $5" sin importar origen/destino | Traslados son ficticios e inútiles para planificación real |
| `profile_service.py` | Guarda preferencias pero NINGÚN servicio las consulta para personalizar | El usuario llena su perfil pero no ve ningún beneficio |
| `feedback_service.py` | Captura ratings pero nunca se analizan para mejorar recomendaciones | El feedback es un callejón sin salida — datos que no generan valor |
| `booking_service.py` | Solo busca hoteles, no permite reservar. Cache en memoria se pierde al reiniciar | El usuario encuentra un hotel pero no puede hacer nada con él |
| Presupuesto | Moneda única (USD implícita), sin tope configurable, sin alertas de sobrecosto | Inútil para viajes donde gastas en euros, yenes, o pesos |

---

## 4. Gap Analysis completo

### Comparación con agente de viajes real (25 servicios)

| # | Servicio del agente real | Estado en Trip Planner | Gap |
|---|--------------------------|----------------------|-----|
| 1 | Consultoría personalizada | ⚠️ Perfil guardado, no usado | **Conectar perfil con recomendaciones del LLM** |
| 2 | Búsqueda de vuelos | ❌ | **Integrar API de vuelos (Amadeus/Kiwi)** |
| 3 | Búsqueda de alojamiento | ✅ Booking.com | Agregar filtros avanzados y reserva |
| 4 | Búsqueda de actividades | ❌ | **Integrar API de tours (Viator/GetYourGuide)** |
| 5 | Transporte terrestre | ❌ | **Integrar API de rutas (Rome2Rio/Google Maps)** |
| 6 | Armado de itinerario | ✅ Funcional | Agregar optimización automática de rutas |
| 7 | Presupuesto detallado | ⚠️ Moneda única | **Agregar multi-moneda y alertas de sobrecosto** |
| 8 | Documentación de viaje | ❌ | **Integrar API de visas/requisitos** |
| 9 | Seguro de viaje | ❌ | Integrar info de seguros por destino |
| 10 | Info del destino | ⚠️ Mock | **Integrar API de clima real + info del país** |
| 11 | Packing list | ❌ | **Crear sistema de checklist** |
| 12 | Reservas | ❌ | Integrar booking real (fase avanzada) |
| 13 | Paquetes bundle | ❌ | Combinar vuelo+hotel+actividad |
| 14 | Briefing pre-salida | ❌ | Generar resumen pre-viaje automático |
| 15 | Soporte 24/7 | ⚠️ Chat existe | El chat no tiene contexto de emergencia |
| 16 | Rebooking emergencia | ❌ | Requiere reservas reales primero |
| 17 | Concierge en destino | ❌ | Recomendaciones por ubicación actual |
| 18 | Tracking de vuelos | ❌ | **Integrar API de estado de vuelos** |
| 19 | Info emergencia | ❌ | **Crear base de datos de emergencias por país** |
| 20 | Registro de gastos | ✅ Funcional | Agregar registro con foto de recibo |
| 21 | Feedback post-viaje | ✅ Guardado | **Conectar feedback con motor de recomendaciones** |
| 22 | Gestión de reclamos | ❌ | Fase avanzada |
| 23 | Análisis financiero | ⚠️ Básico | Agregar análisis por día, tendencias, proyecciones |
| 24 | Aprendizaje | ⚠️ Infraestructura | **Activar el ciclo feedback → perfil → recomendaciones** |
| 25 | Fidelización | ❌ | Fase avanzada |

---

## 5. PRIORIDAD 1 — Funcionalidades Críticas

> Sin estas funcionalidades, el sistema no puede llamarse "agente de viajes".
> Son lo más obvio que falta y lo que un usuario esperaría encontrar.

---

### P1-01. Búsqueda de Vuelos

**Por qué es crítico:** Un agente de viajes que no busca vuelos es como un restaurante sin menú. Es la primera acción que un viajero necesita.

**Estado actual:** No existe. La categoría "vuelos" está en los enums pero solo se usa para items manuales.

**Qué implementar:**

1. **Nuevo servicio `services/flight_service.py`**
   - `search_flights(origin, destination, date, return_date, passengers, cabin_class)` → lista de vuelos
   - `search_cheapest_dates(origin, destination, month)` → calendario de precios
   - `get_flight_details(flight_id)` → detalles completos
   - Cache en memoria con TTL (similar a booking_service)
   - Fallback gracioso si API no disponible

2. **Nuevo intent en el dispatcher**
   - Intent: `flight_search`
   - Agregar al schema Pydantic `ItemExtractionResult`
   - Agregar al system prompt de extracción: "Si el usuario quiere buscar vuelos, aerolíneas, o pasajes..."
   - Agregar handler `_flight_search_response()` en agent_service
   - Agregar keywords de fallback: "vuelo", "vuelos", "pasaje", "avión", "aerolínea"

3. **Renderizado en chat**
   - Nueva función `render_flight_results()` en chat_widget.py
   - Card de vuelo: aerolínea, origen→destino, horarios, escalas, duración, precio, clase, equipaje
   - Botón "Agregar al itinerario" que crea un item tipo "vuelo"

4. **Datos necesarios del usuario**
   - Ciudad de origen (extraer del perfil o preguntar)
   - Preferencia de escalas (directo, 1 escala, cualquiera)
   - Clase (económica, business, primera)
   - Equipaje (mano, bodega)

**API recomendada:** Amadeus Self-Service (free tier: 2,000 calls/mes) o Kiwi.com Tequila (gratis con registro). Amadeus es más completo; Kiwi es más fácil de integrar y permite rutas creativas multi-carrier.

**Archivos a crear/modificar:**
- CREAR: `services/flight_service.py`
- MODIFICAR: `services/agent_service.py` (nuevo intent + handler)
- MODIFICAR: `services/llm_item_extraction.py` (nuevo intent en schema + prompt)
- MODIFICAR: `services/item_extraction.py` (keywords de fallback)
- MODIFICAR: `components/chat_widget.py` (render_flight_results)
- MODIFICAR: `pages/2_Chat.py` (renderizar flight_results)
- MODIFICAR: `config/settings.py` (si se necesitan nuevos enums)
- OPCIONAL: `mcp_servers/flight_server.py` (MCP para vuelos)

**Estimación de complejidad:** Alta. Requiere nueva integración HTTP, nuevo intent end-to-end, nuevo componente de renderizado.

---

### P1-02. Búsqueda de Actividades y Tours

**Por qué es crítico:** El agente puede agregar "Visitar el Coliseo" como item manual, pero no puede buscar tours reales con precios, horarios, disponibilidad y reviews. El usuario no tiene forma de descubrir qué hacer en su destino.

**Estado actual:** No existe. Las actividades se crean manualmente con datos inventados.

**Qué implementar:**

1. **Nuevo servicio `services/activity_service.py`**
   - `search_activities(destination, date, category, price_range)` → lista de actividades
   - `get_activity_details(activity_id)` → detalles con reviews, fotos, horarios
   - `search_restaurants(destination, cuisine, price_range)` → restaurantes recomendados
   - Cache con TTL de 1 hora (consistente con booking_service)

2. **Nuevo intent en el dispatcher**
   - Intent: `activity_search`
   - Triggers: "qué puedo hacer en...", "buscar tours en...", "actividades en...", "restaurantes en...", "qué visitar"
   - Handler `_activity_search_response()` similar a `_hotel_search_response()`

3. **Renderizado en chat**
   - Nueva función `render_activity_results()` en chat_widget.py
   - Card de actividad: nombre, descripción corta, precio, duración, rating, foto, categoría
   - Botón "Agregar al itinerario" que crea un item con datos reales pre-llenados

4. **Categorías de actividades**
   - Tours guiados, Museos y atracciones, Aventura y naturaleza, Gastronomía, Cultura y espectáculos, Bienestar/spa, Vida nocturna

**API recomendada:** Viator Partner API (300,000+ productos, 2,500+ destinos). Alternativa: GetYourGuide (OpenAPI spec disponible en GitHub). Ambas tienen modelo de búsqueda ligera que no requiere ingestión completa de catálogo.

**Archivos a crear/modificar:**
- CREAR: `services/activity_service.py`
- MODIFICAR: `services/agent_service.py` (nuevo intent)
- MODIFICAR: `services/llm_item_extraction.py` (schema + prompt)
- MODIFICAR: `services/item_extraction.py` (keywords)
- MODIFICAR: `components/chat_widget.py` (render_activity_results)
- MODIFICAR: `pages/2_Chat.py` (renderizar activity_results)

---

### P1-03. Clima Real por Destino y Fecha

**Por qué es crítico:** El sistema actual muestra datos climáticos inventados para el 99.9% de destinos. Un agente de viajes real consulta el pronóstico antes de recomendar actividades outdoor, ropa, o fechas alternativas. El usuario toma decisiones basándose en datos falsos.

**Estado actual:** Mock con 3 destinos hardcodeados (Tokio, Barcelona, Lima). Todo lo demás retorna "15-25°C, Variable".

**Qué implementar:**

1. **Reemplazar `services/weather_service.py` completo**
   - `get_current_weather(destination)` → clima actual
   - `get_forecast(destination, start_date, end_date)` → pronóstico por día
   - `get_historical_average(destination, month)` → promedios históricos (para viajes lejanos)
   - Lógica: si el viaje es en <14 días → forecast real. Si es >14 días → promedios históricos
   - Cache con TTL de 3 horas (clima cambia lento)

2. **Enriquecer el dashboard**
   - Pronóstico día a día para el viaje activo (no solo un rango genérico)
   - Iconos de clima por día
   - Alertas: "Se esperan lluvias el día 3 — considera actividades indoor"

3. **Integrar con el LLM**
   - Inyectar clima real en el contexto del chatbot (`_build_trip_context()`)
   - El agente puede responder "¿qué clima habrá?" con datos reales
   - El agente puede sugerir "el día 3 llueve, te recomiendo visitar un museo"

**API recomendada:** Open-Meteo (totalmente gratis, sin API key, open source, alta precisión). Forecast 16 días + histórico. Alternativa: OpenWeatherMap (free tier: 1,000 calls/día).

**Archivos a crear/modificar:**
- REESCRIBIR: `services/weather_service.py` (reemplazar mock por API real)
- MODIFICAR: `pages/1_Dashboard.py` (pronóstico enriquecido)
- MODIFICAR: `services/llm_chatbot.py` (inyectar clima en contexto)

---

### P1-04. Cambio de Moneda y Presupuesto Multi-Divisa

**Por qué es crítico:** El 100% de los viajes internacionales involucran al menos 2 monedas. Un viajero de Uruguay que va a Europa necesita ver precios en euros Y en pesos uruguayos. El sistema actual asume USD para todo, lo cual es irreal.

**Estado actual:** No existe. Todos los costos son numéricos sin campo de moneda. El presupuesto suma todo como si fuera la misma moneda.

**Qué implementar:**

1. **Nuevo servicio `services/currency_service.py`**
   - `get_exchange_rate(from_currency, to_currency)` → tasa actual
   - `convert(amount, from_currency, to_currency)` → monto convertido
   - `get_destination_currency(destination)` → moneda local del destino
   - Cache de tasas por 24 horas (las tasas no cambian por hora)

2. **Cambios en el modelo de datos**
   - Agregar campo `currency` a `trips` (moneda base del viaje)
   - Agregar campo `currency` a `itinerary_items` y `expenses` (moneda del gasto)
   - Agregar campo `home_currency` a `profiles` (moneda del viajero)
   - Migración SQL para nuevos campos (ALTER TABLE con defaults)

3. **Cambios en presupuesto**
   - Mostrar totales en moneda base del viaje Y en moneda del viajero
   - Convertir automáticamente al agregar items/gastos en moneda diferente
   - Indicar tasa de cambio usada

4. **Integración con chat**
   - Intent `currency_info`: "¿cuánto es 100 euros en dólares?", "¿qué moneda usan en Japón?"
   - El agente puede responder preguntas de conversión con datos reales

**API recomendada:** ExchangeRate-API (1,500 calls/mes gratis, 161 monedas) o Open Exchange Rates (1,000 calls/mes gratis).

**Archivos a crear/modificar:**
- CREAR: `services/currency_service.py`
- MODIFICAR: `scripts/setup_database.sql` (campos currency)
- MODIFICAR: `services/trip_service.py` (conversores con currency)
- MODIFICAR: `services/budget_service.py` (cálculos multi-moneda)
- MODIFICAR: `services/expense_service.py` (currency por gasto)
- MODIFICAR: `pages/5_Presupuesto.py` (mostrar dual currency)
- MODIFICAR: `pages/6_Perfil.py` (home_currency)
- MODIFICAR: `config/settings.py` (enum de monedas comunes)

---

### P1-05. Requisitos de Viaje (Visas, Vacunas, Documentos)

**Por qué es crítico:** Un agente de viajes siempre verifica si su cliente necesita visa, vacunas obligatorias, o documentos especiales. Sin esta info, el viajero podría llegar al aeropuerto y ser rechazado. Es información de seguridad, no un nice-to-have.

**Estado actual:** No existe. No hay ninguna tabla, servicio, ni lógica relacionada.

**Qué implementar:**

1. **Nuevo servicio `services/travel_requirements_service.py`**
   - `get_visa_requirements(nationality, destination)` → requisito de visa (libre, eVisa, embajada)
   - `get_health_requirements(destination)` → vacunas obligatorias/recomendadas
   - `get_entry_requirements(destination)` → documentos necesarios, restricciones
   - `get_safety_info(destination)` → nivel de alerta de seguridad, advisories
   - Cache por 7 días (los requisitos de visa cambian poco)

2. **Checklist automático por viaje**
   - Al crear un viaje, generar automáticamente checklist de requisitos
   - Alerta en el dashboard: "Tu viaje a Japón requiere: pasaporte vigente, no requiere visa para estancias <90 días"
   - Estado de cada requisito: pendiente / completado / no aplica

3. **Integración con chat**
   - Intent `travel_requirements`: "¿necesito visa para Japón?", "¿qué vacunas necesito?"
   - El agente responde con datos reales de la API

4. **Alertas proactivas**
   - Al seleccionar destino: "Para viajar a Brasil, ciudadanos uruguayos necesitan..."
   - N días antes del viaje: "Recuerda verificar la vigencia de tu pasaporte"

**API recomendada:** Travel Buddy AI (visa-requirement en RapidAPI, free tier disponible) o Sherpa API v2 (200+ países, RESTful).

**Archivos a crear/modificar:**
- CREAR: `services/travel_requirements_service.py`
- MODIFICAR: `pages/1_Dashboard.py` (alertas de requisitos)
- MODIFICAR: `components/alert_banner.py` (alertas de documentos)
- MODIFICAR: `services/agent_service.py` (nuevo intent)
- MODIFICAR: `services/llm_item_extraction.py` (schema)

---

### P1-06. Transporte Real entre Puntos del Itinerario

**Por qué es crítico:** Actualmente, todos los traslados muestran "Metro/Taxi, 20 min, $5" sin importar si es de París a Marsella o de un hotel al restaurante de al lado. Los tiempos de traslado afectan directamente la viabilidad del itinerario. Un agente real calcula distancias y tiempos.

**Estado actual:** `get_transfer_info()` en trip_service.py retorna datos hardcodeados.

**Qué implementar:**

1. **Nuevo servicio `services/transport_service.py`**
   - `get_route(origin, destination, mode)` → distancia, duración, precio estimado
   - `get_transport_options(origin, destination)` → opciones multimodales (taxi, metro, bus, a pie, tren)
   - `estimate_transfer_time(location_a, location_b)` → tiempo estimado para validar itinerario
   - Geocoding: convertir nombres de lugares a coordenadas

2. **Reemplazar traslados hardcodeados**
   - `get_transfer_info()` debe consultar la API real en lugar de retornar datos fijos
   - Mostrar opciones: "Taxi: 15 min, $12 | Metro: 25 min, $2 | A pie: 40 min"
   - Agregar traslados como items sugeridos automáticamente entre actividades con ubicaciones diferentes

3. **Validación de viabilidad del itinerario**
   - Calcular si hay tiempo suficiente entre items consecutivos
   - Alerta: "Solo tienes 30 min entre el museo y el restaurante, pero el traslado toma 45 min"

4. **Integración con mapas** (ver P2-02)
   - Mostrar ruta en mapa entre puntos del itinerario

**API recomendada:** Rome2Rio Search API (multimodal: avión, tren, bus, ferry, auto — 700+ aerolíneas + 2M rutas terrestres). Para distancias cortas intra-ciudad: OpenRouteService (gratuito, open source) o Google Maps Directions API.

**Archivos a crear/modificar:**
- CREAR: `services/transport_service.py`
- REESCRIBIR: `trip_service.get_transfer_info()` (reemplazar mock)
- MODIFICAR: `components/itinerary_item.py` (render_transfer con datos reales)
- MODIFICAR: `components/alert_banner.py` (alerta de tiempo insuficiente)

---

## 6. PRIORIDAD 2 — Funcionalidades Importantes

> Funcionalidades que mejoran significativamente la experiencia pero que el sistema
> puede funcionar sin ellas en una primera versión.

---

### P2-01. Exportación del Itinerario

**Problema:** El usuario planifica todo en la app pero no puede llevarse nada fuera de ella. No puede imprimir su itinerario, mandarlo por email, o agregarlo a Google Calendar.

**Qué implementar:**
- Exportar itinerario como PDF (resumen día a día con horarios, ubicaciones, confirmaciones)
- Exportar como archivo .ics (importable en Google Calendar, Apple Calendar, Outlook)
- Exportar como JSON (para integración con otras apps)
- Compartir via link público de solo lectura
- Enviar por email (resumen del viaje)

**Archivos a crear:**
- `services/export_service.py` (generación de PDF, ICS, JSON)
- Botón de exportación en `pages/4_Itinerario.py` y `pages/1_Dashboard.py`

---

### P2-02. Mapas Interactivos

**Problema:** El usuario tiene 10 actividades en Roma pero no puede visualizar dónde queda cada una ni cómo se conectan geográficamente. No puede optimizar su ruta.

**Qué implementar:**
- Mapa interactivo con pins para cada item del itinerario (por día)
- Ruta sugerida entre puntos del mismo día
- Puntos de interés cercanos (restaurantes, ATMs, farmacias)
- Vista de mapa del destino en el dashboard
- Geocoding de ubicaciones de items

**Librería recomendada:** `streamlit-folium` (Leaflet.js para Streamlit) o `pydeck` (Deck.gl, ya incluido en Streamlit).

**Archivos a crear/modificar:**
- CREAR: `services/geocoding_service.py` (coordenadas de ubicaciones)
- CREAR: `components/map_widget.py`
- MODIFICAR: `pages/4_Itinerario.py` (mapa por día)
- MODIFICAR: `pages/1_Dashboard.py` (mapa del destino)

---

### P2-03. Checklist de Viaje

**Problema:** El viajero no tiene dónde trackear preparativos: renovar pasaporte, comprar adaptador eléctrico, empacar protector solar, imprimir reservas. Usa apps separadas o papel.

**Qué implementar:**
- Checklist por viaje con items agrupados por categoría:
  - Documentos (pasaporte, visa, seguro, reservas impresas)
  - Equipaje (ropa según clima, artículos de higiene, medicamentos)
  - Tecnología (adaptador, cargadores, power bank)
  - Financiero (tarjetas, efectivo en moneda local)
  - Preparativos (riego de plantas, cuidado de mascotas, aviso al banco)
- Templates por tipo de viaje (playa, montaña, ciudad, business)
- Items sugeridos automáticamente según destino y actividades planificadas
- Estado: pendiente / completado
- Contador de progreso en el dashboard

**Cambios en BD:**
- Nueva tabla `checklist_items` (id, trip_id, category, name, completed, auto_generated)

**Archivos a crear/modificar:**
- CREAR: `services/checklist_service.py`
- CREAR: `pages/8_Checklist.py` (nueva página)
- MODIFICAR: `pages/1_Dashboard.py` (progreso del checklist)
- MODIFICAR: `scripts/setup_database.sql` (nueva tabla)
- MODIFICAR: `app.py` (agregar página a navegación)

---

### P2-04. Compartir Itinerario con Compañeros de Viaje

**Problema:** La mayoría de los viajes son en grupo (pareja, familia, amigos). Actualmente solo un usuario puede ver y editar cada viaje. No hay forma de planificar colaborativamente.

**Qué implementar:**
- Invitar usuarios al viaje por email
- Roles: owner (crear/eliminar), editor (modificar items/gastos), viewer (solo lectura)
- Link compartible de solo lectura (sin login requerido)
- Historial de cambios: quién agregó/modificó qué
- Splitting de gastos: quién pagó qué, quién debe a quién
- Chat grupal dentro del viaje

**Cambios en BD:**
- Nueva tabla `trip_members` (trip_id, user_id, role, invited_at, accepted_at)
- Modificar RLS para permitir acceso a miembros

---

### P2-05. Recomendaciones Personalizadas

**Problema:** La infraestructura existe (ChromaDB con memorias, perfil de preferencias, feedback post-viaje) pero NUNCA se usa para personalizar. El agente sugiere lo mismo a un mochilero que a un viajero de lujo.

**Qué implementar:**
- Al crear un viaje, el LLM consulta:
  - Perfil del usuario (estilo, presupuesto, restricciones)
  - Memorias vectoriales (viajes anteriores, preferencias aprendidas)
  - Feedback de viajes pasados (qué gustó, qué no)
- Sugiere proactivamente: "En tu viaje anterior a Roma disfrutaste mucho los tours de comida. ¿Quieres buscar algo similar en Barcelona?"
- Adapta nivel de sugerencias al presupuesto diario del perfil
- Respeta restricciones alimentarias al sugerir restaurantes

**Archivos a modificar:**
- `services/llm_chatbot.py` (inyectar perfil + feedback en contexto)
- `services/agent_service.py` (consultar perfil al generar sugerencias)
- `services/memory_manager.py` (buscar memorias de viajes similares)

---

### P2-06. Información del Destino Enriquecida

**Problema:** El usuario elige viajar a Tokio pero no sabe: qué moneda usan, huso horario, tipo de enchufes, si se da propina, cómo funciona el transporte público, qué apps necesita, etc.

**Qué implementar:**
- Ficha del destino con:
  - Moneda local + tasa de cambio actual
  - Huso horario + diferencia con el viajero
  - Idioma oficial + frases útiles
  - Tipo de enchufe + voltaje
  - Costumbres de propina
  - Números de emergencia (policía, ambulancia, bomberos)
  - Embajada/consulado del país del viajero
  - Mejor época para visitar
  - Transporte público: apps recomendadas, tarjetas de transporte
- Accesible desde el dashboard del viaje y via chat

**Archivos a crear:**
- CREAR: `services/destination_info_service.py`
- CREAR: `data/destination_data.json` (datos estáticos de países/ciudades)
- MODIFICAR: `pages/1_Dashboard.py` (ficha del destino)

---

## 7. PRIORIDAD 3 — Funcionalidades de Valor Agregado

> Funcionalidades que diferencian la app de competidores y mejoran la retención.

---

### P3-01. Notificaciones y Alertas Inteligentes

**Qué implementar:**
- Alerta N días antes del viaje: "Tu viaje a Barcelona comienza en 7 días"
- Alerta de documentos: "Verifica que tu pasaporte tenga al menos 6 meses de vigencia"
- Alerta de clima: "Se esperan lluvias los días 3-4 de tu viaje"
- Alerta de presupuesto: "Has gastado el 80% de tu presupuesto y te quedan 3 días"
- Alerta de items pendientes: "Tienes 3 items sin confirmar"
- Canal: dentro de la app (ya existe), email (nuevo), push (futuro)

---

### P3-02. Seguros de Viaje

**Qué implementar:**
- Información de seguros recomendados por destino y duración
- Comparativa de coberturas básicas: médico, equipaje, cancelación
- Link a cotización en sitios de aseguradoras
- Recordatorio en checklist: "¿Ya contrataste seguro de viaje?"

---

### P3-03. Resumen Pre-Viaje ("Briefing")

**Qué implementar:**
- Página/PDF automática generada N días antes del viaje con:
  - Itinerario día a día resumido
  - Clima esperado por día
  - Documentos necesarios (checklist)
  - Información de emergencia
  - Tasas de cambio actualizadas
  - Apps recomendadas para el destino
  - Tips culturales

---

### P3-04. Análisis Financiero Avanzado

**Qué implementar:**
- Presupuesto por día (total / días = daily burn rate)
- Proyección: "A este ritmo, tu gasto final será $X (Y% sobre presupuesto)"
- Gráfico temporal: gastos acumulados vs presupuesto día a día
- Comparación con viajes anteriores al mismo destino
- Desglose: qué porcentaje se va en vuelos vs hotel vs actividades vs comida

---

### P3-05. Diario de Viaje

**Qué implementar:**
- Notas y fotos por día del viaje
- Timeline visual del viaje con fotos
- Exportable como recuerdo post-viaje
- Integración con el itinerario (foto tomada en la actividad X)

---

## 8. PRIORIDAD 4 — Funcionalidades Avanzadas

> Funcionalidades de largo plazo que requieren infraestructura compleja.

---

### P4-01. Reservas Reales

**Qué implicaría:**
- Pasar de "buscar hoteles" a "reservar hotel" (requiere acuerdos con proveedores o usar APIs de booking con capacidad transaccional)
- Gestión de confirmaciones, cancelaciones, modificaciones
- Pagos integrados (Stripe/MercadoPago)
- Compliance legal (protección al consumidor, políticas de cancelación)

### P4-02. Viajes Multi-Destino

**Qué implicaría:**
- Un viaje con múltiples destinos: "2 días en Roma → 3 días en Florencia → 2 días en Venecia"
- Transporte entre destinos como parte del itinerario
- Presupuesto desglosado por destino
- Items agrupados por destino, no solo por día

### P4-03. Agentic AI (Planificación Autónoma)

**Qué implicaría:**
- El usuario dice "Quiero 10 días en Japón con presupuesto de $3,000"
- El agente autónomamente: busca vuelos, selecciona hotel, arma itinerario día a día con actividades, calcula presupuesto, presenta plan completo para aprobación
- Tendencia 2026 de la industria (Google, Kayak, Expedia están desarrollando esto)

### P4-04. Viajes Grupales con Splitting de Gastos

**Qué implicaría:**
- Múltiples viajeros con perfiles independientes
- Registro de quién pagó cada gasto
- Cálculo automático de deudas: "Juan le debe $45 a María"
- Integración con métodos de pago para liquidar deudas

### P4-05. Modo Offline

**Qué implicaría:**
- Service worker para PWA
- Cache local del itinerario completo
- Sincronización al recuperar conexión
- Mapas offline del destino

---

## 9. APIs recomendadas por funcionalidad

| Funcionalidad | API Primaria | Free Tier | API Alternativa |
|---------------|-------------|-----------|-----------------|
| **Vuelos** | Amadeus Self-Service | 2,000 calls/mes | Kiwi.com Tequila (gratis) |
| **Hoteles** | Booking.com (RapidAPI) | Ya integrado | Amadeus Hotel Search |
| **Actividades** | Viator Partner API | Partner agreement | GetYourGuide (OpenAPI en GitHub) |
| **Transporte** | Rome2Rio Search API | Contactar | OpenRouteService (gratis) |
| **Clima** | Open-Meteo | Totalmente gratis | OpenWeatherMap (1,000/día) |
| **Visas** | Travel Buddy AI (RapidAPI) | Free tier | Sherpa API v2 |
| **Moneda** | ExchangeRate-API | 1,500/mes | Open Exchange Rates (1,000/mes) |
| **Geocoding** | Nominatim (OpenStreetMap) | Gratis | Google Geocoding ($5/1000) |
| **Mapas** | Leaflet + OpenStreetMap | Gratis | Mapbox (50,000 cargas/mes) |

---

## 10. Impacto arquitectónico

### Nuevos servicios a crear (8)

```
services/
  flight_service.py           ← P1-01 Vuelos
  activity_service.py         ← P1-02 Actividades
  currency_service.py         ← P1-04 Moneda
  travel_requirements_service.py ← P1-05 Visas/documentos
  transport_service.py        ← P1-06 Transporte
  geocoding_service.py        ← P2-02 Mapas
  checklist_service.py        ← P2-03 Checklist
  destination_info_service.py ← P2-06 Info destino
  export_service.py           ← P2-01 Exportación
```

### Servicios existentes a reescribir (1)

```
services/
  weather_service.py          ← P1-03 Reemplazar mock por Open-Meteo
```

### Servicios existentes a modificar significativamente (6)

```
services/
  agent_service.py            ← Nuevos intents: flight_search, activity_search,
                                 currency_info, travel_requirements
  llm_item_extraction.py      ← Nuevos intents en schema Pydantic + system prompt
  item_extraction.py           ← Nuevas keywords de fallback
  budget_service.py           ← Cálculos multi-moneda
  trip_service.py             ← Conversores con currency, transfer real
  llm_chatbot.py              ← Inyectar clima, moneda, requisitos en contexto
```

### Nuevas páginas (1-2)

```
pages/
  8_Checklist.py              ← P2-03
  9_Info_Destino.py           ← P2-06 (o integrar en Dashboard)
```

### Nuevos componentes (3-4)

```
components/
  flight_card.py              ← Renderizado de vuelos
  activity_card.py            ← Renderizado de actividades/tours
  map_widget.py               ← Mapa interactivo
  checklist_widget.py         ← Checklist con checkboxes
```

### Cambios en BD (Supabase)

```sql
-- Nuevos campos en tablas existentes
ALTER TABLE trips ADD COLUMN currency TEXT DEFAULT 'USD';
ALTER TABLE itinerary_items ADD COLUMN currency TEXT DEFAULT 'USD';
ALTER TABLE expenses ADD COLUMN currency TEXT DEFAULT 'USD';
ALTER TABLE profiles ADD COLUMN home_currency TEXT DEFAULT 'USD';
ALTER TABLE profiles ADD COLUMN nationality TEXT;

-- Nueva tabla
CREATE TABLE checklist_items (
  id TEXT PRIMARY KEY,
  trip_id TEXT REFERENCES trips(id) ON DELETE CASCADE,
  category TEXT NOT NULL,        -- documentos, equipaje, tecnologia, financiero, preparativos
  name TEXT NOT NULL,
  completed BOOLEAN DEFAULT FALSE,
  auto_generated BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Nueva tabla (si se implementa compartición)
CREATE TABLE trip_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trip_id TEXT REFERENCES trips(id) ON DELETE CASCADE,
  user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
  role TEXT NOT NULL DEFAULT 'viewer',  -- owner, editor, viewer
  invited_at TIMESTAMPTZ DEFAULT now(),
  accepted_at TIMESTAMPTZ,
  UNIQUE(trip_id, user_id)
);
```

---

## 11. Matriz de dependencias

```
P1-01 Vuelos          → independiente (puede implementarse primero)
P1-02 Actividades     → independiente
P1-03 Clima           → independiente (reemplaza mock, sin dependencias)
P1-04 Multi-moneda    → independiente (pero impacta BD + presupuesto)
P1-05 Visas           → depende de P1-04 (nationality en perfil)
P1-06 Transporte      → depende de geocoding (P2-02 parcial)

P2-01 Exportación     → independiente
P2-02 Mapas           → depende de geocoding service
P2-03 Checklist       → depende de P1-05 (auto-generar items de documentos)
P2-04 Compartir       → independiente (pero complejo en BD)
P2-05 Recomendaciones → depende de que perfil se use + memorias
P2-06 Info destino    → depende de P1-03 (clima) + P1-04 (moneda) + P1-05 (visas)

P3-01 Notificaciones  → depende de tener algo que notificar (P1-*)
P3-02 Seguros         → depende de P1-05 (requisitos de viaje)
P3-03 Briefing        → depende de P1-03 + P1-05 + P2-06
P3-04 Análisis fin.   → depende de P1-04 (multi-moneda)
P3-05 Diario          → independiente
```

### Orden de implementación sugerido

```
FASE 1 (cimientos):  P1-03 Clima → P1-04 Moneda → P1-01 Vuelos → P1-02 Actividades
FASE 2 (core):       P1-06 Transporte → P1-05 Visas → P2-01 Exportación
FASE 3 (experiencia): P2-02 Mapas → P2-03 Checklist → P2-05 Recomendaciones → P2-06 Info destino
FASE 4 (social):     P2-04 Compartir → P3-01 Notificaciones → P3-03 Briefing
FASE 5 (avanzado):   P3-04 Análisis → P4-01 Reservas → P4-03 Agentic AI
```

---

> Este documento debe actualizarse a medida que se implementen las funcionalidades.
> Marcar con ✅ las secciones completadas y actualizar el estado en la tabla del punto 3.
