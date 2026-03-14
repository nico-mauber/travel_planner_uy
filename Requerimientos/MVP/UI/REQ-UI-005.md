# REQ-UI-005 — Itinerario Detallado: Vista Dia por Dia del Viaje

## Codigo
REQ-UI-005

## Titulo
Itinerario Detallado - Vista dia por dia con informacion completa

## Prioridad MVP
Alta

## Historia de Usuario

**Como** viajero registrado,
**Quiero** visualizar mi itinerario de viaje en una vista detallada dia por dia con toda la informacion relevante de cada actividad,
**Para** conocer en detalle los horarios, ubicaciones, notas y estado de confirmacion de cada item de mi viaje.

## Descripcion

El Itinerario Detallado es una vista secuencial dia por dia que presenta toda la informacion del viaje de forma exhaustiva. Cada dia muestra sus items en orden cronologico con informacion completa: horarios, direcciones, notas, enlaces de reserva y estado de cada item (confirmado, pendiente, sugerido). Es la vista de referencia mas completa del viaje planificado.

## Reglas de Negocio

- **RN-001**: Los items del itinerario se agrupan por dia y se ordenan cronologicamente dentro de cada dia.
- **RN-002**: Cada item del itinerario tiene un estado visible que puede ser: "confirmado" (reserva o entrada adquirida), "pendiente" (planificado pero sin confirmacion), o "sugerido" (propuesto por el agente pero no aceptado por el usuario).
- **RN-003**: Los items en estado "sugerido" deben diferenciarse visualmente de los confirmados y pendientes, ya que aun no forman parte del plan definitivo del usuario.
- **RN-004**: Cada item puede contener: nombre, tipo (actividad, traslado, alojamiento, comida), horario de inicio y fin, direccion/ubicacion, notas del usuario o del agente, enlace de reserva (si existe), costo estimado o real, y estado.
- **RN-005**: El usuario puede expandir o colapsar la informacion de cada item para gestionar la cantidad de detalle visible.
- **RN-006**: El usuario puede cambiar el estado de un item de "sugerido" a "pendiente" (aceptar la sugerencia) o descartar un item sugerido directamente desde esta vista. **REQUIERE CLARIFICACION:** No se especifica si el usuario puede cambiar el estado de "pendiente" a "confirmado" desde esta vista o si eso solo ocurre cuando el agente completa una reserva.

## Criterios de Aceptacion

**CA-001:** Vista del itinerario con items agrupados por dia
  **Dado** que el usuario tiene un viaje activo con items en el itinerario
  **Cuando** accede a la seccion Itinerario Detallado
  **Entonces** el sistema muestra los items agrupados por dia del viaje (Dia 1, Dia 2, etc., con la fecha correspondiente), ordenados cronologicamente dentro de cada dia, mostrando para cada item: nombre, tipo, horario, direccion, estado y costo.

**CA-002:** Visualizacion de detalle expandido de un item
  **Dado** que el usuario esta en la seccion Itinerario Detallado y hay items listados
  **Cuando** hace clic en un item para expandirlo
  **Entonces** el sistema muestra toda la informacion disponible del item: nombre, tipo, horario de inicio y fin, direccion completa, notas, enlace de reserva (si existe), costo estimado o real, y estado. El usuario puede colapsar el item para volver a la vista resumida.

**CA-003:** Diferenciacion visual de estados
  **Dado** que el itinerario contiene items en distintos estados (confirmado, pendiente, sugerido)
  **Cuando** el usuario visualiza el itinerario
  **Entonces** cada item muestra un indicador visual claro de su estado: los items "confirmados" se muestran con un indicador de completitud (por ejemplo, un icono de check), los "pendientes" con un indicador neutro, y los "sugeridos" con un estilo visual diferenciado (por ejemplo, borde punteado o color atenuado) que denota que aun no son parte del plan.

