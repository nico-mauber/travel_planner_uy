# REQ-UI-006 — Presupuesto: Desglose y Visualizacion del Presupuesto del Viaje

## Codigo
REQ-UI-006

## Titulo
Presupuesto - Desglose por categoria con visualizacion grafica y comparacion estimado vs. real

## Prioridad MVP
Alta

## Historia de Usuario

**Como** viajero registrado,
**Quiero** visualizar el presupuesto de mi viaje desglosado por categorias con graficos y comparar el presupuesto estimado contra el gasto real,
**Para** controlar mis gastos, identificar en que categorias estoy invirtiendo mas y tomar decisiones informadas sobre ajustes al plan.

## Descripcion

La seccion de Presupuesto muestra el desglose financiero del viaje organizado por categorias: vuelos, alojamiento, actividades, comidas, transporte local y extras. Incluye visualizaciones graficas (por ejemplo, graficos de torta o barras) que permiten al usuario entender la distribucion de su gasto. Ademas, ofrece una comparacion entre el presupuesto estimado (planificado) y el gasto real (cuando aplique), permitiendo al usuario monitorear desviaciones.

## Reglas de Negocio

- **RN-001**: Las categorias de presupuesto son: vuelos, alojamiento, actividades, comidas, transporte local y extras.
- **RN-002**: El presupuesto estimado se calcula como la suma de los costos estimados de todos los items del itinerario en estado "pendiente" o "confirmado", agrupados por categoria. Los items en estado "sugerido" no se contabilizan en el presupuesto estimado.
- **RN-003**: El gasto real se registra a partir de los costos reales de items en estado "confirmado" que tengan un costo real diferente al estimado, o de gastos adicionales registrados por el usuario. **REQUIERE CLARIFICACION:** No se define el mecanismo por el cual el usuario registra gastos reales durante o despues del viaje, ni si esto es parte del MVP.
- **RN-004**: La comparacion estimado vs. real solo se muestra cuando existen datos de gasto real. Si no hay gastos reales registrados, la vista muestra solo el presupuesto estimado.
- **RN-005**: El presupuesto total es la suma de todas las categorias. **REQUIERE CLARIFICACION:** No se especifica si el usuario puede definir un tope de presupuesto maximo para el viaje, y si el sistema debe alertar cuando se supere.
- **RN-006**: Cuando se agregan, eliminan o modifican items del itinerario (desde el chat o desde el itinerario detallado), el presupuesto estimado debe recalcularse automaticamente.

## Criterios de Aceptacion

**CA-001:** Vista del presupuesto con desglose por categorias
  **Dado** que el usuario tiene un viaje activo con items que tienen costos estimados
  **Cuando** accede a la seccion Presupuesto
  **Entonces** el sistema muestra el presupuesto total estimado del viaje y un desglose por cada categoria (vuelos, alojamiento, actividades, comidas, transporte local, extras), indicando el monto estimado de cada categoria y su porcentaje respecto al total.

**CA-002:** Visualizacion grafica del presupuesto
  **Dado** que el usuario esta en la seccion Presupuesto y existen costos estimados
  **Cuando** la vista se renderiza
  **Entonces** el sistema muestra al menos una visualizacion grafica (grafico de torta, barras u otro) que representa la distribucion del presupuesto por categorias, permitiendo al usuario identificar visualmente las categorias de mayor gasto.

**CA-003:** Comparacion presupuesto estimado vs. gasto real
  **Dado** que el usuario tiene un viaje con items que tienen tanto costo estimado como costo real registrado
  **Cuando** accede a la seccion Presupuesto
  **Entonces** el sistema muestra una comparacion visual entre el monto estimado y el monto real para cada categoria, indicando la diferencia (positiva o negativa) y el porcentaje de desviacion.

**CA-004:** Presupuesto sin datos de gasto real
  **Dado** que el usuario tiene un viaje activo pero no se han registrado gastos reales
  **Cuando** accede a la seccion Presupuesto
  **Entonces** el sistema muestra solo el presupuesto estimado con su desglose por categorias, sin la columna o seccion de gasto real. No se muestran valores vacios o ceros confusos en la columna de gasto real.

**CA-005:** Presupuesto vacio (viaje sin costos)
  **Dado** que el usuario tiene un viaje activo pero ningun item del itinerario tiene costo estimado asignado
  **Cuando** accede a la seccion Presupuesto
  **Entonces** el sistema muestra un estado vacio indicando que no hay informacion de presupuesto disponible y sugiere al usuario que interactue con el agente para agregar items con costos estimados.

**CA-006:** Recalculo automatico del presupuesto
  **Dado** que el usuario ha realizado cambios al itinerario (agregar, eliminar o modificar items con costos)
  **Cuando** navega a la seccion Presupuesto
  **Entonces** el presupuesto refleja los cambios: nuevos items estan contabilizados en su categoria correspondiente, items eliminados ya no se contabilizan, e items modificados reflejan su nuevo costo. El total y los graficos estan actualizados.

**CA-007:** Detalle por categoria
  **Dado** que el usuario esta en la seccion Presupuesto y hay items agrupados por categoria
  **Cuando** hace clic en una categoria especifica (por ejemplo, "Alojamiento")
  **Entonces** el sistema muestra el listado de items que componen esa categoria con su nombre, costo estimado (y costo real si existe), permitiendo al usuario entender la composicion del gasto de esa categoria.

**CA-008:** Estado de carga del presupuesto
  **Dado** que el usuario accede a la seccion Presupuesto
  **Cuando** los datos aun estan siendo cargados
  **Entonces** el sistema muestra indicadores de carga en lugar de los graficos y montos, sin mostrar valores parciales o incorrectos.

**CA-009:** Error al cargar el presupuesto
  **Dado** que el usuario accede a la seccion Presupuesto
  **Cuando** ocurre un error al recuperar los datos
  **Entonces** el sistema muestra un mensaje de error y ofrece la opcion de reintentar la carga.

**CA-010:** Visualizacion responsive del presupuesto
  **Dado** que el usuario accede a la seccion Presupuesto desde un dispositivo con pantalla de ancho reducido
  **Cuando** la vista se renderiza
  **Entonces** los graficos se adaptan al ancho disponible manteniendo legibilidad, las tablas de desglose pueden hacer scroll horizontal si es necesario, y los montos son legibles sin necesidad de zoom.

## Dependencias
- REQ-UI-005 (Itinerario Detallado): el presupuesto se calcula a partir de los costos de los items del itinerario.
- REQ-UI-003 (Chat - Acciones sobre itinerario): cambios desde el chat que afecten costos actualizan el presupuesto.

## Notas
- La precision del presupuesto depende de la calidad de los costos estimados proporcionados por el agente. Los costos estimados son aproximaciones que pueden variar al momento de la reserva real.
- **INFORMACION FALTANTE:** No se especifica la moneda en la que se muestra el presupuesto, ni si el sistema soporta multiples monedas o conversion de divisas. Para un viaje internacional, los costos pueden estar en diferentes monedas.
- **INFORMACION FALTANTE:** No se especifica si el usuario puede editar manualmente los costos estimados de un item desde esta vista.
