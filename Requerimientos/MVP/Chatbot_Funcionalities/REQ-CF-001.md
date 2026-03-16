# REQ-CF-001 — Selector Obligatorio de Viaje antes del Chat

## Codigo
REQ-CF-001

## Titulo
Selector Obligatorio de Viaje antes del Chat

## Prioridad MVP
Alta

## Historia de Usuario

**Como** viajero registrado,
**Quiero** seleccionar un viaje antes de iniciar una conversacion con el chatbot,
**Para** que el agente tenga un contexto claro y exclusivo sobre que viaje estoy planificando, evitando confusiones entre viajes.

## Descripcion

Al abrir la pagina de Chat, el usuario debe seleccionar explicitamente un viaje de su lista antes de poder enviar mensajes al agente. Sin una seleccion activa, el campo de texto permanece deshabilitado. Esto elimina la ambiguedad del comportamiento actual, donde el chat puede operar sin viaje asociado o con auto-deteccion implicita por destino mencionado en el mensaje (`_find_trip_by_destination` en `services/agent_service.py`). El selector muestra unicamente viajes en estados activos (`en_planificacion`, `confirmado`, `en_curso`) e incluye una opcion especial "Crear nuevo viaje" para usuarios que no tienen viajes o desean iniciar uno nuevo. La seleccion de viaje determina de forma exclusiva el contexto en el que opera el chatbot: todas las acciones, consultas y sugerencias se refieren al viaje seleccionado. Al cambiar la seleccion de viaje, el sistema carga automaticamente el ultimo chat asociado a ese viaje o crea uno nuevo si no existe ninguno.

Este requerimiento modifica el comportamiento actual donde `trip_id` es opcional en los chats y donde existe un fallback al viaje activo global (`st.session_state.active_trip_id`). Con este cambio, `trip_id` pasa a ser obligatorio en todos los chats (excepto durante el flujo de creacion de viaje nuevo, donde se asigna al completarse la creacion).

## Reglas de Negocio

- **RN-001**: Al abrir la pagina de Chat, el usuario DEBE seleccionar un viaje del selector antes de poder enviar mensajes. Sin seleccion, el campo de texto esta deshabilitado y no permite el envio de mensajes.
- **RN-002**: El selector de viaje solo muestra viajes en estados `en_planificacion`, `confirmado` o `en_curso`. Los viajes en estado `completado` o `cancelado` no aparecen en el selector.
- **RN-003**: Una vez seleccionado un viaje, el chatbot opera EXCLUSIVAMENTE sobre ese viaje. Si el usuario pregunta o solicita acciones sobre un viaje diferente al seleccionado, el agente debe responder indicando que cambie la seleccion de viaje en el selector para interactuar con ese otro viaje.
- **RN-004**: El selector debe incluir una opcion "Crear nuevo viaje" que inicia el flujo de creacion de viaje (definido en `trip_creation_flow.py`) sin requerir seleccion previa de un viaje existente. Durante el flujo de creacion, el chat opera sin `trip_id` asociado; el `trip_id` se asigna al chat al completarse exitosamente la creacion del viaje.
- **RN-005**: Se elimina la logica de auto-deteccion de viaje por destino mencionado en el mensaje (`_find_trip_by_destination` en `services/agent_service.py`), ya que el viaje siempre esta determinado por la seleccion explicita del usuario en el selector.
- **RN-006**: Al crear un nuevo chat, el campo `trip_id` es obligatorio (a excepcion del flujo de creacion de viaje nuevo descrito en RN-004). El fallback al viaje activo global (`st.session_state.active_trip_id`) como fuente implicita de `trip_id` se elimina.
- **RN-007**: Al cambiar el viaje seleccionado en el selector, el sistema carga automaticamente el ultimo chat asociado a ese viaje (ordenado por `last_activity_at` descendente). Si no existe ningun chat para el viaje seleccionado, el sistema crea un nuevo chat asociado a ese viaje automaticamente.
- **RN-008**: La seleccion de viaje activo en el selector se persiste en `session_state` para que no se pierda al navegar entre paginas de la aplicacion y volver a la pagina de Chat.

