# REQ-UI-008 — Mis Viajes: Historial y Gestion de Viajes

## Codigo
REQ-UI-008

## Titulo
Mis Viajes - Historial de viajes planificados con acceso rapido y gestion de estados

## Prioridad MVP
Alta

## Historia de Usuario

**Como** viajero registrado,
**Quiero** acceder a un historial de todos mis viajes (pasados y futuros) con su estado actual y poder seleccionar cualquiera de ellos para ver su detalle,
**Para** gestionar multiples viajes, retomar planificaciones en curso y consultar informacion de viajes anteriores.

## Descripcion

La seccion Mis Viajes presenta el listado completo de viajes del usuario organizados por estado y ordenados cronologicamente. Cada viaje muestra informacion resumida (destino, fechas, estado) y permite al usuario acceder rapidamente a cualquiera de ellos para ver su detalle completo. Los estados posibles de un viaje son: en planificacion, confirmado, en curso y completado.

## Reglas de Negocio

- **RN-001**: Los estados posibles de un viaje son:
  - **En planificacion**: el viaje esta siendo construido, items pueden estar en estado sugerido o pendiente.
  - **Confirmado**: la planificacion esta finalizada y las reservas principales estan realizadas.
  - **En curso**: la fecha de inicio del viaje ha llegado y el viaje aun no ha terminado.
  - **Completado**: la fecha de fin del viaje ha pasado.
- **RN-002**: Los viajes se ordenan por defecto mostrando primero los viajes activos (en curso), luego los proximos (confirmados y en planificacion, por fecha de inicio ascendente), y por ultimo los completados (por fecha de fin descendente).
- **RN-003**: Al seleccionar un viaje de la lista, este se establece como viaje activo y las demas secciones de la interfaz (dashboard, cronograma, itinerario, presupuesto) muestran la informacion de ese viaje.
- **RN-004**: La transicion de estado de "confirmado" a "en curso" ocurre automaticamente cuando se alcanza la fecha de inicio del viaje. La transicion de "en curso" a "completado" ocurre automaticamente cuando se supera la fecha de fin del viaje.
- **RN-005**: El usuario puede tener multiples viajes en estado "en planificacion" simultaneamente, pero solo un viaje puede estar "en curso" a la vez. **REQUIERE CLARIFICACION:** No se define el comportamiento si el usuario tiene viajes con fechas solapadas.

## Criterios de Aceptacion

**CA-001:** Vista del listado de viajes
  **Dado** que el usuario esta autenticado y tiene viajes registrados
  **Cuando** accede a la seccion Mis Viajes
  **Entonces** el sistema muestra una lista de todos los viajes del usuario, cada uno con: nombre del destino, fechas de inicio y fin, estado actual (en planificacion, confirmado, en curso, completado), y una imagen o icono representativo. Los viajes se muestran ordenados segun la regla RN-002.

**CA-002:** Seleccion de viaje activo
  **Dado** que el usuario esta en la seccion Mis Viajes y ve la lista de viajes
  **Cuando** hace clic en un viaje especifico
  **Entonces** ese viaje se establece como viaje activo, el sistema navega al dashboard de ese viaje, y todas las secciones (cronograma, itinerario, presupuesto) muestran la informacion correspondiente a ese viaje.

**CA-003:** Filtrado por estado
  **Dado** que el usuario tiene viajes en distintos estados
  **Cuando** aplica un filtro por estado (por ejemplo, solo "en planificacion" o solo "completados")
  **Entonces** la lista muestra unicamente los viajes que coinciden con el estado seleccionado, manteniendo el ordenamiento cronologico.

**CA-004:** Creacion de nuevo viaje
  **Dado** que el usuario esta en la seccion Mis Viajes
  **Cuando** hace clic en la accion de crear un nuevo viaje
  **Entonces** el sistema abre el chat con el agente para iniciar la planificacion de un nuevo viaje, creando un viaje en estado "en planificacion".

**CA-005:** Transicion automatica a "en curso"
  **Dado** que el usuario tiene un viaje en estado "confirmado" cuya fecha de inicio es la fecha actual
  **Cuando** el sistema evalua los estados de los viajes
  **Entonces** el viaje transiciona automaticamente de "confirmado" a "en curso", y esto se refleja en la lista de Mis Viajes y en el dashboard.

**CA-006:** Transicion automatica a "completado"
  **Dado** que el usuario tiene un viaje en estado "en curso" cuya fecha de fin es anterior a la fecha actual
  **Cuando** el sistema evalua los estados de los viajes
  **Entonces** el viaje transiciona automaticamente de "en curso" a "completado", y esto se refleja en la lista de Mis Viajes.

**CA-007:** Viaje completado - consulta de informacion
  **Dado** que el usuario tiene viajes en estado "completado"
  **Cuando** selecciona un viaje completado de la lista
  **Entonces** puede acceder a toda la informacion del viaje (itinerario, presupuesto, cronograma) en modo de consulta, con los datos tal como quedaron al finalizar el viaje.

**CA-008:** Sin viajes registrados
  **Dado** que el usuario esta autenticado pero no tiene ningun viaje registrado
  **Cuando** accede a la seccion Mis Viajes
  **Entonces** el sistema muestra un estado vacio con un mensaje invitando al usuario a crear su primer viaje y un boton o enlace para iniciar la planificacion (que abre el chat con el agente).

**CA-009:** Estado de carga de la lista de viajes
  **Dado** que el usuario accede a la seccion Mis Viajes
  **Cuando** los datos aun estan siendo cargados
  **Entonces** el sistema muestra indicadores de carga (esqueletos de tarjetas de viaje) hasta que la informacion este disponible.

**CA-010:** Error al cargar la lista de viajes
  **Dado** que el usuario accede a la seccion Mis Viajes
  **Cuando** ocurre un error al recuperar los datos
  **Entonces** el sistema muestra un mensaje de error descriptivo y ofrece la opcion de reintentar la carga.

**CA-011:** Visualizacion responsive de Mis Viajes
  **Dado** que el usuario accede a la seccion Mis Viajes desde un dispositivo con pantalla de ancho reducido
  **Cuando** la vista se renderiza
  **Entonces** las tarjetas de viaje se organizan en una columna vertical adaptada al ancho disponible, manteniendo la informacion esencial visible y los controles accesibles por interaccion tactil.

**CA-012:** Eliminacion de viaje en planificacion
  **Dado** que el usuario tiene un viaje en estado "en planificacion"
  **Cuando** solicita eliminar ese viaje
  **Entonces** el sistema muestra una confirmacion antes de proceder ("Esta accion eliminara el viaje y toda su informacion asociada. Esta seguro?"), y al confirmar, el viaje se elimina de la lista y toda su informacion (itinerario, presupuesto, historial de chat) se elimina.

## Dependencias
- REQ-UI-001 (Dashboard): al seleccionar un viaje, el dashboard muestra su informacion.
- REQ-UI-002 (Chat con el Agente): la creacion de un nuevo viaje puede iniciarse desde el chat.

## Notas
- Los viajes completados funcionan como base de conocimiento para el agente, que utiliza la informacion de viajes pasados para mejorar sugerencias futuras. Sin embargo, la mecanica de este aprendizaje no se detalla en el MVP.
- **INFORMACION FALTANTE:** No se especifica si el usuario puede editar el nombre, destino o fechas de un viaje directamente desde esta lista, o si esas modificaciones solo se realizan a traves del chat con el agente.
- **INFORMACION FALTANTE:** No se define si los viajes pueden ser compartidos con otros usuarios (planificacion colaborativa) ni si existe un concepto de viaje archivado diferente a completado.
