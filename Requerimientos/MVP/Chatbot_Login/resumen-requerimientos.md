# Indice de Requerimientos Funcionales — Trip Planner MVP (Chatbot y Login)

## Informacion General
- **Proyecto**: Trip Planner
- **Alcance**: MVP - Login OAuth y Chatbot Multiusuario
- **Total de requerimientos**: 5
- **Fecha de generacion**: 2026-03-14

---

## Lista de Requerimientos

| Codigo | Titulo | Seccion | Prioridad |
|--------|--------|---------|-----------|
| REQ-CL-001 | Login y Registro con Google OAuth 2.0 | Autenticacion | Alta |
| REQ-CL-002 | Sesion Persistente del Usuario | Autenticacion | Alta |
| REQ-CL-003 | Aislamiento de Datos del Chatbot por Usuario | Datos / Seguridad | Alta |
| REQ-CL-004 | Gestion de Conversaciones Multiples en el Chatbot | Chat | Alta |
| REQ-CL-005 | Contexto Aislado por Conversacion de Chat | Chat | Alta |

---

## Descripcion de cada Requerimiento

### REQ-CL-001 — Login y Registro con Google OAuth 2.0
Autenticacion mediante Google OAuth 2.0. Registro automatico al primer login con datos del perfil de Google (email, nombre, foto). Pagina de login como unica vista publica. Todas las demas paginas requieren sesion activa. Almacenamiento de usuarios en JSON local.

### REQ-CL-002 — Sesion Persistente del Usuario
Token de sesion que persiste entre recargas del navegador y visitas posteriores. Expiracion configurable (7 dias por defecto). Cierre de sesion manual con limpieza completa de session_state. Soporte de sesiones concurrentes en multiples dispositivos.

### REQ-CL-003 — Aislamiento de Datos del Chatbot por Usuario
Cada viaje, historial de chat, memoria vectorial (ChromaDB) y perfil de preferencias se asocia al `user_id` del usuario autenticado. Filtrado por usuario en todas las operaciones de lectura. Datos de ejemplo cargados independientemente para cada nuevo usuario.

### REQ-CL-004 — Gestion de Conversaciones Multiples en el Chatbot
Soporte de multiples conversaciones de chat por usuario. Crear nuevo chat, ver lista de chats anteriores ordenados por actividad reciente, seleccionar chat para retomarlo, eliminar chats. Titulo generado automaticamente. Asociacion opcional a viaje activo.

### REQ-CL-005 — Contexto Aislado por Conversacion de Chat
Cada conversacion de chat mantiene su propio contexto conversacional (historial de mensajes, checkpoints de LangGraph) independiente de otras conversaciones. Las memorias vectoriales se comparten a nivel de usuario para enriquecer todas las conversaciones con preferencias personales.

---

## Resumen de Decisiones de Diseno

1. **Memorias vectoriales compartidas, contexto conversacional aislado**: Las memorias de ChromaDB (preferencias, hechos personales) se comparten entre todos los chats del usuario. El contexto conversacional (historial de mensajes, checkpoints de LangGraph) es independiente por chat. Esto permite que el agente recuerde preferencias generales sin mezclar los hilos de conversacion.

2. **Persistencia en JSON**: Consistente con el patron existente del proyecto (`trips.json`, `profiles.json`), se agregan `users.json`, `sessions.json`, y `chats.json` (o estructura por usuario). No se introduce base de datos relacional en el MVP.

3. **IDs consistentes**: Nuevos identificadores siguen el formato existente: `user-{hex8}`, `chat-{hex8}`, `session-{hex8}`.

4. **Google OAuth unico**: El MVP solo soporta Google como proveedor de autenticacion, simplificando la implementacion.

---

## Mapa de Dependencias

```
REQ-CL-001 (Login OAuth)
  └── REQ-CL-002 (Sesion Persistente) [depende del login]
        └── REQ-CL-003 (Aislamiento por Usuario) [depende de la sesion]
              ├── REQ-CL-004 (Chats Multiples) [depende del aislamiento]
              │     └── REQ-CL-005 (Contexto por Chat) [depende de chats multiples]
              └── REQ-UI-002 (Chat existente) [se extiende]

REQ-CL-003 → REQ-UI-008 (Mis Viajes, filtrado por usuario)
REQ-CL-004 → REQ-UI-002 (Chat, interfaz extendida)
REQ-CL-005 → REQ-UI-003 (Chat - Acciones, aplica sobre viaje del chat)
```

---

## Impacto en Componentes Existentes

| Componente | Archivo | Cambios Requeridos |
|------------|---------|-------------------|
| Punto de entrada | `app.py` | Agregar verificacion de sesion antes de inicializar session_state. Cargar datos filtrados por usuario. |
| Servicio de viajes | `services/trip_service.py` | Agregar `user_id` como parametro en `load_trips()`, `save_trips()`, `create_trip()`. Filtrar por usuario. |
| Servicio del agente | `services/agent_service.py` | Pasar `user_id` al LLM. Asociar acciones al viaje del chat. |
| Servicio LLM | `services/llm_agent_service.py` | Usar `chat_id` del chat activo (no `trip_id`) para el `thread_id`. |
| Chatbot LangGraph | `services/llm_chatbot.py` | Cambiar `thread_id` a formato `trip_chat_{user_id}_{chat_id}`. |
| Memoria vectorial | `services/memory_manager.py` | Agregar `user_id` a metadata de memorias. Filtrar busquedas por `user_id`. |
| Pagina de chat | `pages/2_Chat.py` | Agregar lista de chats, selector de chat activo, boton "Nuevo chat". |
| Widget de chat | `components/chat_widget.py` | Sin cambios significativos (renderiza mensajes individuales). |
| Configuracion | `config/settings.py` | Agregar constantes para sesion (expiracion, etc.). |
| Datos | `data/` | Nuevos archivos: `users.json`, `sessions.json`, `chats.json`. |
| Navegacion | Todas las paginas | Verificar autenticacion al inicio de cada pagina. |

---

## Informacion Pendiente de Clarificacion

1. **Proveedor OAuth adicional**: Para futuras iteraciones, se necesita definir si se soportaran otros proveedores (GitHub, Microsoft, etc.).
2. **Eliminacion de cuenta**: No se define si el usuario puede eliminar su cuenta y todos sus datos.
3. **Limite de chats**: No se establece un limite maximo de conversaciones por usuario.
4. **Exportacion de chats**: No se define si el usuario puede exportar el historial de una conversacion.
5. **Busqueda en chats**: No se define si el usuario puede buscar mensajes dentro de sus conversaciones.
6. **Notificaciones de sesion**: No se define si se notifica al usuario cuando su sesion esta proxima a expirar.
