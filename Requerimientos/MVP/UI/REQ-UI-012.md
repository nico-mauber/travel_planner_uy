# REQ-UI-012 — Perfil y Preferencias: Aprendizaje y Retroalimentacion Post-Viaje

## Codigo
REQ-UI-012

## Titulo
Perfil y Preferencias - Retroalimentacion post-viaje y aprendizaje de preferencias

## Prioridad MVP
Media

## Historia de Usuario

**Como** viajero registrado que ha completado un viaje,
**Quiero** poder indicar que me gusto y que no me gusto del viaje completado,
**Para** que el agente aprenda de mi experiencia y mejore las sugerencias para mis proximos viajes.

## Descripcion

Una vez que un viaje pasa al estado "completado", el sistema ofrece al usuario la posibilidad de proporcionar retroalimentacion sobre la experiencia. Esta retroalimentacion puede ser general (calificacion del viaje) o especifica (valorar items individuales del itinerario). El agente utiliza esta informacion para refinar el perfil de preferencias del usuario y mejorar la calidad de las sugerencias en viajes futuros.

## Reglas de Negocio

- **RN-001**: La retroalimentacion se habilita cuando un viaje transiciona al estado "completado".
- **RN-002**: La retroalimentacion es opcional. El usuario no esta obligado a proporcionarla.
- **RN-003**: El usuario puede valorar items individuales del itinerario indicando si le gusto o no le gusto, y opcionalmente agregar un comentario breve. **REQUIERE CLARIFICACION:** No se define la escala de valoracion (binaria gusta/no gusta, estrellas 1-5, etc.) ni que items son valorables.
- **RN-004**: El agente utiliza la retroalimentacion acumulada de viajes completados para ajustar las sugerencias futuras. Por ejemplo, si el usuario valoró negativamente un tipo de actividad de forma recurrente, el agente evitara sugerirla en el futuro. **REQUIERE CLARIFICACION:** No se define la mecanica exacta de como la retroalimentacion ajusta el comportamiento del agente.
- **RN-005**: La retroalimentacion proporcionada se almacena asociada al viaje completado y al perfil del usuario.

## Criterios de Aceptacion

**CA-001:** Solicitud de retroalimentacion post-viaje
  **Dado** que un viaje del usuario transiciona al estado "completado"
  **Cuando** el usuario accede al sistema despues de la finalizacion del viaje
  **Entonces** el sistema presenta una invitacion a proporcionar retroalimentacion sobre el viaje completado (por ejemplo, una notificacion en el dashboard o un mensaje del agente en el chat).

**CA-002:** Retroalimentacion general del viaje
  **Dado** que el usuario accede a la retroalimentacion de un viaje completado
  **Cuando** proporciona una valoracion general del viaje
  **Entonces** la valoracion se guarda asociada al viaje y al perfil del usuario.

**CA-003:** Retroalimentacion por item del itinerario
  **Dado** que el usuario accede a la retroalimentacion de un viaje completado
  **Cuando** valora un item individual del itinerario (indicando si le gusto o no le gusto, con comentario opcional)
  **Entonces** la valoracion se guarda asociada al item, al viaje y al perfil del usuario.

**CA-004:** Omitir retroalimentacion
  **Dado** que el sistema invita al usuario a proporcionar retroalimentacion sobre un viaje completado
  **Cuando** el usuario decide omitir o cerrar la invitacion de retroalimentacion
  **Entonces** la invitacion se cierra, el viaje completado queda sin retroalimentacion, y el sistema no vuelve a solicitar retroalimentacion para ese viaje de forma intrusiva (puede mantener un acceso discreto desde la vista del viaje completado).

**CA-005:** Acceso posterior a retroalimentacion
  **Dado** que el usuario tiene un viaje completado para el cual no proporcionó retroalimentacion, o desea modificar la retroalimentacion ya dada
  **Cuando** accede al viaje completado desde la seccion Mis Viajes
  **Entonces** la opcion de proporcionar o editar retroalimentacion esta disponible desde la vista del viaje.

## Dependencias
- REQ-UI-008 (Mis Viajes): la transicion a "completado" habilita la retroalimentacion.
- REQ-UI-007 (Perfil y Preferencias): la retroalimentacion alimenta el perfil de preferencias del usuario.
- REQ-UI-005 (Itinerario Detallado): la retroalimentacion por item se basa en los items del itinerario.

## Notas
- Este requerimiento es clave para la propuesta de valor del sistema ("cada viaje lo hace mas inteligente"). Sin embargo, el mecanismo de aprendizaje del agente es un aspecto del backend/agente y no de la interfaz. El MVP de la interfaz debe cubrir la captura de retroalimentacion.
- **INFORMACION FALTANTE:** No se define si el sistema sugiere actualizaciones al perfil de preferencias basandose en la retroalimentacion (por ejemplo, "notamos que te gustaron las actividades culturales, quieres agregar 'cultural' a tus estilos de viaje preferidos?").
