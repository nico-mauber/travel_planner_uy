"""Componente de tarjeta de viaje para la lista Mis Viajes.

Usa clases tp-trip-card y tp-status-badge del design system para
hover lift effect y badges de estado consistentes.
"""

import html

import streamlit as st
from config.settings import TripStatus, TRIP_STATUS_LABELS


# Mapeo de estados a clases CSS del design system
_STATUS_CSS_CLASS = {
    TripStatus.PLANNING.value: "tp-status-badge tp-status-badge--planning",
    TripStatus.CONFIRMED.value: "tp-status-badge tp-status-badge--confirmed",
    TripStatus.IN_PROGRESS.value: "tp-status-badge tp-status-badge--in-progress",
    TripStatus.COMPLETED.value: "tp-status-badge tp-status-badge--completed",
}


def _format_date_readable(date_str: str) -> str:
    """Convierte YYYY-MM-DD a formato legible (ej: '15 Mar 2026')."""
    try:
        from datetime import date
        d = date.fromisoformat(date_str)
        months = [
            "", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
        ]
        return f"{d.day} {months[d.month]} {d.year}"
    except (ValueError, IndexError):
        return date_str


def render_trip_card(trip: dict, index: int) -> dict:
    """Renderiza una tarjeta de viaje. Retorna dict con accion si el usuario interactua.

    Acciones posibles: {"action": "view"}, {"action": "delete"}, {}
    """
    result = {}
    status = trip.get("status", "")
    status_label = TRIP_STATUS_LABELS.get(TripStatus(status), status)
    status_css = _STATUS_CSS_CLASS.get(status, "tp-status-badge tp-status-badge--completed")

    safe_name = html.escape(str(trip.get("name", "")))
    safe_dest = html.escape(str(trip.get("destination", "")))
    safe_status = html.escape(status_label)

    # Fechas formateadas
    start_fmt = _format_date_readable(trip.get("start_date", ""))
    end_fmt = _format_date_readable(trip.get("end_date", ""))
    safe_dates = f"{html.escape(start_fmt)} \u2192 {html.escape(end_fmt)}"

    # Presupuesto
    budget = trip.get("budget_total", 0) or 0
    budget_html = ""
    if budget > 0:
        budget_html = (
            f'<div class="tp-trip-card__detail">'
            f'  \U0001F4B0 <span class="tp-trip-card__budget">USD {budget:,.0f}</span>'
            f'</div>'
        )

    card_html = (
        f'<div class="tp-trip-card">'
        f'  <div class="tp-trip-card__header">'
        f'    <h3 class="tp-trip-card__name">{safe_name}</h3>'
        f'    <span class="{status_css}">{safe_status}</span>'
        f'  </div>'
        f'  <div class="tp-trip-card__info">'
        f'    <div class="tp-trip-card__detail">\U0001F4CD <strong>{safe_dest}</strong></div>'
        f'    <div class="tp-trip-card__detail">\U0001F4C5 {safe_dates}</div>'
        f'    {budget_html}'
        f'  </div>'
        f'</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)

    # Botones nativos Streamlit para interactividad
    btn_cols = st.columns([0.5, 0.5] if status == TripStatus.PLANNING.value else [1])

    with btn_cols[0]:
        if st.button(
            "\U0001F441\uFE0F Ver viaje",
            key=f"view_{trip['id']}_{index}",
            type="primary",
            use_container_width=True,
            help="Ver detalles del viaje",
        ):
            result = {"action": "view", "trip_id": trip["id"]}

    if status == TripStatus.PLANNING.value:
        with btn_cols[1]:
            if st.button(
                "\U0001F5D1\uFE0F Eliminar",
                key=f"del_{trip['id']}_{index}",
                use_container_width=True,
                help="Eliminar viaje",
            ):
                result = {"action": "delete", "trip_id": trip["id"]}

    return result
