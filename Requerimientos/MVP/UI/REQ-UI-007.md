# REQ-UI-007 — Perfil y Preferencias del Viajero

## Codigo
REQ-UI-007

## Titulo
Perfil y Preferencias del Viajero - Configuracion de preferencias para personalizar sugerencias del agente

## Prioridad MVP
Alta

## Historia de Usuario

**Como** viajero registrado,
**Quiero** configurar mi perfil con mis preferencias de viaje (tipo de alojamiento, restricciones alimentarias, estilo de viaje, presupuesto habitual, aerolineas y cadenas preferidas),
**Para** que el agente personalice sus sugerencias y planificaciones de acuerdo a mis gustos y necesidades sin que tenga que repetir esta informacion en cada viaje.

## Descripcion

La seccion de Perfil y Preferencias permite al usuario configurar informacion personal relevante para la planificacion de viajes. Estas preferencias son utilizadas por el agente para personalizar las sugerencias, busquedas y recomendaciones. Incluye: tipo de alojamiento preferido, restricciones alimentarias, estilo de viaje, presupuesto habitual, aerolineas o cadenas hoteleras preferidas, y otra informacion relevante. El perfil es persistente y se aplica a todos los viajes del usuario, aunque el agente puede ajustar sus sugerencias segun el contexto especifico de cada viaje.

## Reglas de Negocio

- **RN-001**: Las preferencias del perfil son opcionales. El usuario no esta obligado a completar todas las secciones. El agente funciona con o sin preferencias configuradas, pero su nivel de personalizacion aumenta con mas informacion.
- **RN-002**: Las preferencias del perfil se aplican como valores predeterminados para todos los viajes. El usuario puede solicitar al agente que ignore una preferencia particular para un viaje especifico.
- **RN-003**: Las categorias de preferencias incluyen:
  - Tipo de alojamiento preferido (hotel, hostel, apartamento, resort, etc.)
  - Restricciones alimentarias (vegetariano, vegano, celiaco, alergias especificas, etc.)
  - Estilo de viaje (aventura, relax, cultural, gastronomico, familiar, etc.)
  - Presupuesto habitual (rango de gasto diario o por viaje)
  - Aerolineas preferidas
  - Cadenas hoteleras preferidas
- **RN-004**: Los cambios en las preferencias se guardan y aplican a partir de la siguiente interaccion con el agente. No modifican retroactivamente viajes ya planificados. **REQUIERE CLARIFICACION:** No se define si el agente debe notificar al usuario cuando detecta una contradiccion entre las preferencias del perfil y una solicitud especifica del viaje.
- **RN-005**: El sistema aprende de viajes anteriores y puede sugerir actualizaciones a las preferencias del perfil. **REQUIERE CLARIFICACION:** No se define la mecanica exacta de este aprendizaje ni como se presentan las sugerencias de actualizacion al usuario.

## Criterios de Aceptacion

**CA-001:** Visualizacion del perfil de preferencias
  **Dado** que el usuario esta autenticado
  **Cuando** accede a la seccion Perfil y Preferencias del Viajero
  **Entonces** el sistema muestra un formulario organizado por categorias (alojamiento, alimentacion, estilo de viaje, presupuesto, aerolineas, cadenas hoteleras) con los valores actuales guardados (si existen) o los campos vacios si el usuario no ha configurado preferencias aun.

**CA-002:** Edicion de preferencias de alojamiento
  **Dado** que el usuario esta en la seccion de preferencias
  **Cuando** selecciona o modifica su tipo de alojamiento preferido (hotel, hostel, apartamento, resort, etc.)
  **Entonces** la seleccion se guarda y se aplica como preferencia predeterminada para futuras planificaciones del agente.

**CA-003:** Configuracion de restricciones alimentarias
  **Dado** que el usuario esta en la seccion de preferencias
  **Cuando** agrega, modifica o elimina restricciones alimentarias (vegetariano, vegano, celiaco, alergias especificas, etc.)
  **Entonces** las restricciones se guardan y el agente las considera al sugerir restaurantes y opciones de comida en futuros viajes.

