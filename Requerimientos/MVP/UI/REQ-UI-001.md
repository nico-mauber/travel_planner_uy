# REQ-UI-001 — Panel Overview (Dashboard): Vista General del Viaje

## Codigo
REQ-UI-001

## Titulo
Panel Overview - Vista general del viaje activo

## Prioridad MVP
Alta

## Historia de Usuario

**Como** viajero registrado,
**Quiero** visualizar un panel resumen con los datos clave de mi viaje en planificacion o mi proximo viaje,
**Para** tener una vision rapida del estado general de mi viaje sin necesidad de navegar a secciones individuales.

## Descripcion

El Panel Overview es la pantalla principal que el usuario ve al ingresar al sistema. Presenta un resumen visual consolidado del viaje activo (en planificacion o el proximo viaje confirmado). Incluye informacion clave como destino, fechas, presupuesto total, estado de la planificacion, informacion climatica y alertas relevantes. Debe funcionar como punto de entrada que permite al usuario entender de un vistazo el estado de su viaje y acceder rapidamente a las secciones de detalle.

## Reglas de Negocio

- **RN-001**: Si el usuario tiene un viaje en estado "en planificacion", el dashboard debe mostrar ese viaje. Si no tiene ninguno en planificacion, debe mostrar el proximo viaje en estado "confirmado" ordenado por fecha de inicio mas cercana.
- **RN-002**: Si el usuario no tiene ningun viaje (ni en planificacion ni confirmado), el dashboard debe mostrar un estado vacio con una invitacion a comenzar a planificar un viaje.
- **RN-003**: Los datos climaticos mostrados corresponden al destino principal del viaje y a las fechas planificadas. **REQUIERE CLARIFICACION:** No se especifica la fuente de datos climaticos ni la frecuencia de actualizacion.
- **RN-004**: Las alertas pueden incluir: items pendientes de confirmacion, documentos requeridos (pasaporte, visa), cambios en reservas, o informacion relevante del destino. **REQUIERE CLARIFICACION:** No se define la taxonomia completa de tipos de alerta ni sus niveles de prioridad.
- **RN-005**: El estado de la planificacion refleja el progreso general del viaje considerando los items confirmados versus los pendientes o sugeridos.
- **RN-006**: El presupuesto mostrado en el dashboard es un resumen del presupuesto total estimado del viaje.

## Criterios de Aceptacion

**CA-001:** Vista del dashboard con viaje en planificacion
  **Dado** que el usuario esta autenticado y tiene un viaje en estado "en planificacion"
  **Cuando** accede al Panel Overview
  **Entonces** el sistema muestra el resumen del viaje en planificacion con: nombre del destino, fechas de inicio y fin, presupuesto total estimado, estado de la planificacion, informacion climatica del destino para las fechas del viaje, y alertas activas si las hay.

**CA-002:** Vista del dashboard sin viaje en planificacion pero con viaje confirmado
  **Dado** que el usuario esta autenticado, no tiene viajes en estado "en planificacion", pero tiene al menos un viaje en estado "confirmado" con fecha futura
  **Cuando** accede al Panel Overview
  **Entonces** el sistema muestra el resumen del proximo viaje confirmado (el de fecha de inicio mas cercana) con los mismos datos clave: destino, fechas, presupuesto, estado, clima y alertas.

**CA-003:** Vista del dashboard sin ningun viaje
  **Dado** que el usuario esta autenticado y no tiene ningun viaje registrado (ni en planificacion, ni confirmado, ni en curso)
  **Cuando** accede al Panel Overview
  **Entonces** el sistema muestra un estado vacio con un mensaje que invita al usuario a comenzar a planificar un viaje, y ofrece al menos una accion clara para iniciar (por ejemplo, abrir el chat con el agente o crear un nuevo viaje).

**CA-004:** Visualizacion de alertas activas
  **Dado** que el usuario tiene un viaje activo en el dashboard y existen alertas asociadas a ese viaje (items pendientes de confirmacion, documentos requeridos, cambios en reservas)
  **Cuando** accede al Panel Overview
  **Entonces** el sistema muestra las alertas de forma visible y diferenciada del resto del contenido, permitiendo al usuario identificar rapidamente que elementos requieren su atencion.

**CA-005:** Navegacion desde el dashboard a secciones de detalle
  **Dado** que el usuario esta visualizando el Panel Overview con un viaje activo
  **Cuando** hace clic en cualquiera de los bloques de informacion del resumen (presupuesto, cronograma, itinerario, etc.)
  **Entonces** el sistema navega a la seccion de detalle correspondiente manteniendo el contexto del viaje activo.

**CA-006:** Estado de carga del dashboard
  **Dado** que el usuario accede al Panel Overview
  **Cuando** los datos del viaje aun estan siendo recuperados
  **Entonces** el sistema muestra indicadores de carga (esqueletos de contenido o spinners) en cada bloque de informacion, sin bloquear la interaccion con el menu de navegacion ni el acceso al chat con el agente.

**CA-007:** Error al cargar datos del dashboard
  **Dado** que el usuario accede al Panel Overview
  **Cuando** ocurre un error al recuperar los datos del viaje
  **Entonces** el sistema muestra un mensaje de error descriptivo y ofrece la opcion de reintentar la carga, sin perder el acceso a la navegacion general del sistema.

**CA-008:** Visualizacion responsive del dashboard
  **Dado** que el usuario accede al Panel Overview desde un dispositivo con pantalla de ancho reducido (tablet o movil)
  **Cuando** el dashboard se renderiza
  **Entonces** los bloques de informacion se reorganizan para adaptarse al ancho disponible, manteniendo toda la informacion legible y los elementos interactivos accesibles mediante toque.

## Dependencias
- REQ-UI-007 (Perfil y Preferencias del Viajero): el dashboard puede mostrar informacion personalizada basada en las preferencias del usuario.
- REQ-UI-008 (Mis Viajes): la seleccion del viaje a mostrar en el dashboard depende del historial y estados de los viajes del usuario.

## Notas
- La informacion climatica es de caracter informativo y su precision depende de la proximidad de las fechas del viaje. Para viajes lejanos en el tiempo, podria mostrarse informacion climatica historica o estacional.
- El dashboard debe ser la vista predeterminada al iniciar sesion en el sistema.
