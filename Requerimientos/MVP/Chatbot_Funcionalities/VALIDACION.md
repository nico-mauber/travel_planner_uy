# Informe de Validacion — REQ-CF-001, REQ-CF-002, REQ-CF-003

**Fecha**: 2026-03-16
**Validador**: Agente Validador (equipo req-cf-pipeline)
**Alcance**: Consistencia interna, consistencia cruzada, consistencia con reqs existentes, completitud, formato, ambiguedades, trazabilidad

---

## Resumen Ejecutivo

| Severidad | Cantidad |
|-----------|----------|
| CRITICO | 2 |
| MAYOR | 6 |
| MENOR | 3 |
| OBSERVACION | 7 |

---

## Hallazgos CRITICOS

### CRIT-01: CF-002 CA-002 usa status "pendiente" que no existe en el codebase

**Requerimiento**: REQ-CF-002, CA-002 (linea 52)
**Descripcion**: CA-002 especifica que el item creado tiene `status = "pendiente"`. Sin embargo, el enum `ItemStatus` en `config/settings.py` define los valores: `planificado`, `confirmado`, `sugerido`, `completado`, `cancelado`. El valor `"pendiente"` **no existe** en el sistema.
**Impacto**: El CA no es verificable tal como esta escrito. Si se implementa literalmente, el status del item no seria reconocido por el sistema.
**Origen**: REQ-UI-005 RN-002 tambien usa "pendiente" como sinonimo informal de "planificado", creando la confusion. Esta inconsistencia terminologica entre UI-005 y el codebase se propago a CF-002.
**Accion requerida**: Cambiar `status = "pendiente"` por `status = "planificado"` en CA-002, o documentar explicitamente el mapeo "pendiente" = "planificado" en un glosario de terminos.

### CRIT-02: CF-003 RN-011 depende de end_time para detectar conflictos, pero end_time esta sin definir

**Requerimiento**: REQ-CF-003, RN-011 vs REQUIERE CLARIFICACION de end_time
**Descripcion**: RN-011 dice: "el agente verifica si existe otro item ya registrado en el mismo dia y en un horario que se solape con el item propuesto (comparando `start_time` y `end_time`)". Pero el valor de `end_time` para items creados por extraccion inteligente esta marcado como REQUIERE CLARIFICACION (notas, linea 135). Sin `end_time` definido, la deteccion de conflictos horarios de RN-011 **no puede implementarse** para los items nuevos.
**Impacto**: CA-005 (deteccion de conflicto horario) no es verificable hasta que se resuelva la clarificacion de end_time.
**Accion requerida**: Resolver REQUIERE CLARIFICACION de end_time antes de implementar. Se sugiere definir duraciones por defecto por tipo de item (ej: actividad=2h, comida=1.5h, vuelo=3h, traslado=1h, alojamiento=0 o check-in, extra=1h).

---

## Hallazgos MAYORES

### MAY-01: CF-001 RN-005 (eliminar auto-deteccion) no tiene CA directo

**Requerimiento**: REQ-CF-001, RN-005
**Descripcion**: RN-005 dice: "Se elimina la logica de auto-deteccion de viaje por destino (`_find_trip_by_destination`)". No hay un CA que verifique explicitamente que esta funcionalidad fue eliminada. CA-006 (rechazar preguntas sobre otros viajes) cubre parcialmente la consecuencia, pero no valida la eliminacion de la auto-deteccion en si.
**Accion requerida**: Agregar un CA que verifique que si el usuario menciona un destino en el mensaje (sin cambiar el selector), el agente NO cambia automaticamente de viaje. Ejemplo: "Dado que el usuario tiene Tokio seleccionado y tambien tiene un viaje a Lima, Cuando escribe 'busca hoteles en Lima', Entonces el agente NO auto-detecta el viaje a Lima y responde en contexto de Tokio."

### MAY-02: Conflicto CF-001 vs REQ-CL-004 RN-005/CA-007/CA-008 — asociacion automatica de chat a viaje

