"""Mis Viajes — Historial y gestión (REQ-UI-008, REQ-UI-009, REQ-UI-012)."""

import streamlit as st
from datetime import date, timedelta

from config.settings import TripStatus, TRIP_STATUS_LABELS
from services.trip_service import (
    sort_trips, filter_trips_by_status, delete_trip,
    create_trip, save_trips,
)
from services.feedback_service import has_feedback, save_feedback
from components.trip_card import render_trip_card


try:
    trips = st.session_state.trips

    st.title("🌍 Mis Viajes")
    st.markdown("---")

    # ─── Barra superior: filtro + nuevo viaje ───
    top_cols = st.columns([0.6, 0.4])

    with top_cols[0]:
        filter_options = ["Todos"] + [
            TRIP_STATUS_LABELS[s] for s in TripStatus
        ]
        status_filter = st.selectbox(
            "Filtrar por estado",
            options=filter_options,
            label_visibility="collapsed",
        )

    with top_cols[1]:
        if st.button("➕ Nuevo viaje", type="primary", use_container_width=True):
            st.session_state._show_new_trip_form = True

    # ─── Formulario nuevo viaje ───
    if st.session_state.get("_show_new_trip_form", False):
        with st.container(border=True):
            st.subheader("Crear nuevo viaje")
            with st.form("new_trip_form"):
                nt_name = st.text_input("Nombre del viaje", placeholder="Ej: Vacaciones en Roma")
                nt_dest = st.text_input("Destino", placeholder="Ej: Roma, Italia")
                nt_col1, nt_col2 = st.columns(2)
                with nt_col1:
                    nt_start = st.date_input("Fecha inicio", value=date.today() + timedelta(days=30))
                with nt_col2:
                    nt_end = st.date_input("Fecha fin", value=date.today() + timedelta(days=37))

                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    create_btn = st.form_submit_button("✅ Crear", type="primary",
                                                       use_container_width=True)
                with col_cancel:
                    cancel_btn = st.form_submit_button("❌ Cancelar",
                                                       use_container_width=True)

                if create_btn:
                    if not nt_name or not nt_dest:
                        st.error("Nombre y destino son obligatorios.")
                    elif nt_end <= nt_start:
                        st.error("La fecha de fin debe ser posterior a la fecha de inicio.")
                    else:
                        new_trip = create_trip(
                            trips, nt_name, nt_dest,
                            str(nt_start), str(nt_end),
                        )
                        st.session_state.active_trip_id = new_trip["id"]
                        st.session_state.trips = trips
                        st.session_state._show_new_trip_form = False
                        # Crear historial de chat para el nuevo viaje
                        if new_trip["id"] not in st.session_state.chat_histories:
                            st.session_state.chat_histories[new_trip["id"]] = [{
                                "role": "assistant",
                                "type": "text",
                                "content": (
                                    f"¡Perfecto! He creado tu viaje '{new_trip['name']}' "
                                    f"a {new_trip['destination']}. ¿Qué te gustaría planificar?"
                                ),
                            }]
                        st.success(f"Viaje '{nt_name}' creado. Redirigiendo al Chat...")
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

    # ─── Confirmación de eliminación ───
    if st.session_state.get("_confirm_delete"):
        trip_id = st.session_state._confirm_delete
        trip_to_del = next((t for t in trips if t["id"] == trip_id), None)
        if trip_to_del:
            st.warning(f"¿Estás seguro de eliminar el viaje **{trip_to_del['name']}**?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Sí, eliminar", type="primary"):
                    delete_trip(trips, trip_id)
                    st.session_state.trips = trips
                    if st.session_state.active_trip_id == trip_id:
                        st.session_state.active_trip_id = None
                    st.session_state._confirm_delete = None
                    st.rerun()
            with c2:
                if st.button("Cancelar"):
                    st.session_state._confirm_delete = None
                    st.rerun()

    # ─── Lista de viajes ───
    for idx, trip in enumerate(sorted_trips):
        # Indicador de feedback pendiente para viajes completados
        is_completed = trip["status"] == TripStatus.COMPLETED.value
        needs_feedback = is_completed and not has_feedback(trip["id"])

        result = render_trip_card(trip, idx)

        if needs_feedback:
            _render_feedback_section(trip, idx)

        if result.get("action") == "view":
            st.session_state.active_trip_id = result["trip_id"]
            st.switch_page("pages/1_Dashboard.py")

        elif result.get("action") == "delete":
            st.session_state._confirm_delete = result["trip_id"]
            st.rerun()

except Exception as e:
    st.error(f"Error al cargar Mis Viajes: {e}")
    if st.button("🔄 Reintentar"):
        st.rerun()


def _render_feedback_section(trip: dict, idx: int) -> None:
    """Renderiza la sección de feedback para un viaje completado."""
    with st.expander(f"📝 Dar feedback — {trip['name']}", expanded=False):
        with st.form(f"feedback_form_{trip['id']}_{idx}"):
            overall_rating = st.slider(
                "Valoración general",
                min_value=1, max_value=5, value=3,
                key=f"rating_{trip['id']}_{idx}",
            )
            comment = st.text_area(
                "Comentarios",
                placeholder="¿Cómo fue tu experiencia?",
                key=f"comment_{trip['id']}_{idx}",
            )

            # Feedback por item
            item_feedbacks = []
            items = trip.get("items", [])
            if items:
                st.markdown("**Valoración por actividad:**")
                for item in items[:10]:  # Limitar a 10 items
                    item_cols = st.columns([0.6, 0.2, 0.2])
                    with item_cols[0]:
                        st.caption(item["name"])
                    with item_cols[1]:
                        item_rating = st.slider(
                            "Rating",
                            1, 5, 3,
                            key=f"item_rating_{item['id']}_{idx}",
                            label_visibility="collapsed",
                        )
                    with item_cols[2]:
                        item_comment = st.text_input(
                            "Nota",
                            key=f"item_comment_{item['id']}_{idx}",
                            label_visibility="collapsed",
                            placeholder="Nota...",
                        )
                    item_feedbacks.append({
                        "item_id": item["id"],
                        "item_name": item["name"],
                        "rating": item_rating,
                        "comment": item_comment,
                    })

            fc1, fc2 = st.columns(2)
            with fc1:
                submit_fb = st.form_submit_button("📤 Enviar feedback", type="primary")
            with fc2:
                skip_fb = st.form_submit_button("⏭️ Omitir")

            if submit_fb:
                feedback_data = {
                    "trip_id": trip["id"],
                    "overall_rating": overall_rating,
                    "comment": comment,
                    "item_feedbacks": item_feedbacks,
                }
                if save_feedback(trip["id"], feedback_data):
                    st.success("¡Gracias por tu feedback!")
                    st.rerun()
                else:
                    st.error("Error al guardar el feedback.")

            if skip_fb:
                # Guardar feedback vacío para marcar como "omitido"
                save_feedback(trip["id"], {
                    "trip_id": trip["id"],
                    "overall_rating": 0,
                    "comment": "Omitido",
                    "item_feedbacks": [],
                    "skipped": True,
                })
                st.rerun()
