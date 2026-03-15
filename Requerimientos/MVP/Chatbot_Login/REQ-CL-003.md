# REQ-CL-003 — Aislamiento de Datos del Chatbot por Usuario

## Codigo
REQ-CL-003

## Titulo
Aislamiento de Datos del Chatbot por Usuario

## Prioridad MVP
Alta

## Historia de Usuario

**Como** usuario autenticado de Trip Planner,
**Quiero** que mis viajes, chats y memorias del chatbot sean visibles unicamente para mi,
**Para** tener privacidad sobre mi informacion de viajes y que el agente no mezcle mis datos con los de otros usuarios.

## Descripcion

Con la introduccion de autenticacion multiusuario (REQ-CL-001), todos los datos del sistema deben asociarse al `user_id` del usuario autenticado. Esto incluye: viajes (`trips`), historiales de chat (`chat_histories`), memorias vectoriales de ChromaDB, checkpoints de LangGraph, y perfil del usuario (`user_profile`). Cada usuario solo debe ver y acceder a sus propios datos. El agente (LLM y mock) solo debe operar sobre datos del usuario logueado.

Actualmente la aplicacion es single-user: `trips.json` almacena todos los viajes sin distincion de usuario, `chat_histories` en `session_state` se indexa por `trip_id`, y ChromaDB tiene una unica coleccion `trip_planner_memories` sin filtro de usuario (`memory_manager.py` linea 51-54).

## Reglas de Negocio

- **RN-001**: Cada viaje (`trip`) debe tener un campo `user_id` que identifica al usuario propietario. Solo el propietario puede ver, editar o eliminar sus viajes.
- **RN-002**: Al cargar viajes al iniciar sesion, el sistema debe filtrar por `user_id` del usuario autenticado. Ningun viaje de otro usuario debe aparecer en `session_state.trips`.
- **RN-003**: Los historiales de chat (`chat_histories`) deben asociarse al `user_id`. Un usuario no puede ver ni acceder a conversaciones de otro usuario.
- **RN-004**: Las memorias vectoriales en ChromaDB deben almacenarse con metadata `user_id`. Las busquedas semanticas (`search_vector_memory`) deben filtrar por `user_id` del usuario autenticado.
- **RN-005**: Los checkpoints de LangGraph deben usar `thread_id` que incluya el `user_id` para evitar colisiones. Formato: `trip_chat_{user_id}_{chat_id}` (actualmente `trip_chat_{chat_id}` en `llm_chatbot.py` linea 176).
- **RN-006**: El perfil del usuario (`user_profile`, persistido en `data/profiles.json`) debe asociarse al `user_id`. Cada usuario tiene su propio perfil de preferencias.
- **RN-007**: Los datos de ejemplo (`sample_data.py`) se cargan unicamente la primera vez que un nuevo usuario accede, asociados a su `user_id`. No se comparten entre usuarios.
- **RN-008**: La persistencia en JSON (`trips.json`, `profiles.json`) debe soportar multiples usuarios. Se puede usar un unico archivo con filtrado por `user_id`, o archivos separados por usuario (`data/users/{user_id}/trips.json`).

## Criterios de Aceptacion

**CA-001:** Viajes filtrados por usuario
  **Dado** que el usuario A esta autenticado y tiene 2 viajes, y el usuario B tiene 3 viajes en el sistema
  **Cuando** el usuario A accede al Dashboard o a "Mis Viajes"
  **Entonces** el sistema muestra unicamente los 2 viajes del usuario A; los viajes del usuario B no son visibles.

**CA-002:** Chat filtrado por usuario
  **Dado** que el usuario A tiene conversaciones de chat asociadas a sus viajes
  **Cuando** el usuario B accede al Chat
  **Entonces** el usuario B no puede ver ni acceder a las conversaciones del usuario A. Solo ve sus propias conversaciones o un chat vacio si no tiene historial.

