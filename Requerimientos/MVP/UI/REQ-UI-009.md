# REQ-UI-009 — Navegacion General y Estructura de la Interfaz

## Codigo
REQ-UI-009

## Titulo
Navegacion General - Estructura de navegacion, menu principal y accesibilidad global de la interfaz

## Prioridad MVP
Alta

## Historia de Usuario

**Como** viajero registrado,
**Quiero** navegar de forma clara e intuitiva entre las distintas secciones del sistema (Dashboard, Chat, Cronograma, Itinerario, Presupuesto, Perfil, Mis Viajes),
**Para** acceder rapidamente a cualquier funcionalidad sin perder el contexto de mi viaje activo.

## Descripcion

Este requerimiento define la estructura de navegacion global de la interfaz web del Trip Planner. Incluye el menu principal de navegacion, la disposicion general de las secciones, la persistencia del contexto del viaje activo al navegar entre secciones, y los aspectos transversales de accesibilidad y experiencia de uso. El chat con el agente es un panel lateral siempre accesible superpuesto a cualquier seccion.

## Reglas de Negocio

- **RN-001**: La interfaz cuenta con un menu de navegacion principal que da acceso a las secciones: Dashboard, Cronograma, Itinerario Detallado, Presupuesto, Perfil y Preferencias, y Mis Viajes.
- **RN-002**: El chat con el agente es accesible desde un boton o control fijo visible en todas las secciones, y se abre como un panel lateral que no reemplaza la seccion actual.
- **RN-003**: Al navegar entre secciones, el viaje activo se mantiene como contexto. Todas las secciones (excepto Perfil y Mis Viajes) muestran informacion del viaje activo seleccionado.
- **RN-004**: La interfaz debe indicar claramente en que seccion se encuentra el usuario y cual es el viaje activo actualmente.
- **RN-005**: La navegacion debe ser accesible mediante teclado (tabulacion y tecla Enter para activar controles). **REQUIERE CLARIFICACION:** No se define el nivel de cumplimiento de accesibilidad requerido (WCAG 2.1 nivel A, AA, etc.).

## Criterios de Aceptacion

**CA-001:** Menu de navegacion principal visible
  **Dado** que el usuario esta autenticado
  **Cuando** se encuentra en cualquier seccion de la interfaz
  **Entonces** el menu de navegacion principal es visible y muestra acceso a todas las secciones: Dashboard, Cronograma, Itinerario Detallado, Presupuesto, Perfil y Preferencias, Mis Viajes. La seccion actual esta destacada visualmente en el menu.

**CA-002:** Navegacion sin perdida de contexto
  **Dado** que el usuario tiene un viaje activo seleccionado y esta en la seccion de Cronograma
  **Cuando** navega a la seccion de Presupuesto
  **Entonces** la seccion de Presupuesto muestra la informacion del mismo viaje activo, sin que el usuario tenga que seleccionarlo nuevamente.

**CA-003:** Indicador de viaje activo
  **Dado** que el usuario tiene un viaje activo seleccionado
  **Cuando** se encuentra en cualquier seccion
  **Entonces** la interfaz muestra de forma visible el nombre y/o destino del viaje activo (por ejemplo, en la barra superior o en el encabezado de la seccion).

**CA-004:** Acceso al chat desde cualquier seccion
  **Dado** que el usuario esta en cualquier seccion de la interfaz
  **Cuando** hace clic en el boton/control de acceso al chat
  **Entonces** el panel lateral de chat se abre sin reemplazar la seccion actual, permitiendo al usuario interactuar con el agente mientras mantiene la vista de la seccion.

**CA-005:** Menu responsive en dispositivos moviles
  **Dado** que el usuario accede desde un dispositivo con pantalla de ancho reducido
  **Cuando** la interfaz se renderiza
  **Entonces** el menu de navegacion se adapta a un formato apropiado para pantallas pequenas (por ejemplo, menu hamburguesa o barra de navegacion inferior), manteniendo acceso a todas las secciones.

**CA-006:** Navegacion por teclado
  **Dado** que el usuario utiliza el teclado para navegar la interfaz
  **Cuando** presiona la tecla Tab
  **Entonces** el foco se desplaza de forma logica y secuencial entre los elementos interactivos del menu y la seccion activa, y la tecla Enter activa el elemento enfocado.

**CA-007:** Sin viaje activo - navegacion limitada
  **Dado** que el usuario esta autenticado pero no tiene ningun viaje seleccionado como activo
  **Cuando** intenta acceder a secciones que requieren un viaje activo (Dashboard, Cronograma, Itinerario, Presupuesto)
  **Entonces** el sistema redirige al usuario a la seccion Mis Viajes o muestra un mensaje indicando que debe seleccionar o crear un viaje primero.

## Dependencias
- Todos los demas requerimientos dependen de la estructura de navegacion definida en este requerimiento.

## Notas
- El menu de navegacion y la estructura general de la interfaz son transversales a todas las secciones. Cambios en este requerimiento impactan la experiencia global del usuario.
- **INFORMACION FALTANTE:** No se especifica si la interfaz soporta modo oscuro, personalizacion de temas, o configuracion de idioma.
- **INFORMACION FALTANTE:** No se define el flujo de autenticacion (login, registro, recuperacion de contrasena). Se asume que el usuario esta autenticado, pero no se documentan los requerimientos de autenticacion como parte de este MVP.
