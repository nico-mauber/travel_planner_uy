# REQ-UI-004 — Cronograma / Calendario: Vista de Calendario del Itinerario

## Codigo
REQ-UI-004

## Titulo
Cronograma / Calendario - Vista de calendario con itinerario planificado

## Prioridad MVP
Alta

## Historia de Usuario

**Como** viajero registrado,
**Quiero** visualizar mi itinerario de viaje en una vista de calendario organizada por dia, semana o mes con bloques horarios,
**Para** comprender de un vistazo la distribucion temporal de mis actividades, traslados y reservas, y poder reorganizarlas visualmente.

## Descripcion

El Cronograma presenta el itinerario del viaje en formato de calendario interactivo. Las actividades, traslados y reservas se muestran como bloques dentro de franjas horarias. El usuario puede alternar entre vistas de dia, semana y mes. La funcionalidad principal diferenciadora es el drag & drop que permite al usuario reordenar actividades arrastrando los bloques a nuevas posiciones temporales.

## Reglas de Negocio

- **RN-001**: El calendario muestra solo los dias comprendidos entre la fecha de inicio y la fecha de fin del viaje activo.
- **RN-002**: Cada item del itinerario (actividad, traslado, reserva) se representa como un bloque visual dentro del calendario, posicionado en el dia y la franja horaria correspondiente.
- **RN-003**: Los bloques deben diferenciarse visualmente por tipo de item: actividades, traslados, alojamiento, comidas, y otros. **REQUIERE CLARIFICACION:** No se define la categorizacion exacta ni la paleta de colores o iconografia para cada tipo.
- **RN-004**: El drag & drop permite mover un bloque a otro dia y/o franja horaria dentro del calendario. Al soltar el bloque, el sistema debe validar que no existan conflictos horarios con otros items antes de aplicar el cambio.
- **RN-005**: Si el usuario mueve un bloque mediante drag & drop y genera un conflicto horario, el sistema debe notificar al usuario y no aplicar el movimiento hasta que el conflicto se resuelva.
- **RN-006**: Los cambios realizados mediante drag & drop deben reflejarse en el itinerario detallado y en el presupuesto (si el cambio tiene impacto economico).
- **RN-007**: Los items deben mostrar un indicador visual de su estado: confirmado, pendiente, o sugerido.

## Criterios de Aceptacion

**CA-001:** Vista del calendario con itinerario planificado
  **Dado** que el usuario tiene un viaje activo con items en el itinerario
  **Cuando** accede a la seccion Cronograma / Calendario
  **Entonces** el sistema muestra un calendario con los dias del viaje, donde cada item del itinerario aparece como un bloque visual posicionado en su dia y franja horaria, diferenciado por tipo (actividad, traslado, alojamiento, comida) y con indicador de estado (confirmado, pendiente, sugerido).

**CA-002:** Alternancia entre vistas dia, semana y mes
  **Dado** que el usuario esta en la seccion Cronograma / Calendario
  **Cuando** selecciona una vista diferente (dia, semana o mes)
  **Entonces** el calendario cambia su presentacion al modo seleccionado: la vista de dia muestra las franjas horarias detalladas de un solo dia; la vista de semana muestra 7 dias con franjas horarias; la vista de mes muestra todos los dias del viaje con los bloques resumidos.

**CA-003:** Drag & drop de actividad sin conflicto
  **Dado** que el usuario esta visualizando el cronograma y hay un bloque de actividad en el dia 2 a las 10:00
  **Cuando** arrastra el bloque y lo suelta en el dia 3 a las 14:00, y no hay conflicto horario en esa franja
  **Entonces** el bloque se reubica en el dia 3 a las 14:00, el itinerario detallado se actualiza para reflejar el nuevo dia y horario, y si hay impacto en presupuesto (por ejemplo, cambio de tarifa), este tambien se actualiza.

**CA-004:** Drag & drop con conflicto horario
  **Dado** que el usuario arrastra un bloque de actividad a una franja horaria donde ya existe otro item
  **Cuando** suelta el bloque en esa franja
  **Entonces** el sistema muestra una notificacion indicando el conflicto horario con el item existente, el bloque vuelve a su posicion original, y el usuario debe resolver el conflicto antes de poder completar el movimiento (por ejemplo, mover el item existente primero).

**CA-005:** Visualizacion de detalle al hacer clic en un bloque
  **Dado** que el usuario esta visualizando el cronograma
  **Cuando** hace clic en un bloque de actividad, traslado o reserva
  **Entonces** el sistema muestra informacion de detalle del item (nombre, horario, ubicacion, estado, notas) en un panel emergente o tooltip sin salir de la vista de calendario.

**CA-006:** Calendario sin items (viaje nuevo)
  **Dado** que el usuario tiene un viaje activo sin items en el itinerario (recien creado)
  **Cuando** accede a la seccion Cronograma / Calendario
  **Entonces** el sistema muestra el calendario con los dias del viaje vacios y un mensaje indicando que el itinerario esta vacio, sugiriendo al usuario que utilice el chat con el agente para comenzar a planificar actividades.

**CA-007:** Estado de carga del calendario
  **Dado** que el usuario accede a la seccion Cronograma / Calendario
  **Cuando** los datos del itinerario aun estan siendo cargados
  **Entonces** el sistema muestra un indicador de carga (esqueleto del calendario) hasta que los datos esten disponibles.

**CA-008:** Error al cargar el cronograma
  **Dado** que el usuario accede a la seccion Cronograma / Calendario
  **Cuando** ocurre un error al recuperar los datos del itinerario
  **Entonces** el sistema muestra un mensaje de error y ofrece la opcion de reintentar la carga.

**CA-009:** Visualizacion responsive del calendario
  **Dado** que el usuario accede al cronograma desde un dispositivo con pantalla de ancho reducido
  **Cuando** el cronograma se renderiza
  **Entonces** la vista predeterminada es la de "dia" (por ser la mas adecuada para pantallas pequenas), los bloques se muestran en lista vertical dentro de cada dia, y el drag & drop funciona mediante interaccion tactil (press and hold para activar el arrastre).

**CA-010:** Sincronizacion de cambios con otras secciones
  **Dado** que el usuario ha movido un bloque en el cronograma mediante drag & drop y el cambio se ha aplicado
  **Cuando** navega a la seccion de Itinerario Detallado
  **Entonces** el item movido aparece en su nueva posicion (dia y horario) con los datos actualizados.

## Dependencias
- REQ-UI-005 (Itinerario Detallado): el cronograma y el itinerario detallado comparten los mismos datos y deben estar sincronizados.
- REQ-UI-006 (Presupuesto): cambios en el cronograma que afecten costos deben reflejarse en el presupuesto.
- REQ-UI-003 (Chat - Acciones sobre itinerario): cambios realizados desde el chat se reflejan en el cronograma.

## Notas
- La experiencia de drag & drop debe ser fluida y con feedback visual claro (sombra del bloque arrastrado, indicador de posicion destino, indicador de conflicto).
- En vista de mes, los bloques pueden mostrarse de forma resumida (solo nombre e icono de tipo) para evitar saturacion visual.
- **INFORMACION FALTANTE:** No se especifica si el usuario puede crear items directamente desde el calendario (haciendo clic en un espacio vacio) o si la creacion de items solo se realiza a traves del chat con el agente.
