"""Componente de alertas descartables.

Usa clases tp-alert del design system para bordes izquierdos semanticos
y layout mejorado (icono + mensaje + boton dismiss en fila).
"""

import html

import streamlit as st
from config.settings import ItemStatus


def get_alerts(trip: dict) -> list:
    """Genera alertas para un viaje."""
    alerts = []

    # Items pendientes de confirmacion
    pending_items = [
        i for i in trip.get("items", [])
        if i["status"] == ItemStatus.PENDING.value
    ]
    if pending_items:
        alerts.append({
            "id": f"alert_pending_{trip['id']}",
            "type": "warning",
            "message": f"Tienes {len(pending_items)} item(s) pendientes de confirmacion.",
            "icon": "\u23F3",
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
            "icon": "\U0001F4A1",
        })

    # Dias sin actividades
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
                "message": f"Hay {empty_days} dia(s) sin actividades planificadas.",
                "icon": "\U0001F4C5",
            })

    return alerts


# Mapeo de tipo de alerta a clase CSS
_ALERT_CSS_CLASS = {
    "warning": "tp-alert tp-alert--warning",
    "error": "tp-alert tp-alert--error",
    "info": "tp-alert tp-alert--info",
}


def render_alerts(alerts: list) -> None:
    """Renderiza alertas descartables con bordes semanticos."""
    if "dismissed_alerts" not in st.session_state:
        st.session_state.dismissed_alerts = set()

    for alert in alerts:
        if alert["id"] in st.session_state.dismissed_alerts:
            continue

        alert_css = _ALERT_CSS_CLASS.get(alert["type"], "tp-alert tp-alert--info")
        safe_msg = html.escape(str(alert["message"]))
        alert_icon = alert.get("icon", "\u2139\uFE0F")

        # Renderizar alerta con HTML estilizado + boton nativo Streamlit
        alert_html = (
            f'<div class="{alert_css}" role="alert">'
            f'  <span class="tp-alert__icon">{alert_icon}</span>'
            f'  <span class="tp-alert__message">{safe_msg}</span>'
            f'</div>'
        )

        cols = st.columns([0.92, 0.08])
        with cols[0]:
            st.markdown(alert_html, unsafe_allow_html=True)
        with cols[1]:
            if st.button(
                "\u2715",
                key=f"dismiss_{alert['id']}",
                help="Descartar esta alerta",
            ):
                st.session_state.dismissed_alerts.add(alert["id"])
                st.rerun()
