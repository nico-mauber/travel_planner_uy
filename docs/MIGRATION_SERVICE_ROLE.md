# Plan de Migracion: service_role → anon_key + RLS por user_id

**Fecha:** 2026-03-15
**Estado:** Borrador
**Autor:** arch-planner (agente automatico)

---

## 1. Estado Actual

### 1.1 Cliente Supabase (`services/supabase_client.py`)

El cliente singleton usa `SUPABASE_SERVICE_KEY` (service_role key):

```python
key = os.environ.get("SUPABASE_SERVICE_KEY", "")
_client = create_client(url, key)
```

**Implicaciones:**
- La service_role key **bypasea completamente RLS** en Supabase
- Un unico cliente compartido por todos los usuarios de la app
- Si la key se filtra (logs, frontend, git history), el atacante tiene acceso total a la DB
- No hay aislamiento a nivel de base de datos: la seguridad depende enteramente del codigo Python

### 1.2 RLS Policies (`scripts/schema.sql`)

RLS esta **habilitado** en todas las tablas, pero las policies son completamente permisivas:

```sql
CREATE POLICY users_self ON public.users FOR ALL USING (true);
CREATE POLICY profiles_self ON public.profiles FOR ALL USING (true);
CREATE POLICY trips_self ON public.trips FOR ALL USING (true);
-- ... todas las demas tablas igual
```

**Resultado:** Incluso con anon_key, cualquier request puede leer/escribir todo.

### 1.3 DEMO_USER_ID (`config/settings.py:101`)

```python
DEMO_USER_ID = "user-demo0001"
```

Todos los usuarios sin OAuth comparten este mismo user_id. El fallback esta hardcodeado en:
- `auth_service.py:84-89` — `get_current_user_id()` retorna `DEMO_USER_ID`
- `trip_service.py:84,121,144` — hardcodeado como `"user-demo0001"` (no usa la constante)
- `profile_service.py:23,50` — usa `DEMO_USER_ID`
- `data/sample_data.py:8` — hardcodeado

**Riesgo:** Multiples usuarios demo concurrentes ven y modifican los mismos viajes, chats y perfil.

---

## 2. Analisis de Servicios — Impacto de RLS Restrictivo

### 2.1 trip_service.py

| Operacion | Filtra por user_id | Impacto con RLS restrictivo |
|---|---|---|
| `load_trips()` | Si (`.eq("user_id", uid)`) | OK — RLS reforzaria el filtro |
| `create_trip()` | Si (inserta con user_id) | OK — RLS permitiria insert con matching user_id |
| `delete_trip()` | Parcial — check opcional en Python | **RIESGO**: `delete().eq("id", trip_id)` sin user_id. RLS bloquearia si el trip no es del usuario |
| `update_trip_statuses()` | No — actualiza por trip ID | **RIESGO**: `update().eq("id", trip["id"])` sin user_id. Funciona porque los trips ya fueron filtrados en memoria, pero RLS deberia proteger |
| `sync_trip_changes()` | No — actualiza por trip ID | **RIESGO**: Igual que arriba. RLS protegeria si trip no es del usuario |
| `accept_suggestion()` | No — solo por item_id | **RIESGO**: Requiere join con trips para validar ownership. Items no tienen user_id directo |
| `discard_suggestion()` | No — solo por item_id | Mismo riesgo |
| `add_item_to_trip()` | No — solo upsert por item | RLS en items necesitaria validar via trips.user_id |
| `remove_item_from_trip()` | No — delete por item_id | Mismo riesgo |

**Nota critica:** `itinerary_items` no tiene columna `user_id` directa. La ownership se valida transitivamente via `trips.user_id`. Las RLS policies necesitarian un subquery o un campo adicional.

### 2.2 chat_service.py

