# REQ-CF-003 — Creacion de Items en el Itinerario desde el Chatbot con Extraccion Inteligente

## Codigo
REQ-CF-003

## Titulo
Creacion de Items en el Itinerario desde el Chatbot con Extraccion Inteligente de Datos

## Prioridad MVP
Alta

## Historia de Usuario

**Como** viajero registrado,
**Quiero** decirle al chatbot frases como "agregar ir al Cristo Redentor el martes 15 a las 10:00" y que extraiga automaticamente los datos,
**Para** agregar items a mi itinerario de forma rapida y natural sin rellenar formularios.

## Descripcion

Actualmente, cuando el usuario solicita agregar un item al itinerario desde el chat, el sistema detecta las palabras clave "agregar"/"anadir" mediante pattern matching simple (`services/agent_service.py`, metodo `_add_item_response`) y genera un item generico hardcodeado: `name="Nueva actividad"`, `day=1`, `start_time="10:00"`, `end_time="12:00"`, `item_type="actividad"`, `cost_estimated=25.0`, `location=` primera parte del destino del viaje. No se extraen datos del mensaje del usuario: ni nombre, ni fecha, ni hora, ni tipo, ni ubicacion.

Este requerimiento reemplaza ese comportamiento por un sistema de extraccion inteligente que analiza el mensaje del usuario en lenguaje natural y extrae automaticamente los datos estructurados necesarios para crear un item del itinerario: nombre de la actividad, fecha/dia, horario, tipo de item, ubicacion y costo. El sistema opera en dos modos: en modo LLM (cuando `OPENAI_API_KEY` esta disponible), la extraccion la realiza OpenAI mediante structured output; en modo mock (sin LLM), la extraccion se realiza mediante expresiones regulares y heuristicas de texto.

Si el mensaje del usuario no contiene suficiente informacion para crear el item, el agente inicia un flujo multi-turn haciendo preguntas de seguimiento para completar los datos faltantes, siguiendo un patron analogo al flujo de creacion de viajes existente (`services/trip_creation_flow.py`). Antes de crear el item, el agente presenta una tarjeta de confirmacion con todos los datos extraidos/inferidos para que el usuario los revise y confirme o cancele.

## Reglas de Negocio

- **RN-001**: **Extraccion de nombre.** Del mensaje del usuario se extrae la descripcion o nombre de la actividad. El agente puede reformular el texto para mayor claridad (ejemplo: "agregar ir al Cristo Redentor" se extrae como `name="Visita al Cristo Redentor"`). Si el mensaje contiene una intencion de agregar pero no incluye un nombre o descripcion identificable de la actividad, el agente debe preguntar explicitamente "Que actividad quieres agregar?".

- **RN-002**: **Extraccion de fecha y conversion a dia relativo.** Se extraen referencias temporales del mensaje del usuario y se convierten al campo `day` (entero 1-based relativo a `trip["start_date"]`). Formatos reconocidos:
  - Fechas absolutas con dia del mes: "el 15 de abril", "el martes 15", "el 20"
  - Referencias relativas: "manana", "pasado manana"
  - Dia relativo explicito: "el dia 3", "dia 5"
  - La conversion a `day` se calcula como: `day = (fecha_extraida - start_date).days + 1`.

- **RN-003**: **Validacion de rango de fechas del viaje.** Si la fecha extraida del mensaje cae fuera del rango del viaje (antes de `trip["start_date"]` o despues de `trip["end_date"]`), el agente informa al usuario indicando el rango valido del viaje (ejemplo: "Esa fecha esta fuera de tu viaje, que va del 10 al 20 de abril") y solicita que indique una fecha dentro del rango. El item NO se crea con una fecha fuera de rango.

- **RN-004**: **Extraccion de hora de inicio.** Se extraen horarios del mensaje del usuario. Formatos reconocidos:
  - Hora explicita: "a las 10:00", "a las 6:30", "10 de la manana"
  - Franja horaria generica: "por la manana" se convierte a `start_time="09:00"`, "al mediodia" a `start_time="12:00"`, "por la tarde" a `start_time="15:00"`, "por la noche" a `start_time="20:00"`.
  - Si no se especifica hora, el agente propone un horario por defecto segun el tipo de item: comida de tipo desayuno a las 08:00, almuerzo a las 12:30, cena a las 20:00; vuelo a las 08:00; actividad a las 10:00; traslado a las 09:00; alojamiento a las 15:00 (check-in).

