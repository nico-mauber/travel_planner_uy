# REQ-CL-004 — Gestion de Conversaciones Multiples en el Chatbot

## Codigo
REQ-CL-004

## Titulo
Gestion de Conversaciones Multiples en el Chatbot

## Prioridad MVP
Alta

## Historia de Usuario

**Como** usuario autenticado de Trip Planner,
**Quiero** crear nuevas conversaciones de chat y ver el historial de conversaciones anteriores,
**Para** organizar mis consultas al agente por temas o viajes y poder retomar conversaciones previas.

## Descripcion

El chatbot debe soportar multiples conversaciones (chats) por usuario. El usuario puede crear un nuevo chat, ver una lista de sus chats anteriores, seleccionar un chat para retomarlo, y eliminar chats que ya no necesite. Cada chat tiene un titulo (generado automaticamente o definido por el usuario), una fecha de creacion, y opcionalmente una asociacion a un viaje activo.

Actualmente el sistema mantiene un unico historial por viaje en `chat_histories[trip_id]` (`pages/2_Chat.py` linea 32-55). Este requerimiento extiende el modelo para soportar multiples chats independientes por usuario, ya no indexados unicamente por `trip_id`.

## Reglas de Negocio

- **RN-001**: Cada usuario puede tener multiples conversaciones de chat. No hay limite maximo en el MVP.
- **RN-002**: Cada conversacion de chat tiene un identificador unico con formato `chat-{hex8}`, un titulo, una fecha de creacion (`created_at`), una fecha de ultima actividad (`last_activity_at`), el `user_id` del propietario, y opcionalmente un `trip_id` asociado.
- **RN-003**: Al crear un nuevo chat, el sistema genera un titulo automatico basado en el primer mensaje del usuario (por ejemplo, los primeros 50 caracteres) o un titulo por defecto "Nuevo chat — {fecha}". El usuario puede renombrar el chat posteriormente.
- **RN-004**: La lista de chats se muestra ordenada por `last_activity_at` descendente (el mas reciente primero).
- **RN-005**: Si el usuario tiene un viaje activo al crear un nuevo chat, el chat se asocia automaticamente a ese viaje. El usuario puede crear chats sin viaje activo (para consultas generales o para crear un nuevo viaje desde el chat).
- **RN-006**: Al seleccionar un chat de la lista, se carga su historial completo de mensajes y se retoma la conversacion desde donde se dejo.
- **RN-007**: El usuario puede eliminar un chat. La eliminacion es logica (se marca como eliminado) o fisica. En el MVP se permite eliminacion fisica por simplicidad.
- **RN-008**: Cada chat que interactua con el LLM tiene su propio `thread_id` para LangGraph, asegurando que los checkpoints de conversacion sean independientes.

## Criterios de Aceptacion

**CA-001:** Visualizacion de la lista de chats
  **Dado** que el usuario esta autenticado y tiene 3 conversaciones de chat previas
  **Cuando** accede a la seccion de Chat
  **Entonces** el sistema muestra una lista lateral o superior con las 3 conversaciones, cada una con su titulo y fecha de ultima actividad, ordenadas de la mas reciente a la mas antigua.

**CA-002:** Crear nueva conversacion
  **Dado** que el usuario esta en la seccion de Chat
  **Cuando** hace clic en el boton "Nuevo chat" (o equivalente)
  **Entonces** el sistema crea una nueva conversacion con un titulo por defecto, la selecciona como chat activo, muestra el area de chat vacia con un mensaje de bienvenida del agente, y el campo de entrada esta listo para recibir el primer mensaje.

**CA-003:** Titulo automatico del chat
  **Dado** que el usuario crea un nuevo chat y envia su primer mensaje (por ejemplo, "Quiero planificar un viaje a Roma")
  **Cuando** el sistema procesa el primer mensaje
  **Entonces** el titulo del chat se actualiza automaticamente a un resumen del primer mensaje (por ejemplo, "Viaje a Roma") y se refleja en la lista de chats.

