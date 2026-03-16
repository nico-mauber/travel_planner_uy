"""Itinerario Detallado (REQ-UI-005, REQ-UI-011)."""

import streamlit as st
from datetime import date, timedelta

from config.settings import ItemStatus, TripStatus
from services.trip_service import (
    get_active_trip, get_trip_by_id, group_items_by_day, accept_suggestion,
    discard_suggestion, sync_trip_changes, get_transfer_info,
)
from components.itinerary_item import render_itinerary_item, render_transfer


try:
    trips = st.session_state.trips

    st.title("Itinerario Detallado")

    # ─── Selector de viaje ───
    active_statuses = [TripStatus.PLANNING.value, TripStatus.CONFIRMED.value, TripStatus.IN_PROGRESS.value]
    available_trips = [t for t in trips if t["status"] in active_statuses]

    if not available_trips:
        st.info("No hay viajes activos. Ve a **Mis Viajes** para crear uno.")
        if st.button("Ir a Mis Viajes", type="primary"):
            st.switch_page("pages/7_Mis_Viajes.py")
        st.stop()

    # Construir opciones
    trip_options = {t["id"]: f"{t['name']} — {t['destination']} ({t['start_date']} a {t['end_date']})" for t in available_trips}

    # Determinar seleccion actual
    current_active = st.session_state.get("active_trip_id")
    default_keys = list(trip_options.keys())
    default_idx = default_keys.index(current_active) if current_active in default_keys else 0

    selected_trip_id = st.selectbox(
        "Selecciona un viaje",
        options=default_keys,
        format_func=lambda k: trip_options[k],
        index=default_idx,
        key="itinerary_trip_selector",
    )

    # Actualizar active_trip_id
    st.session_state.active_trip_id = selected_trip_id
    trip = get_trip_by_id(trips, selected_trip_id)

    if not trip:
        st.info("No hay viaje activo. Ve a **Mis Viajes** para seleccionar o crear uno.")
        if st.button("Ir a Mis Viajes", type="primary"):
            st.switch_page("pages/7_Mis_Viajes.py")
        st.stop()

    st.caption(f"**{trip['name']}** — {trip['destination']}")

    items = trip.get("items", [])

    if not items:
        st.warning(
            "No hay items planificados. Interactúa con el agente en el **Chat** "
            "para comenzar a construir tu itinerario."
        )
        if st.button("💬 Abrir Chat"):
            st.switch_page("pages/2_Chat.py")
        st.stop()

    # ─── Agrupar por día ───
    start_date = date.fromisoformat(trip["start_date"])
    end_date = date.fromisoformat(trip["end_date"])
    total_days = (end_date - start_date).days + 1
    groups = group_items_by_day(items)

    # ─── Leyenda de estados ───
    st.markdown(
        "✅ Confirmado &nbsp;&nbsp; ⏳ Pendiente &nbsp;&nbsp; "
        "💡 Sugerido (no incluido en el plan)"
    )
    st.markdown("---")

    # ─── Tabs por día ───
    day_labels = []
    for d in range(1, total_days + 1):
        dt = start_date + timedelta(days=d - 1)
        day_labels.append(f"Día {d} — {dt.strftime('%a %d %b')}")

    tabs = st.tabs(day_labels)

    for d, tab in enumerate(tabs, start=1):
        with tab:
            day_items = groups.get(d, [])

            if not day_items:
                st.caption("Sin actividades para este día. Usa el Chat para agregar.")
                continue

            for idx, item in enumerate(day_items):
                # Traslado entre items consecutivos
                if idx > 0:
                    transfer = get_transfer_info(day_items[idx - 1], item)
                    if transfer:
                        render_transfer(transfer)

                action = render_itinerary_item(item, index=d * 100 + idx)

                if action.get("action") == "accept":
                    if accept_suggestion(trip, action["item_id"]):
                        sync_trip_changes(trips, trip)
                        st.session_state.trips = trips
                        st.success("Sugerencia aceptada.")
                        st.rerun()

                elif action.get("action") == "discard":
                    if discard_suggestion(trip, action["item_id"]):
                        sync_trip_changes(trips, trip)
                        st.session_state.trips = trips
                        st.info("Sugerencia descartada.")
                        st.rerun()

except Exception as e:
    st.error(f"Error al cargar el itinerario: {e}")
    if st.button("🔄 Reintentar"):
        st.rerun()