## Criterios de Aceptacion

**CA-001:** Selector visible y obligatorio al abrir el chat
  **Dado** que el usuario esta autenticado, tiene al menos un viaje en estado `en_planificacion`, `confirmado` o `en_curso`, y accede a la pagina de Chat sin haber seleccionado un viaje previamente
  **Cuando** se carga la pagina de Chat
  **Entonces** el sistema muestra un selector de viaje en la parte superior de la pagina con la lista de viajes disponibles (solo estados `en_planificacion`, `confirmado`, `en_curso`) y la opcion "Crear nuevo viaje". El campo de texto del chat esta deshabilitado y muestra un mensaje indicando que debe seleccionar un viaje para comenzar a chatear.

**CA-002:** Solo viajes activos en el selector
  **Dado** que el usuario tiene 5 viajes: 2 en estado `en_planificacion`, 1 `confirmado`, 1 `en_curso` y 1 `completado`
  **Cuando** se despliega el selector de viaje en la pagina de Chat
  **Entonces** el selector muestra unicamente los 4 viajes activos (2 `en_planificacion`, 1 `confirmado`, 1 `en_curso`) y la opcion "Crear nuevo viaje". El viaje `completado` no aparece en la lista.

**CA-003:** Opcion "Crear nuevo viaje" en el selector
  **Dado** que el usuario accede a la pagina de Chat y despliega el selector de viaje
  **Cuando** selecciona la opcion "Crear nuevo viaje"
  **Entonces** el campo de texto del chat se habilita, el sistema inicia el flujo de creacion de viaje, y el agente envía un mensaje de bienvenida invitando al usuario a indicar el destino deseado. El chat opera sin `trip_id` hasta que el viaje se cree exitosamente, momento en el cual se asigna el `trip_id` del nuevo viaje al chat.

**CA-004:** Al seleccionar viaje, se carga su ultimo chat o se crea uno nuevo
  **Dado** que el usuario selecciona el viaje "Tokio" en el selector, y tiene 2 chats previos asociados a ese viaje (Chat A con ultima actividad hace 3 dias, Chat B con ultima actividad hace 1 dia)
  **Cuando** se completa la seleccion del viaje
  **Entonces** el sistema carga automaticamente el Chat B (el mas reciente por `last_activity_at`), muestra su historial completo de mensajes, y el campo de texto del chat se habilita para continuar la conversacion.

**CA-005:** Seleccionar viaje sin chats previos
  **Dado** que el usuario selecciona el viaje "Barcelona" en el selector, y no tiene ningun chat previo asociado a ese viaje
  **Cuando** se completa la seleccion del viaje
  **Entonces** el sistema crea automaticamente un nuevo chat asociado al viaje "Barcelona", el campo de texto se habilita, y el agente muestra un mensaje de bienvenida con el contexto del viaje seleccionado (por ejemplo, "Estoy listo para ayudarte con tu viaje a Barcelona").

**CA-006:** Chatbot rechaza preguntas sobre otros viajes
  **Dado** que el usuario tiene el viaje "Tokio" seleccionado en el selector
  **Cuando** envia un mensaje preguntando sobre otro viaje (por ejemplo, "que hoteles tengo reservados en Barcelona?")
  **Entonces** el agente responde indicando que actualmente esta operando en el contexto del viaje a Tokio, y sugiere al usuario cambiar la seleccion en el selector si desea interactuar con el viaje a Barcelona. El agente NO proporciona informacion ni ejecuta acciones sobre el viaje a Barcelona.

