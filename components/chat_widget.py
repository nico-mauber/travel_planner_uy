"""Componentes del chat: tarjetas ricas y confirmaciones."""

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


def render_confirmation(action_data: dict, msg_index: int) -> str:
    """Renderiza una solicitud de confirmación. Retorna 'confirm', 'cancel' o ''."""
    with st.container(border=True):
        st.markdown(f"⚠️ **{action_data.get('summary', 'Acción pendiente')}**")

        details = action_data.get("details", {})
        if details:
            detail_items = []
            for key, val in details.items():
                if key not in ("action",) and val:
                    detail_items.append(f"- **{key}**: {val}")
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
