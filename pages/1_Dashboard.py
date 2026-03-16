"""Dashboard — Panel Overview del viaje activo (REQ-UI-001, REQ-UI-010)."""

import streamlit as st
from datetime import date

from config.settings import TripStatus, ItemStatus, TRIP_STATUS_LABELS
from services.trip_service import get_active_trip, get_trip_by_id
from services.budget_service import calculate_budget_summary, calculate_planning_progress
from services.feedback_service import has_pending_feedback
from components.alert_banner import get_alerts, render_alerts

try:
    trips = st.session_state.trips

    st.title("📊 Dashboard")

    # ─── Banner feedback pendiente ───
    if has_pending_feedback(trips):
        st.info(
            "📝 Tienes viajes completados sin retroalimentación. "
            "Ve a **Mis Viajes** para dar tu feedback."
        )

    # ─── Selector de viaje ───
    active_statuses = [TripStatus.PLANNING.value, TripStatus.CONFIRMED.value, TripStatus.IN_PROGRESS.value]
    available_trips = [t for t in trips if t["status"] in active_statuses]

    if not available_trips:
        st.info("No hay viajes activos. Ve a **Mis Viajes** para crear uno.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🌍 Ir a Mis Viajes", type="primary", use_container_width=True):
                st.switch_page("pages/7_Mis_Viajes.py")
        with col2:
            if st.button("💬 Abrir Chat", use_container_width=True):
                st.switch_page("pages/2_Chat.py")
        st.stop()

    trip_options = {t["id"]: f"{t['name']} — {t['destination']}" for t in available_trips}

    current_active = st.session_state.get("active_trip_id")
    default_keys = list(trip_options.keys())
    default_idx = default_keys.index(current_active) if current_active in default_keys else 0

    selected_trip_id = st.selectbox(
        "Selecciona un viaje",
        options=default_keys,
        format_func=lambda k: trip_options[k],
        index=default_idx,
        key="dashboard_trip_selector",
    )

    st.session_state.active_trip_id = selected_trip_id
    trip = get_trip_by_id(trips, selected_trip_id)

    if not trip:
        st.warning("No se pudo cargar el viaje seleccionado.")
        st.stop()

    # ─── Dashboard con viaje activo ───
    st.subheader(f"{trip['name']}")
    st.caption(f"📍 {trip['destination']} — {trip['start_date']} a {trip['end_date']}")

    # ─── Fila 1: Métricas ───
    items = trip.get("items", [])
    non_suggested = [i for i in items if i["status"] != ItemStatus.SUGGESTED.value]
    confirmed = [i for i in non_suggested if i["status"] == ItemStatus.CONFIRMED.value]
    budget = calculate_budget_summary(items)

    start_date = date.fromisoformat(trip["start_date"])
    days_left = (start_date - date.today()).days

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Destino", trip["destination"].split(",")[0])
    with m2:
        if days_left > 0:
            st.metric("Días restantes", f"{days_left} días")
        elif days_left == 0:
            st.metric("Estado", "¡Hoy empieza!")
        else:
            st.metric("Estado", "En curso / Completado")
    with m3:
        st.metric("Presupuesto", f"USD {budget['total_estimated']:,.0f}")
    with m4:
        st.metric("Items confirmados", f"{len(confirmed)}/{len(non_suggested)}")

    st.markdown("---")

    # ─── Fila 2: Progreso ───
    st.subheader("📈 Progreso de planificación")
    progress = calculate_planning_progress(items)
    st.progress(progress, text=f"{progress * 100:.0f}% completado")

    status_label = TRIP_STATUS_LABELS.get(TripStatus(trip["status"]), trip["status"])
    total_days = (date.fromisoformat(trip["end_date"]) - start_date).days + 1
    st.caption(f"Estado: **{status_label}** — Duración: **{total_days} días**")

    st.markdown("---")

    # ─── Fila 3: Alertas ───
    alerts = get_alerts(trip)
    if alerts:
        st.subheader("🔔 Alertas")
        render_alerts(alerts)
        st.markdown("---")

    # ─── Fila 4: Accesos rápidos ───
    st.subheader("⚡ Accesos rápidos")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button("💬 Chat", use_container_width=True):
            st.switch_page("pages/2_Chat.py")
    with q2:
        if st.button("📅 Cronograma", use_container_width=True):
            st.switch_page("pages/3_Cronograma.py")
    with q3:
        if st.button("📋 Itinerario", use_container_width=True):
            st.switch_page("pages/4_Itinerario.py")
    with q4:
        if st.button("💰 Presupuesto", use_container_width=True):
            st.switch_page("pages/5_Presupuesto.py")

except Exception as e:
    st.error(f"Error al cargar el dashboard: {e}")
    if st.button("🔄 Reintentar"):
        st.rerun()
