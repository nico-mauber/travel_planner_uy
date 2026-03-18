"""Dashboard — Panel Overview del viaje activo (REQ-UI-001, REQ-UI-010)."""

import streamlit as st
from datetime import date

if "trips" not in st.session_state:
    st.switch_page("app.py")

from config.settings import TripStatus, ItemStatus, TRIP_STATUS_LABELS
from services.trip_service import get_active_trip, get_trip_by_id
from services.budget_service import calculate_budget_summary, calculate_planning_progress
from services.feedback_service import has_pending_feedback
from services.weather_service import get_weather
from components.alert_banner import get_alerts, render_alerts

try:
    trips = st.session_state.trips

    st.title("Dashboard")

    # ─── Banner feedback pendiente ───
    if has_pending_feedback(trips):
        st.info(
            "Tienes viajes completados sin retroalimentacion. "
            "Ve a **Mis Viajes** para dar tu feedback."
        )

    # ─── Selector de viaje ───
    active_statuses = [TripStatus.PLANNING.value, TripStatus.CONFIRMED.value, TripStatus.IN_PROGRESS.value]
    available_trips = [t for t in trips if t["status"] in active_statuses]

    if not available_trips:
        # Onboarding para usuarios sin viajes
        st.markdown("""
<div class="tp-onboarding">
  <div class="tp-onboarding__title">👋 ¡Bienvenido a Trip Planner!</div>
  <div class="tp-onboarding__steps">
    <div class="tp-onboarding__step">
      <div class="tp-onboarding__step-num">1</div>
      <div class="tp-onboarding__step-text"><strong>Creá un viaje</strong> — Definí destino, fechas y nombre</div>
    </div>
    <div class="tp-onboarding__step">
      <div class="tp-onboarding__step-num">2</div>
      <div class="tp-onboarding__step-text"><strong>Chateá con el asistente</strong> — Agregá actividades, hoteles y vuelos con lenguaje natural</div>
    </div>
    <div class="tp-onboarding__step">
      <div class="tp-onboarding__step-num">3</div>
      <div class="tp-onboarding__step-text"><strong>Revisá tu itinerario</strong> — Todo organizado día a día con presupuesto y cronograma</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Crear mi primer viaje", type="primary", use_container_width=True, help="Navegar a la pagina de gestion de viajes"):
                st.switch_page("pages/7_Mis_Viajes.py")
        with col2:
            if st.button("💬 Abrir Chat", use_container_width=True, help="Navegar al chat con el asistente"):
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
    st.markdown(f'<div class="tp-breadcrumb">🏠 Dashboard  ›  {trip.get("destination", "")}</div>', unsafe_allow_html=True)
    st.header(f"{trip['name']}")
    st.caption(f"Destino: {trip['destination']} — {trip['start_date']} a {trip['end_date']}")

    # ─── Fila 1: Métricas ───
    items = trip.get("items", [])
    non_suggested = [i for i in items if i["status"] != ItemStatus.SUGGESTED.value]
    confirmed = [i for i in non_suggested if i["status"] == ItemStatus.CONFIRMED.value]
    budget = calculate_budget_summary(items)

    start_date = date.fromisoformat(trip["start_date"])
    days_left = (start_date - date.today()).days

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            "Destino", trip["destination"].split(",")[0],
            help="Ciudad o region principal del viaje",
        )
    with m2:
        if days_left > 0:
            delta_text = "¡Muy pronto!" if days_left < 7 else None
            st.metric(
                "Dias restantes", f"{days_left} días",
                delta=delta_text,
                delta_color="inverse" if days_left < 7 else "off",
                help="Dias hasta la fecha de inicio del viaje",
            )
        elif days_left == 0:
            st.metric(
                "Estado", "¡Hoy empieza! 🎉",
                help="El viaje comienza hoy",
            )
        else:
            st.metric(
                "Estado", "En curso / Completado",
                help="El viaje ya esta en curso o ha finalizado",
            )
    with m3:
        st.metric(
            "Presupuesto", f"USD {budget['total_estimated']:,.0f}",
            help="Suma de costos estimados de todos los items confirmados y pendientes",
        )
    with m4:
        st.metric(
            "Items confirmados", f"{len(confirmed)}/{len(non_suggested)}",
            help="Cantidad de items confirmados sobre el total de items no sugeridos",
        )

    st.divider()

    # ─── Fila 2: Progreso ───
    st.subheader("Progreso de planificacion")
    progress = calculate_planning_progress(items)
    progress_pct = f"{progress * 100:.0f}%"
    st.progress(progress, text=f"{progress_pct} completado")
    st.caption(f"Progreso de planificacion: {progress_pct} de los items estan confirmados.")

    status_label = TRIP_STATUS_LABELS.get(TripStatus(trip["status"]), trip["status"])
    total_days = (date.fromisoformat(trip["end_date"]) - start_date).days + 1
    st.caption(f"Estado: **{status_label}** — Duración: **{total_days} días**")

    st.divider()

    # ─── Fila 3: Alertas ───
    alerts = get_alerts(trip)
    if alerts:
        st.subheader("Alertas")
        render_alerts(alerts)
        st.divider()

    # ─── Widget de clima ───
    weather = get_weather(trip.get("destination", ""))
    if weather:
        st.markdown(
            f'<div class="tp-weather">'
            f'<div class="tp-weather__icon">{weather["icon"]}</div>'
            f'<div class="tp-weather__info">'
            f'<div class="tp-weather__temp">{weather["temp_min"]}°–{weather["temp_max"]}°C</div>'
            f'<div class="tp-weather__condition">{weather["condition"]}</div>'
            f'<div class="tp-weather__desc">{weather["description"]}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ─── Fila 4: Accesos rapidos ───
    st.subheader("Accesos rapidos")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button("Chat", use_container_width=True, help="Abrir el chat con el asistente de viajes"):
            st.switch_page("pages/2_Chat.py")
    with q2:
        if st.button("Cronograma", use_container_width=True, help="Ver el calendario con todas las actividades"):
            st.switch_page("pages/3_Cronograma.py")
    with q3:
        if st.button("Itinerario", use_container_width=True, help="Ver el itinerario detallado dia a dia"):
            st.switch_page("pages/4_Itinerario.py")
    with q4:
        if st.button("Presupuesto", use_container_width=True, help="Ver el desglose de costos del viaje"):
            st.switch_page("pages/5_Presupuesto.py")

except Exception as e:
    st.error("❌ No se pudo cargar el dashboard. Verificá tu conexión e intentá de nuevo.")
    with st.expander("Detalles técnicos", expanded=False):
        st.code(str(e))
    if st.button("Reintentar", help="Recargar la pagina del dashboard"):
        st.rerun()
