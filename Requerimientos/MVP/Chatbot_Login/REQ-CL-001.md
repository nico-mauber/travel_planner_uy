# REQ-CL-001 — Login y Registro con Google OAuth 2.0

## Codigo
REQ-CL-001

## Titulo
Login y Registro con Google OAuth 2.0

## Prioridad MVP
Alta

## Historia de Usuario

**Como** usuario nuevo o recurrente de Trip Planner,
**Quiero** iniciar sesion o registrarme utilizando mi cuenta de Google,
**Para** acceder a la aplicacion de forma rapida y segura sin necesidad de crear credenciales adicionales.

## Descripcion

La aplicacion debe implementar autenticacion mediante Google OAuth 2.0 como metodo unico de login para el MVP. Al hacer clic en "Iniciar sesion con Google", el usuario es redirigido al flujo de consentimiento de Google. Si es la primera vez que accede, se crea automaticamente una cuenta en el sistema con los datos basicos del perfil de Google (nombre, email, foto). Si ya tiene cuenta, se inicia sesion directamente. La pantalla de login es la unica vista accesible sin autenticacion; todas las demas paginas (Dashboard, Chat, Cronograma, Itinerario, Presupuesto, Perfil, Mis Viajes) requieren sesion activa.

Actualmente la aplicacion es single-user sin autenticacion (`app.py` linea 64-78 inicializa `session_state` sin ningun control de identidad). Este requerimiento introduce la capa de autenticacion que habilita el modelo multiusuario.

## Reglas de Negocio

- **RN-001**: Google OAuth 2.0 es el unico metodo de autenticacion en el MVP. No se soportan credenciales locales (usuario/contrasena).
- **RN-002**: Si el email de Google no existe en el sistema, se crea automaticamente un registro de usuario con: `user_id` (generado), `email`, `display_name`, `photo_url`, `created_at`. No se requiere formulario de registro adicional.
- **RN-003**: Si el email de Google ya existe en el sistema, se inicia sesion directamente y se actualiza `last_login_at`.
- **RN-004**: Todas las paginas de la aplicacion (excepto la pagina de login) requieren sesion activa. Si un usuario no autenticado intenta acceder a cualquier ruta protegida, debe ser redirigido a la pagina de login.
- **RN-005**: Los datos minimos que se obtienen del perfil de Google son: email (identificador unico), nombre visible y URL de foto de perfil.
- **RN-006**: El `user_id` interno del sistema es independiente del ID de Google. Se genera con formato `user-{hex8}` (consistente con el formato de IDs existente: `trip-{hex8}`, `item-{hex8}`).
- **RN-007**: No se permite el acceso con cuentas de Google deshabilitadas o revocadas. Si el token de Google es invalido o esta expirado, el usuario debe re-autenticarse.

## Criterios de Aceptacion

**CA-001:** Visualizacion de la pagina de login
  **Dado** que un usuario no autenticado accede a la aplicacion
  **Cuando** se carga la pagina inicial
  **Entonces** el sistema muestra una pantalla de login con el nombre y logo de Trip Planner, y un boton "Iniciar sesion con Google" claramente visible como accion principal.

**CA-002:** Flujo exitoso de login con cuenta existente
  **Dado** que el usuario tiene una cuenta previamente registrada en Trip Planner
  **Cuando** hace clic en "Iniciar sesion con Google" y completa el flujo de consentimiento de Google exitosamente
  **Entonces** el sistema autentica al usuario, crea una sesion, actualiza `last_login_at`, y redirige al Dashboard (pagina principal) con el `session_state` inicializado con los datos del usuario.

**CA-003:** Flujo exitoso de registro automatico (primer login)
  **Dado** que el usuario nunca ha accedido a Trip Planner
  **Cuando** hace clic en "Iniciar sesion con Google" y completa el flujo de consentimiento de Google exitosamente
  **Entonces** el sistema crea automaticamente un registro de usuario con los datos del perfil de Google (email, nombre, foto), genera un `user_id` unico, crea una sesion, y redirige al Dashboard mostrando un mensaje de bienvenida para nuevos usuarios.

**CA-004:** Redireccion de rutas protegidas
  **Dado** que un usuario no autenticado intenta acceder directamente a una URL de una seccion protegida (por ejemplo, /Chat, /Cronograma, /Presupuesto)
  **Cuando** el sistema verifica la sesion
  **Entonces** el usuario es redirigido a la pagina de login sin mostrar contenido de la seccion protegida.

**CA-005:** Error en el flujo de OAuth
  **Dado** que el usuario inicia el flujo de login con Google
  **Cuando** ocurre un error en la autenticacion (usuario cancela el consentimiento, error de red, error de Google)
  **Entonces** el sistema muestra un mensaje de error descriptivo en la pagina de login (por ejemplo, "No se pudo completar la autenticacion. Intenta de nuevo.") y el boton de login permanece disponible para reintentar.

**CA-006:** Login con cuenta de Google deshabilitada
  **Dado** que el usuario intenta autenticarse con una cuenta de Google cuyo acceso ha sido revocado o deshabilitado
  **Cuando** el flujo de OAuth retorna un token invalido
  **Entonces** el sistema muestra un mensaje de error indicando que la autenticacion fallo y no crea ni inicia sesion.

**CA-007:** Datos del usuario en session_state tras login exitoso
  **Dado** que el usuario se ha autenticado exitosamente
  **Cuando** se inicializa el `session_state`
  **Entonces** el sistema almacena en `st.session_state` al menos: `user_id`, `user_email`, `user_name`, `user_photo`, y el indicador de sesion activa `authenticated = True`.

**CA-008:** Persistencia del registro de usuario
  **Dado** que se crea un nuevo usuario por primer login con Google
  **Cuando** el registro se completa
  **Entonces** los datos del usuario se persisten en almacenamiento local (archivo JSON en `data/users.json` o similar, consistente con el patron de persistencia existente en `data/trips.json` y `data/profiles.json`).

## Dependencias

- REQ-CL-002 (Sesion Persistente): El login genera el token de sesion cuyo ciclo de vida gestiona REQ-CL-002.
- REQ-UI-009 (Navegacion General): La navegacion debe incluir la pagina de login y el control de acceso a rutas protegidas.
- REQ-UI-007 (Perfil y Preferencias): El perfil del usuario existente (`user_profile` en `session_state`, `data/profiles.json`) debe asociarse al `user_id` del usuario autenticado.

## Notas
- Streamlit no tiene soporte nativo para OAuth. Se recomienda evaluar librerias como `streamlit-google-auth` o `streamlit-oauth` para la implementacion.
- La configuracion de la aplicacion OAuth (Client ID, Client Secret) de Google Cloud Console se almacenara en variables de entorno (`.env`), consistente con el patron existente de `GOOGLE_API_KEY`.
- En el MVP solo se soporta Google OAuth. Otros proveedores (GitHub, Microsoft, etc.) podrian agregarse en futuras iteraciones.
- La estructura actual de `session_state` en `app.py` (lineas 64-78) debera extenderse para incluir los datos del usuario autenticado antes de cargar trips y chat_histories.
