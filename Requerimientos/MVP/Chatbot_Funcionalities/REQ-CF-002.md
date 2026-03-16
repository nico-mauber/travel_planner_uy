# REQ-CF-002 — Creacion de Eventos en el Cronograma desde el Chatbot

## Codigo
REQ-CF-002

## Titulo
Creacion de Eventos en el Cronograma desde el Chatbot

## Prioridad MVP
Media

## Historia de Usuario

**Como** viajero registrado,
**Quiero** poder decirle al chatbot "agrega mi viaje al cronograma" o "crea un evento con las fechas de mi viaje",
**Para** visualizar un bloque multi-dia en el cronograma que represente la duracion completa de mi viaje y tener una referencia temporal clara de toda la planificacion.

## Descripcion

Este requerimiento introduce la capacidad de crear eventos en el cronograma directamente desde el chatbot. El caso principal es la creacion de un evento multi-dia que represente la duracion completa del viaje como un bloque visual que abarca desde la fecha de inicio hasta la fecha de fin. Esto requiere extender el modelo de datos del item de itinerario con un nuevo campo `end_day` que permita que un item abarque multiples dias, manteniendo retrocompatibilidad total con los items existentes de un solo dia. El chatbot detecta la intencion del usuario de crear eventos de cronograma, propone el evento con sus detalles, solicita confirmacion, y lo crea tanto en el itinerario como en la vista de calendario (FullCalendar).

Actualmente, el modelo de datos solo soporta items de un solo dia (campo `day` como entero singular), y el chatbot no tiene logica para crear eventos de cronograma. Este requerimiento extiende ambas capacidades.

## Reglas de Negocio

- **RN-001**: El agente detecta la intencion de crear un evento de cronograma mediante keywords especificas: "cronograma", "calendario", "agregar al calendario", "crear evento", "bloque de viaje", "fechas del viaje al cronograma". En modo mock (sin LLM), la deteccion opera exclusivamente por pattern matching sobre estas keywords. En modo LLM, el modelo interpreta la intencion en lenguaje natural.

- **RN-002**: Se introduce un campo opcional `end_day: int | null` en el modelo de item de itinerario. Si `end_day` es `null` o no esta presente, el item se comporta como un item de un solo dia (comportamiento actual sin cambios). Si `end_day` tiene valor, el item abarca desde `day` hasta `end_day` (ambos inclusive).

- **RN-003**: Cuando el usuario solicita "agrega mi viaje al cronograma" (o expresion equivalente detectada por RN-001), el sistema crea un item con los siguientes valores: `day = 1`, `end_day = N` (donde N es el numero total de dias del viaje, calculado como `(end_date - start_date).days + 1`), `item_type = "extra"`, `name = "Viaje a {destino}"` (donde `{destino}` es el campo `destination` del viaje activo), `cost_estimated = 0`, `cost_real = 0`, `start_time = "00:00"`, `end_time = "23:59"`. Este item se considera un evento allDay (sin horario especifico).

- **RN-004**: Los items con `end_day` definido se renderizan en FullCalendar como eventos multi-dia. La conversion a evento de calendario utiliza la propiedad `allDay: true` y calcula `start` como la fecha correspondiente a `day` y `end` como la fecha correspondiente a `end_day + 1` (FullCalendar usa `end` exclusivo).

- **RN-005**: Los eventos multi-dia deben tener un color o estilo visual diferente a los items regulares de un solo dia para distinguirlos en el cronograma. **REQUIERE CLARIFICACION:** No se define la paleta de colores especifica ni el estilo visual diferenciador para los eventos multi-dia. Se necesita definir si se usa un color fijo, un patron visual (rayas, borde), o un mecanismo basado en el tipo de item.

- **RN-006**: Los items creados como eventos de cronograma con `cost_estimated = 0` y `cost_real = 0` no impactan el calculo de presupuesto. Esto es consistente con la regla existente de que solo los items con costo mayor a cero se contabilizan en el resumen financiero. **REQUIERE CLARIFICACION:** Se necesita definir si un evento de cronograma creado desde el chatbot puede tener un costo asociado (diferente de cero) o si siempre se crea con costo cero.

- **RN-007**: Antes de crear el evento, el chatbot presenta una tarjeta de confirmacion (tipo `"confirmation"`) con los detalles del evento propuesto: nombre, fechas de inicio y fin, duracion en dias, y tipo de item. El evento solo se crea si el usuario confirma explicitamente. Si el usuario cancela, no se realiza ninguna modificacion.

- **RN-008**: Items existentes que no tengan el campo `end_day` (o que lo tengan con valor `null`) continuan funcionando como items de un solo dia sin ningun cambio de comportamiento. La ausencia del campo `end_day` es funcionalmente equivalente a `end_day = null`.

## Criterios de Aceptacion

**CA-001:** Creacion de evento multi-dia del viaje completo
  **Dado** que el usuario tiene un viaje activo con destino "Tokio", `start_date = "2026-04-01"`, `end_date = "2026-04-10"` (10 dias), y el viaje esta en estado "en_planificacion" o "confirmado"
  **Cuando** escribe en el chat "agrega mi viaje al cronograma"
  **Entonces** el agente presenta una tarjeta de confirmacion con los detalles: nombre "Viaje a Tokio", fecha inicio "2026-04-01", fecha fin "2026-04-10", duracion "10 dias", tipo "extra". El usuario ve botones para Confirmar o Cancelar.

