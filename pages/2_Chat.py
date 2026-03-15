"""Chat con el Agente — Multiples conversaciones (REQ-UI-002, REQ-UI-003, REQ-CL-004, REQ-CL-005)."""

import streamlit as st
from datetime import date, timedelta

from services.trip_service import get_active_trip, get_trip_by_id, create_trip
from services.agent_service import process_message, apply_confirmed_action, is_llm_active, is_booking_active
from services.auth_service import get_current_user_id
from services.chat_service import (
    load_chats, create_chat, get_chat_by_id, delete_chat,
    rename_chat, add_message, persist_chat, auto_generate_title,
)
from components.chat_widget import render_rich_card, render_confirmation, render_hotel_results


def _find_trip_by_destination(msg_lower: str, trips: list):
    """Busca un viaje cuyo destino sea mencionado en el mensaje (longest match)."""
    best = None
    best_len = 0
    for t in trips:
        dest = (t.get("destination") or "").strip()
        if not dest:
            continue
        for part in [dest] + [p.strip() for p in dest.split(",")]:
            pl = part.lower()
            if len(pl) > 2 and pl in msg_lower:
                if len(pl) > best_len:
                    best = t
                    best_len = len(pl)
    return best


try:
    trips = st.session_state.trips
    active_trip_id = st.session_state.get("active_trip_id")
    trip = get_active_trip(trips, active_trip_id)
    user_id = get_current_user_id()

    st.title("Chat con el Agente")

    # Indicador de modo
    mode_parts = []
    if is_llm_active():
        mode_parts.append("Gemini")
    else:
        mode_parts.append("Modo basico")
    if is_booking_active():
        mode_parts.append("Booking.com")
    st.caption(f"Asistente IA ({' + '.join(mode_parts)})")

    # ─── Layout dos columnas ───
    col_list, col_chat = st.columns([0.3, 0.7])

    # ─── Columna izquierda: lista de chats ───
    with col_list:
        st.markdown("#### Conversaciones")

        # Boton nuevo chat
        if st.button("Nuevo Chat", use_container_width=True, type="primary"):
            new_chat = create_chat(
                user_id=user_id,
                trip_id=trip["id"] if trip else None,
                title="Nueva conversacion",
            )
            st.session_state.active_chat_id = new_chat["chat_id"]
            st.session_state.user_chats = load_chats(user_id)
            st.rerun()

        st.markdown("---")

        # Cargar chats del usuario
        if "user_chats" not in st.session_state:
            st.session_state.user_chats = load_chats(user_id)

        user_chats = st.session_state.user_chats
        active_chat_id = st.session_state.get("active_chat_id")

        if not user_chats:
            st.caption("No tienes conversaciones. Crea una nueva.")
        else:
            for chat in user_chats:
                chat_id = chat["chat_id"]
                is_active = chat_id == active_chat_id

                # Contenedor para cada chat
                with st.container():
                    btn_cols = st.columns([0.75, 0.25])
                    with btn_cols[0]:
                        label = chat["title"]
                        if is_active:
                            label = f"**{label}**"
                        if st.button(
                            label,
                            key=f"select_{chat_id}",
                            use_container_width=True,
                        ):
                            st.session_state.active_chat_id = chat_id
                            st.rerun()
                    with btn_cols[1]:
                        if st.button(
                            "X",
                            key=f"del_{chat_id}",
                            help="Eliminar conversacion",
                        ):
                            st.session_state._confirm_delete_chat = chat_id
                            st.rerun()

            # Confirmacion de eliminacion de chat
            if st.session_state.get("_confirm_delete_chat"):
                _del_id = st.session_state._confirm_delete_chat
                st.warning("¿Eliminar esta conversación?")
                dc1, dc2 = st.columns(2)
                with dc1:
                    if st.button("Si, eliminar", key="confirm_del_chat", type="primary"):
                        delete_chat(_del_id, user_id=user_id)
                        if active_chat_id == _del_id:
                            st.session_state.active_chat_id = None
                        st.session_state._confirm_delete_chat = None
                        st.session_state.user_chats = load_chats(user_id)
                        st.rerun()
                with dc2:
                    if st.button("Cancelar", key="cancel_del_chat"):
                        st.session_state._confirm_delete_chat = None
                        st.rerun()

    # ─── Columna derecha: chat activo ───
    with col_chat:
        # Obtener chat activo
        active_chat = None
        if active_chat_id:
            active_chat = get_chat_by_id(user_chats, active_chat_id)

        if not active_chat:
            st.info("Selecciona una conversacion o crea una nueva para comenzar.")
            st.stop()

        # Info del viaje asociado
        chat_trip = None
        if active_chat.get("trip_id"):
            chat_trip = get_trip_by_id(trips, active_chat["trip_id"])
        if not chat_trip:
            chat_trip = trip  # Usar viaje activo global como fallback

        if chat_trip:
            st.caption(f"Viaje activo: **{chat_trip['name']}** — {chat_trip['destination']}")
        else:
            st.caption("Sin viaje activo — puedes crear uno desde aquí")

        st.markdown("---")

        # ─── Historial del chat activo ───
        history = active_chat.get("messages", [])

        # Mensaje de bienvenida si el chat esta vacio
        if not history:
            welcome_msg = {
                "role": "assistant",
                "type": "text",
                "content": (
                    "¡Hola! Soy tu asistente de viajes. "
                    "Puedo ayudarte a planificar viajes, buscar hoteles, "
                    "organizar actividades y más. ¿En qué puedo ayudarte?"
                ),
            }
            add_message(active_chat, welcome_msg)
            persist_chat(active_chat)
            st.session_state.user_chats = load_chats(user_id)
            history = active_chat["messages"]

        # ─── Renderizar mensajes ───
        for i, msg in enumerate(history):
            role = msg.get("role", "assistant")
            msg_type = msg.get("type", "text")

            with st.chat_message(role):
                if msg_type == "text":
                    st.markdown(msg["content"])

                elif msg_type == "card":
                    st.markdown("He encontrado esta opcion para ti:")
                    render_rich_card(msg["content"])

                elif msg_type == "hotel_results":
                    render_hotel_results(msg["content"])

                elif msg_type == "confirmation":
                    action_data = msg["content"]
                    if msg.get("processed"):
                        st.markdown(
                            f"*{action_data.get('summary', '')}* — {msg.get('result', '')}"
                        )
                    else:
                        result = render_confirmation(action_data, i)
                        if result == "confirm":
                            if action_data.get("action") == "create_trip":
                                details = action_data.get("details", {})
                                fallback_start = str(date.today() + timedelta(days=30))
                                fallback_end = str(date.today() + timedelta(days=37))
                                new_trip = create_trip(
                                    trips,
                                    name=details.get("name", "Nuevo viaje"),
                                    destination=details.get("destination", "Sin destino"),
                                    start_date=details.get("start_date", fallback_start),
                                    end_date=details.get("end_date", fallback_end),
                                    user_id=user_id,
                                )
                                st.session_state.active_trip_id = new_trip["id"]
                                # Asociar chat al nuevo viaje
                                active_chat["trip_id"] = new_trip["id"]
                                msg["processed"] = True
                                result_msg = (
                                    f"✅ Viaje creado: **{new_trip['name']}** a {new_trip['destination']} "
                                    f"({new_trip['start_date']} — {new_trip['end_date']})"
                                )
                                msg["result"] = result_msg
                                st.session_state.trips = trips
                                # Limpiar draft de creación
                                st.session_state.pop("_trip_creation_draft", None)
                                add_message(active_chat, {
                                    "role": "assistant",
                                    "type": "text",
                                    "content": (
                                        f"{result_msg}\n\n"
                                        "El viaje ya está activo. Puedes verlo en **Mis Viajes** "
                                        "o empezar a planificar aquí mismo."
                                    ),
                                })
                                persist_chat(active_chat)
                                st.session_state.user_chats = load_chats(user_id)
                            elif chat_trip:
                                result_msg = apply_confirmed_action(
                                    action_data, chat_trip, trips
                                )
                                msg["processed"] = True
                                msg["result"] = result_msg
                                st.session_state.trips = trips
                                add_message(active_chat, {
                                    "role": "assistant",
                                    "type": "text",
                                    "content": result_msg,
                                })
                                persist_chat(active_chat)
                                st.session_state.user_chats = load_chats(user_id)
                            st.rerun()

                        elif result == "cancel":
                            msg["processed"] = True
                            msg["result"] = "Cancelado por el usuario"
                            # Limpiar draft de creación si existía
                            st.session_state.pop("_trip_creation_draft", None)
                            add_message(active_chat, {
                                "role": "assistant",
                                "type": "text",
                                "content": "Entendido, he cancelado la acción. ¿En qué más puedo ayudarte?",
                            })
                            persist_chat(active_chat)
                            st.session_state.user_chats = load_chats(user_id)
                            st.rerun()

        # ─── Input del usuario ───
        if user_input := st.chat_input("Escribe tu mensaje..."):
            # Agregar mensaje del usuario
            user_msg = {
                "role": "user",
                "type": "text",
                "content": user_input,
            }
            add_message(active_chat, user_msg)

            # Auto-generar titulo al primer mensaje del usuario
            user_messages = [m for m in active_chat["messages"] if m.get("role") == "user"]
            if len(user_messages) == 1:
                new_title = auto_generate_title(user_input)
                active_chat["title"] = new_title
                rename_chat(active_chat["chat_id"], new_title)

            # Detectar contexto de viaje desde el mensaje
            detected = _find_trip_by_destination(user_input.lower(), trips)
            if detected and detected["id"] != (chat_trip or {}).get("id"):
                chat_trip = detected
                active_chat["trip_id"] = detected["id"]
                st.session_state.active_trip_id = detected["id"]

            with st.spinner("El asistente esta procesando tu solicitud..."):
                trip_creation_draft = st.session_state.get("_trip_creation_draft")
                response = process_message(
                    user_input, chat_trip,
                    user_id=user_id,
                    chat_id=active_chat["chat_id"],
                    trip_creation_draft=trip_creation_draft,
                )

            # Manejar draft de creación de viaje en la respuesta
            if "_trip_creation_draft" in response:
                draft_value = response.pop("_trip_creation_draft")
                if draft_value is None:
                    st.session_state.pop("_trip_creation_draft", None)
                else:
                    st.session_state["_trip_creation_draft"] = draft_value

            add_message(active_chat, response)
            persist_chat(active_chat)
            st.session_state.user_chats = load_chats(user_id)
            st.rerun()

except Exception as e:
    st.error(f"Error en el chat: {e}")
    if st.button("Reintentar"):
        st.rerun()
