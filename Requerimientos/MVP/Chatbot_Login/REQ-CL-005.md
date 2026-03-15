# REQ-CL-005 — Contexto Aislado por Conversacion de Chat

## Codigo
REQ-CL-005

## Titulo
Contexto Aislado por Conversacion de Chat

## Prioridad MVP
Alta

## Historia de Usuario

**Como** usuario autenticado de Trip Planner,
**Quiero** que cada conversacion de chat mantenga su propio contexto independiente,
**Para** que al retomar una conversacion anterior, el agente recuerde lo que hablamos en esa conversacion sin mezclar informacion de otros chats.

## Descripcion

Cada conversacion de chat (REQ-CL-004) debe mantener su propio contexto conversacional aislado. Esto significa que el historial de mensajes, los checkpoints de LangGraph, y el contexto del viaje asociado son independientes para cada chat. Al retomar una conversacion, el agente tiene acceso al historial completo de esa conversacion y puede continuar donde se dejo, sin contaminacion de contexto de otras conversaciones.

Actualmente, el pipeline LangGraph en `llm_chatbot.py` usa `thread_id = f"trip_chat_{chat_id}"` (linea 176) donde `chat_id` es el `trip_id` del viaje activo. Esto ya provee aislamiento por viaje, pero no soporta multiples conversaciones dentro del mismo viaje. Este requerimiento extiende el modelo para que cada chat (no cada viaje) tenga su propio `thread_id`.

## Reglas de Negocio

- **RN-001**: Cada conversacion de chat tiene su propio `thread_id` para LangGraph, con formato `trip_chat_{user_id}_{chat_id}`. Esto garantiza aislamiento de checkpoints entre conversaciones y entre usuarios.
- **RN-002**: El historial de mensajes de cada chat se almacena de forma independiente. Al cargar un chat, solo se muestran los mensajes de esa conversacion.
- **RN-003**: Las memorias vectoriales (ChromaDB) son compartidas a nivel de usuario, no aisladas por chat. Esto permite que el agente recuerde preferencias del usuario (por ejemplo, "prefiere hoteles boutique") en todas las conversaciones, enriqueciendo la experiencia. Las memorias se filtran por `user_id` (REQ-CL-003 RN-004), no por `chat_id`.
- **RN-004**: Si un chat tiene un viaje asociado (`trip_id`), el agente utiliza el contexto actual de ese viaje (destino, fechas, presupuesto, items) en sus respuestas. Si el viaje es modificado desde otra conversacion o seccion, el agente refleja los datos actualizados.
- **RN-005**: Las acciones confirmadas (agregar item, eliminar item, crear viaje) se aplican sobre el viaje asociado al chat. Si el chat no tiene viaje asociado, solo se permite la accion de crear viaje.
- **RN-006**: Al trimear mensajes para respetar el limite de tokens del LLM (`message_trimmer` en `llm_chatbot.py` linea 58-64), se aplica sobre el historial del chat individual, no sobre un historial global.
- **RN-007**: Las confirmaciones pendientes (`type: "confirmation"` con `processed: false`) son especificas de cada chat. Una confirmacion pendiente en el chat A no aparece en el chat B.

## Criterios de Aceptacion

**CA-001:** Contexto independiente entre conversaciones
  **Dado** que el usuario tiene dos chats: Chat A (sobre un viaje a Roma) y Chat B (sobre un viaje a Tokio)
  **Cuando** interactua en el Chat A y dice "agrega un tour por el Coliseo"
  **Entonces** la sugerencia del agente se refiere al viaje a Roma (contexto del Chat A), no al viaje a Tokio.

**CA-002:** Retomar conversacion con historial intacto
  **Dado** que el usuario tuvo una conversacion de 15 mensajes en el Chat A hace 3 dias
  **Cuando** selecciona el Chat A desde la lista de chats
  **Entonces** se cargan los 15 mensajes completos en orden cronologico, y el agente puede referenciar informacion mencionada anteriormente en esa conversacion (por ejemplo, si el usuario dijo "mi presupuesto es de 2000 USD", el agente lo recuerda en el contexto de ese chat).

**CA-003:** Sin contaminacion de contexto entre chats
  **Dado** que en el Chat A el usuario dijo "quiero hoteles de lujo" y en el Chat B dijo "busco hosteles economicos"
  **Cuando** el agente responde en cada chat
  **Entonces** en el Chat A sugiere opciones de lujo y en el Chat B sugiere opciones economicas, sin mezclar contextos conversacionales.

