# Plan de Implementacion — Login OAuth + Chat Multiusuario (Trip Planner)

## Contexto

Trip Planner es actualmente single-user sin autenticacion. Este plan agrega Login Google OAuth 2.0, sesiones persistentes, aislamiento de datos por usuario, y gestion de multiples conversaciones de chat. El objetivo es transformar la app de usuario unico a multiusuario manteniendo compatibilidad hacia atras (modo demo sin credenciales OAuth).

Los requerimientos estan documentados en `Requerimientos/MVP/Chatbot_Login/` (REQ-CL-001 a REQ-CL-005).

---

## Estrategia General

Usar **Streamlit nativo** (`st.login()` / `st.logout()` / `st.user`, disponible desde v1.42.0) para autenticacion Google OIDC. Esto elimina dependencias de terceros inestables y maneja sesiones con cookies encriptadas automaticamente.

**Modo dual:**
- Con `GOOGLE_CLIENT_ID` configurado en `.streamlit/secrets.toml` → flujo OAuth completo
- Sin credenciales → modo demo actual (user_id fijo `"user-demo0001"`)

---

## Dependencias Nuevas

En `requirements.txt`:
```
streamlit>=1.42.0          # (antes >=1.40.0) — Necesario para st.login/st.logout
Authlib>=1.3.2             # NUEVA — Requerida por OIDC nativo de Streamlit
```

---

## Archivos a Crear (4)