**CA-004:** Seleccion de estilo de viaje
  **Dado** que el usuario esta en la seccion de preferencias
  **Cuando** selecciona uno o mas estilos de viaje (aventura, relax, cultural, gastronomico, familiar, etc.)
  **Entonces** la seleccion se guarda y el agente prioriza actividades y experiencias alineadas con el estilo seleccionado.

**CA-005:** Configuracion de presupuesto habitual
  **Dado** que el usuario esta en la seccion de preferencias
  **Cuando** define su rango de presupuesto habitual
  **Entonces** el valor se guarda y el agente lo utiliza como referencia para las sugerencias de costo, a menos que el usuario indique un presupuesto diferente para un viaje especifico.

**CA-006:** Seleccion de aerolineas y cadenas preferidas
  **Dado** que el usuario esta en la seccion de preferencias
  **Cuando** agrega o elimina aerolineas o cadenas hoteleras de su lista de preferidas
  **Entonces** la seleccion se guarda y el agente prioriza estas opciones en sus busquedas y sugerencias.

**CA-007:** Guardado de cambios en preferencias
  **Dado** que el usuario ha modificado una o mas preferencias
  **Cuando** confirma el guardado de los cambios
  **Entonces** el sistema guarda las preferencias, muestra una confirmacion visual de que los cambios se guardaron exitosamente, y las nuevas preferencias se aplican a partir de la siguiente interaccion con el agente.

**CA-008:** Perfil sin preferencias configuradas
  **Dado** que el usuario accede por primera vez a la seccion de preferencias y no ha configurado ninguna
  **Cuando** la vista se renderiza
  **Entonces** el sistema muestra todos los campos de preferencias vacios o con placeholders explicativos, y un mensaje indicando que completar las preferencias mejorara la calidad de las sugerencias del agente, sin bloquear ninguna funcionalidad del sistema.

**CA-009:** Validacion de datos de preferencias
  **Dado** que el usuario introduce un valor invalido en algun campo de preferencias (por ejemplo, un presupuesto negativo o caracteres no validos)
  **Cuando** intenta guardar los cambios
  **Entonces** el sistema muestra un mensaje de validacion claro junto al campo con error, indicando que debe corregir el valor, y no guarda los cambios hasta que la validacion sea exitosa.

**CA-010:** Estado de carga de preferencias
  **Dado** que el usuario accede a la seccion Perfil y Preferencias
  **Cuando** los datos de preferencias aun estan siendo cargados
  **Entonces** el sistema muestra indicadores de carga en los campos de preferencias hasta que los datos esten disponibles.

**CA-011:** Error al guardar preferencias
  **Dado** que el usuario ha modificado preferencias y confirma el guardado
  **Cuando** ocurre un error al guardar los datos
  **Entonces** el sistema muestra un mensaje de error indicando que los cambios no pudieron guardarse, los datos modificados se mantienen en el formulario para que el usuario no pierda sus cambios, y se ofrece la opcion de reintentar.

**CA-012:** Visualizacion responsive del perfil
  **Dado** que el usuario accede a la seccion de preferencias desde un dispositivo con pantalla de ancho reducido
  **Cuando** la vista se renderiza
  **Entonces** el formulario se adapta al ancho disponible con los campos organizados en una columna, manteniendo la legibilidad y la facilidad de interaccion tactil.

## Dependencias
- Ninguna. El perfil de preferencias es una seccion independiente que alimenta transversalmente al agente.

## Notas
- Las preferencias deben ser lo suficientemente flexibles para cubrir distintos perfiles de viajero sin ser abrumadoras. En el MVP, se recomienda un conjunto limitado de opciones predefinidas con la posibilidad de agregar texto libre para especificaciones adicionales.
- **INFORMACION FALTANTE:** No se especifica si el perfil incluye datos personales del viajero (nombre, documento de identidad, numero de pasaporte, fecha de nacimiento) necesarios para reservas, o si esos datos se manejan en otro modulo.
- **INFORMACION FALTANTE:** No se especifica si se permite multiples perfiles dentro de una misma cuenta (por ejemplo, para viajes familiares donde cada miembro tiene preferencias distintas).
