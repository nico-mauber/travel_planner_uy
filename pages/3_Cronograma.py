"""Cronograma / Calendario (REQ-UI-004). Vista global de todos los viajes."""

import html

import streamlit as st
from datetime import date, timedelta

from config.settings import ITEM_TYPE_COLORS, ITEM_TYPE_ICONS, ItemType, ItemStatus, STATUS_ICONS


def _render_fallback_calendar(valid_trips: list) -> None:
    """Vista alternativa como tabla cuando streamlit-calendar no esta disponible.

    Muestra items de todos los viajes agrupados por fecha real.
    """
    # Recopilar todas las fechas con items, agrupadas por fecha real
    date_items: dict[date, list[tuple[dict, dict]]] = {}

    for trip in valid_trips:
        trip_start = date.fromisoformat(trip["start_date"])
        items = trip.get("items", [])

        for item in items:
            day_offset = item["day"] - 1
            item_date = trip_start + timedelta(days=day_offset)

            end_day = item.get("end_day")
            if end_day and end_day > item["day"]:
                # Item multi-dia: agregar a cada fecha del rango
                for d in range(item["day"], end_day + 1):
                    multi_date = trip_start + timedelta(days=d - 1)
                    if multi_date not in date_items:
                        date_items[multi_date] = []
                    date_items[multi_date].append((trip, item))
            else:
                if item_date not in date_items:
                    date_items[item_date] = []
                date_items[item_date].append((trip, item))

    if not date_items:
        st.info("No hay actividades planificadas.")
        return

    # Ordenar fechas y crear tabs
    sorted_dates = sorted(date_items.keys())
    date_labels = [dt.strftime("%a %d %b %Y") for dt in sorted_dates]
    tabs = st.tabs(date_labels)

    for tab, dt in zip(tabs, sorted_dates):
        with tab:
            for trip, item in date_items[dt]:
                icon = ITEM_TYPE_ICONS.get(ItemType(item["item_type"]), "")
                status = STATUS_ICONS.get(ItemStatus(item["status"]), "")
                try:
                    color = ITEM_TYPE_COLORS.get(ItemType(item["item_type"]), "#9E9E9E")
                except ValueError:
                    color = "#9E9E9E"

                is_multiday = item.get("end_day") and item["end_day"] > item["day"]
                duration_label = f" (Dias {item['day']}-{item['end_day']})" if is_multiday else ""
                if is_multiday:
                    color = "#607D8B"

                safe_dest = html.escape(trip["destination"])
                safe_name = html.escape(item["name"])
                safe_loc = html.escape(item.get("location", ""))
                time_display = f"Todo el dia{duration_label}" if is_multiday else f"{item['start_time']} — {item['end_time']}"
                st.markdown(
                    f"<div style='border-left: 4px solid {color}; "
                    f"padding: 8px 12px; margin: 4px 0; border-radius: 4px; "
                    f"background-color: #1E1E2E;'>"
                    f"🌍 <i>{safe_dest}</i>&nbsp;&nbsp;"
                    f"{status} {icon} <b>{safe_name}</b>{html.escape(duration_label)}<br>"
                    f"🕐 {time_display}"
                    f"{'&nbsp;&nbsp;📍 ' + safe_loc if safe_loc else ''}"
                    f"</div>",
                    unsafe_allow_html=True,
                )


try:
    trips = st.session_state.trips

    st.title("Cronograma")

    # ─── Recopilar items de TODOS los viajes con fechas definidas ───
    all_events_data = []  # Lista de (trip, item) tuples
    valid_trips = []      # Viajes con items y fechas

    for trip in trips:
        if not trip.get("start_date") or not trip.get("end_date"):
            continue
        items = trip.get("items", [])
        if items:
            valid_trips.append(trip)
            for item in items:
                all_events_data.append((trip, item))

    if not all_events_data:
        st.info(
            "No hay actividades en ningun viaje. Usa el **Chat** para comenzar a planificar."
        )
        if st.button("Abrir Chat"):
            st.switch_page("pages/2_Chat.py")
        st.stop()

    # ─── Selector de vista ───
    view = st.radio(
        "Vista", ["Semana", "Dia", "Mes"],
        horizontal=True,
        label_visibility="collapsed",
    )

    # ─── Intentar usar streamlit-calendar ───
    try:
        from streamlit_calendar import calendar as st_calendar

        # Calcular rango global (min start_date, max end_date de todos los viajes)
        all_start_dates = [date.fromisoformat(t["start_date"]) for t in valid_trips]
        all_end_dates = [date.fromisoformat(t["end_date"]) for t in valid_trips]
        global_start = min(all_start_dates)
        global_end = max(all_end_dates)

        # Convertir items a eventos de calendario
        events = []
        seen_multiday = set()

        for trip, item in all_events_data:
            trip_start = date.fromisoformat(trip["start_date"])
            day_offset = item["day"] - 1
            event_date = trip_start + timedelta(days=day_offset)

            event_title = f"{trip['destination']}: {item['name']}"

            item_type = item.get("item_type", "extra")
            try:
                color = ITEM_TYPE_COLORS.get(ItemType(item_type), "#9E9E9E")
            except ValueError:
                color = "#9E9E9E"

            if item["status"] == ItemStatus.SUGGESTED.value:
                color = color + "80"

            end_day = item.get("end_day")
            if end_day and end_day > item["day"]:
                if item["id"] in seen_multiday:
                    continue
                seen_multiday.add(item["id"])
                event_end_date = trip_start + timedelta(days=end_day)
                events.append({
                    "title": event_title,
                    "start": str(event_date),
                    "end": str(event_end_date),
                    "allDay": True,
                    "color": "#607D8B",
                    "extendedProps": {
                        "id": item["id"],
                        "type": item["item_type"],
                        "status": item["status"],
                        "location": item.get("location", ""),
                        "cost": item.get("cost_estimated", 0),
                        "multiday": True,
                        "trip_destination": trip["destination"],
                    },
                })
            else:
                events.append({
                    "title": event_title,
                    "start": f"{event_date}T{item['start_time']}:00",
                    "end": f"{event_date}T{item['end_time']}:00",
                    "color": color,
                    "extendedProps": {
                        "id": item["id"],
                        "type": item["item_type"],
                        "status": item["status"],
                        "location": item.get("location", ""),
                        "cost": item.get("cost_estimated", 0),
                        "trip_destination": trip["destination"],
                    },
                })

        view_map = {
            "Dia": "timeGridDay",
            "Semana": "timeGridWeek",
            "Mes": "dayGridMonth",
        }

        calendar_options = {
            "initialView": view_map.get(view, "timeGridWeek"),
            "initialDate": str(global_start),
            "validRange": {
                "start": str(global_start),
                "end": str(global_end + timedelta(days=1)),
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

        if state and state.get("eventClick"):
            event_data = state["eventClick"].get("event", {})
            ext = event_data.get("extendedProps", {})
            with st.popover(f"{event_data.get('title', '')}"):
                st.markdown(f"**{event_data.get('title', '')}**")
                if ext.get("trip_destination"):
                    st.caption(f"Viaje: {ext['trip_destination']}")
                if ext.get("location"):
                    st.caption(f"{ext['location']}")
                if ext.get("cost"):
                    st.caption(f"USD {ext['cost']:,.0f}")
                st.caption(f"Estado: {ext.get('status', '')}")

    except ImportError:
        st.warning("`streamlit-calendar` no instalado. Mostrando vista alternativa.")
        _render_fallback_calendar(valid_trips)

except Exception as e:
    st.error(f"Error al cargar el cronograma: {e}")
    if st.button("Reintentar"):
        st.rerun()