- **RN-005**: **Inferencia de tipo de item (`item_type`).** El tipo se infiere automaticamente a partir de keywords presentes en el mensaje del usuario:
  - Keywords "restaurante", "cena", "almuerzo", "desayuno", "comer", "comida" → `item_type="comida"`
  - Keywords "hotel", "hospedaje", "airbnb", "hostel", "alojamiento" → `item_type="alojamiento"`
  - Keywords "vuelo", "avion", "aeropuerto", "volar" → `item_type="vuelo"`
  - Keywords "taxi", "uber", "bus", "traslado", "transfer", "metro", "tren" → `item_type="traslado"`
  - Keywords "extra", "seguro", "equipaje", "compras" → `item_type="extra"`
  - Si no se detecta ningun keyword especifico, el tipo por defecto es `item_type="actividad"`.

- **RN-006**: **Extraccion de ubicacion.** Si el mensaje menciona un lugar especifico (nombre de establecimiento, direccion, punto de interes), se extrae como campo `location` del item. Si no se menciona ubicacion, el campo queda vacio.

- **RN-007**: **Estimacion de costo.** **REQUIERE CLARIFICACION:** El usuario no ha definido si el agente debe estimar costos automaticamente basandose en el tipo de actividad y destino, o si solo debe registrar un costo cuando el usuario lo menciona explicitamente en su mensaje (ejemplo: "agregar cena por 50 dolares"). Se necesita definir: (a) si el agente estima costos cuando el usuario no los menciona, y en caso afirmativo, (b) las franjas de estimacion por tipo de item y destino, o si el costo por defecto es 0 cuando no se menciona.

- **RN-008**: **Datos minimos requeridos para crear un item.** Para que el agente pueda generar la tarjeta de confirmacion de creacion de un item, se requiere como minimo: `name` (nombre de la actividad) y `day` (dia del viaje). Si alguno de estos dos datos no puede extraerse del mensaje, el agente inicia un flujo multi-turn para solicitarlos.

- **RN-009**: **Flujo multi-turn para datos faltantes.** Cuando el mensaje del usuario no contiene suficiente informacion para los datos minimos (RN-008), el agente formula preguntas de seguimiento para completar los campos faltantes. El orden de prioridad de las preguntas es: (1) nombre de la actividad si no se pudo extraer, (2) dia del viaje si no se pudo extraer. Opcionalmente, si la hora no fue especificada, el agente puede proponerla junto con la confirmacion. El flujo multi-turn tiene un maximo de 3 turnos de preguntas; si despues de 3 turnos no se han completado los datos minimos, el agente cancela el flujo e informa al usuario que puede intentarlo nuevamente proporcionando mas detalle.

- **RN-010**: **Confirmacion obligatoria con tarjeta rica.** Antes de crear el item en el itinerario, el agente presenta una tarjeta de confirmacion (mensaje tipo `"confirmation"` con `action: "add_item"`) que muestra todos los datos extraidos e inferidos: nombre, dia (con fecha absoluta), hora de inicio, tipo de item, ubicacion (si se extrajo) y costo (si aplica). El usuario debe confirmar para que el item se cree, o cancelar para abortar la operacion.

- **RN-011**: **Deteccion de conflictos horarios.** Antes de presentar la tarjeta de confirmacion, el agente verifica si existe otro item ya registrado en el mismo dia y en un horario que se solape con el item propuesto (comparando `start_time` y `end_time`). Si detecta un conflicto, lo informa al usuario (ejemplo: "Ya tienes 'Visita al museo' de 10:00 a 12:00 ese dia") y permite que el usuario decida si desea continuar con la creacion a pesar del conflicto o si prefiere ajustar el horario.

- **RN-012**: **Dual-mode: LLM y mock.** La extraccion de datos funciona en ambos modos del chatbot:
  - **Modo LLM** (cuando `OPENAI_API_KEY` esta disponible): La extraccion se delega a OpenAI mediante structured output, que analiza el mensaje en lenguaje natural y retorna los campos estructurados (name, day, start_time, item_type, location, cost).
  - **Modo mock** (sin `OPENAI_API_KEY`): La extraccion se realiza mediante expresiones regulares y heuristicas de texto (patrones de fecha, hora, keywords de tipo de item) siguiendo las mismas reglas de RN-001 a RN-006.
  - En ambos modos, los datos extraidos pasan por la misma validacion (rango de fechas, datos minimos, conflictos horarios) y se presentan con la misma tarjeta de confirmacion.

## Criterios de Aceptacion

**CA-001:** Extraccion completa de datos desde mensaje con informacion suficiente
  **Dado** que el usuario tiene un viaje activo seleccionado a "Rio de Janeiro" con `start_date="2026-04-10"` y `end_date="2026-04-20"`, y el itinerario no tiene items el dia 6
  **Cuando** el usuario envia el mensaje "agregar ir al Cristo Redentor el 15 de abril a las 10:00"
  **Entonces** el agente extrae: `name="Visita al Cristo Redentor"`, `day=6` (15 abril - 10 abril + 1 = 6), `start_time="10:00"`, `item_type="actividad"` (inferido por defecto), `location="Cristo Redentor"`, y presenta una tarjeta de confirmacion mostrando todos estos datos. Al confirmar, el item se crea en el itinerario con esos valores.