**CA-004:** Aceptar sugerencia del agente
  **Dado** que el itinerario contiene un item en estado "sugerido" por el agente
  **Cuando** el usuario hace clic en la accion de aceptar la sugerencia sobre ese item
  **Entonces** el estado del item cambia de "sugerido" a "pendiente", el item se integra visualmente al itinerario como parte del plan, y el presupuesto se actualiza para incluir el costo de este item.

**CA-005:** Descartar sugerencia del agente
  **Dado** que el itinerario contiene un item en estado "sugerido" por el agente
  **Cuando** el usuario hace clic en la accion de descartar la sugerencia sobre ese item
  **Entonces** el item se elimina del itinerario, el cronograma se actualiza para remover el bloque correspondiente, y el presupuesto no se ve afectado (ya que el item sugerido no estaba contabilizado como plan).

**CA-006:** Navegacion entre dias
  **Dado** que el viaje tiene multiples dias planificados
  **Cuando** el usuario esta en la vista de itinerario detallado
  **Entonces** puede navegar facilmente entre dias (scroll continuo o controles de navegacion por dia) y el dia actual o mas cercano se destaca visualmente si el viaje esta en curso.

**CA-007:** Itinerario vacio
  **Dado** que el usuario tiene un viaje activo sin ningun item en el itinerario
  **Cuando** accede a la seccion Itinerario Detallado
  **Entonces** el sistema muestra un estado vacio con un mensaje indicando que no hay items planificados y sugiere al usuario interactuar con el agente a traves del chat para comenzar a construir el itinerario.

**CA-008:** Estado de carga del itinerario
  **Dado** que el usuario accede a la seccion Itinerario Detallado
  **Cuando** los datos aun estan siendo cargados
  **Entonces** el sistema muestra indicadores de carga (esqueletos de contenido) manteniendo la estructura visual de agrupacion por dia.

**CA-009:** Error al cargar el itinerario
  **Dado** que el usuario accede a la seccion Itinerario Detallado
  **Cuando** ocurre un error al recuperar los datos
  **Entonces** el sistema muestra un mensaje de error descriptivo y ofrece la opcion de reintentar la carga.

**CA-010:** Acceso a enlace de reserva
  **Dado** que un item del itinerario tiene un enlace de reserva asociado
  **Cuando** el usuario hace clic en el enlace de reserva
  **Entonces** el enlace se abre en una nueva pestana del navegador, permitiendo al usuario gestionar su reserva sin perder el contexto del itinerario.

**CA-011:** Visualizacion responsive del itinerario
  **Dado** que el usuario accede al itinerario detallado desde un dispositivo con pantalla de ancho reducido
  **Cuando** la vista se renderiza
  **Entonces** los items se muestran en una lista vertical adaptada al ancho disponible, con la informacion esencial visible y la informacion detallada accesible mediante expansion, y todos los controles son accesibles por interaccion tactil.

**CA-012:** Sincronizacion con cambios desde el chat
  **Dado** que el usuario ha realizado cambios al itinerario desde el chat con el agente (agregar, eliminar, modificar items)
  **Cuando** navega a la seccion Itinerario Detallado
  **Entonces** los cambios estan reflejados: nuevos items aparecen en su posicion cronologica, items eliminados ya no aparecen, e items modificados muestran la informacion actualizada.

## Dependencias
- REQ-UI-004 (Cronograma / Calendario): ambas vistas comparten los mismos datos del itinerario y deben estar sincronizadas.
- REQ-UI-006 (Presupuesto): cambios en el itinerario que afecten costos deben reflejarse en el presupuesto.
- REQ-UI-002 (Chat con el Agente): las sugerencias del agente generan items en estado "sugerido" en el itinerario.
- REQ-UI-003 (Chat - Acciones sobre itinerario): cambios desde el chat se reflejan aqui.

## Notas
- Esta es la vista mas completa e informativa del viaje. Debe ser clara y organizada para que el usuario pueda revisar su plan sin sentirse abrumado.
- Los enlaces de reserva son externos al sistema y su disponibilidad depende de los proveedores.
