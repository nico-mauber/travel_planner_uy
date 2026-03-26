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
    """Renderiza resultados de busqueda de hoteles como cards compactas."""
    text = data.get("text", "")
    hotels = data.get("hotels", [])

    if text:
        st.markdown(text)

    if not hotels:
        st.info("No se encontraron hoteles disponibles para las fechas del viaje.")
        return

    # Header
    header_html = (
        '<div class="tp-hotel-header">'
        f'  <span class="tp-hotel-header__count">\U0001F3E8 {len(hotels)} hoteles encontrados</span>'
        '  <span class="tp-hotel-header__badge">Booking.com</span>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # Renderizar cada hotel como card con thumbnail
    for h in hotels:
        name = html_module.escape(str(h.get("name", "Hotel")))
        location = html_module.escape(str(h.get("location", "")))
        price = h.get("price", 0)
        price_str = f"US${price:,.0f}" if price else "\u2014"
        stars = int(h.get("stars", 0) or 0)
        stars_html = "\u2B50" * stars if stars else ""
        review_score = h.get("review_score", 0)
        review_word = html_module.escape(str(h.get("review_word", "")))
        review_count = h.get("review_count", 0)
        checkin_time = html_module.escape(str(h.get("checkin_time", "")))
        checkout_time = html_module.escape(str(h.get("checkout_time", "")))
        booking_url = h.get("booking_url", "")
        photo_url = h.get("photo_url", "")

        # Rating badge
        rating_html = ""
        if review_score:
            if review_score >= 8.5:
                rating_color = "#56D364"
            elif review_score >= 7.0:
                rating_color = "#58A6FF"
            else:
                rating_color = "#E3B341"
            count_str = f" ({review_count:,})" if review_count else ""
            rating_html = (
                f'<span style="background:{rating_color};color:#000;padding:2px 6px;'
                f'border-radius:4px;font-weight:700;font-size:0.75rem;">{review_score}</span>'
                f' <span style="font-size:0.75rem;color:#B8BFC6;">'
                f'{review_word}{count_str}</span>'
            )

        # Horarios
        times_parts = []
        if checkin_time:
            times_parts.append(f"In {checkin_time}")
        if checkout_time:
            times_parts.append(f"Out {checkout_time}")
        times_str = " \u00B7 ".join(times_parts)

        # Layout: foto | info | precio
        col_img, col_info, col_price = st.columns([0.18, 0.55, 0.27])

        with col_img:
            if photo_url:
                st.image(photo_url, use_container_width=True)
            else:
                st.markdown(
                    '<div style="background:#242D35;border-radius:8px;height:80px;'
                    'display:flex;align-items:center;justify-content:center;'
                    'font-size:2rem;">\U0001F3E8</div>',
                    unsafe_allow_html=True,
                )

        with col_info:
            info_html = (
                f'<div style="font-weight:600;font-size:0.95rem;color:#F0F2F4;'
                f'margin-bottom:2px;">{name} {stars_html}</div>'
                f'<div style="font-size:0.8rem;color:#B8BFC6;margin-bottom:4px;">'
                f'\U0001F4CD {location}</div>'
                f'<div style="margin-bottom:2px;">{rating_html}</div>'
            )
            if times_str:
                info_html += (
                    f'<div style="font-size:0.7rem;color:#8B949E;">{times_str}</div>'
                )
            st.markdown(info_html, unsafe_allow_html=True)

        with col_price:
            price_html = (
                f'<div style="text-align:right;padding-top:4px;">'
                f'<div style="font-size:1.15rem;font-weight:700;color:#56D364;'
                f'margin-bottom:6px;">{price_str}</div>'
            )
            st.markdown(price_html, unsafe_allow_html=True)
            if booking_url:
                st.link_button("Ver en Booking", booking_url, use_container_width=True)

        # Separador sutil
        st.markdown(
            '<hr style="border:none;border-top:1px solid #373E47;margin:4px 0 8px 0;">',
            unsafe_allow_html=True,
        )

    # Crédito
    st.markdown(
        '<div class="tp-hotel-credit">Datos de Booking.com</div>',
        unsafe_allow_html=True,
    )


def render_flight_results(data: dict) -> None:
    """Renderiza resultados de busqueda de vuelos como tabla compacta."""
    text = data.get("text", "")
    flights = data.get("flights", [])

    if text:
        st.markdown(text)

    if not flights:
        st.info("No se encontraron vuelos disponibles para las fechas del viaje.")
        return

    # Header
    header_html = (
        '<div class="tp-hotel-header">'
        f'  <span class="tp-hotel-header__count">\u2708\uFE0F {len(flights)} vuelos encontrados</span>'
        '  <span class="tp-hotel-header__badge">Google Flights</span>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # Construir tabla HTML compacta
    rows_html = ""
    for f in flights:
        airline = html_module.escape(str(f.get("provider", "") or f.get("name", "\u2014")))
        departure = html_module.escape(str(f.get("departure", "\u2014")))
        arrival = html_module.escape(str(f.get("arrival", "\u2014")))
        duration = html_module.escape(str(f.get("duration", "\u2014")))
        notes = html_module.escape(str(f.get("notes", "")))
        price = f.get("price", 0)
        price_str = f"US${price:,.0f}" if price else "\u2014"
        booking_url = f.get("booking_url", "")

        # Extraer solo hora de datetime strings como "2026-04-15 10:10"
        if len(departure) > 5 and " " in departure:
            departure = departure.split(" ")[-1][:5]
        if len(arrival) > 5 and " " in arrival:
            arrival = arrival.split(" ")[-1][:5]

        # Escalas compactas
        stops_raw = notes.split("|")[0].strip() if notes else ""

        link_html = ""
        if booking_url:
            safe_url = html_module.escape(booking_url)
            link_html = f'<a href="{safe_url}" target="_blank" rel="noopener" style="color:var(--tp-accent-blue, #58A6FF);text-decoration:none;">\U0001F517</a>'

        rows_html += (
            "<tr>"
            f'<td style="padding:0.4rem 0.6rem;border-bottom:1px solid var(--tp-border, #30363d);white-space:nowrap;font-weight:500;">{airline}</td>'
            f'<td style="padding:0.4rem 0.6rem;border-bottom:1px solid var(--tp-border, #30363d);white-space:nowrap;">{departure}</td>'
            f'<td style="padding:0.4rem 0.6rem;border-bottom:1px solid var(--tp-border, #30363d);white-space:nowrap;">{arrival}</td>'
            f'<td style="padding:0.4rem 0.6rem;border-bottom:1px solid var(--tp-border, #30363d);white-space:nowrap;">{duration}</td>'
            f'<td style="padding:0.4rem 0.6rem;border-bottom:1px solid var(--tp-border, #30363d);font-weight:600;color:var(--tp-accent-green, #56D364);white-space:nowrap;">{price_str}</td>'
            f'<td style="padding:0.4rem 0.6rem;border-bottom:1px solid var(--tp-border, #30363d);max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:0.8rem;color:var(--tp-text-secondary, #8B949E);">{stops_raw}</td>'
            f'<td style="padding:0.4rem 0.3rem;border-bottom:1px solid var(--tp-border, #30363d);">{link_html}</td>'
            "</tr>"
        )

    table_html = (
        '<div style="overflow-x:auto;margin:0.5rem 0;">'
        '<table style="width:100%;border-collapse:collapse;font-size:0.85rem;">'
        '<thead>'
        '<tr style="border-bottom:1px solid var(--tp-border, #30363d);text-align:left;">'
        '<th style="padding:0.4rem 0.6rem;color:var(--tp-text-secondary, #8B949E);font-weight:500;">Aerol\u00EDnea</th>'
        '<th style="padding:0.4rem 0.6rem;color:var(--tp-text-secondary, #8B949E);font-weight:500;">Salida</th>'
        '<th style="padding:0.4rem 0.6rem;color:var(--tp-text-secondary, #8B949E);font-weight:500;">Llegada</th>'
        '<th style="padding:0.4rem 0.6rem;color:var(--tp-text-secondary, #8B949E);font-weight:500;">Duraci\u00F3n</th>'
        '<th style="padding:0.4rem 0.6rem;color:var(--tp-text-secondary, #8B949E);font-weight:500;">Precio</th>'
        '<th style="padding:0.4rem 0.6rem;color:var(--tp-text-secondary, #8B949E);font-weight:500;">Escalas</th>'
        '<th style="padding:0.4rem 0.3rem;"></th>'
        '</tr>'
        '</thead>'
        f'<tbody style="color:var(--tp-text-primary, #E6EDF3);">{rows_html}</tbody>'
        '</table>'
        '</div>'
    )

    st.markdown(table_html, unsafe_allow_html=True)

    # Credito
    st.markdown(
        '<div class="tp-hotel-credit">Datos de Google Flights</div>',
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
    "item_name": "Actividad",
    "item_names": "Items a eliminar",
    "item_count": "Cantidad",
}

_EXPENSE_LABELS = {
    "name": "Gasto",
    "category": "Categoria",
    "amount": "Monto",
    "Gasto actual": "Gasto actual",
    "Nuevo nombre": "Nuevo nombre",
    "Nuevo monto": "Nuevo monto",
    "Nueva categoria": "Nueva categoria",
    "item_count": "Cantidad",
}

# Iconos contextuales por tipo de accion
_ACTION_ICONS = {
    "create_trip": "\U0001F30D",
    "add_item": "\u2795",
    "remove_item": "\U0001F5D1\uFE0F",
    "calendar_event": "\U0001F4C5",
    "add_expense": "\U0001F4B0",
    "modify_expense": "\u270F\uFE0F",
    "remove_expense": "\U0001F5D1\uFE0F",
}

# Modificador CSS por tipo de accion
_ACTION_CSS_MODIFIER = {
    "create_trip": "tp-confirmation--add",
    "add_item": "tp-confirmation--add",
    "remove_item": "tp-confirmation--delete",
    "calendar_event": "",
    "add_expense": "tp-confirmation--add",
    "modify_expense": "",
    "remove_expense": "tp-confirmation--delete",
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
            # Omitir campos internos (prefijo _) y valores vacios/None
            if key.startswith("_") or key in ("action",) or val is None or val == "":
                continue
            if is_create_trip:
                label = _CREATE_TRIP_LABELS.get(key, key)
            elif action == "add_item":
                label = _ADD_ITEM_LABELS.get(key, key)
            elif action == "remove_item":
                label = _REMOVE_ITEM_LABELS.get(key, key)
            elif action in ("add_expense", "modify_expense", "remove_expense"):
                label = _EXPENSE_LABELS.get(key, key)
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