**CA-002:** Flujo multi-turn cuando falta la fecha
  **Dado** que el usuario tiene un viaje activo seleccionado y envia el mensaje "agregar cena en restaurante japones"
  **Cuando** el agente analiza el mensaje y detecta que no hay fecha ni dia especificado
  **Entonces** el agente extrae los datos disponibles (`name="Cena en restaurante japones"`, `item_type="comida"`) y pregunta al usuario "Que dia de tu viaje quieres programar esta cena?". Tras recibir respuesta con el dia, el agente presenta la tarjeta de confirmacion con todos los datos completos (incluyendo `start_time="20:00"` por defecto para cena segun RN-004).

**CA-003:** Inferencia de tipo de item por keywords
  **Dado** que el usuario tiene un viaje activo seleccionado
  **Cuando** envia el mensaje "anadir vuelo a las 6:30"
  **Entonces** el agente infiere `item_type="vuelo"` por la keyword "vuelo" y extrae `start_time="06:30"`. Como falta el dia, el agente pregunta "Que dia de tu viaje es el vuelo?". Tras recibir la respuesta, presenta la tarjeta de confirmacion con tipo "vuelo" y hora 06:30.

**CA-004:** Fecha fuera del rango del viaje
  **Dado** que el usuario tiene un viaje activo con `start_date="2026-04-10"` y `end_date="2026-04-20"`
  **Cuando** envia el mensaje "agregar visita al museo el 25 de abril a las 14:00"
  **Entonces** el agente detecta que el 25 de abril esta fuera del rango del viaje y responde: "Esa fecha esta fuera de tu viaje, que va del 10 al 20 de abril. Indica una fecha dentro de ese rango." El item NO se crea y el agente espera una nueva fecha valida del usuario.

**CA-005:** Deteccion de conflicto horario
  **Dado** que el usuario tiene un viaje activo y el dia 3 del viaje ya tiene un item "Visita al museo" con `start_time="10:00"` y `end_time="12:00"`
  **Cuando** envia el mensaje "agregar tour por la ciudad el dia 3 a las 10:30"
  **Entonces** el agente detecta la superposicion horaria y responde informando: "Ya tienes 'Visita al museo' de 10:00 a 12:00 ese dia. Deseas agregarlo de todas formas o prefieres cambiar el horario?" El agente espera la decision del usuario antes de proceder.

**CA-006:** Confirmacion exitosa — item creado y visible en itinerario y cronograma
  **Dado** que el agente presenta una tarjeta de confirmacion con los datos extraidos de un item (name, day, start_time, item_type, location)
  **Cuando** el usuario hace clic en el boton "Confirmar" de la tarjeta
  **Entonces** el item se crea en el itinerario del viaje activo con todos los datos de la tarjeta, el item aparece en la pagina de Itinerario Detallado (REQ-UI-005) en la posicion cronologica correspondiente a su dia y hora, y aparece en el Cronograma/Calendario (REQ-UI-004) como un bloque en la fecha y hora asignada. El presupuesto (REQ-UI-006) se recalcula si el item tiene costo asociado.

**CA-007:** Cancelacion de confirmacion — item no se crea
  **Dado** que el agente presenta una tarjeta de confirmacion con los datos extraidos de un item
  **Cuando** el usuario hace clic en el boton "Cancelar" de la tarjeta
  **Entonces** el item NO se crea en el itinerario, la tarjeta de confirmacion se marca como procesada (`msg["processed"] = True`), y el agente responde con un mensaje indicando que la operacion fue cancelada (ejemplo: "Operacion cancelada. Si quieres agregar algo, indicamelo.").

**CA-008:** Modo mock extrae datos basicos por regex
  **Dado** que el sistema esta operando sin `OPENAI_API_KEY` (modo mock) y el usuario tiene un viaje activo con `start_date="2026-04-10"`
  **Cuando** el usuario envia el mensaje "agregar visita a la torre Eiffel el 12 de abril a las 14:00"
  **Entonces** el modo mock extrae mediante regex: `day=3` (12 abril - 10 abril + 1), `start_time="14:00"`, `item_type="actividad"` (defecto), y el nombre "visita a la torre Eiffel" del texto. El agente presenta la misma tarjeta de confirmacion que en modo LLM con los datos extraidos.

**CA-009:** Extraccion con franja horaria generica
  **Dado** que el usuario tiene un viaje activo seleccionado
  **Cuando** envia el mensaje "agregar algo por la manana el dia 3"
  **Entonces** el agente extrae `start_time="09:00"` (segun RN-004, "por la manana" = 09:00) y `day=3`. Como falta un nombre descriptivo, el agente pregunta "Que actividad quieres agregar por la manana del dia 3?". Tras la respuesta del usuario, presenta la tarjeta de confirmacion con todos los datos completos.

