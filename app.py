"""Trip Planner MVP — Punto de entrada Streamlit."""

import html
import logging

from dotenv import load_dotenv
load_dotenv(override=True)

# Logging para ver actividad del LLM en consola
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

import streamlit as st

from config.settings import TRIP_STATUS_LABELS, TripStatus
from services.trip_service import load_trips, get_active_trip, update_trip_statuses
from services.auth_service import is_auth_enabled, require_auth, get_current_user_id
from services.chat_service import load_chats


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
    .status-planning { background-color: #3E2E00; color: #FFD54F; }
    .status-confirmed { background-color: #1B3A1B; color: #66BB6A; }
    .status-in-progress { background-color: #0D2744; color: #64B5F6; }
    .status-completed { background-color: #2A2A2A; color: #9E9E9E; }

    /* Items sugeridos */
    .suggested-item {
        border: 2px dashed #FFB74D !important;
        opacity: 0.85;
    }

    /* Sidebar viaje activo */
    .active-trip-box {
        background-color: #1A2332;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #42A5F5;
        margin-bottom: 12px;
    }

    /* Transfers */
    .transfer-block {
        background-color: #1E1E2E;
        padding: 8px 16px;
        border-radius: 8px;
        border-left: 3px solid #78909C;
        margin: 4px 0;
    }
</style>
""", unsafe_allow_html=True)

# ─── Verificar conexión Supabase ───
from services.supabase_client import is_supabase_available
if not is_supabase_available():
    st.error(
        "**No se pudo conectar a Supabase.** Verifica que las variables "
        "`SUPABASE_URL` y `SUPABASE_SERVICE_KEY` estén configuradas en `.env` "
        "y que el schema haya sido creado en Supabase."
    )
    st.stop()

# ─── Verificar entorno ───
from services.auth_service import _AUTHLIB_AVAILABLE, _PYTHON_EXECUTABLE
if not _AUTHLIB_AVAILABLE:
    _is_venv = "venv" in _PYTHON_EXECUTABLE or "envs" in _PYTHON_EXECUTABLE
    st.warning(
        f"**Login con Google deshabilitado** — Authlib no esta instalado.\n\n"
        f"Python en uso: `{_PYTHON_EXECUTABLE}`\n\n"
        + (
            "Ejecuta:\n```\npip install Authlib>=1.3.2\n```\nY reinicia la app."
            if _is_venv else
            "**No estas usando el venv del proyecto.** Ejecuta:\n"
            "```\nvenv\\Scripts\\activate\npython -m streamlit run app.py\n```"
        )
        + "\n\nContinuando en modo demo (sin login).",
        icon="⚠️",
    )

# ─── Guard de autenticacion ───
require_auth()

# ─── Detectar logout y limpiar session_state ───
if is_auth_enabled():
    user_info = getattr(st, "user", None)
    was_logged_in = "current_user" in st.session_state
    is_logged_in = user_info and getattr(user_info, "is_logged_in", False)
    if was_logged_in and not is_logged_in:
        for key in ["trips", "active_trip_id", "user_chats", "active_chat_id",
                     "dismissed_alerts", "user_profile", "current_user"]:
            st.session_state.pop(key, None)

# ─── Obtener user_id actual ───
current_user_id = get_current_user_id()

# ─── Inicializar session_state ───
if "trips" not in st.session_state:
    st.session_state.trips = load_trips(user_id=current_user_id)

if "active_trip_id" not in st.session_state:
    st.session_state.active_trip_id = None

if "user_chats" not in st.session_state:
    st.session_state.user_chats = load_chats(current_user_id)

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None

if "dismissed_alerts" not in st.session_state:
    st.session_state.dismissed_alerts = set()

if "user_profile" not in st.session_state:
    from services.profile_service import load_profile
    st.session_state.user_profile = load_profile(user_id=current_user_id)

# ─── Sincronizar active_trip_id desde el selector del Chat (REQ-CF-001) ───
# El selector del Chat es la fuente de verdad para el viaje activo.
# Sin esto, al navegar a otra página, active_trip_id puede caer al fallback
# (primer viaje en planificación) en vez de usar el viaje seleccionado.
_chat_sel = st.session_state.get("chat_selected_trip_id")
if _chat_sel and _chat_sel not in ("__placeholder__", "__crear_nuevo__"):
    # Validar que el trip_id siga existiendo en la lista de viajes
    if any(t["id"] == _chat_sel for t in st.session_state.trips):
        st.session_state.active_trip_id = _chat_sel
    else:
        # Trip eliminado o inexistente — limpiar referencia obsoleta
        st.session_state.pop("chat_selected_trip_id", None)
        st.session_state.active_trip_id = None

# ─── Actualizar estados por fecha (persiste automaticamente en Supabase) ───
update_trip_statuses(st.session_state.trips)

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

    # Info del usuario autenticado
    current_user = st.session_state.get("current_user")
    if current_user:
        user_cols = st.columns([0.25, 0.75])
        with user_cols[0]:
            picture = current_user.get("picture", "")
            if picture:
                st.image(picture, width=40)
        with user_cols[1]:
            st.markdown(f"**{current_user.get('name', '')}**")
            st.caption(current_user.get("email", ""))

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

        safe_name = html.escape(trip['name'])
        safe_dest = html.escape(trip['destination'])
        st.markdown(
            f"""<div class="active-trip-box">
            <strong>{safe_name}</strong><br>
            📍 {safe_dest}<br>
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

    # Boton de cerrar sesion (solo si auth habilitada)
    if is_auth_enabled() and current_user:
        st.divider()
        if st.button("Cerrar sesion", use_container_width=True):
            st.logout()

# ─── Ejecutar página ───
pg.run()
