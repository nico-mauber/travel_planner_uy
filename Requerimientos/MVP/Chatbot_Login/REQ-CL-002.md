# REQ-CL-002 — Sesion Persistente del Usuario

## Codigo
REQ-CL-002

## Titulo
Sesion Persistente del Usuario

## Prioridad MVP
Alta

## Historia de Usuario

**Como** usuario autenticado de Trip Planner,
**Quiero** que mi sesion se mantenga activa entre recargas del navegador y visitas posteriores,
**Para** no tener que iniciar sesion cada vez que accedo a la aplicacion.

## Descripcion

Tras un login exitoso con Google OAuth (REQ-CL-001), el sistema debe generar y almacenar un token de sesion que permita al usuario mantener su sesion activa sin re-autenticarse en cada visita. La sesion tiene un tiempo de vida configurable y se invalida automaticamente al expirar o cuando el usuario cierra sesion manualmente. El cierre de sesion limpia el `session_state` de Streamlit y el token almacenado.

Actualmente el `session_state` de Streamlit se pierde al recargar la pagina. Este requerimiento garantiza persistencia de la sesion entre recargas mediante almacenamiento del token en cookies del navegador o mecanismo equivalente.

## Reglas de Negocio

- **RN-001**: El token de sesion se genera tras un login exitoso y tiene una duracion por defecto de 7 dias. Este valor es configurable via variable de entorno `SESSION_EXPIRY_DAYS`.
- **RN-002**: En cada carga de pagina, el sistema verifica la validez del token de sesion antes de mostrar contenido protegido. Si el token es invalido o esta expirado, el usuario es redirigido al login.
- **RN-003**: Al cerrar sesion, se invalidan todos los tokens de sesion del usuario y se limpia el `session_state` completo (trips, chat_histories, user_profile, active_trip_id, etc.).
- **RN-004**: Un mismo usuario puede tener sesiones activas en multiples navegadores o dispositivos simultaneamente.
- **RN-005**: El token de sesion debe almacenarse de forma segura. No debe contener datos sensibles en texto plano. Se recomienda un token opaco (UUID) con la informacion real almacenada del lado del servidor.
- **RN-006**: Si la sesion expira mientras el usuario esta interactuando con la aplicacion (por ejemplo, en medio de un chat), al intentar la siguiente accion que requiera comunicacion con el servidor, el sistema debe redirigir al login mostrando un mensaje "Tu sesion ha expirado. Por favor, inicia sesion nuevamente."

## Criterios de Aceptacion

**CA-001:** Persistencia de sesion tras recarga del navegador
  **Dado** que el usuario se ha autenticado exitosamente y tiene una sesion activa
  **Cuando** recarga la pagina del navegador (F5 / Ctrl+R)
  **Entonces** el sistema recupera la sesion del usuario automaticamente sin mostrar la pagina de login, y el `session_state` se reinicializa con los datos del usuario autenticado.

**CA-002:** Persistencia de sesion al cerrar y reabrir el navegador
  **Dado** que el usuario se ha autenticado exitosamente y el token de sesion no ha expirado
  **Cuando** cierra el navegador y lo reabre accediendo a la URL de Trip Planner
  **Entonces** el sistema recupera la sesion automaticamente y muestra el Dashboard sin solicitar login.

**CA-003:** Expiracion automatica de sesion
  **Dado** que el usuario se autentico hace mas de 7 dias (o el periodo configurado) y no ha renovado su sesion
  **Cuando** intenta acceder a la aplicacion
  **Entonces** el sistema muestra la pagina de login con un mensaje informativo "Tu sesion ha expirado. Por favor, inicia sesion nuevamente." y requiere re-autenticacion con Google.

**CA-004:** Cierre de sesion manual
  **Dado** que el usuario esta autenticado y visualiza cualquier seccion de la aplicacion
  **Cuando** hace clic en el boton "Cerrar sesion" (ubicado en el sidebar o menu de usuario)
  **Entonces** el sistema invalida el token de sesion, limpia todo el `session_state`, y redirige al usuario a la pagina de login.

**CA-005:** Verificacion de sesion en cada carga de pagina
  **Dado** que la aplicacion recibe una solicitud de un usuario
  **Cuando** el sistema verifica el token de sesion almacenado
  **Entonces** si el token es valido y no ha expirado, se permite el acceso; si el token es invalido, esta expirado o no existe, se redirige al login.

**CA-006:** Sesion expirada durante interaccion activa
  **Dado** que el usuario esta usando la aplicacion activamente (por ejemplo, chateando con el agente)
  **Cuando** la sesion expira en ese momento
  **Entonces** la siguiente accion que requiera procesamiento del servidor muestra un mensaje "Tu sesion ha expirado. Por favor, inicia sesion nuevamente." y redirige al login tras un breve delay, sin perdida de datos del viaje (los datos ya persisten en JSON).

**CA-007:** Limpieza completa del session_state al cerrar sesion
  **Dado** que el usuario cierra sesion
  **Cuando** se procesa el cierre de sesion
  **Entonces** se eliminan del `session_state` todos los datos del usuario: `trips`, `chat_histories`, `active_trip_id`, `user_profile`, `user_id`, `user_email`, `user_name`, `user_photo`, `authenticated`, `dismissed_alerts`, y cualquier otra clave asociada al usuario.

**CA-008:** Boton de cerrar sesion visible
  **Dado** que el usuario esta autenticado
  **Cuando** visualiza el sidebar de la aplicacion
  **Entonces** el sidebar muestra, ademas del viaje activo y el boton de abrir chat (existentes), la informacion del usuario (nombre y/o foto) y un boton o enlace "Cerrar sesion" claramente identificable.

**CA-009:** Multiples sesiones concurrentes
  **Dado** que el usuario tiene una sesion activa en el navegador A
  **Cuando** inicia sesion desde el navegador B con la misma cuenta de Google
  **Entonces** ambas sesiones funcionan de forma independiente; cerrar sesion en B no afecta la sesion en A.

## Dependencias

- REQ-CL-001 (Login con Google OAuth): Este requerimiento depende del login exitoso para generar el token de sesion.
- REQ-UI-009 (Navegacion General): El sidebar debe incluir la informacion del usuario y el boton de cerrar sesion.

## Notas
- Streamlit recrea el `session_state` en cada recarga. La persistencia de sesion requiere almacenar el token en cookies del navegador (via `streamlit-cookies-manager`, `extra-streamlit-components`, o similar) y validarlo al inicio de cada ejecucion.
- El almacenamiento de sesiones del lado del servidor puede usar un archivo JSON local (`data/sessions.json`) en el MVP, consistente con el patron de persistencia existente.
- La seguridad del token de sesion en el MVP es basica (token opaco + validacion server-side). Para produccion se recomienda HTTPS obligatorio, tokens firmados (JWT), y rotacion de tokens.