| Operacion | Filtra por user_id | Impacto con RLS restrictivo |
|---|---|---|
| `load_chats()` | Si (`.eq("user_id", user_id)`) | OK |
| `create_chat()` | Si (inserta con user_id) | OK |
| `delete_chat()` | Parcial — check opcional | **RIESGO**: Si no se pasa user_id, borra sin verificar |
| `rename_chat()` | No | **RIESGO**: Cualquiera podria renombrar un chat ajeno |
| `add_message()` | No | **RIESGO**: Inserta sin validar ownership del chat |
| `persist_chat()` | No | **RIESGO**: Borra y reinserta mensajes sin validar ownership |

### 2.3 auth_service.py

| Operacion | Filtra por user_id | Impacto con RLS restrictivo |
|---|---|---|
| `get_or_create_user()` | Si (por email) | OK — pero busca por email, no por JWT |
| `ensure_user_exists()` | Si (por user_id) | **NOTA**: Crea usuarios demo con email falso |

### 2.4 profile_service.py

| Operacion | Filtra por user_id | Impacto con RLS restrictivo |
|---|---|---|
| `load_profile()` | Si (`.eq("user_id", uid)`) | OK |
| `save_profile()` | Si (upsert con user_id) | OK |

### 2.5 feedback_service.py

| Operacion | Filtra por user_id | Impacto con RLS restrictivo |
|---|---|---|
| `save_feedback()` | No — solo por trip_id | **RIESGO**: Cualquiera podria escribir feedback para trips ajenos |
| `has_feedback()` | No — solo por trip_id | **RIESGO**: Podria ver si un trip ajeno tiene feedback |
| `get_feedback()` | No — solo por trip_id | **RIESGO**: Podria leer feedback ajeno |

**Mitigacion necesaria:** RLS en feedbacks debe validar via `trips.user_id`.

---

## 3. Estado Objetivo

### 3.1 Arquitectura Target

```
                 ┌──────────────────────────────┐
                 │     Streamlit App (Python)    │
                 │                               │
                 │  ┌─────────────────────────┐  │
                 │  │   Supabase Client        │  │
                 │  │   (service_role key)     │  │
                 │  │   SOLO para operaciones  │  │
                 │  │   admin (auth, etc.)     │  │
                 │  └─────────────────────────┘  │
                 │                               │
                 │  ┌─────────────────────────┐  │
                 │  │   Supabase Client        │  │
                 │  │   (anon key + JWT)       │  │
                 │  │   Para queries de datos  │  │
                 │  └─────────────────────────┘  │
                 └──────────┬───────────────────┘
                            │
                 ┌──────────▼───────────────────┐
                 │       Supabase (PostgreSQL)   │
                 │                               │
                 │  RLS activo con policies      │
                 │  que validan user_id via JWT   │
                 │  auth.uid() = user_id          │
                 └──────────────────────────────┘
```

### 3.2 RLS Policies Objetivo

```sql
-- Users: solo el propio usuario puede leer/modificar su registro
CREATE POLICY users_own ON public.users
  FOR ALL USING (user_id = current_setting('request.jwt.claims')::json->>'sub');

-- Trips: solo el owner puede ver/modificar sus viajes
CREATE POLICY trips_own ON public.trips
  FOR ALL USING (user_id = current_setting('request.jwt.claims')::json->>'sub');

-- Items: ownership via trip
CREATE POLICY items_own ON public.itinerary_items
  FOR ALL USING (
    trip_id IN (
      SELECT id FROM public.trips
      WHERE user_id = current_setting('request.jwt.claims')::json->>'sub'
    )
  );

-- Chats: solo el owner
CREATE POLICY chats_own ON public.chats
  FOR ALL USING (user_id = current_setting('request.jwt.claims')::json->>'sub');

-- Messages: ownership via chat
CREATE POLICY messages_own ON public.chat_messages
  FOR ALL USING (
    chat_id IN (
      SELECT chat_id FROM public.chats
      WHERE user_id = current_setting('request.jwt.claims')::json->>'sub'
    )
  );

-- Profiles: solo el owner
CREATE POLICY profiles_own ON public.profiles
  FOR ALL USING (user_id = current_setting('request.jwt.claims')::json->>'sub');

-- Feedbacks: ownership via trip
CREATE POLICY feedbacks_own ON public.feedbacks
  FOR ALL USING (
    trip_id IN (
      SELECT id FROM public.trips
      WHERE user_id = current_setting('request.jwt.claims')::json->>'sub'
    )
  );
```

