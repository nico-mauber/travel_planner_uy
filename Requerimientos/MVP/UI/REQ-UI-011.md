# REQ-UI-011 — Itinerario Detallado: Visualizacion de Traslados y Logistica

## Codigo
REQ-UI-011

## Titulo
Itinerario Detallado - Visualizacion de traslados, transporte y logistica entre actividades

## Prioridad MVP
Media

## Historia de Usuario

**Como** viajero registrado,
**Quiero** visualizar dentro del itinerario detallado los traslados y logistica de transporte entre actividades (como llegar de un lugar a otro, tiempos de desplazamiento, opciones de transporte),
**Para** planificar adecuadamente los tiempos de desplazamiento y evitar conflictos logisticos durante mi viaje.

## Descripcion

Este requerimiento extiende el itinerario detallado para incluir la visualizacion de traslados entre actividades. Cuando el itinerario tiene actividades consecutivas en ubicaciones diferentes, el sistema muestra la informacion de traslado sugerida: medio de transporte recomendado, tiempo estimado de desplazamiento, y costo estimado si aplica. Los traslados se integran dentro del flujo dia por dia como items adicionales entre actividades.

## Reglas de Negocio

- **RN-001**: Los traslados se muestran como items entre actividades consecutivas que se realizan en ubicaciones diferentes dentro del mismo dia.
- **RN-002**: Cada traslado incluye: origen (ubicacion de la actividad anterior), destino (ubicacion de la actividad siguiente), medio de transporte sugerido, tiempo estimado de desplazamiento, y costo estimado (si aplica).
- **RN-003**: Los traslados son generados por el agente y pueden estar en estado "sugerido". El usuario puede aceptarlos o solicitar alternativas de transporte a traves del chat.
- **RN-004**: El tiempo de traslado se considera al validar conflictos horarios: si dos actividades consecutivas no tienen suficiente margen para el traslado, se debe indicar como una alerta logistica. **REQUIERE CLARIFICACION:** No se define el margen minimo aceptable ni como se calcula el tiempo de traslado (si se considera trafico, hora del dia, etc.).

## Criterios de Aceptacion

**CA-001:** Visualizacion de traslado entre actividades
  **Dado** que el itinerario tiene dos actividades consecutivas en ubicaciones diferentes dentro del mismo dia
  **Cuando** el usuario visualiza el itinerario detallado de ese dia
  **Entonces** entre ambas actividades se muestra un item de traslado con: medio de transporte sugerido (taxi, metro, caminar, etc.), tiempo estimado de desplazamiento, y costo estimado si aplica. El item de traslado se diferencia visualmente de las actividades.

**CA-002:** Alerta de conflicto logistico por tiempo de traslado
  **Dado** que el tiempo de traslado estimado entre dos actividades consecutivas excede el margen disponible entre la hora de fin de la primera actividad y la hora de inicio de la segunda
  **Cuando** el usuario visualiza el itinerario detallado
  **Entonces** el traslado se muestra con una alerta visual indicando que el tiempo de desplazamiento puede ser insuficiente, sugiriendo al usuario ajustar los horarios.

**CA-003:** Actividades en la misma ubicacion
  **Dado** que dos actividades consecutivas se realizan en la misma ubicacion o en ubicaciones muy cercanas
  **Cuando** el usuario visualiza el itinerario detallado
  **Entonces** no se muestra un item de traslado entre ellas, o se muestra un indicador minimo (por ejemplo, "a pie, 5 minutos").

**CA-004:** Traslado sin informacion disponible
  **Dado** que el agente no ha generado informacion de traslado entre dos actividades consecutivas en ubicaciones diferentes
  **Cuando** el usuario visualiza el itinerario detallado
  **Entonces** se muestra un indicador de que la informacion de traslado no esta disponible, sugiriendo al usuario consultar al agente para obtenerla.

## Dependencias
- REQ-UI-005 (Itinerario Detallado): este requerimiento extiende la funcionalidad del itinerario.
- REQ-UI-006 (Presupuesto): los costos de traslado se contabilizan en la categoria "transporte local" del presupuesto.
- REQ-UI-004 (Cronograma): los traslados deben reflejarse como bloques en el calendario.

## Notas
- La calidad de la informacion de traslado depende de los datos que el agente pueda obtener sobre transporte en el destino.
- En el MVP, los traslados son informativos y sugeridos. No implican reserva automatica de transporte.
