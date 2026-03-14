"""Componente de alertas descartables."""

import streamlit as st
from config.settings import ItemStatus


def get_alerts(trip: dict) -> list:
    """Genera alertas para un viaje."""
    alerts = []

    # Items pendientes de confirmación
    pending_items = [
        i for i in trip.get("items", [])
        if i["status"] == ItemStatus.PENDING.value
    ]
    if pending_items:
        alerts.append({
            "id": f"alert_pending_{trip['id']}",
            "type": "warning",
            "message": f"Tienes {len(pending_items)} item(s) pendientes de confirmación.",
            "icon": "⏳",
        })

    # Items sugeridos sin aceptar
    suggested_items = [
        i for i in trip.get("items", [])
        if i["status"] == ItemStatus.SUGGESTED.value
    ]
    if suggested_items:
        alerts.append({
            "id": f"alert_suggested_{trip['id']}",
            "type": "info",
            "message": f"El agente tiene {len(suggested_items)} sugerencia(s) para ti. Revisa tu itinerario.",
            "icon": "💡",
        })

    # Días sin actividades
    from services.trip_service import group_items_by_day
    from datetime import date
    if trip.get("items"):
        start = date.fromisoformat(trip["start_date"])
        end = date.fromisoformat(trip["end_date"])
        total_days = (end - start).days + 1
        days_with_items = set(i["day"] for i in trip["items"])
        empty_days = total_days - len(days_with_items)
        if empty_days > 0:
            alerts.append({
                "id": f"alert_empty_days_{trip['id']}",
                "type": "info",
                "message": f"Hay {empty_days} día(s) sin actividades planificadas.",
                "icon": "📅",
            })

    return alerts


def render_alerts(alerts: list) -> None:
    """Renderiza alertas descartables."""
    if "dismissed_alerts" not in st.session_state:
        st.session_state.dismissed_alerts = set()

    for alert in alerts:
        if alert["id"] in st.session_state.dismissed_alerts:
            continue

        cols = st.columns([0.9, 0.1])
        with cols[0]:
            if alert["type"] == "warning":
                st.warning(f"{alert['icon']} {alert['message']}")
            elif alert["type"] == "error":
                st.error(f"{alert['icon']} {alert['message']}")
            else:
                st.info(f"{alert['icon']} {alert['message']}")
        with cols[1]:
            if st.button("✕", key=f"dismiss_{alert['id']}"):
                st.session_state.dismissed_alerts.add(alert["id"])
                st.rerun()
