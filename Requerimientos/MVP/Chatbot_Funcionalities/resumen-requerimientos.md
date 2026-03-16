# Indice de Requerimientos Funcionales — Trip Planner MVP (Chatbot Funcionalities)

## Informacion General
- **Proyecto**: Trip Planner
- **Alcance**: MVP - Nuevas funcionalidades del Chatbot
- **Total de requerimientos**: 3
- **Fecha de generacion**: 2026-03-16

---

## Lista de Requerimientos

| Codigo | Titulo | Prioridad |
|--------|--------|-----------|
| REQ-CF-001 | Selector Obligatorio de Viaje antes del Chat | Alta |
| REQ-CF-002 | Creacion de Eventos en el Cronograma desde el Chatbot | Media |
| REQ-CF-003 | Creacion de Items en el Itinerario desde el Chatbot con Extraccion Inteligente | Alta |

---

## Descripcion de cada Requerimiento

### REQ-CF-001 — Selector Obligatorio de Viaje antes del Chat
Al abrir la pagina de Chat, el usuario debe seleccionar explicitamente un viaje antes de poder enviar mensajes. El selector muestra solo viajes activos (en_planificacion, confirmado, en_curso) e incluye opcion "Crear nuevo viaje". Elimina la auto-deteccion de viaje por destino y hace obligatorio el campo `trip_id` en los chats. Al cambiar viaje, carga el ultimo chat asociado o crea uno nuevo.

### REQ-CF-002 — Creacion de Eventos en el Cronograma desde el Chatbot
Permite crear eventos multi-dia en el cronograma desde el chatbot (ej: "agrega mi viaje al cronograma"). Introduce un nuevo campo `end_day: int | null` en el modelo de item para soportar items que abarcan multiples dias. El evento se renderiza como bloque allDay en FullCalendar. Requiere confirmacion antes de crear. Retrocompatibilidad total con items existentes de un solo dia.

### REQ-CF-003 — Creacion de Items en el Itinerario con Extraccion Inteligente
Reemplaza la creacion de items genericos hardcodeados por extraccion inteligente de datos del mensaje del usuario: nombre, fecha/dia, hora, tipo de item, ubicacion y costo. Funciona en dual-mode (LLM via OpenAI structured output / mock via regex). Flujo multi-turn para datos faltantes (max 3 turnos). Deteccion de conflictos horarios. Confirmacion con tarjeta rica antes de crear.

---

## Resumen de Decisiones de Diseno

1. **Prefijo de numeracion `REQ-CF`**: "CF" = Chatbot Funcionalities, consistente con los prefijos existentes CL (Chatbot Login) y UI (User Interface).

2. **Selector obligatorio como prerequisito**: REQ-CF-001 es prerequisito de REQ-CF-002 y REQ-CF-003. Todas las funcionalidades del chatbot asumen que hay un viaje explicitamente seleccionado.

3. **Campo `end_day` para items multi-dia**: Se extiende el modelo de datos con un campo opcional en lugar de crear un modelo separado de eventos. Esto mantiene retrocompatibilidad y simplifica la implementacion.

4. **Dual-mode (LLM / mock)**: Tanto la extraccion inteligente (REQ-CF-003) como la deteccion de intencion de cronograma (REQ-CF-002) funcionan en ambos modos del chatbot. En modo LLM se usa OpenAI structured output; en modo mock se usan regex y heuristicas.

5. **Confirmacion obligatoria**: Todas las acciones que modifican datos (crear eventos, crear items) requieren confirmacion explicita del usuario via tarjeta de confirmacion, consistente con REQ-UI-003 RN-001.

---

## Mapa de Dependencias

```
REQ-CF-001 (Selector Obligatorio de Viaje)
├── depende de: REQ-CL-004 (Chats Multiples)
├── depende de: REQ-CL-005 (Contexto Aislado)
├── depende de: REQ-UI-002 (Chat - Interfaz)
└── depende de: REQ-UI-008 (Mis Viajes)

REQ-CF-002 (Eventos en Cronograma)
├── depende de: REQ-CF-001 (Selector Obligatorio)
├── depende de: REQ-UI-004 (Cronograma/Calendario)
└── depende de: REQ-UI-003 (Chat - Acciones Itinerario)

REQ-CF-003 (Items con Extraccion Inteligente)
├── depende de: REQ-CF-001 (Selector Obligatorio)
├── depende de: REQ-UI-003 (Chat - Acciones Itinerario)
├── depende de: REQ-UI-005 (Itinerario Detallado)
├── depende de: REQ-UI-004 (Cronograma/Calendario)
└── depende de: REQ-UI-006 (Presupuesto)
```

**Orden de implementacion sugerido**: REQ-CF-001 → REQ-CF-003 → REQ-CF-002 (CF-001 es prerequisito; CF-003 es prioridad Alta; CF-002 es prioridad Media y requiere extension del modelo de datos).

---

## Impacto en Componentes Existentes

| Componente | Archivo | REQ-CF-001 | REQ-CF-002 | REQ-CF-003 |
|------------|---------|------------|------------|------------|
| Pagina de chat | `pages/2_Chat.py` | Selector de viaje, deshabilitar input | — | — |
| Servicio de chat | `services/chat_service.py` | trip_id obligatorio | — | — |
| Servicio del agente | `services/agent_service.py` | Eliminar auto-deteccion | Deteccion intencion cronograma | Reescribir `_add_item_response` |
| Servicio de viajes | `services/trip_service.py` | — | Soportar `end_day` en CRUD | — |
| Cronograma | `pages/3_Cronograma.py` | — | Renderizar multi-dia | — |
| Modelo de item | `models/itinerary_item.py` | — | Campo `end_day` | — |
| Schema SQL | `scripts/schema.sql` | — | ALTER TABLE `end_day` | — |
| Extraccion (nuevo) | `services/item_extraction.py` | — | — | Logica NLP/regex |

---

## Estado de Implementacion

| Codigo | Estado | Notas |
|--------|--------|-------|
| REQ-CF-001 | Implementado | Selector obligatorio de viaje en `pages/2_Chat.py`. `trip_id` obligatorio en chats. Filtra viajes activos + opcion "Crear nuevo viaje" |
| REQ-CF-002 | Implementado | Campo `end_day` en modelo de item. Migracion SQL en `scripts/migration_cf002_end_day.sql`. Renderizado `allDay` en FullCalendar (color `#607D8B`). Deteccion de intent por LLM o keywords |
| REQ-CF-003 | Implementado | Extraccion via LLM structured output (`llm_item_extraction.py`) con schema Pydantic `ItemExtractionResult`. Fallback a keywords basico (`item_extraction.py`). Flujo multi-turn (max 3 turnos). Deteccion de conflictos horarios. Confirmacion con tarjeta rica |

---

## Informacion Pendiente de Clarificacion

1. **REQ-CF-001**: Formato de visualizacion de viajes en el selector (solo destino, o destino + fechas + estado).
2. **REQ-CF-001**: Comportamiento si un viaje seleccionado transiciona a completado/cancelado durante el chat.
3. **REQ-CF-002**: Paleta de colores y estilo visual para eventos multi-dia en el cronograma.
4. **REQ-CF-002**: Si eventos de cronograma pueden tener costo asociado o siempre costo cero.
5. **REQ-CF-003**: Si el agente debe estimar costos automaticamente o solo registrar costos mencionados por el usuario.
6. **REQ-CF-003**: Valor de `end_time` por defecto segun tipo de item (duracion estimada) o vacio si no se especifica.
7. **REQ-CF-003**: Si items creados via extraccion inteligente reciben `status="planificado"` o `status="sugerido"`.