**CA-002:** Confirmacion y creacion efectiva del evento multi-dia
  **Dado** que el agente ha presentado la tarjeta de confirmacion del evento "Viaje a Tokio" (CA-001) y el usuario aun no ha respondido
  **Cuando** el usuario hace clic en "Confirmar"
  **Entonces** el sistema crea un nuevo item con `day = 1`, `end_day = 10`, `item_type = "extra"`, `name = "Viaje a Tokio"`, `cost_estimated = 0`, `cost_real = 0`, `status = "planificado"`, y lo persiste en la base de datos. El item aparece en el itinerario del viaje activo.

**CA-003:** Renderizado del evento multi-dia en FullCalendar
  **Dado** que existe un item con `day = 1`, `end_day = 10` en el viaje activo con `start_date = "2026-04-01"`
  **Cuando** el usuario accede a la seccion Cronograma / Calendario
  **Entonces** el calendario muestra un bloque visual que abarca desde el 1 de abril hasta el 10 de abril (inclusive), renderizado como evento allDay, visualmente distinto de los items regulares de un solo dia (actividades, traslados, comidas).

**CA-004:** Retrocompatibilidad de items existentes de un solo dia
  **Dado** que existen items de itinerario creados antes de esta funcionalidad, sin el campo `end_day` (o con `end_day = null`)
  **Cuando** el sistema renderiza estos items en el cronograma, itinerario detallado o presupuesto
  **Entonces** los items se comportan exactamente como antes: se muestran en un solo dia, se posicionan en su franja horaria correspondiente, y se contabilizan en el presupuesto segun su costo. No hay cambio de comportamiento ni de presentacion visual.

**CA-005:** Evento de cronograma no afecta el calculo de presupuesto
  **Dado** que se ha creado un evento multi-dia "Viaje a Tokio" con `cost_estimated = 0` y `cost_real = 0`
  **Cuando** el sistema calcula el resumen de presupuesto del viaje
  **Entonces** el evento no aparece en el desglose por categoria del presupuesto y no modifica el total estimado ni el total real. Los demas items del itinerario se contabilizan normalmente.

**CA-006:** Cancelacion de la creacion del evento
  **Dado** que el agente ha presentado la tarjeta de confirmacion del evento de cronograma
  **Cuando** el usuario hace clic en "Cancelar"
  **Entonces** el sistema no crea ningun item, el agente responde con un mensaje indicando que la operacion fue cancelada, y el itinerario permanece sin cambios.

**CA-007:** Deteccion de intencion en modo mock (sin LLM)
  **Dado** que la aplicacion esta operando en modo mock (sin `OPENAI_API_KEY` configurada) y el usuario tiene un viaje activo
  **Cuando** el usuario escribe en el chat un mensaje que contiene alguna de las keywords definidas en RN-001 (por ejemplo, "quiero agregar las fechas del viaje al cronograma")
  **Entonces** el agente detecta la intencion de crear un evento de cronograma y presenta la tarjeta de confirmacion con los detalles del evento propuesto, siguiendo el mismo flujo que en modo LLM.

**CA-008:** Viaje sin fechas definidas
  **Dado** que el usuario tiene un viaje activo pero las fechas de inicio (`start_date`) o fin (`end_date`) no estan definidas o estan vacias
  **Cuando** el usuario solicita al chatbot crear un evento de cronograma para el viaje
  **Entonces** el agente responde con un mensaje informativo indicando que no es posible crear el evento porque el viaje no tiene fechas definidas, y sugiere al usuario que primero defina las fechas del viaje. No se crea ningun item.

## Dependencias

- **REQ-CF-001** (Selector Obligatorio de Viaje): El usuario debe tener un viaje activo seleccionado para poder crear eventos de cronograma desde el chatbot.
- **REQ-UI-004** (Cronograma / Calendario): Vista donde se renderizan los eventos multi-dia. Este requerimiento extiende la capacidad de renderizado del cronograma para soportar items con `end_day`.
- **REQ-UI-003** (Chat - Acciones sobre Itinerario): Extiende las acciones disponibles desde el chat, agregando la creacion de eventos de cronograma al repertorio de acciones del agente.

## Notas

- **Extension del modelo de datos**: El campo `end_day` se agrega al modelo de item de itinerario (`models/itinerary_item.py`) y a la tabla `itinerary_items` en Supabase (ALTER TABLE para agregar columna `end_day INTEGER NULL`).
- **Servicios afectados**: `services/trip_service.py` debe soportar `end_day` en operaciones CRUD de items. `services/agent_service.py` requiere nueva logica de deteccion de intencion de cronograma. `services/budget_service.py` ya excluye items con costo cero, pero debe verificarse que no se vea afectado por items multi-dia.
- **Renderizado en FullCalendar**: `pages/3_Cronograma.py` debe extenderse para convertir items con `end_day` en eventos multi-dia de FullCalendar, usando `allDay: true` y calculando `end` como `start_date + end_day` (exclusivo en FullCalendar).
- **Vista fallback (sin streamlit-calendar)**: La funcion `_render_fallback_calendar` en `pages/3_Cronograma.py` debe considerar como representar un item multi-dia en la vista de tabs por dia. Una opcion es mostrar el item en cada tab de dia que abarca.
- **Prioridad de ruteo en agent_service**: La deteccion de intencion de cronograma debe integrarse en la cadena de prioridades existente del agente. Se sugiere ubicarla entre la deteccion de agregar/eliminar item y la busqueda de hoteles, pero la posicion final requiere analisis de implementacion.

---

**RESUMEN DE INFORMACION PENDIENTE**

1. **RN-005**: No se define la paleta de colores especifica ni el estilo visual diferenciador para los eventos multi-dia en el cronograma. Se necesita decidir si se usa un color fijo, un patron visual, o un mecanismo basado en tipo de item.
2. **RN-006**: No se define si un evento de cronograma creado desde el chatbot puede tener un costo asociado (diferente de cero) o si siempre se crea con costo cero.
