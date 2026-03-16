"""Componentes del chat: tarjetas ricas, resultados de hoteles y confirmaciones."""

import streamlit as st
from config.settings import ITEM_TYPE_ICONS, ItemType


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
        "📦",
    )

    with st.container(border=True):
        cols = st.columns([0.1, 0.9])
        with cols[0]:
            st.markdown(f"### {icon}")
        with cols[1]:
            st.markdown(f"**{card_data.get('name', 'Sin nombre')}**")

            info_cols = st.columns(2)
            with info_cols[0]:
                if card_data.get("provider"):
                    st.caption(f"Proveedor: {card_data['provider']}")
                if card_data.get("location"):
                    st.caption(f"📍 {card_data['location']}")
                if card_data.get("duration"):
                    st.caption(f"⏱️ {card_data['duration']}")
            with info_cols[1]:
                if card_data.get("price"):
                    st.markdown(f"**USD {card_data['price']:,.0f}**")
                if card_data.get("rating"):
                    st.caption(card_data["rating"])
                if card_data.get("departure"):
                    st.caption(
                        f"🕐 {card_data['departure']} → {card_data.get('arrival', '')}"
                    )

            if card_data.get("notes"):
                st.caption(card_data["notes"])

            if card_data.get("booking_url"):
                st.link_button("🔗 Ver en Booking.com", card_data["booking_url"])


def render_hotel_results(data: dict) -> None:
    """Renderiza resultados de busqueda de hoteles de Booking.com."""
    text = data.get("text", "")
    hotels = data.get("hotels", [])

    if text:
        st.markdown(text)

    if not hotels:
        st.info("No se encontraron hoteles disponibles para las fechas del viaje.")
        return

    st.markdown(f"**🏨 {len(hotels)} hoteles encontrados en Booking.com:**")

    for hotel in hotels:
        render_rich_card(hotel)

    st.caption("*Datos proporcionados por Booking.com via RapidAPI*")


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


def render_confirmation(action_data: dict, msg_index: int) -> str:
    """Renderiza una solicitud de confirmación. Retorna 'confirm', 'cancel' o ''."""
    with st.container(border=True):
        st.markdown(f"⚠️ **{action_data.get('summary', 'Acción pendiente')}**")

        details = action_data.get("details", {})
        is_create_trip = action_data.get("action") == "create_trip"
        if details:
            detail_items = []
            for key, val in details.items():
                # Omitir campos internos (prefijo _) y valores vacios
                if key.startswith("_") or key in ("action",) or not val:
                    continue
                if is_create_trip:
                    label = _CREATE_TRIP_LABELS.get(key, key)
                elif action_data.get("action") == "add_item":
                    label = _ADD_ITEM_LABELS.get(key, key)
                else:
                    label = key
                detail_items.append(f"- **{label}**: {val}")
            if detail_items:
                st.markdown("\n".join(detail_items))

        cols = st.columns(2)
        with cols[0]:
            if st.button("✅ Confirmar", key=f"confirm_{msg_index}", type="primary"):
                return "confirm"
        with cols[1]:
            if st.button("❌ Cancelar", key=f"cancel_{msg_index}"):
                return "cancel"

    return ""
