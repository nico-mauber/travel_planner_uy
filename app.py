"""Trip Planner MVP — Punto de entrada Streamlit."""

from dotenv import load_dotenv
load_dotenv()

import streamlit as st

from config.settings import TRIP_STATUS_LABELS, TripStatus
from services.trip_service import load_trips, get_active_trip, update_trip_statuses, save_trips
from data.sample_data import get_sample_chat_histories


# ─── Page config ───
st.set_page_config(
    page_title="Trip Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS custom ───
st.markdown("""
<style>
    /* Badge de estado */
    .status-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: 500;
    }
    .status-planning { background-color: #FFF9C4; color: #F9A825; }
    .status-confirmed { background-color: #C8E6C9; color: #2E7D32; }
    .status-in-progress { background-color: #BBDEFB; color: #1565C0; }
    .status-completed { background-color: #E0E0E0; color: #616161; }

    /* Items sugeridos */
    .suggested-item {
        border: 2px dashed #FFB74D !important;
        opacity: 0.85;
    }

    /* Sidebar viaje activo */
    .active-trip-box {
        background-color: #E3F2FD;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #1E88E5;
        margin-bottom: 12px;
    }

    /* Transfers */
    .transfer-block {
        background-color: #f5f5f5;
        padding: 8px 16px;
        border-radius: 8px;
        border-left: 3px solid #9E9E9E;
        margin: 4px 0;
    }
</style>
""", unsafe_allow_html=True)

# ─── Inicializar session_state ───
if "trips" not in st.session_state:
    st.session_state.trips = load_trips()

if "active_trip_id" not in st.session_state:
    st.session_state.active_trip_id = None

if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = get_sample_chat_histories()

if "dismissed_alerts" not in st.session_state:
    st.session_state.dismissed_alerts = set()

if "user_profile" not in st.session_state:
    from services.profile_service import load_profile
    st.session_state.user_profile = load_profile()

# ─── Actualizar estados por fecha ───
update_trip_statuses(st.session_state.trips)
save_trips(st.session_state.trips)

# ─── Navegación ───
pages = [
    st.Page("pages/1_Dashboard.py", title="Dashboard", icon="📊"),
    st.Page("pages/2_Chat.py", title="Chat", icon="💬"),
    st.Page("pages/3_Cronograma.py", title="Cronograma", icon="📅"),
    st.Page("pages/4_Itinerario.py", title="Itinerario", icon="📋"),
    st.Page("pages/5_Presupuesto.py", title="Presupuesto", icon="💰"),
    st.Page("pages/6_Perfil.py", title="Perfil", icon="👤"),
    st.Page("pages/7_Mis_Viajes.py", title="Mis Viajes", icon="🌍"),
]

pg = st.navigation(pages)

# ─── Sidebar ───
with st.sidebar:
    st.markdown("## ✈️ Trip Planner")
    st.divider()

    # Viaje activo
    trip = get_active_trip(st.session_state.trips, st.session_state.active_trip_id)
    if trip:
        status_label = TRIP_STATUS_LABELS.get(
            TripStatus(trip["status"]), trip["status"]
        )
        status_class = {
            TripStatus.PLANNING.value: "status-planning",
            TripStatus.CONFIRMED.value: "status-confirmed",
            TripStatus.IN_PROGRESS.value: "status-in-progress",
            TripStatus.COMPLETED.value: "status-completed",
        }.get(trip["status"], "")

        st.markdown(
            f"""<div class="active-trip-box">
            <strong>{trip['name']}</strong><br>
            📍 {trip['destination']}<br>
            📅 {trip['start_date']} → {trip['end_date']}<br>
            <span class="status-badge {status_class}">{status_label}</span>
            </div>""",
            unsafe_allow_html=True,
        )

        # Sincronizar active_trip_id
        st.session_state.active_trip_id = trip["id"]
    else:
        st.info("No hay viaje activo. Ve a **Mis Viajes** para crear uno.")

    st.divider()

    # Botón fijo "Abrir Chat"
    if st.button("💬 Abrir Chat", use_container_width=True):
        st.switch_page("pages/2_Chat.py")

# ─── Ejecutar página ───
pg.run()