**Requerimiento**: REQ-CF-001 vs REQ-CL-004
**Descripcion**: REQ-CL-004 RN-005 establece: "Si el usuario tiene un viaje activo al crear un nuevo chat, el chat se asocia automaticamente a ese viaje." CF-001 reemplaza esta logica: la asociacion ya no es al "viaje activo global" (`active_trip_id`) sino al viaje seleccionado en el selector de la pagina de Chat.
- CL-004 CA-007: "crea un nuevo chat [...] el chat se asocia automaticamente al viaje activo" — necesita actualizarse para reflejar que la asociacion es al viaje del selector.
- CL-004 CA-008: "usuario no tiene ningun viaje activo [...] el chat se crea sin asociacion a viaje, y el campo de entrada esta habilitado" — **contradice** CF-001 RN-001 donde el campo esta deshabilitado sin seleccion.
**Impacto**: Si CL-004 no se actualiza, los implementadores pueden seguir la logica vieja.
**CF-001 lo reconoce**: Si, en la seccion de Notas ("Relacion con REQ-CL-004 RN-005").
**Accion requerida**: Actualizar REQ-CL-004 RN-005, CA-007 y CA-008 para reflejar el nuevo comportamiento. Marcar la version anterior como superseded por CF-001.

### MAY-03: Conflicto CF-001 vs REQ-UI-002 CA-010 — comportamiento sin viaje activo

**Requerimiento**: REQ-CF-001 CA-009 vs REQ-UI-002 CA-010
**Descripcion**: UI-002 CA-010 dice: "Chat sin viaje activo [...] el campo de entrada esta habilitado para recibir la primera instruccion." CF-001 CA-009 dice: "el selector muestra unicamente la opcion 'Crear nuevo viaje', el campo de texto esta deshabilitado [...] Al seleccionar 'Crear nuevo viaje', el campo de texto se habilita."
**Impacto**: UI-002 permite chat libre sin viaje; CF-001 requiere seleccionar "Crear nuevo viaje" primero. Comportamientos contradictorios.
**Accion requerida**: Actualizar REQ-UI-002 CA-010 para alinearse con CF-001 CA-009, o documentar explicitamente que CF-001 supersede UI-002 en este aspecto.

### MAY-04: CF-002 no define como se visualiza un item multi-dia en la vista de Itinerario Detallado (REQ-UI-005)

**Requerimiento**: REQ-CF-002
**Descripcion**: CF-002 define como se renderiza el item multi-dia en FullCalendar (CA-003) pero no define como se muestra en la pagina de Itinerario Detallado (`pages/4_Itinerario.py`). UI-005 agrupa items por dia. Un item con `day=1, end_day=10` apareceria: en todos los dias? Solo en el dia 1? Como cabecera?
**Impacto**: Ambiguedad de implementacion. El item se creara y aparecera en el itinerario pero la presentacion queda indefinida.
**Accion requerida**: Agregar un CA que defina el comportamiento en la vista de itinerario detallado. Sugerencia: mostrar el item solo en el Dia 1 con una etiqueta que indique la duracion total ("Dias 1-10").

### MAY-05: CF-003 RN-007 (estimacion de costo) no tiene ningun CA que lo cubra

**Requerimiento**: REQ-CF-003, RN-007
**Descripcion**: RN-007 esta marcado como REQUIERE CLARIFICACION respecto a si el agente estima costos automaticamente. Pero independientemente de la resolucion, **no hay ningun CA que verifique el manejo de costos** — ni para cuando el usuario menciona un costo, ni para cuando no lo menciona.
**Accion requerida**: Agregar al menos 2 CAs: (1) cuando el usuario menciona costo ("agregar cena por 50 dolares"), verificar que se extrae el costo; (2) cuando no menciona costo, verificar el comportamiento por defecto (sea estimacion o costo 0).

### MAY-06: CF-002 CA-002 no muestra start_time/end_time en la confirmacion, pero RN-003 los define

**Requerimiento**: REQ-CF-002, CA-001 vs RN-003
**Descripcion**: RN-003 define `start_time = "00:00"`, `end_time = "23:59"` para el item. CA-001 muestra los datos de la tarjeta de confirmacion: "nombre, fecha inicio, fecha fin, duracion, tipo". No incluye start_time/end_time. CA-002 lista los campos del item creado pero tampoco incluye `start_time` ni `end_time`.
**Impacto**: Los tiempos se definen en la RN pero no se verifican en los CAs.
**Accion requerida**: Agregar `start_time` y `end_time` a la verificacion de CA-002, o documentar que son implicitos para eventos allDay.

