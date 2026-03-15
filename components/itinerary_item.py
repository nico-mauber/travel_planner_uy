"""Componente de item del itinerario expandible."""

import streamlit as st
from config.settings import (
    ITEM_TYPE_ICONS, STATUS_ICONS, ITEM_TYPE_LABELS,
    ItemStatus, ItemType,
)


def render_itinerary_item(item: dict, index: int) -> dict:
    """Renderiza un item del itinerario como expander.

    Retorna: {"action": "accept"|"discard"} o {}
    """
    result = {}
    icon = ITEM_TYPE_ICONS.get(ItemType(item["item_type"]), "📦")
    status_icon = STATUS_ICONS.get(ItemStatus(item["status"]), "")
    type_label = ITEM_TYPE_LABELS.get(ItemType(item["item_type"]), item["item_type"])

    title = f"{icon} {item['name']} — {item['start_time']} a {item['end_time']}"

    # Estilo visual para sugeridos
    is_suggested = item["status"] == ItemStatus.SUGGESTED.value

    with st.expander(f"{status_icon} {title}", expanded=False):
        if is_suggested:
            st.caption("💡 *Sugerencia del agente — aún no es parte del plan*")

        info_cols = st.columns(2)
        with info_cols[0]:
            st.markdown(f"**Tipo:** {type_label}")
            if item.get("location"):
                st.markdown(f"**Ubicación:** {item['location']}")
            if item.get("address"):
                st.markdown(f"**Dirección:** {item['address']}")
        with info_cols[1]:
            if item.get("cost_estimated", 0) > 0:
                st.markdown(f"**Costo estimado:** USD {item['cost_estimated']:,.0f}")
            if item.get("cost_real", 0) > 0:
                st.markdown(f"**Costo real:** USD {item['cost_real']:,.0f}")
            if item.get("provider"):
                st.markdown(f"**Proveedor:** {item['provider']}")

        if item.get("notes"):
            st.markdown(f"**Notas:** {item['notes']}")

        if item.get("booking_url"):
            st.link_button("🔗 Ver reserva", item["booking_url"])

        # Acciones para sugeridos
        if is_suggested:
            act_cols = st.columns(2)
            with act_cols[0]:
                if st.button("✅ Aceptar", key=f"accept_{item['id']}_{index}",
                             type="primary", use_container_width=True):
                    result = {"action": "accept", "item_id": item["id"]}
            with act_cols[1]:
                if st.button("❌ Descartar", key=f"discard_{item['id']}_{index}",
                             use_container_width=True):
                    result = {"action": "discard", "item_id": item["id"]}

    return result


def render_transfer(transfer_info: dict) -> None:
    """Renderiza un bloque visual de traslado entre items."""
    with st.container():
        st.markdown(
            f"<div style='background-color: #1E1E2E; padding: 8px 16px; "
            f"border-radius: 8px; margin: 4px 0; border-left: 3px solid #78909C;'>"
            f"🚕 <b>Traslado:</b> {transfer_info['from']} → {transfer_info['to']} "
            f"&nbsp;|&nbsp; {transfer_info['transport']} "
            f"&nbsp;|&nbsp; ⏱️ {transfer_info['duration']} "
            f"&nbsp;|&nbsp; ~USD {transfer_info['cost_estimated']:,.0f}"
            f"</div>",
            unsafe_allow_html=True,
        )
