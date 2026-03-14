# REQ-UI-003 — Chat con el Agente: Acciones y Modificaciones al Itinerario

## Codigo
REQ-UI-003

## Titulo
Chat con el Agente - Solicitud de cambios y acciones sobre el itinerario desde el chat

## Prioridad MVP
Alta

## Historia de Usuario

**Como** viajero registrado,
**Quiero** solicitar cambios a mi itinerario, agregar o quitar actividades, y recibir alternativas a traves del chat con el agente,
**Para** ajustar mi planificacion de viaje de forma conversacional sin necesidad de editar manualmente cada seccion.

## Descripcion

Este requerimiento cubre la capacidad del chat para que el usuario solicite modificaciones al itinerario vigente mediante instrucciones en lenguaje natural. El agente interpreta la solicitud, presenta las opciones o el impacto del cambio, solicita confirmacion y aplica las modificaciones que se reflejan en tiempo real en las demas secciones de la interfaz (cronograma, itinerario detallado, presupuesto).

## Reglas de Negocio

- **RN-001**: Toda modificacion solicitada por el usuario a traves del chat que afecte el itinerario, el cronograma o el presupuesto requiere confirmacion explicita del usuario antes de aplicarse.
- **RN-002**: Cuando el agente aplica un cambio confirmado, las secciones afectadas (cronograma, itinerario detallado, presupuesto) deben reflejar la actualizacion sin necesidad de que el usuario recargue manualmente la pagina.
- **RN-003**: Si el usuario solicita un cambio que entra en conflicto con otro item del itinerario (superposicion horaria, exceso de presupuesto), el agente debe informar del conflicto antes de solicitar confirmacion.
- **RN-004**: El agente puede sugerir alternativas cuando el usuario expresa insatisfaccion con un item existente (por ejemplo, "no me gusta este hotel, busca otro").
- **RN-005**: Los items del itinerario modificados desde el chat mantienen trazabilidad del cambio (estado anterior y estado nuevo). **REQUIERE CLARIFICACION:** No se define si el historial de cambios debe ser visible para el usuario o solo interno.

## Criterios de Aceptacion

**CA-001:** Solicitud de agregar actividad al itinerario
  **Dado** que el usuario tiene un viaje en planificacion con un itinerario existente
  **Cuando** solicita al agente en el chat agregar una actividad (por ejemplo, "agrega una visita al museo del Louvre el dia 3 por la manana")
  **Entonces** el agente presenta una tarjeta con la actividad propuesta (nombre, horario sugerido, costo estimado, ubicacion), solicita confirmacion, y al confirmar el usuario, la actividad aparece en el itinerario detallado y en el cronograma en el dia y horario correspondiente, y el presupuesto se actualiza.

**CA-002:** Solicitud de eliminar item del itinerario
  **Dado** que el usuario tiene un viaje con items en el itinerario
  **Cuando** solicita al agente eliminar un item especifico (por ejemplo, "quita la cena del dia 2")
  **Entonces** el agente confirma el item que se eliminara, solicita confirmacion, y al confirmar el usuario, el item se elimina del itinerario detallado y del cronograma, y el presupuesto se recalcula.

**CA-003:** Solicitud de cambio con conflicto horario
  **Dado** que el usuario tiene un viaje con actividades planificadas
  **Cuando** solicita agregar o mover una actividad a un horario que se superpone con otra actividad existente
  **Entonces** el agente informa del conflicto horario, indica cual es la actividad existente que se superpone, y ofrece alternativas (mover la actividad existente, cambiar el horario de la nueva, o cancelar la solicitud).

**CA-004:** Solicitud de cambio con impacto en presupuesto
  **Dado** que el usuario tiene un presupuesto definido para el viaje
  **Cuando** solicita un cambio que incrementa el presupuesto total por encima del presupuesto estimado original
  **Entonces** el agente informa del impacto en el presupuesto (monto adicional y nuevo total), y solicita confirmacion antes de aplicar el cambio.

**CA-005:** Solicitud de alternativas
  **Dado** que el usuario tiene un item en el itinerario que no le satisface
  **Cuando** solicita al agente buscar alternativas (por ejemplo, "busca otro hotel mas economico")
  **Entonces** el agente presenta varias opciones alternativas en tarjetas ricas comparables, permitiendo al usuario seleccionar una para reemplazar el item actual, y al confirmar, el itinerario y el presupuesto se actualizan.

**CA-006:** Reflejo de cambios en tiempo real
  **Dado** que el usuario ha confirmado un cambio al itinerario a traves del chat
  **Cuando** navega a la seccion de cronograma, itinerario detallado o presupuesto
  **Entonces** los cambios estan reflejados sin necesidad de recargar la pagina, y los datos son consistentes entre todas las secciones.

**CA-007:** Solicitud ambigua del usuario
  **Dado** que el usuario envia una instruccion ambigua al agente (por ejemplo, "cambia el hotel" sin especificar cual hotel o que tipo de cambio)
  **Cuando** el agente recibe la instruccion
  **Entonces** el agente solicita clarificacion mediante preguntas especificas antes de proceder con cualquier cambio.

## Dependencias
- REQ-UI-002 (Chat con el Agente - Interfaz conversacional): este requerimiento extiende la funcionalidad del chat.
- REQ-UI-005 (Itinerario Detallado): los cambios solicitados se reflejan en el itinerario.
- REQ-UI-004 (Cronograma/Calendario): los cambios se reflejan en la vista de calendario.
- REQ-UI-006 (Presupuesto): los cambios con impacto economico se reflejan en el presupuesto.

## Notas
- La experiencia conversacional debe ser fluida: el agente debe interpretar instrucciones en lenguaje natural sin requerir comandos rigidos.
- La sincronizacion de cambios entre el chat y las demas secciones es critica para evitar inconsistencias.