---

## Hallazgos MENORES

### MEN-01: CF-001 CA-003 usa tilde en "envia"

**Requerimiento**: REQ-CF-001, CA-003, linea 50
**Descripcion**: El texto dice "el agente envi**a** un mensaje de bienvenida" — contiene la palabra "envia" con tilde (i con acento). Las reglas de formato establecen "Sin tildes/acentos".
**Accion requerida**: Cambiar "envía" por "envia".

### MEN-02: REQ-CL-005 CA-009 referencia GOOGLE_API_KEY en vez de OPENAI_API_KEY

**Requerimiento**: REQ-CL-005, CA-009, linea 77
**Descripcion**: CA-009 dice "no hay `GOOGLE_API_KEY`" pero el sistema usa `OPENAI_API_KEY` para habilitar el LLM. Este es un error pre-existente en CL-005, no introducido por los REQ-CF, pero es relevante porque CF-002 y CF-003 referencian correctamente `OPENAI_API_KEY` y un implementador que lea CL-005 podria confundirse.
**Accion requerida**: Corregir CL-005 CA-009 para usar `OPENAI_API_KEY`.

### MEN-03: Inconsistencia terminologica "viaje activo" vs "viaje seleccionado"

**Requerimiento**: REQ-CF-001 vs REQ-UI-002 RN-002 y multiples CAs en CL-004/CL-005
**Descripcion**: Los REQ-CF usan "viaje seleccionado" (del selector) pero los reqs existentes usan "viaje activo" (de `active_trip_id`). Con CF-001, el concepto de "viaje activo" en el contexto del chat cambia a "viaje seleccionado en el selector". No se define si ambos conceptos coexisten o si el selector reemplaza el concepto de viaje activo para toda la aplicacion.
**Accion requerida**: Definir si la seleccion en el chat page sincroniza con `active_trip_id` (usado por otras paginas) o si son conceptos independientes. Documentar la relacion.

---

## OBSERVACIONES

### OBS-01: Edge case no cubierto — CF-001: Transicion de viaje durante flujo de creacion

Si el usuario selecciona "Crear nuevo viaje", inicia el flujo de creacion (trip_creation_flow), y luego cambia el selector a un viaje existente antes de completar la creacion, no se define que ocurre con el flujo en curso. Sugerencia: cancelar el flujo de creacion al cambiar el selector y notificar al usuario.

### OBS-02: Edge case no cubierto — CF-002: Evento duplicado

No hay validacion de duplicados. Si el usuario dice "agrega mi viaje al cronograma" dos veces, se crearian dos items identicos `day=1, end_day=N`. Sugerencia: verificar si ya existe un item similar antes de proponer la creacion, o informar que ya existe uno.

### OBS-03: Edge case no cubierto — CF-003: "manana"/"pasado manana" fuera del rango del viaje

RN-002 acepta "manana" como referencia relativa. Si el usuario planifica un viaje que empieza en 2 semanas y dice "manana", la fecha calculada estaria fuera del rango del viaje. RN-003 lo atraparia, pero la interaccion seria confusa. Sugerencia: si la fecha relativa cae fuera del rango, el agente podria interpretar "manana" como "el segundo dia del viaje" o aclarar proactivamente.

### OBS-04: Edge case no cubierto — CF-003: Dia ambiguo ("martes" con multiples martes en el viaje)

RN-002 no define como resolver "el martes" cuando hay multiples martes dentro del rango del viaje. Sugerencia: seleccionar el proximo martes mas cercano al dia actual del viaje, o preguntar al usuario.

### OBS-05: Prioridad de ruteo entre CF-002 y CF-003 para mensajes ambiguos

Un mensaje como "agregar un evento al calendario el dia 3" contiene keywords de ambos: "agregar" (CF-003) y "calendario" (CF-002). La nota de CF-002 sugiere que cronograma se evalua antes de add_item, pero no esta formalizado en una RN. Si el orden cambia, el comportamiento cambia. Sugerencia: formalizar la prioridad de ruteo en una RN de CF-002 o en un documento de arquitectura.

### OBS-06: CF-003 — Modo demo (sin auth)