**CA-004:** Memorias vectoriales compartidas entre chats
  **Dado** que en el Chat A el usuario dijo "soy vegetariano" y el sistema extrajo esta memoria
  **Cuando** el usuario crea el Chat B y pregunta sobre restaurantes
  **Entonces** el agente en el Chat B tiene acceso a la memoria "soy vegetariano" (porque las memorias vectoriales son por usuario, no por chat) y sugiere opciones vegetarianas.

**CA-005:** Confirmaciones aisladas por chat
  **Dado** que en el Chat A el agente propuso una confirmacion "Agregar Hotel Boutique Roma al itinerario" que el usuario aun no confirmo ni cancelo
  **Cuando** el usuario cambia al Chat B
  **Entonces** la confirmacion pendiente del Chat A no aparece en el Chat B. Al volver al Chat A, la confirmacion sigue disponible para ser procesada.

**CA-006:** Contexto del viaje actualizado en tiempo real
  **Dado** que el Chat A esta asociado al viaje "Roma" y desde la seccion de Itinerario se agrego un item "Visita al Vaticano"
  **Cuando** el usuario retoma el Chat A y pregunta "que tengo planeado?"
  **Entonces** el agente incluye "Visita al Vaticano" en su respuesta, porque lee el estado actual del viaje (no una copia estatica del momento en que se creo el chat).

**CA-007:** Chat nuevo sin historial del LLM
  **Dado** que el usuario crea un nuevo Chat C
  **Cuando** envia su primer mensaje
  **Entonces** el pipeline de LangGraph comienza con un `thread_id` nuevo y sin checkpoints previos. El agente no tiene contexto de conversaciones anteriores (excepto memorias vectoriales del usuario, que si se inyectan).

**CA-008:** Multiples chats para el mismo viaje
  **Dado** que el usuario tiene un viaje activo "Roma" y ya tiene el Chat A asociado a ese viaje
  **Cuando** crea un nuevo Chat D (tambien asociado al viaje "Roma")
  **Entonces** el Chat D tiene su propio contexto conversacional independiente del Chat A, aunque ambos estan asociados al mismo viaje. Las acciones confirmadas en cualquiera de los dos afectan al mismo viaje.

**CA-009:** Modo mock con contexto aislado
  **Dado** que el LLM no esta disponible (no hay `GOOGLE_API_KEY`) y el sistema usa el fallback mock
  **Cuando** el usuario interactua en diferentes chats
  **Entonces** cada chat mantiene su historial de mensajes independiente, y las respuestas del mock se basan en el viaje asociado a ese chat, no a otro.

## Dependencias

- REQ-CL-003 (Aislamiento de Datos por Usuario): Provee el aislamiento a nivel de usuario; este requerimiento agrega aislamiento a nivel de chat.
- REQ-CL-004 (Gestion de Conversaciones Multiples): Define la estructura de chats multiples sobre la cual opera este requerimiento.
- REQ-UI-002 (Chat con el Agente): Interfaz de chat existente que soporta el rendering de mensajes, tarjetas y confirmaciones.
- REQ-UI-003 (Chat - Acciones sobre Itinerario): Las acciones confirmadas en un chat se aplican sobre el viaje asociado.

## Notas
- La clave del aislamiento de contexto conversacional es el `thread_id` de LangGraph. Actualmente en `llm_chatbot.py` linea 176 se usa `trip_chat_{chat_id}`. El cambio a `trip_chat_{user_id}_{chat_id}` garantiza unicidad entre usuarios y entre chats.
- Las memorias vectoriales se comparten a nivel de usuario deliberadamente. Esto es una decision de diseno: las preferencias y hechos personales del usuario deben enriquecer todas sus conversaciones. Solo el contexto conversacional (historial de mensajes) es aislado por chat.
- El `message_trimmer` en `llm_chatbot.py` (linea 58-64) con `max_tokens=4000` ya opera sobre los mensajes del thread individual gracias al checkpoint de LangGraph, por lo que no requiere cambios funcionales.
- Para el modo mock (sin LLM), el aislamiento es automatico ya que el mock no mantiene estado entre invocaciones (`agent_service.py` procesa cada mensaje individualmente). El historial se mantiene en la lista de mensajes del chat.
