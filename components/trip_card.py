"""Componente de tarjeta de viaje para la lista Mis Viajes."""

import streamlit as st
from config.settings import TripStatus, TRIP_STATUS_LABELS


STATUS_BADGE_COLORS = {
    TripStatus.PLANNING.value: "🟡",
    TripStatus.CONFIRMED.value: "🟢",
    TripStatus.IN_PROGRESS.value: "🔵",
    TripStatus.COMPLETED.value: "⚪",
}


def render_trip_card(trip: dict, index: int) -> dict:
    """Renderiza una tarjeta de viaje. Retorna dict con acción si el usuario interactúa.

    Acciones posibles: {"action": "view"}, {"action": "delete"}, {}
    """
    result = {}
    badge = STATUS_BADGE_COLORS.get(trip["status"], "⚪")
    status_label = TRIP_STATUS_LABELS.get(TripStatus(trip["status"]), trip["status"])

    with st.container(border=True):
        cols = st.columns([0.7, 0.3])

        with cols[0]:
            st.markdown(f"### {trip['name']}")
            st.markdown(
                f"📍 **{trip['destination']}** &nbsp;&nbsp; "
                f"{badge} {status_label}"
            )
            st.caption(f"📅 {trip['start_date']} → {trip['end_date']}")
            if trip.get("budget_total", 0) > 0:
                st.caption(f"💰 USD {trip['budget_total']:,.0f}")

        with cols[1]:
            st.write("")  # spacing
            if st.button("👁️ Ver viaje", key=f"view_{trip['id']}_{index}",
                         type="primary", use_container_width=True):
                result = {"action": "view", "trip_id": trip["id"]}

            if trip["status"] == TripStatus.PLANNING.value:
                if st.button("🗑️ Eliminar", key=f"del_{trip['id']}_{index}",
                             use_container_width=True):
                    result = {"action": "delete", "trip_id": trip["id"]}

    return result