**Nota:** Las policies de ejemplo arriba usan JWT claims. Sin embargo, **rls-fixer (Task #1) ya implemento policies usando `current_setting('app.current_user_id', true)`**, que es mas practico para el estado actual de la app (sin Supabase Auth). Para la migracion, el backend debera hacer `SET LOCAL app.current_user_id = '<user_id>'` antes de cada operacion con anon_key. Las policies con JWT claims son el objetivo final (Fase 4).

---

## 4. Pasos de Migracion (Ordenados)

### Fase 0 — Mitigaciones Inmediatas (sin cambios en Supabase)

Estas se pueden hacer YA sin romper la app:

- [x] **0.1** Reemplazar hardcoded `"user-demo0001"` en `trip_service.py` con `DEMO_USER_ID` de settings
- [x] **0.2** Agregar validacion de user_id en operaciones de escritura que no la tienen:
  - `chat_service.delete_chat()` — ahora requiere user_id obligatorio (rls-fixer, Task #1)
  - `chat_service.rename_chat()` — verifica ownership si user_id proporcionado (rls-fixer, Task #1)
  - `feedback_service.save_feedback()` — verifica que el trip pertenece al usuario (rls-fixer, Task #1)
  - `chat_service.add_message()` — pendiente: validar que el chat pertenece al usuario
  - `chat_service.persist_chat()` — pendiente: validar ownership antes de borrar/reinsertar
- [ ] **0.3** Generar DEMO_USER_ID unico por sesion de navegador (ver seccion 6)
- [ ] **0.4** Agregar logging de operaciones sensibles (delete, update) con user_id para auditoría

### Fase 1 — RLS Policies Restrictivas (cambios en Supabase SQL)

**Prerequisito:** Definir como se inyectara el user_id en las queries. Dos opciones:

**Opcion A — Custom claims via `set_config`:**
```python
# Antes de cada operacion con anon client:
sb.postgrest.auth(token)  # o
sb.rpc("set_claim", {"claim": "user_id", "value": uid}).execute()
```

**Opcion B — Supabase Auth completo:**
Requiere integrar Google OAuth de Streamlit con Supabase Auth para obtener JWTs validos.

**Recomendacion:** Opcion A es mas rapida de implementar y no requiere cambiar el flujo de autenticacion.

Pasos:
1. Crear funcion SQL `set_app_user(user_id TEXT)` que setea `request.jwt.claims`
2. Reemplazar policies `USING (true)` con policies que validen `user_id`
3. Mantener service_role client para operaciones admin (ensure_user_exists, etc.)
4. Crear segundo client con anon_key para operaciones de datos

### Fase 2 — Dual Client en Python

```python
# supabase_client.py
_admin_client = None  # service_role — solo para auth/admin
_anon_client = None   # anon — para queries de datos

def get_admin_client():
    """Client con service_role key. Solo para operaciones admin."""
    ...

def get_data_client(user_id: str):
    """Client con anon key. Setea user_id para RLS."""
    client = get_anon_client()
    # Inyectar user_id en el contexto de la sesion PostgreSQL
    client.rpc("set_app_user", {"p_user_id": user_id}).execute()
    return client
```

### Fase 3 — Migrar Servicios

Orden recomendado (de menor a mayor riesgo):
1. `profile_service.py` — ya filtra por user_id, cambio minimo
2. `feedback_service.py` — agregar user_id validation, luego migrar a anon client
3. `chat_service.py` — agregar ownership checks, luego migrar
4. `trip_service.py` — el mas complejo por la relacion transitiva items→trips
5. `auth_service.py` — mantener service_role (es admin por naturaleza)

### Fase 4 — Supabase Auth (Largo Plazo)

1. Integrar Google OAuth de Streamlit con Supabase Auth
2. Usar JWTs de Supabase en lugar de custom user_id
3. Reemplazar `set_app_user()` con `auth.uid()` nativo
4. Eliminar `ensure_user_exists()` (Supabase Auth maneja usuarios)

---

## 5. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|---|---|---|---|
| RLS policies bloquean operaciones legitimas | Alta | Alto | Testing exhaustivo con usuario de prueba antes de deploy |
| Items sin user_id directo complican RLS | Media | Medio | Subquery via trips o agregar columna user_id a items |
| service_role key en .env expuesta | Baja | Critico | .gitignore, rotacion de keys, variables de entorno en produccion |
| Demo users pierden datos al hacer user_id unico | Alta | Bajo | Aceptable — datos demo son efimeros |
| Trigger `recalculate_trip_budget` usa SECURITY DEFINER | Baja | Medio | OK — triggers DB corren con permisos del definer, no del caller |
| Rollback si algo falla en produccion | Media | Alto | Hacer backup de policies antes de cambiar. Mantener service_role client como fallback |
| Checkpoints LangGraph compartidos entre demos | Media | Medio | thread_id usa user_id (`trip_chat_{user_id}_{chat_id}`). Con DEMO_USER_ID compartido, si dos demos crean un chat con el mismo chat_id, los checkpoints SQLite se mezclan. Fix: user_id unico por sesion (Fase 0.3) |

---

## 6. DEMO_USER_ID — Analisis y Riesgo

### Problema Actual

`DEMO_USER_ID = "user-demo0001"` es un valor **estatico compartido por TODOS los usuarios sin OAuth**.

**Escenario de riesgo:**
1. Usuario A abre la app sin OAuth → user_id = "user-demo0001"
2. Usuario A crea un viaje a Tokio con datos personales
3. Usuario B abre la app sin OAuth → user_id = "user-demo0001"
4. Usuario B **ve el viaje de Usuario A** con todos sus datos
5. Usuario B puede **eliminar o modificar** el viaje de Usuario A

**Esto NO es un bug hipotetico**: es el comportamiento actual de la app cuando OAuth no esta habilitado.

### Mitigaciones Inmediatas

**Opcion A — user_id unico por sesion de navegador:**
```python
# En app.py, al inicializar session_state:
if not st.session_state.get("current_user"):
    demo_uid = f"demo-{uuid.uuid4().hex[:8]}"
    st.session_state.current_user = {
        "user_id": demo_uid,
        "name": "Usuario Demo",
        "email": f"{demo_uid}@demo.local",
    }
```

**Pros:** Aislamiento inmediato entre sesiones demo.
**Contras:** Datos se "pierden" entre sesiones (nuevo ID = nueva cuenta). Pero esto es preferible al data leakage actual.

**Opcion B — Mantener DEMO_USER_ID pero read-only:**
Restringir usuarios demo a solo lectura con datos de ejemplo precargados. Requiere cambios mas amplios en la UI.

**Recomendacion:** Opcion A. Es la mas rapida y segura. Los usuarios demo no esperan persistencia entre sesiones.

### Inconsistencia en trip_service.py

`trip_service.py` tiene el valor hardcodeado `"user-demo0001"` en 3 lugares (lineas 84, 121, 144) en lugar de usar `DEMO_USER_ID` de settings. Esto dificulta cambiar el valor centralmente.

**Fix inmediato:** Reemplazar los 3 hardcoded con `from config.settings import DEMO_USER_ID` y usar la constante.

---

## 7. Resumen de Acciones

### Se puede hacer YA (Fase 0):
1. Unificar hardcoded `"user-demo0001"` → usar constante `DEMO_USER_ID`
2. Agregar ownership checks en servicios que no los tienen
3. Generar DEMO_USER_ID unico por sesion
4. Documentar que service_role key NO debe exponerse nunca al frontend

### Requiere cambios en Supabase (Fase 1-3):
1. Reemplazar policies `USING (true)` con policies restrictivas
2. Crear funcion `set_app_user()` para inyectar user_id
3. Crear dual client (admin + anon)
4. Migrar servicios uno por uno

### Largo plazo (Fase 4):
1. Integrar Supabase Auth con Google OAuth de Streamlit
2. Usar JWTs nativos en lugar de custom user_id
