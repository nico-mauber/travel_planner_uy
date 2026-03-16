"""Componentes del chat: tarjetas ricas, resultados de hoteles y confirmaciones.

Usa clases tp-* del design system (config/styles/base.py) para estilos
consistentes con micro-interacciones. Todos los elementos HTML incluyen
atributos ARIA para accesibilidad.
"""

import html as html_module

import streamlit as st
from config.settings import ITEM_TYPE_ICONS, ItemType


def _format_rating_stars(rating_str: str) -> str:
    """Convierte un rating numerico a estrellas visuales con valor.

    Soporta formatos: "8.5", "8.5/10", "4.2/5".
    Retorna estrellas (sobre 5) mas el valor numerico original.
    """
    if not rating_str:
        return ""
    # Extraer el numero del rating
    clean = str(rating_str).strip()
    try:
        # Manejar formatos como "8.5/10" o "4.2/5"
        if "/" in clean:
            parts = clean.split("/")
            value = float(parts[0])
            scale = float(parts[1])
        else:
            value = float(clean)
            scale = 10.0 if value > 5 else 5.0
        # Normalizar a escala de 5
        normalized = (value / scale) * 5
        full_stars = int(normalized)
        has_half = (normalized - full_stars) >= 0.25
        empty_stars = 5 - full_stars - (1 if has_half else 0)
        stars = "\u2605" * full_stars
        if has_half:
            stars += "\u2606"
        stars += "\u2606" * empty_stars
        return f"{stars} {clean}"
    except (ValueError, ZeroDivisionError):
        return clean


