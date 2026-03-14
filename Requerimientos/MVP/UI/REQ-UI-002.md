# REQ-UI-002 — Chat con el Agente: Interfaz Conversacional

## Codigo
REQ-UI-002

## Titulo
Chat con el Agente - Interfaz conversacional lateral

## Prioridad MVP
Alta

## Historia de Usuario

**Como** viajero registrado,
**Quiero** interactuar con el agente de planificacion a traves de una interfaz de chat siempre accesible desde un panel lateral,
**Para** dar instrucciones, hacer preguntas y solicitar cambios a mi itinerario de forma natural mediante lenguaje conversacional.

## Descripcion

El Chat con el Agente es un panel lateral siempre accesible desde cualquier seccion de la interfaz. Permite al usuario comunicarse con el agente de planificacion mediante texto. El agente responde con texto enriquecido y puede presentar tarjetas ricas (vuelos, hoteles, actividades) dentro del flujo conversacional. El agente puede solicitar confirmaciones al usuario antes de ejecutar acciones. El chat mantiene el historial de la conversacion asociado al viaje activo.

## Reglas de Negocio

- **RN-001**: El panel de chat debe estar accesible desde todas las secciones de la interfaz (dashboard, cronograma, itinerario, presupuesto, perfil, mis viajes).
- **RN-002**: El historial de conversacion se mantiene asociado al viaje activo. Al cambiar de viaje, el historial mostrado corresponde al viaje seleccionado.
- **RN-003**: El agente puede presentar contenido enriquecido dentro del chat: tarjetas de vuelos, tarjetas de hoteles, tarjetas de actividades, con informacion visual estructurada.
- **RN-004**: Antes de ejecutar acciones que modifiquen el itinerario, el presupuesto o cualquier reserva, el agente debe solicitar confirmacion explicita del usuario. **REQUIERE CLARIFICACION:** No se define que acciones especificas requieren confirmacion y cuales puede ejecutar el agente autonomamente.
- **RN-005**: El panel de chat puede abrirse y cerrarse sin perder el contexto de la conversacion en curso.
- **RN-006**: El usuario puede iniciar una nueva planificacion de viaje directamente desde el chat dando una instruccion al agente (por ejemplo: "quiero viajar a Europa en septiembre").

## Criterios de Aceptacion

**CA-001:** Acceso al chat desde cualquier seccion
  **Dado** que el usuario esta autenticado y se encuentra en cualquier seccion de la interfaz (dashboard, cronograma, itinerario, presupuesto, perfil, mis viajes)
  **Cuando** hace clic en el control de apertura del panel de chat
  **Entonces** el panel lateral de chat se abre mostrando el historial de conversacion del viaje activo, sin perder la vista de la seccion actual.

**CA-002:** Envio de mensaje al agente
  **Dado** que el usuario tiene el panel de chat abierto
  **Cuando** escribe un mensaje en el campo de entrada y lo envia (mediante boton de envio o tecla Enter)
  **Entonces** el mensaje del usuario aparece en el flujo conversacional, se muestra un indicador de que el agente esta procesando la respuesta, y el agente responde con texto, tarjetas ricas o una combinacion de ambos segun corresponda al contexto de la consulta.

**CA-003:** Visualizacion de tarjetas ricas en el chat
  **Dado** que el usuario solicita al agente informacion sobre vuelos, hoteles o actividades
  **Cuando** el agente responde con opciones
  **Entonces** el chat muestra tarjetas ricas con informacion estructurada (nombre, precio, horarios, imagenes si aplica, calificacion) que permiten al usuario visualizar las opciones sin salir del chat.

**CA-004:** Confirmacion de acciones del agente
  **Dado** que el usuario solicita al agente una accion que modifica el itinerario o el presupuesto
  **Cuando** el agente esta listo para ejecutar la accion
  **Entonces** el agente presenta un resumen de la accion a realizar y solicita confirmacion explicita del usuario (por ejemplo, botones de "Confirmar" y "Cancelar") antes de proceder.

**CA-005:** Cierre y reapertura del panel de chat
  **Dado** que el usuario tiene el panel de chat abierto con una conversacion en curso
  **Cuando** cierra el panel de chat y luego lo vuelve a abrir
  **Entonces** el historial de la conversacion se mantiene intacto, incluyendo todos los mensajes y tarjetas ricas previas, y el scroll se posiciona en el ultimo mensaje.

**CA-006:** Inicio de planificacion desde el chat
  **Dado** que el usuario no tiene un viaje en planificacion y abre el chat
  **Cuando** escribe una instruccion de planificacion (por ejemplo, "quiero viajar a Japon en diciembre")
  **Entonces** el agente inicia el proceso de planificacion creando un nuevo viaje en estado "en planificacion" y comienza a recopilar informacion y ofrecer sugerencias basadas en las preferencias del usuario.

**CA-007:** Cambio de contexto entre viajes
  **Dado** que el usuario tiene multiples viajes y cambia el viaje activo desde la seccion "Mis Viajes"
  **Cuando** abre el panel de chat
  **Entonces** el historial de conversacion mostrado corresponde al viaje activo seleccionado, no al viaje anterior.

**CA-008:** Estado de carga de respuesta del agente
  **Dado** que el usuario ha enviado un mensaje al agente
  **Cuando** el agente esta procesando la respuesta
  **Entonces** el sistema muestra un indicador visual de que el agente esta "pensando" o procesando (por ejemplo, indicador de escritura con puntos animados), el campo de entrada permanece visible pero puede deshabilitarse para evitar envios multiples simultaneos.

**CA-009:** Error en la comunicacion con el agente
  **Dado** que el usuario ha enviado un mensaje al agente
  **Cuando** ocurre un error de comunicacion o el agente no puede procesar la solicitud
  **Entonces** el sistema muestra un mensaje de error en el flujo conversacional indicando que la solicitud no pudo ser procesada, y ofrece la opcion de reintentar el envio del ultimo mensaje.

**CA-010:** Chat sin viaje activo
  **Dado** que el usuario esta autenticado pero no tiene ningun viaje creado
  **Cuando** abre el panel de chat
  **Entonces** el chat muestra un mensaje de bienvenida del agente invitando al usuario a comenzar a planificar un viaje, y el campo de entrada esta habilitado para recibir la primera instruccion.

**CA-011:** Scroll en conversaciones extensas
  **Dado** que el historial de conversacion del viaje activo contiene muchos mensajes
  **Cuando** el usuario abre el panel de chat
  **Entonces** el chat se posiciona automaticamente en el ultimo mensaje, y el usuario puede hacer scroll hacia arriba para ver mensajes anteriores de forma fluida.

**CA-012:** Visualizacion responsive del panel de chat
  **Dado** que el usuario accede desde un dispositivo con pantalla de ancho reducido
  **Cuando** abre el panel de chat
  **Entonces** el panel de chat ocupa el ancho completo de la pantalla (en lugar de ser un panel lateral parcial), con un control claro para cerrarlo y volver a la vista principal.

## Dependencias
- REQ-UI-007 (Perfil y Preferencias del Viajero): el agente utiliza las preferencias del usuario para personalizar sus respuestas y sugerencias.

## Notas
- El chat es el canal principal de interaccion del usuario con el sistema agente. Su disponibilidad y fluidez son criticos para la experiencia de uso.
- Las tarjetas ricas dentro del chat deben ser consistentes visualmente con las tarjetas mostradas en el itinerario detallado.
- **INFORMACION FALTANTE:** No se especifica si el chat soporta envio de imagenes, documentos o notas de voz por parte del usuario, ni si el agente puede responder con contenido multimedia mas alla de tarjetas ricas.