**CA-004:** Seleccionar chat existente
  **Dado** que el usuario tiene multiples chats y uno de ellos tiene un historial de 10 mensajes
  **Cuando** selecciona ese chat de la lista
  **Entonces** el sistema carga el historial completo de los 10 mensajes en el area de chat, con scroll posicionado en el ultimo mensaje, y el campo de entrada esta listo para continuar la conversacion.

**CA-005:** Eliminar un chat
  **Dado** que el usuario tiene un chat que ya no necesita
  **Cuando** hace clic en la opcion de eliminar el chat (icono de papelera o menu contextual)
  **Entonces** el sistema solicita confirmacion ("Eliminar esta conversacion?"), y si el usuario confirma, elimina el chat de la lista y sus mensajes. Si el chat eliminado era el activo, se selecciona el chat mas reciente o se muestra un estado vacio.

**CA-006:** Chat sin conversaciones previas
  **Dado** que un nuevo usuario accede por primera vez a la seccion de Chat
  **Cuando** se carga la pagina
  **Entonces** el sistema muestra un estado vacio con un mensaje invitando a iniciar su primera conversacion y un boton "Nuevo chat" claramente visible.

**CA-007:** Asociacion automatica con viaje activo
  **Dado** que el usuario tiene un viaje activo (por ejemplo, "Viaje a Tokio")
  **Cuando** crea un nuevo chat
  **Entonces** el chat se asocia automaticamente al viaje activo, y el agente tiene contexto del viaje ("Estoy listo para ayudarte con tu viaje a Tokio").

**CA-008:** Chat sin viaje activo
  **Dado** que el usuario no tiene ningun viaje activo
  **Cuando** crea un nuevo chat
  **Entonces** el chat se crea sin asociacion a viaje, y el agente invita al usuario a indicar a donde quiere viajar, consistente con el comportamiento actual del mock (`agent_service.py` linea 79-88).

**CA-009:** Persistencia de la lista de chats
  **Dado** que el usuario tiene multiples chats creados
  **Cuando** cierra la aplicacion y vuelve a abrirla (con sesion activa)
  **Entonces** la lista de chats se mantiene intacta con todos los chats previamente creados, sus titulos, y sus historiales de mensajes.

**CA-010:** Renombrar un chat
  **Dado** que el usuario quiere cambiar el titulo de un chat existente
  **Cuando** hace doble clic en el titulo del chat en la lista (o accede a una opcion de "Renombrar")
  **Entonces** puede editar el titulo, y el nuevo titulo se guarda y se muestra en la lista.

**CA-011:** Indicador de chat activo
  **Dado** que el usuario tiene multiples chats en la lista
  **Cuando** selecciona uno de ellos
  **Entonces** el chat seleccionado se muestra visualmente diferenciado (resaltado, borde, fondo diferente) para indicar que es el chat activo.

## Dependencias

- REQ-CL-001 (Login con Google OAuth): Provee el `user_id` para asociar chats al usuario.
- REQ-CL-003 (Aislamiento de Datos): Los chats solo son visibles para su propietario.
- REQ-CL-005 (Contexto Aislado por Chat): Cada chat de esta lista tiene su propio contexto.
- REQ-UI-002 (Chat con el Agente): Este requerimiento extiende la interfaz de chat existente para soportar multiples conversaciones.

## Notas
- La estructura actual de `chat_histories` en `session_state` (diccionario indexado por `trip_id`) debe migrarse a un modelo donde cada chat es un objeto con metadatos propios. Estructura propuesta: `{ "chat_id": "chat-abc123", "user_id": "user-xyz", "trip_id": "trip-123" | null, "title": "...", "created_at": "...", "last_activity_at": "...", "messages": [...] }`.
- La persistencia de chats puede implementarse en un archivo JSON (`data/chats.json` o `data/users/{user_id}/chats.json`), consistente con el patron de persistencia del proyecto.
- La lista de chats podria integrarse en el sidebar de Streamlit (debajo del viaje activo y del boton "Abrir Chat" existente en `app.py` linea 133) o como un panel lateral dentro de la pagina de Chat.
- Para el MVP, la generacion automatica del titulo puede ser simplemente los primeros N caracteres del primer mensaje. Con LLM disponible, se podria generar un titulo mas inteligente usando el modelo.