Los tres reqs asumen "viajero registrado" en sus historias de usuario. No mencionan el modo demo (`DEMO_USER_ID`) que la app soporta. Esto no es un problema funcional (el demo user puede usar el selector), pero deberia verificarse en implementacion.

### OBS-07: Orden de implementacion — CF-002 y CF-003 son independientes entre si

El resumen-requerimientos.md sugiere CF-001 → CF-003 → CF-002. Esto es correcto: CF-002 y CF-003 no dependen entre si, solo de CF-001. Pueden implementarse en paralelo tras completar CF-001.

---

## Matriz de Cobertura RN → CA

### REQ-CF-001

| RN | CAs que la cubren | Estado |
|----|-------------------|--------|
| RN-001 | CA-001 | OK |
| RN-002 | CA-002 | OK |
| RN-003 | CA-006 | OK |
| RN-004 | CA-003, CA-009 | OK |
| RN-005 | *(ninguno directo)* | **FALTA CA** (MAY-01) |
| RN-006 | CA-003 (parcial) | PARCIAL |
| RN-007 | CA-004, CA-005, CA-007 | OK |
| RN-008 | CA-008 | OK |

### REQ-CF-002

| RN | CAs que la cubren | Estado |
|----|-------------------|--------|
| RN-001 | CA-001, CA-007 | OK |
| RN-002 | CA-002, CA-003, CA-004 | OK |
| RN-003 | CA-001, CA-002 | OK |
| RN-004 | CA-003 | OK |
| RN-005 | CA-003 (parcial) | OK (REQUIERE CLARIFICACION reconocido) |
| RN-006 | CA-005 | OK |
| RN-007 | CA-001, CA-002, CA-006 | OK |
| RN-008 | CA-004 | OK |

### REQ-CF-003

| RN | CAs que la cubren | Estado |
|----|-------------------|--------|
| RN-001 | CA-001, CA-009 | OK |
| RN-002 | CA-001, CA-008 | OK |
| RN-003 | CA-004 | OK |
| RN-004 | CA-001, CA-003, CA-009 | OK |
| RN-005 | CA-003 | OK |
| RN-006 | CA-001 | OK |
| RN-007 | *(ninguno)* | **FALTA CA** (MAY-05) |
| RN-008 | CA-002, CA-009, CA-010 | OK |
| RN-009 | CA-002, CA-003, CA-009, CA-010 | OK |
| RN-010 | CA-006, CA-007 | OK |
| RN-011 | CA-005 | OK (pero depende de CRIT-02) |
| RN-012 | CA-008 | OK |

---

## Resumen de REQUIERE CLARIFICACION

Todos los items marcados como REQUIERE CLARIFICACION en los documentos son **genuinos** y necesarios para implementacion:

| Req | Item | Genuino | Prioridad para resolver |
|-----|------|---------|------------------------|
| CF-001 | Formato de viajes en selector | Si | Antes de implementar UI |
| CF-001 | Transicion de estado durante chat | Si | Antes de implementar |
| CF-002 | Paleta de colores multi-dia | Si | Puede diferirse a diseno |
| CF-002 | Costo en eventos cronograma | Si | Antes de implementar |
| CF-003 | Estimacion automatica de costos | Si | Antes de implementar |
| CF-003 | end_time por defecto | Si | **BLOQUEANTE** (CRIT-02) |
| CF-003 | Status planificado vs sugerido | Si | Antes de implementar |

---

## Conclusion

Los tres requerimientos estan **bien estructurados** y cubren la gran mayoria de escenarios. Las dependencias entre CF-001→CF-002 y CF-001→CF-003 son correctas y coherentes. Los principales riesgos son:

1. **CRIT-02 es bloqueante**: sin definir `end_time`, la deteccion de conflictos (RN-011) no se puede implementar.
2. **CRIT-01 es correccion inmediata**: cambiar "pendiente" por "planificado" en CF-002 CA-002.
3. **Los conflictos con CL-004 y UI-002** (MAY-02, MAY-03) requieren actualizacion de esos reqs para evitar ambiguedad durante implementacion.
4. **Las 7 clarificaciones pendientes** deben resolverse antes o durante la implementacion. La de `end_time` (CF-003) es la mas urgente.