def render_rich_card(card_data: dict) -> None:
    """Renderiza una tarjeta rica dentro del chat (vuelo, hotel, actividad, comida)."""
    card_type = card_data.get("card_type", "activity")
    icon = ITEM_TYPE_ICONS.get(
        {
            "flight": ItemType.FLIGHT,
            "hotel": ItemType.ACCOMMODATION,
            "activity": ItemType.ACTIVITY,
            "food": ItemType.FOOD,
        }.get(card_type, ItemType.ACTIVITY),
        "\U0001F4E6",
    )

    name = html_module.escape(str(card_data.get("name", "Sin nombre")))
    provider = html_module.escape(str(card_data.get("provider", "")))
    location = html_module.escape(str(card_data.get("location", "")))
    duration = html_module.escape(str(card_data.get("duration", "")))
    departure = html_module.escape(str(card_data.get("departure", "")))
    arrival = html_module.escape(str(card_data.get("arrival", "")))
    notes = html_module.escape(str(card_data.get("notes", "")))

    # Precio y clase de color
    price = card_data.get("price")
    price_html = ""
    if price:
        try:
            price_val = float(price)
            # Precios bajo 200 USD se consideran economicos
            price_class = "tp-rich-card__price" if price_val < 200 else "tp-rich-card__price tp-rich-card__price--high"
            price_html = f'<div class="{price_class}">USD {price_val:,.0f}</div>'
        except (ValueError, TypeError):
            price_html = f'<div class="tp-rich-card__price">{html_module.escape(str(price))}</div>'

    # Rating con estrellas
    rating_raw = card_data.get("rating", "")
    rating_html = ""
    if rating_raw:
        rating_formatted = _format_rating_stars(str(rating_raw))
        rating_html = f'<div class="tp-rich-card__rating">{html_module.escape(rating_formatted)}</div>'

    # Construir grid de detalles
    left_details = ""
    if location:
        left_details += f'<div class="tp-rich-card__detail">\U0001F4CD {location}</div>'
    if duration:
        left_details += f'<div class="tp-rich-card__detail">\u23F1\uFE0F {duration}</div>'
    if departure:
        flight_info = f"\U0001F551 {departure}"
        if arrival:
            flight_info += f" \u2192 {arrival}"
        left_details += f'<div class="tp-rich-card__detail">{flight_info}</div>'

    right_details = price_html + rating_html

    # Provider
    provider_html = f'<div class="tp-rich-card__provider">{provider}</div>' if provider else ""

    # Notas
    notes_html = f'<div class="tp-rich-card__notes">{notes}</div>' if notes else ""

    # Grid: solo si hay contenido en ambas columnas
    grid_html = ""
    if left_details or right_details:
        grid_html = f'<div class="tp-rich-card__grid">'
        grid_html += f'<div>{left_details}</div>'
        grid_html += f'<div>{right_details}</div>'
        grid_html += '</div>'

    # Aria label descriptivo
    aria_label = f"Tarjeta de {card_type}: {card_data.get('name', 'Sin nombre')}"

    card_html = (
        f'<div class="tp-rich-card" role="article" aria-label="{html_module.escape(aria_label)}">'
        f'  <div class="tp-rich-card__icon">{icon}</div>'
        f'  <div class="tp-rich-card__body">'
        f'    <div class="tp-rich-card__name">{name}</div>'
        f'    {provider_html}'
        f'    {grid_html}'
        f'    {notes_html}'
        f'  </div>'
        f'</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)

    # Boton de enlace fuera del HTML (Streamlit nativo para interactividad)
    if card_data.get("booking_url"):
        st.link_button("\U0001F517 Ver en Booking.com", card_data["booking_url"])


def render_hotel_results(data: dict) -> None:
    """Renderiza resultados de busqueda de hoteles de Booking.com."""
    text = data.get("text", "")
    hotels = data.get("hotels", [])

    if text:
        st.markdown(text)

    if not hotels:
        st.info("No se encontraron hoteles disponibles para las fechas del viaje.")
        return

    # Header con contador y badge Booking.com
    header_html = (
        '<div class="tp-hotel-header">'
        f'  <span class="tp-hotel-header__count">\U0001F3E8 {len(hotels)} hoteles encontrados</span>'
        '  <span class="tp-hotel-header__badge">Booking.com</span>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    for i, hotel in enumerate(hotels):
        render_rich_card(hotel)
        # Separador sutil entre cards (excepto la ultima)
        if i < len(hotels) - 1:
            st.markdown('<hr class="tp-hotel-separator">', unsafe_allow_html=True)

    # Credito estilizado
    st.markdown(
        '<div class="tp-hotel-credit">Datos proporcionados por Booking.com via RapidAPI</div>',
        unsafe_allow_html=True,
    )


_CREATE_TRIP_LABELS = {
    "destination": "Destino",
    "name": "Nombre",
    "start_date": "Fecha inicio",
    "end_date": "Fecha fin",
}

_ADD_ITEM_LABELS = {
    "name": "Actividad",
    "day": "Dia",
    "start_time": "Hora inicio",
    "end_time": "Hora fin",
    "item_type": "Tipo",
    "location": "Ubicacion",
    "cost_estimated": "Costo estimado",
    "end_day": "Hasta dia",
}

_REMOVE_ITEM_LABELS = {
    "name": "Actividad",
    "item_id": "ID",
}

# Iconos contextuales por tipo de accion
_ACTION_ICONS = {
    "create_trip": "\U0001F30D",
    "add_item": "\u2795",
    "remove_item": "\U0001F5D1\uFE0F",
    "calendar_event": "\U0001F4C5",
}

# Modificador CSS por tipo de accion
_ACTION_CSS_MODIFIER = {
    "create_trip": "tp-confirmation--add",
    "add_item": "tp-confirmation--add",
    "remove_item": "tp-confirmation--delete",
    "calendar_event": "",
}


def render_confirmation(action_data: dict, msg_index: int) -> str:
    """Renderiza una solicitud de confirmacion. Retorna 'confirm', 'cancel' o ''."""
    action = action_data.get("action", "")
    summary = html_module.escape(str(action_data.get("summary", "Accion pendiente")))
    action_icon = _ACTION_ICONS.get(action, "\u26A0\uFE0F")
    css_modifier = _ACTION_CSS_MODIFIER.get(action, "")

    details = action_data.get("details", {})
    is_create_trip = action == "create_trip"

    # Construir lista de detalles formateada
    detail_items_html = ""
    if details:
        items_html = ""
        for key, val in details.items():
            # Omitir campos internos (prefijo _) y valores vacios
            if key.startswith("_") or key in ("action",) or not val:
                continue
            if is_create_trip:
                label = _CREATE_TRIP_LABELS.get(key, key)
            elif action == "add_item":
                label = _ADD_ITEM_LABELS.get(key, key)
            elif action == "remove_item":
                label = _REMOVE_ITEM_LABELS.get(key, key)
            else:
                label = key
            safe_val = html_module.escape(str(val))
            safe_label = html_module.escape(str(label))
            items_html += f'<li><strong>{safe_label}:</strong> {safe_val}</li>'
        if items_html:
            detail_items_html = f'<ul class="tp-confirmation__details">{items_html}</ul>'

    confirmation_html = (
        f'<div class="tp-confirmation {css_modifier}">'
        f'  <div class="tp-confirmation__header">'
        f'    <span class="tp-confirmation__icon">{action_icon}</span>'
        f'    <span class="tp-confirmation__title">{summary}</span>'
        f'  </div>'
        f'  {detail_items_html}'
        f'</div>'
    )

    st.markdown(confirmation_html, unsafe_allow_html=True)

    # Botones nativos Streamlit para interactividad
    cols = st.columns(2)
    with cols[0]:
        if st.button(
            "\u2705 Confirmar",
            key=f"confirm_{msg_index}",
            type="primary",
            use_container_width=True,
        ):
            return "confirm"
    with cols[1]:
        if st.button(
            "\u274C Cancelar",
            key=f"cancel_{msg_index}",
            use_container_width=True,
        ):
            return "cancel"

    return ""