**CA-007:** Cambio de seleccion de viaje
  **Dado** que el usuario tiene el viaje "Tokio" seleccionado con el Chat B activo, y cambia la seleccion al viaje "Lima"
  **Cuando** se completa el cambio de seleccion
  **Entonces** el sistema carga el ultimo chat asociado al viaje "Lima" (o crea uno nuevo si no existe), el historial mostrado corresponde al viaje "Lima", y el contexto del agente cambia al viaje "Lima". El Chat B del viaje "Tokio" se preserva y estara disponible al volver a seleccionar "Tokio".

**CA-008:** Seleccion persiste al navegar entre paginas
  **Dado** que el usuario tiene el viaje "Tokio" seleccionado en la pagina de Chat
  **Cuando** navega a la pagina de Itinerario y luego vuelve a la pagina de Chat
  **Entonces** el viaje "Tokio" sigue seleccionado en el selector, el Chat activo se mantiene, y el campo de texto esta habilitado sin requerir una nueva seleccion.

**CA-009:** Modo sin viajes — solo crear viaje nuevo disponible
  **Dado** que el usuario esta autenticado pero no tiene ningun viaje en estados `en_planificacion`, `confirmado` o `en_curso` (puede tener viajes `completado` o `cancelado`, o no tener ningun viaje)
  **Cuando** accede a la pagina de Chat
  **Entonces** el selector muestra unicamente la opcion "Crear nuevo viaje", el campo de texto esta deshabilitado, y se muestra un mensaje invitando al usuario a crear su primer viaje. Al seleccionar "Crear nuevo viaje", el campo de texto se habilita y se inicia el flujo de creacion.

## Dependencias

- REQ-CL-004 (Gestion de Conversaciones Multiples): Define la estructura multi-chat sobre la cual opera el selector. El selector determina que chat se carga al seleccionar un viaje.
- REQ-CL-005 (Contexto Aislado por Conversacion): El selector refuerza el aislamiento de contexto al hacer explicita la asociacion entre viaje y chat, eliminando fuentes implicitas de contexto.
- REQ-UI-002 (Chat con el Agente): Interfaz de chat que se modifica para incorporar el selector obligatorio y la deshabilitacion del campo de texto sin seleccion.
- REQ-UI-008 (Mis Viajes): Provee la lista de viajes del usuario y sus estados, que alimentan el selector de viaje en la pagina de Chat.

## Notas
- **Impacto en `pages/2_Chat.py`**: Agregar widget selector de viaje (por ejemplo, `st.selectbox`) en la parte superior de la pagina. Deshabilitar el campo de texto (`st.chat_input`) cuando no hay viaje seleccionado.
- **Impacto en `services/chat_service.py`**: El campo `trip_id` pasa a ser obligatorio al crear un chat (excepto flujo de creacion de viaje). Agregar logica para obtener el ultimo chat de un viaje por `last_activity_at`.
- **Impacto en `services/agent_service.py`**: Eliminar `_find_trip_by_destination` y toda logica de auto-deteccion de viaje por destino. Validar que `trip_id` siempre este presente antes de procesar un mensaje. Agregar respuesta de rechazo cuando el usuario pregunta sobre un viaje distinto al seleccionado.
- **Relacion con REQ-CL-004 RN-005**: Ese requerimiento establece que al crear un chat se asocia automaticamente al viaje activo. Con REQ-CF-001, la asociacion pasa a ser explicita via el selector (no via `active_trip_id` global), lo cual refuerza el aislamiento pero modifica el mecanismo de asociacion descrito en REQ-CL-004.
- **REQUIERE CLARIFICACION:** No se especifica el formato de visualizacion de los viajes en el selector (solo nombre del destino, o nombre + fechas + estado). Se recomienda incluir al menos destino y estado para facilitar la identificacion.
- **REQUIERE CLARIFICACION:** No se define el comportamiento si un viaje seleccionado transiciona a estado `completado` o `cancelado` mientras el usuario esta chateando (por ejemplo, por actualizacion automatica de estado por fecha). Se sugiere definir si el chat se mantiene activo o se fuerza una nueva seleccion.
