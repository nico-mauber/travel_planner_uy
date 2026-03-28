"""Mis Viajes — Historial y gestión (REQ-UI-008, REQ-UI-009, REQ-UI-012)."""

import streamlit as st
from datetime import date, timedelta

if "trips" not in st.session_state:
    st.switch_page("app.py")

from config.settings import TripStatus, TRIP_STATUS_LABELS
from services.trip_service import (
    sort_trips, filter_trips_by_status, delete_trip,
    create_trip,
)
from services.auth_service import get_current_user_id
from services.chat_service import create_chat, load_chats
from services.feedback_service import has_feedback, save_feedback
from components.trip_card import render_trip_card


def _render_feedback_section(trip: dict, idx: int, user_id: str = None) -> None:
    """Renderiza la seccion de feedback para un viaje completado."""
    with st.expander(f"Dar feedback — {trip['name']}", expanded=False):
        with st.form(f"feedback_form_{trip['id']}_{idx}"):
            overall_rating = st.slider(
                f"Valoracion general del viaje (1 = malo, 5 = excelente)",
                min_value=1, max_value=5, value=3,
                key=f"rating_{trip['id']}_{idx}",
                help="Califica tu experiencia general en este viaje",
            )
            comment = st.text_area(
                "Comentarios generales",
                placeholder="Cuenta como fue tu experiencia...",
                key=f"comment_{trip['id']}_{idx}",
                help="Comparte detalles sobre tu experiencia en este viaje",
            )

            # Feedback por item
            item_feedbacks = []
            items = trip.get("items", [])
            if items:
                st.subheader("Valoracion por actividad")
                for item in items[:10]:  # Limitar a 10 items
                    # Layout responsivo: cada item en su propio bloque
                    st.markdown(f"**{item['name']}**")
                    item_cols = st.columns([0.5, 0.5])
                    with item_cols[0]:
                        item_rating = st.slider(
                            f"Rating de {item['name']}",
                            1, 5, 3,
                            key=f"item_rating_{item['id']}_{idx}",
                            help=f"Califica tu experiencia con {item['name']}",
                        )
                    with item_cols[1]:
                        item_comment = st.text_input(
                            f"Nota sobre {item['name']}",
                            key=f"item_comment_{item['id']}_{idx}",
                            placeholder="Comentario breve...",
                            help=f"Agrega un comentario sobre {item['name']}",
                        )
                    item_feedbacks.append({
                        "item_id": item["id"],
                        "item_name": item["name"],
                        "rating": item_rating,
                        "comment": item_comment,
                    })

            fc1, fc2 = st.columns(2)
            with fc1:
                submit_fb = st.form_submit_button(
                    "Enviar feedback", type="primary",
                    help="Guardar tu retroalimentacion sobre este viaje",
                )
            with fc2:
                skip_fb = st.form_submit_button(
                    "Omitir",
                    help="No dar feedback por ahora — podras hacerlo mas tarde",
                )

            if submit_fb:
                feedback_data = {
                    "trip_id": trip["id"],
                    "overall_rating": overall_rating,
                    "comment": comment,
                    "item_feedbacks": item_feedbacks,
                }
                if save_feedback(trip["id"], feedback_data, user_id=user_id):
                    st.toast("✅ ¡Gracias por tu feedback!")
                    st.rerun()
                else:
                    st.error("❌ Error al guardar el feedback. Intentá de nuevo.")

            if skip_fb:
                # Guardar feedback vacío para marcar como "omitido"
                save_feedback(trip["id"], {
                    "trip_id": trip["id"],
                    "overall_rating": 0,
                    "comment": "Omitido",
                    "item_feedbacks": [],
                    "skipped": True,
                }, user_id=user_id)
                st.rerun()