**CA-003:** Creacion de viaje asociada al usuario
  **Dado** que el usuario esta autenticado con `user_id = "user-abc123"`
  **Cuando** crea un nuevo viaje (desde "Mis Viajes" o desde el chat)
  **Entonces** el viaje creado contiene el campo `user_id: "user-abc123"` y solo es visible para ese usuario.

**CA-004:** Memorias vectoriales aisladas por usuario
  **Dado** que el usuario A ha interactuado con el chatbot y se han extraido memorias ("prefiere hoteles boutique")
  **Cuando** el usuario B interactua con el chatbot y el sistema busca memorias relevantes
  **Entonces** las memorias del usuario A no aparecen en los resultados de busqueda del usuario B. Cada usuario tiene su propio espacio de memorias.

**CA-005:** Contexto del LLM aislado por usuario
  **Dado** que el usuario A ha tenido una conversacion extensa con el agente sobre un viaje a Tokio
  **Cuando** el usuario B inicia una nueva conversacion con el agente
  **Entonces** el agente no tiene contexto de las conversaciones del usuario A; responde al usuario B como si fuera una interaccion nueva.

**CA-006:** Perfil de preferencias aislado por usuario
  **Dado** que el usuario A ha configurado preferencias (presupuesto alto, hoteles de lujo) en su perfil
  **Cuando** el usuario B accede a la seccion de Perfil
  **Entonces** el usuario B ve su propio perfil (vacio o con sus propias preferencias), no las del usuario A.

**CA-007:** Datos de ejemplo para nuevos usuarios
  **Dado** que un nuevo usuario se registra e inicia sesion por primera vez
  **Cuando** accede al Dashboard
  **Entonces** el sistema carga los viajes de ejemplo (Tokio, Barcelona, Lima de `sample_data.py`) asociados a su `user_id`, de forma independiente a los datos de otros usuarios.

**CA-008:** Persistencia multiusuario en JSON
  **Dado** que multiples usuarios utilizan la aplicacion
  **Cuando** cada uno crea, modifica o elimina viajes
  **Entonces** los cambios de un usuario no afectan los datos de otro usuario. La persistencia en JSON mantiene la integridad de los datos por usuario.

**CA-009:** Intento de acceso a datos de otro usuario via manipulacion
  **Dado** que el usuario A conoce el `trip_id` de un viaje del usuario B
  **Cuando** el usuario A intenta acceder o modificar ese viaje (por ejemplo, cambiando el `active_trip_id` manualmente)
  **Entonces** el sistema verifica que el `user_id` del viaje coincida con el usuario autenticado y rechaza el acceso.

## Dependencias

- REQ-CL-001 (Login con Google OAuth): Provee el `user_id` que se usa para filtrar datos.
- REQ-CL-002 (Sesion Persistente): La sesion contiene el `user_id` necesario para el filtrado.
- REQ-UI-002 (Chat con el Agente): La interfaz del chat debe usar los datos filtrados.
- REQ-UI-008 (Mis Viajes): La lista de viajes debe mostrar solo los del usuario autenticado.

## Notas
- La migracion del modelo single-user al multiusuario requiere modificar: `trip_service.py` (agregar `user_id` a todas las funciones de carga/guardado), `agent_service.py` (pasar `user_id` al LLM), `llm_chatbot.py` (incluir `user_id` en `thread_id`), `memory_manager.py` (filtrar ChromaDB por `user_id`), y `app.py` (inicializar `session_state` con datos filtrados).
- Para el MVP, se puede mantener un unico archivo `trips.json` con todos los viajes y filtrar en memoria por `user_id`. Para escalabilidad futura, considerar archivos por usuario o migracion a base de datos.
- Las memorias vectoriales en ChromaDB soportan filtrado por metadata nativamente (`where={"user_id": "..."}` en `collection.query()`), lo que facilita el aislamiento sin crear colecciones separadas.
