# Indice de Requerimientos Funcionales — Trip Planner MVP (Interfaz Web)

## Informacion General
- **Proyecto**: Trip Planner
- **Alcance**: MVP - Interfaz Web
- **Total de requerimientos**: 12
- **Fecha de generacion**: 2026-03-14

---

## Lista de Requerimientos

| Codigo | Titulo | Seccion | Prioridad |
|--------|--------|---------|-----------|
| REQ-UI-001 | Panel Overview - Vista general del viaje activo | Dashboard | Alta |
| REQ-UI-002 | Chat con el Agente - Interfaz conversacional lateral | Chat | Alta |
| REQ-UI-003 | Chat con el Agente - Solicitud de cambios y acciones sobre el itinerario | Chat | Alta |
| REQ-UI-004 | Cronograma / Calendario - Vista de calendario con itinerario planificado | Cronograma | Alta |
| REQ-UI-005 | Itinerario Detallado - Vista dia por dia con informacion completa | Itinerario | Alta |
| REQ-UI-006 | Presupuesto - Desglose por categoria con visualizacion grafica y comparacion estimado vs. real | Presupuesto | Alta |
| REQ-UI-007 | Perfil y Preferencias del Viajero - Configuracion de preferencias para personalizar sugerencias | Perfil | Alta |
| REQ-UI-008 | Mis Viajes - Historial de viajes planificados con acceso rapido y gestion de estados | Mis Viajes | Alta |
| REQ-UI-009 | Navegacion General - Estructura de navegacion, menu principal y accesibilidad global | Transversal | Alta |
| REQ-UI-010 | Dashboard - Visualizacion de informacion climatica y sistema de alertas | Dashboard | Media |
| REQ-UI-011 | Itinerario Detallado - Visualizacion de traslados y logistica entre actividades | Itinerario | Media |
| REQ-UI-012 | Perfil y Preferencias - Retroalimentacion post-viaje y aprendizaje de preferencias | Perfil | Media |

---

## Descripcion de cada Requerimiento

### REQ-UI-001 — Panel Overview - Vista general del viaje activo
Dashboard principal que muestra el resumen visual del viaje activo con datos clave: destino, fechas, presupuesto total, estado de planificacion, clima y alertas. Es la pantalla de entrada al sistema.

### REQ-UI-002 — Chat con el Agente - Interfaz conversacional lateral
Panel lateral siempre accesible para interactuar con el agente mediante texto. Soporta respuestas con tarjetas ricas (vuelos, hoteles, actividades), confirmaciones, y mantiene historial por viaje.

### REQ-UI-003 — Chat con el Agente - Solicitud de cambios y acciones sobre el itinerario
Capacidad del chat para que el usuario solicite modificaciones al itinerario (agregar, eliminar, reemplazar items) con deteccion de conflictos, confirmacion y sincronizacion en tiempo real con las demas secciones.

### REQ-UI-004 — Cronograma / Calendario - Vista de calendario con itinerario planificado
Vista de calendario interactiva (dia/semana/mes) con actividades, traslados y reservas como bloques horarios. Incluye drag & drop para reordenar actividades con validacion de conflictos.

### REQ-UI-005 — Itinerario Detallado - Vista dia por dia con informacion completa
Vista secuencial dia por dia con informacion exhaustiva de cada item: horarios, direcciones, notas, enlaces de reserva, estados (confirmado, pendiente, sugerido). Permite aceptar o descartar sugerencias del agente.

### REQ-UI-006 — Presupuesto - Desglose por categoria con visualizacion grafica
Desglose del presupuesto por categorias (vuelos, alojamiento, actividades, comidas, transporte local, extras) con graficos de distribucion y comparacion entre presupuesto estimado y gasto real.

### REQ-UI-007 — Perfil y Preferencias del Viajero - Configuracion de preferencias
Formulario para configurar preferencias de viaje: tipo de alojamiento, restricciones alimentarias, estilo de viaje, presupuesto habitual, aerolineas y cadenas preferidas. Alimenta al agente para personalizar sugerencias.

### REQ-UI-008 — Mis Viajes - Historial de viajes planificados con acceso rapido
Listado de todos los viajes del usuario con estados (en planificacion, confirmado, en curso, completado), filtrado por estado, creacion de nuevos viajes, y acceso rapido a cualquier viaje para ver su detalle.

### REQ-UI-009 — Navegacion General - Estructura de navegacion y accesibilidad
Menu de navegacion principal, estructura de secciones, persistencia del contexto del viaje activo al navegar, y aspectos transversales de accesibilidad (teclado) y responsive.

### REQ-UI-010 — Dashboard - Informacion climatica y alertas
Bloque de pronostico climatico del destino (pronostico para viajes proximos, datos historicos para viajes lejanos) y sistema de alertas sobre items que requieren atencion (documentos, confirmaciones, cambios).

### REQ-UI-011 — Itinerario Detallado - Traslados y logistica
Visualizacion de traslados entre actividades consecutivas en ubicaciones diferentes: medio de transporte, tiempo estimado, costo, y alertas de conflicto logistico por margen insuficiente.