**CA-010:** Maximo de turnos en flujo multi-turn alcanzado
  **Dado** que el agente ha realizado 3 preguntas de seguimiento al usuario para completar los datos de un item y el usuario no ha proporcionado la informacion minima requerida (name y day)
  **Cuando** el agente alcanza el limite de 3 turnos de preguntas
  **Entonces** el agente cancela el flujo de creacion e informa al usuario: "No pude obtener los datos suficientes para crear el item. Puedes intentarlo nuevamente indicando al menos el nombre de la actividad y el dia." El estado del flujo se reinicia.

## Dependencias

- **REQ-CF-001** (Selector Obligatorio de Viaje antes del Chat): El viaje debe estar seleccionado para que el agente tenga contexto de fechas (`start_date`, `end_date`), destino y items existentes del viaje. Sin viaje seleccionado, el agente no puede procesar solicitudes de agregar items.
- **REQ-UI-003** (Chat - Acciones sobre Itinerario): Define la mecanica general de acciones sobre el itinerario desde el chat (confirmacion, creacion, eliminacion). REQ-CF-003 extiende y reemplaza el comportamiento basico de agregar items con extraccion inteligente.
- **REQ-UI-005** (Itinerario Detallado): Pagina donde se renderizan los items creados. Los items creados via extraccion inteligente deben aparecer correctamente en esta vista.
- **REQ-UI-004** (Cronograma/Calendario): Los items creados tambien deben aparecer como bloques en la vista de calendario.
- **REQ-UI-006** (Presupuesto): Si el item tiene costo asociado, debe reflejarse en el calculo de presupuesto (solo items no sugeridos, segun RN-002 de REQ-UI-006).

## Notas

- **Impacto en `services/agent_service.py`**: El metodo `_add_item_response` (lineas 298-315) actualmente retorna un item generico hardcodeado. Debe reescribirse para invocar la logica de extraccion inteligente antes de generar la tarjeta de confirmacion. La deteccion de keywords de agregar (linea 113: "agregar", "anadir", "agrega", "anade") se mantiene como punto de entrada pero la respuesta pasa a depender de los datos extraidos.
- **Posible nuevo modulo `services/item_extraction.py`**: Para encapsular la logica de extraccion (regex para modo mock, structured output para modo LLM), validacion de rango de fechas, deteccion de conflictos horarios y manejo del flujo multi-turn. Seguiria el patron de `services/trip_creation_flow.py` (logica pura sin Streamlit, solo re y datetime).
- **Patron de referencia `services/trip_creation_flow.py`**: Este modulo implementa deteccion de intencion con strong/weak keywords, extraccion de datos con regex (destino, fechas, meses en espanol) y flujo multi-turn con estado. La extraccion inteligente de items puede reutilizar patrones similares: mapeo de meses en espanol (`_MESES`), regex de fechas, keywords de cancelacion, y la estructura de estado del flujo.
- **Impacto en `services/llm_chatbot.py`**: En modo LLM, se puede agregar una tool/function al pipeline de LangGraph para extraccion estructurada de datos del item, o manejar la extraccion como un paso de pre-procesamiento antes de invocar al LLM.
- **Modelo de datos de items**: Los items son dicts con campos: `id` (item-{hex8}), `trip_id`, `name`, `item_type` (actividad/traslado/alojamiento/comida/vuelo/extra), `day` (int 1-based), `start_time`/`end_time` ("HH:MM"), `status` (planificado/confirmado/sugerido/completado/cancelado), `cost` (float), `location`, `notes`, `details` (strings opcionales). Los items creados via extraccion inteligente deben ajustarse a esta estructura exacta.
- **Duraciones por defecto para `end_time`**: Cuando el usuario no especifica hora de fin, el agente calcula `end_time` sumando una duracion por defecto segun el tipo de item: actividad = 2 horas, comida = 1.5 horas, vuelo = 3 horas, traslado = 1 hora, alojamiento = 0 (solo check-in, sin end_time), extra = 1 hora. Esto permite la deteccion de conflictos horarios (RN-011). Si el usuario especifica end_time explicitamente, se usa el valor dado.
- **REQUIERE CLARIFICACION:** No se define si el `status` de los items creados via extraccion inteligente desde el chat es `"planificado"` (como item aceptado directamente por el usuario) o `"sugerido"` (como propuesta del agente). Dado que el usuario esta solicitando explicitamente agregar el item y lo confirma con la tarjeta, el estado logico seria `"planificado"`, pero esto requiere confirmacion.