### 1. `.streamlit/secrets.toml`
Configuracion OIDC para Google OAuth. Agregar a `.gitignore`.
```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "RANDOM_SECRET_STRING"

[auth.google]
client_id = "xxx.apps.googleusercontent.com"
client_secret = "GOCSPX-xxx"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

### 2. `services/auth_service.py`
Servicio de autenticacion y gestion de usuarios.

**Funciones:**
- `is_auth_enabled() -> bool` — Verifica si secrets de auth estan configurados
- `get_or_create_user(email, name, picture) -> dict` — Busca por email en `data/users.json`; si no existe, crea con `user-{hex8}`
- `get_current_user_id() -> str` — Lee de session_state o retorna `"user-demo0001"`
- `load_users() / save_users()` — CRUD sobre `data/users.json`
- `require_auth()` — Guard: si auth habilitada y no logueado, muestra login y `st.stop()`

**Estructura de `data/users.json`:**
```json
[
  {
    "user_id": "user-a1b2c3d4",
    "email": "usuario@gmail.com",
    "name": "Juan Perez",
    "picture": "https://...",
    "created_at": "2026-03-14T10:00:00",
    "last_login": "2026-03-14T15:30:00"
  }
]
```

### 3. `services/chat_service.py`
Servicio de gestion de conversaciones multiples.

**Funciones:**
- `load_chats(user_id) -> list` — Carga de `data/chats.json`, filtrado por user_id, ordenado por `last_activity_at` desc
- `save_chats(chats)` — Persiste todo el archivo (patron igual a trips.json)
- `create_chat(user_id, trip_id=None, title="Nueva conversacion") -> dict` — ID `chat-{hex8}`
- `get_chat_by_id(chats, chat_id) -> dict | None`
- `delete_chat(chats, chat_id) -> bool`
- `rename_chat(chats, chat_id, new_title) -> bool`
- `add_message(chat, message)` — Agrega mensaje, actualiza `last_activity_at`
- `auto_generate_title(first_message) -> str` — Primeros ~50 chars del primer mensaje

**Estructura de `data/chats.json`:**
```json
[
  {
    "chat_id": "chat-a1b2c3d4",
    "user_id": "user-a1b2c3d4",
    "trip_id": "trip-001",
    "title": "Planificando vuelos a Tokio",
    "created_at": "2026-03-14T10:00:00",
    "last_activity_at": "2026-03-14T15:30:00",
    "messages": [
      {"role": "assistant", "type": "text", "content": "..."}
    ]
  }
]
```

### 4. `.streamlit/secrets.toml.example`
Archivo de ejemplo (sin credenciales reales) para documentar la configuracion requerida.

---

## Archivos a Modificar (10)

### 1. `app.py` — Cambios Significativos
- Agregar guard de autenticacion despues de CSS: si `is_auth_enabled()` y no logueado → mostrar pantalla de login con `st.login("google")` y `st.stop()`
- Si logueado: `get_or_create_user()` con datos de `st.user`, guardar en `st.session_state.current_user`
- Cambiar inicializacion de session_state:
  - `trips = load_trips(user_id=current_user_id)` (filtrado)
  - Reemplazar `chat_histories` por `user_chats = load_chats(user_id)` y `active_chat_id = None`
  - `user_profile = load_profile(user_id=current_user_id)`
- Sidebar: agregar info del usuario (foto, nombre) y boton `st.logout()` (solo si auth habilitada)

### 2. `services/trip_service.py` — Cambios Moderados
- `load_trips(user_id=None)`: filtrar por `trip["user_id"] == user_id` si user_id proporcionado. Viajes sin user_id se tratan como demo. Si no hay viajes para el user_id, cargar sample_data con ese user_id
- `create_trip(..., user_id=None)`: agregar campo `"user_id": user_id` al dict

### 3. `services/agent_service.py` — Cambios Menores
- `process_message(message, trip, user_id=None, chat_id=None)`: agregar parametros
- Propagar user_id y chat_id a `process_message_llm()`

### 4. `services/llm_agent_service.py` — Cambios Menores
- `process_message_llm(message, trip, user_profile, user_id=None, chat_id=None)`: recibir y propagar user_id/chat_id al chatbot
- Usar `chat_id` recibido en lugar de `trip["id"]`

### 5. `services/llm_chatbot.py` — Cambios Moderados
- `chat(self, message, trip=None, user_profile=None, user_id="demo", chat_id="default")`: recibir user_id y chat_id
- `thread_id`: cambiar de `f"trip_chat_{chat_id}"` a `f"trip_chat_{user_id}_{chat_id}"`
- Pasar `user_id` al memory_manager en memory_retrieval_node y memory_extraction_node

### 6. `services/memory_manager.py` — Cambios Moderados
- `save_vector_memory(text, metadata, user_id=None)`: agregar `"user_id": user_id` a metadata en ChromaDB
- `search_vector_memory(query, k, user_id=None)`: usar `where={"user_id": user_id}` en `collection.query()`. Si user_id es None, buscar sin filtro (compatibilidad)
- `extract_and_store_memories(user_message, user_id=None)`: propagar user_id

### 7. `services/profile_service.py` — Cambios Menores
- Cambiar de archivo plano a dict keyed por user_id en `profiles.json`: `{"user-abc": {...}, "user-demo0001": {...}}`
- `load_profile(user_id=None)` / `save_profile(profile, user_id=None)`

### 8. `pages/2_Chat.py` — Cambios Significativos (reescritura parcial)
- Layout en dos columnas: sidebar izq (~30%) con lista de chats + area principal (~70%)
- Columna izquierda: boton "Nuevo Chat", lista de chats del usuario (titulo, fecha), opciones eliminar/renombrar
- Columna derecha: historial del chat activo, input de mensajes
- Reemplazar `chat_histories[trip_id]` por `chat_service` (user_chats + active_chat_id)
- Titulo auto-generado al primer mensaje
- Pasar user_id y chat_id a `process_message()`
- Persistir chats despues de cada mensaje

### 9. `pages/6_Perfil.py` — Cambios Menores
- Pasar `user_id` a `save_profile()`
- Mostrar info del usuario logueado (email, nombre, foto) como seccion read-only

### 10. `data/sample_data.py` — Cambios Menores
- `get_sample_trips(user_id=None)`: agregar `"user_id": user_id` a cada viaje sample

---

## Archivos Sin Cambios

- `components/chat_widget.py` — Renderiza mensajes individuales, no necesita user_id
- `components/trip_card.py` — Componente de presentacion
- `components/budget_charts.py` — Graficos de presupuesto
- `components/itinerary_item.py` — Item del itinerario
- `components/alert_banner.py` — Alertas
- `config/llm_config.py` — Configuracion del LLM (no cambia)
- `pages/1_Dashboard.py` — Lee `session_state.trips` ya filtrado
- `pages/3_Cronograma.py` — Idem
- `pages/4_Itinerario.py` — Idem
- `pages/5_Presupuesto.py` — Idem
- `models/` — No se usan en runtime actualmente

Nota: `config/settings.py` podria recibir constantes nuevas (ej: `SESSION_EXPIRY_DAYS = 7`, `DEMO_USER_ID = "user-demo0001"`) pero es un cambio minimo.

---

## Orden de Implementacion

### Fase 1: Infraestructura de Auth
1. Actualizar `requirements.txt` (Streamlit >=1.42.0, Authlib >=1.3.2)
2. Crear `services/auth_service.py`
3. Crear `.streamlit/secrets.toml` (placeholder) + `.streamlit/secrets.toml.example`
4. Agregar `.streamlit/secrets.toml`, `data/users.json`, `data/chats.json` a `.gitignore`

### Fase 2: Aislamiento de Datos por Usuario
5. Modificar `data/sample_data.py` — agregar user_id a get_sample_trips()
6. Modificar `services/trip_service.py` — parametro user_id en load_trips/create_trip
7. Modificar `services/profile_service.py` — dict keyed por user_id
8. Modificar `services/memory_manager.py` — user_id en ChromaDB
9. Modificar `services/llm_chatbot.py` — thread_id compuesto
10. Modificar `services/llm_agent_service.py` y `services/agent_service.py` — propagar user_id/chat_id

### Fase 3: Sistema de Chats Multiples
11. Crear `services/chat_service.py`
12. Reescribir parcialmente `pages/2_Chat.py` — layout dos columnas, lista de chats

### Fase 4: Integracion de Auth en UI
13. Modificar `app.py` — guard de auth, session_state con user_id, sidebar con logout
14. Modificar `pages/6_Perfil.py` — info del usuario
15. Actualizar `pages/7_Mis_Viajes.py` — crear chats via chat_service (si aplica)

### Fase 5: Verificacion
16. Probar modo demo (sin secrets) — todo funciona como antes
17. Probar modo OAuth (con secrets reales de Google)
18. Probar aislamiento: dos usuarios ven solo sus datos
19. Probar chats multiples: crear, listar, seleccionar, eliminar

---

## Decisiones Arquitectonicas

| Decision | Eleccion | Justificacion |
|----------|----------|---------------|
| Metodo de auth | Streamlit nativo (`st.login`) | Oficial, mantenido, sin dependencias inestables |
| Pagina de login | Estado en `app.py`, no pagina separada | `st.login()` redirige a Google, no necesita pagina |
| Persistencia de sesion | Cookie nativa de Streamlit | Automatica, encriptada, 30 dias |
| Archivo de datos | Unico por tipo (trips.json, chats.json) con filtrado en memoria | Consistente con patron actual, simple para MVP |
| Singleton TripChatbot | Se mantiene | LangGraph aisla por thread_id, no necesita instancias separadas |
| thread_id LangGraph | `trip_chat_{user_id}_{chat_id}` | Aisla por usuario Y por conversacion |
| Memorias ChromaDB | Compartidas por usuario, NO por chat | Preferencias del usuario enriquecen todas las conversaciones |
| chat_histories | Reemplazado por chat_service | Modelo de "un historial por viaje" no soporta multiples chats |

---

## Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigacion |
|--------|---------|------------|
| Sesion Streamlit no configurable (30 dias, no 7) | Bajo | Aceptar para MVP, documentar divergencia con REQ-CL-002 |
| Concurrencia en archivos JSON | Bajo | Streamlit es secuencial por sesion; aceptable para MVP |
| Memorias ChromaDB existentes sin user_id | Medio | Busqueda sin filtro si user_id es None (fallback permisivo) |
| Datos demo al activar auth | Bajo | Cada usuario nuevo recibe sample data fresco |
| streamlit-calendar compatible con Streamlit >=1.42 | Bajo | Verificar al actualizar requirements |

---

## Verificacion End-to-End

1. `pip install -r requirements.txt` — verificar instalacion limpia
2. `python -m streamlit run app.py` **sin** secrets.toml → debe funcionar en modo demo identico al actual
3. Configurar secrets.toml con credenciales reales de Google Cloud Console
4. `python -m streamlit run app.py` **con** secrets.toml → debe mostrar boton "Iniciar sesion con Google"
5. Login con cuenta Google → registro automatico, redirect a Dashboard
6. Crear viaje → verificar que tiene user_id
7. Abrir Chat → ver lista vacia, crear nuevo chat, enviar mensaje, verificar titulo auto-generado
8. Crear segundo chat → verificar que ambos aparecen en la lista
9. Cerrar sesion → verificar limpieza de session_state
10. Login con segunda cuenta → verificar que no ve datos de la primera cuenta