try:
    trips = st.session_state.trips
    user_id = get_current_user_id()

    st.title("Mis Viajes")
    st.markdown('<div class="tp-breadcrumb">🏠 Dashboard  ›  🧳 Mis Viajes</div>', unsafe_allow_html=True)
    st.divider()

    # ─── Barra superior: filtro + nuevo viaje ───
    top_cols = st.columns([0.6, 0.4])

    with top_cols[0]:
        filter_options = ["Todos"] + [
            TRIP_STATUS_LABELS[s] for s in TripStatus
        ]
        status_filter = st.selectbox(
            "Filtrar viajes por estado",
            options=filter_options,
            help="Filtra la lista para mostrar solo viajes con un estado especifico",
        )

    with top_cols[1]:
        if st.button("Nuevo viaje", type="primary", use_container_width=True, help="Abrir formulario para crear un viaje nuevo"):
            st.session_state._show_new_trip_form = True

    # ─── Formulario nuevo viaje ───
    if st.session_state.get("_show_new_trip_form", False):
        with st.container(border=True):
            st.header("Crear nuevo viaje")
            with st.form("new_trip_form"):
                nt_name = st.text_input(
                    "Nombre del viaje",
                    placeholder="Ej: Vacaciones en Roma",
                    help="Un nombre descriptivo para identificar este viaje",
                )
                nt_dest = st.text_input(
                    "Destino",
                    placeholder="Ej: Roma, Italia",
                    help="Ciudad y pais de destino",
                )
                nt_col1, nt_col2 = st.columns(2)
                with nt_col1:
                    nt_start = st.date_input(
                        "Fecha de inicio",
                        value=date.today() + timedelta(days=30),
                        help="Primer dia del viaje",
                    )
                with nt_col2:
                    nt_end = st.date_input(
                        "Fecha de fin",
                        value=date.today() + timedelta(days=37),
                        help="Ultimo dia del viaje",
                    )

                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    create_btn = st.form_submit_button(
                        "Crear viaje", type="primary",
                        use_container_width=True,
                        help="Crear el viaje con los datos ingresados",
                    )
                with col_cancel:
                    cancel_btn = st.form_submit_button(
                        "Cancelar",
                        use_container_width=True,
                        help="Cerrar el formulario sin crear viaje",
                    )

                if create_btn:
                    if not nt_name or not nt_dest:
                        st.error("Nombre y destino son obligatorios.")
                    elif nt_start < date.today():
                        st.warning("⚠️ La fecha de inicio es en el pasado. ¿Estás planificando un viaje ya realizado?")
                    elif nt_end <= nt_start:
                        st.error("La fecha de fin debe ser posterior a la fecha de inicio.")
                    else:
                        new_trip = create_trip(
                            trips, nt_name, nt_dest,
                            str(nt_start), str(nt_end),
                            user_id=user_id,
                        )
                        st.session_state.active_trip_id = new_trip["id"]
                        st.session_state.trips = trips
                        st.session_state._show_new_trip_form = False
                        # Crear chat asociado al nuevo viaje
                        new_chat = create_chat(
                            user_id=user_id,
                            trip_id=new_trip["id"],
                            title=f"Chat — {new_trip['name']}",
                        )
                        st.session_state.active_chat_id = new_chat["chat_id"]
                        st.session_state.user_chats = load_chats(user_id)
                        st.toast(f"🎉 Viaje '{nt_name}' creado correctamente")
                        st.switch_page("pages/2_Chat.py")

                if cancel_btn:
                    st.session_state._show_new_trip_form = False
                    st.rerun()

    # ─── Mapear filtro a valor de enum ───
    label_to_status = {v: k.value for k, v in TRIP_STATUS_LABELS.items()}
    active_filter = label_to_status.get(status_filter, None)

    # ─── Filtrar y ordenar ───
    filtered = filter_trips_by_status(trips, active_filter)
    sorted_trips = sort_trips(filtered)

    # ─── Estado vacío ───
    if not sorted_trips:
        st.info(
            "No tienes viajes registrados. Crea uno nuevo para empezar a planificar."
        )
        st.stop()

    # ─── Confirmacion de eliminacion ───
    if st.session_state.get("_confirm_delete"):
        trip_id = st.session_state._confirm_delete
        trip_to_del = next((t for t in trips if t["id"] == trip_id), None)
        if trip_to_del:
            st.warning(f"Estas seguro de eliminar el viaje **{trip_to_del['name']}**? Esta accion no se puede deshacer.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Si, eliminar viaje", type="primary", help="Confirmar eliminacion permanente del viaje"):
                    delete_trip(trips, trip_id, user_id=user_id)
                    st.session_state.trips = trips
                    if st.session_state.active_trip_id == trip_id:
                        st.session_state.active_trip_id = None
                    # Limpiar estado de chat si apuntaba al viaje eliminado
                    if st.session_state.get("chat_selected_trip_id") == trip_id:
                        st.session_state.pop("chat_selected_trip_id", None)
                    if st.session_state.get("_chat_prev_trip_id") == trip_id:
                        st.session_state.pop("_chat_prev_trip_id", None)
                    st.session_state.pop("active_chat_id", None)
                    st.session_state.pop("user_chats", None)
                    st.session_state._confirm_delete = None
                    st.rerun()
            with c2:
                if st.button("Cancelar eliminacion", help="No eliminar, mantener el viaje"):
                    st.session_state._confirm_delete = None
                    st.rerun()

    # ─── Lista de viajes ───
    for idx, trip in enumerate(sorted_trips):
        # Indicador de feedback pendiente para viajes completados
        is_completed = trip["status"] == TripStatus.COMPLETED.value
        needs_feedback = is_completed and not has_feedback(trip["id"])

        result = render_trip_card(trip, idx)

        if needs_feedback:
            _render_feedback_section(trip, idx, user_id=user_id)

        if result.get("action") == "view":
            st.session_state.active_trip_id = result["trip_id"]
            st.session_state.chat_selected_trip_id = result["trip_id"]
            st.switch_page("pages/1_Dashboard.py")

        elif result.get("action") == "delete":
            st.session_state._confirm_delete = result["trip_id"]
            st.rerun()

except Exception as e:
    st.error(f"Error al cargar Mis Viajes: {e}")
    if st.button("Reintentar", help="Recargar la pagina de mis viajes"):
        st.rerun()