### REQ-UI-012 — Perfil y Preferencias - Retroalimentacion post-viaje
Captura de retroalimentacion del usuario sobre viajes completados (valoracion general y por item individual) para que el agente aprenda y mejore sugerencias futuras.

---

## Resumen de Informacion Pendiente

A lo largo de los requerimientos se identificaron los siguientes vacios de informacion que requieren clarificacion del equipo de producto:

1. **Fuente de datos climaticos** (REQ-UI-001, REQ-UI-010): No se define la fuente ni la frecuencia de actualizacion.
2. **Taxonomia de alertas** (REQ-UI-001, REQ-UI-010): No se define la clasificacion completa de tipos de alerta ni sus niveles de prioridad ni las reglas de temporalidad para su generacion.
3. **Acciones que requieren confirmacion del agente** (REQ-UI-002): No se define que acciones requieren confirmacion explicita y cuales puede ejecutar el agente autonomamente.
4. **Soporte multimedia en el chat** (REQ-UI-002): No se especifica si el chat soporta imagenes, documentos o notas de voz.
5. **Historial de cambios del itinerario** (REQ-UI-003): No se define si el historial de cambios es visible para el usuario.
6. **Categorizacion visual del calendario** (REQ-UI-004): No se define la paleta de colores o iconografia para cada tipo de item.
7. **Creacion de items desde el calendario** (REQ-UI-004): No se especifica si se pueden crear items directamente haciendo clic en un espacio vacio.
8. **Transicion de estados de items** (REQ-UI-005): No se define si el usuario puede cambiar un item de "pendiente" a "confirmado" manualmente.
9. **Registro de gastos reales** (REQ-UI-006): No se define el mecanismo para registrar gastos reales ni si es parte del MVP.
10. **Moneda y conversion de divisas** (REQ-UI-006): No se especifica la moneda del presupuesto ni si se soportan multiples monedas.
11. **Tope de presupuesto** (REQ-UI-006): No se define si el usuario puede establecer un presupuesto maximo con alertas de exceso.
12. **Datos personales del viajero** (REQ-UI-007): No se especifica si el perfil incluye datos de identidad para reservas (pasaporte, etc.).
13. **Perfiles multiples** (REQ-UI-007): No se define si se permiten multiples perfiles por cuenta (viajes familiares).
14. **Viajes con fechas solapadas** (REQ-UI-008): No se define el comportamiento si el usuario tiene viajes con fechas que se superponen.
15. **Edicion de viaje desde lista** (REQ-UI-008): No se especifica si se puede editar nombre/fechas del viaje desde la lista.
16. **Viajes compartidos** (REQ-UI-008): No se define si existe planificacion colaborativa.
17. **Nivel de accesibilidad** (REQ-UI-009): No se define el nivel de cumplimiento WCAG requerido.
18. **Autenticacion** (REQ-UI-009): No se documentan los flujos de login, registro y recuperacion de contrasena.
19. **Modo oscuro e idioma** (REQ-UI-009): No se especifica soporte de temas o internacionalizacion.
20. **Calculo de tiempos de traslado** (REQ-UI-011): No se define como se calculan los tiempos ni si se considera trafico.
21. **Escala de valoracion post-viaje** (REQ-UI-012): No se define la escala de retroalimentacion ni que items son valorables.
22. **Mecanica de aprendizaje del agente** (REQ-UI-012): No se define como la retroalimentacion ajusta el comportamiento del agente.

---

## Mapa de Dependencias

```
REQ-UI-009 (Navegacion General)
  └── Todos los demas requerimientos dependen de la navegacion

REQ-UI-001 (Dashboard)
  ├── REQ-UI-007 (Perfil)
  ├── REQ-UI-008 (Mis Viajes)
  └── REQ-UI-010 (Clima y Alertas) [extiende Dashboard]

REQ-UI-002 (Chat - Interfaz)
  ├── REQ-UI-007 (Perfil)
  └── REQ-UI-003 (Chat - Acciones) [extiende Chat]

REQ-UI-003 (Chat - Acciones)
  ├── REQ-UI-002 (Chat - Interfaz)
  ├── REQ-UI-004 (Cronograma)
  ├── REQ-UI-005 (Itinerario)
  └── REQ-UI-006 (Presupuesto)

REQ-UI-004 (Cronograma)
  ├── REQ-UI-005 (Itinerario) [datos compartidos]
  └── REQ-UI-006 (Presupuesto)

REQ-UI-005 (Itinerario)
  ├── REQ-UI-004 (Cronograma) [datos compartidos]
  ├── REQ-UI-006 (Presupuesto)
  └── REQ-UI-011 (Traslados) [extiende Itinerario]

REQ-UI-006 (Presupuesto)
  └── REQ-UI-005 (Itinerario)

REQ-UI-008 (Mis Viajes)
  ├── REQ-UI-001 (Dashboard)
  ├── REQ-UI-002 (Chat)
  └── REQ-UI-012 (Retroalimentacion) [extiende Mis Viajes]

REQ-UI-012 (Retroalimentacion)
  ├── REQ-UI-008 (Mis Viajes)
  ├── REQ-UI-007 (Perfil)
  └── REQ-UI-005 (Itinerario)
```
