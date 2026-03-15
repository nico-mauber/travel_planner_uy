"""Cronograma / Calendario (REQ-UI-004)."""

import streamlit as st
from datetime import date, timedelta

from config.settings import ITEM_TYPE_COLORS, ITEM_TYPE_ICONS, ItemType, ItemStatus
from services.trip_service import get_active_trip, group_items_by_day


try:
    trips = st.session_state.trips
    trip = get_active_trip(trips, st.session_state.get("active_trip_id"))

    st.title("📅 Cronograma")

    if not trip:
        st.info("No hay viaje activo. Ve a **Mis Viajes** para seleccionar o crear uno.")
        if st.button("🌍 Ir a Mis Viajes", type="primary"):
            st.switch_page("pages/7_Mis_Viajes.py")
        st.stop()

    st.caption(f"**{trip['name']}** — {trip['destination']}")

    items = trip.get("items", [])

    if not items:
        st.warning(
            "El itinerario está vacío. Usa el **Chat** para comenzar a planificar actividades."
        )
        if st.button("💬 Abrir Chat"):
            st.switch_page("pages/2_Chat.py")
        st.stop()

    # ─── Selector de vista ───
    view = st.radio(
        "Vista", ["Semana", "Día", "Mes"],
        horizontal=True,
        label_visibility="collapsed",
    )

    # ─── Intentar usar streamlit-calendar ───
    try:
        from streamlit_calendar import calendar as st_calendar

        start_date = date.fromisoformat(trip["start_date"])
        end_date = date.fromisoformat(trip["end_date"])

        # Convertir items a eventos de calendario
        events = []
        for item in items:
            day_offset = item["day"] - 1
            event_date = start_date + timedelta(days=day_offset)

            item_type = item.get("item_type", "extra")
            try:
                color = ITEM_TYPE_COLORS.get(ItemType(item_type), "#9E9E9E")
            except ValueError:
                color = "#9E9E9E"

            # Ajustar opacidad para sugeridos
            if item["status"] == ItemStatus.SUGGESTED.value:
                color = color + "80"  # 50% opacity

            events.append({
                "title": item["name"],
                "start": f"{event_date}T{item['start_time']}:00",
                "end": f"{event_date}T{item['end_time']}:00",
                "color": color,
                "extendedProps": {
                    "id": item["id"],
                    "type": item["item_type"],
                    "status": item["status"],
                    "location": item.get("location", ""),
                    "cost": item.get("cost_estimated", 0),
                },
            })

        # Mapeo de vista
        view_map = {
            "Día": "timeGridDay",
            "Semana": "timeGridWeek",
            "Mes": "dayGridMonth",
        }

        calendar_options = {
            "initialView": view_map.get(view, "timeGridWeek"),
            "initialDate": str(start_date),
            "validRange": {
                "start": str(start_date),
                "end": str(end_date + timedelta(days=1)),
            },
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "",
            },
            "slotMinTime": "05:00:00",
            "slotMaxTime": "24:00:00",
            "height": 600,
            "locale": "es",
        }

        state = st_calendar(events=events, options=calendar_options)

        # Click en evento → detalle
        if state and state.get("eventClick"):
            event_data = state["eventClick"].get("event", {})
            ext = event_data.get("extendedProps", {})
            with st.popover(f"📌 {event_data.get('title', '')}"):
                st.markdown(f"**{event_data.get('title', '')}**")
                if ext.get("location"):
                    st.caption(f"📍 {ext['location']}")
                if ext.get("cost"):
                    st.caption(f"💰 USD {ext['cost']:,.0f}")
                st.caption(f"Estado: {ext.get('status', '')}")

    except ImportError:
        # Fallback sin streamlit-calendar — tabla por día
        st.warning("📦 `streamlit-calendar` no instalado. Mostrando vista alternativa.")
        _render_fallback_calendar(trip, items)

except Exception as e:
    st.error(f"Error al cargar el cronograma: {e}")
    if st.button("🔄 Reintentar"):
        st.rerun()


def _render_fallback_calendar(trip: dict, items: list) -> None:
    """Vista alternativa como tabla cuando streamlit-calendar no está disponible."""
    from datetime import date, timedelta
    from config.settings import ITEM_TYPE_ICONS, STATUS_ICONS, ItemType, ItemStatus

    start_date = date.fromisoformat(trip["start_date"])
    groups = group_items_by_day(items)
    total_days = (date.fromisoformat(trip["end_date"]) - start_date).days + 1

    days_labels = []
    for d in range(1, total_days + 1):
        dt = start_date + timedelta(days=d - 1)
        days_labels.append(f"Día {d} — {dt.strftime('%a %d %b')}")

    tabs = st.tabs(days_labels)

    for d, tab in enumerate(tabs, start=1):
        with tab:
            day_items = groups.get(d, [])
            if not day_items:
                st.caption("Sin actividades planificadas para este día.")
            else:
                for item in day_items:
                    icon = ITEM_TYPE_ICONS.get(ItemType(item["item_type"]), "📦")
                    status = STATUS_ICONS.get(ItemStatus(item["status"]), "")
                    try:
                        color = ITEM_TYPE_COLORS.get(ItemType(item["item_type"]), "#9E9E9E")
                    except ValueError:
                        color = "#9E9E9E"
                    st.markdown(
                        f"<div style='border-left: 4px solid {color}; "
                        f"padding: 8px 12px; margin: 4px 0; border-radius: 4px; "
                        f"background-color: #1E1E2E;'>"
                        f"{status} {icon} <b>{item['name']}</b><br>"
                        f"🕐 {item['start_time']} — {item['end_time']}"
                        f"{'&nbsp;&nbsp;📍 ' + item['location'] if item.get('location') else ''}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
