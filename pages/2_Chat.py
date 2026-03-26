"""Chat con el Agente — Selector obligatorio de viaje + multiples conversaciones
(REQ-CF-001, REQ-UI-002, REQ-UI-003, REQ-CL-004, REQ-CL-005)."""

import html
import streamlit as st
from datetime import date, timedelta

if "trips" not in st.session_state:
    st.switch_page("app.py")

from config.settings import TripStatus
from services.trip_service import get_trip_by_id, create_trip
from services.agent_service import process_message, apply_confirmed_action, is_llm_active, is_booking_active, is_flights_active
from services.auth_service import get_current_user_id
from services.chat_service import (
    load_chats, create_chat, get_chat_by_id, delete_chat,
    rename_chat, add_message, persist_chat, auto_generate_title,
    get_latest_chat_for_trip,
)
from components.chat_widget import render_rich_card, render_confirmation, render_hotel_results, render_flight_results


# Sentinel para opcion "Crear nuevo viaje" en el selector
_CREAR_NUEVO = "__crear_nuevo__"
_PLACEHOLDER = "__placeholder__"


def _clear_drafts():
    """Limpia drafts de creacion de viaje e item del session_state.

    Evita que un draft persista al cambiar de chat, eliminar chat o cambiar viaje.
    """
    st.session_state.pop("_trip_creation_draft", None)
    st.session_state.pop("_item_creation_draft", None)


try:
    trips = st.session_state.trips
    user_id = get_current_user_id()

    # ─── Selector obligatorio de viaje (REQ-CF-001) ───
    active_statuses = [TripStatus.PLANNING.value, TripStatus.CONFIRMED.value, TripStatus.IN_PROGRESS.value]
    available_trips = [t for t in trips if t["status"] in active_statuses]

    # Construir opciones del selector
    selector_options = [_PLACEHOLDER]
    selector_labels = {_PLACEHOLDER: "-- Selecciona un viaje --"}
    for t in available_trips:
        selector_options.append(t["id"])
        selector_labels[t["id"]] = f"{t['name']} — {t['destination']} ({t['status']})"
    selector_options.append(_CREAR_NUEVO)
    selector_labels[_CREAR_NUEVO] = "Crear nuevo viaje"

    # Determinar indice inicial basado en session_state
    saved_selection = st.session_state.get("chat_selected_trip_id")
    default_index = 0
    if not available_trips:
        # Usuario sin viajes: pre-seleccionar "Crear nuevo viaje" automáticamente
        default_index = selector_options.index(_CREAR_NUEVO)
    elif saved_selection and saved_selection in selector_options:
        default_index = selector_options.index(saved_selection)

    selected_key = st.selectbox(
        "Selecciona un viaje para chatear",
        options=selector_options,
        format_func=lambda k: selector_labels.get(k, k),
        index=default_index,
        key="trip_selector_widget",
    )

    # Persistir seleccion en session_state (RN-008)
    if selected_key != _PLACEHOLDER:
        st.session_state.chat_selected_trip_id = selected_key

    # Determinar viaje seleccionado y estado del chat
    chat_trip = None
    chat_enabled = False
    is_creating_new_trip = False

    if selected_key == _PLACEHOLDER:
        st.info("Selecciona un viaje del selector para comenzar a chatear.")

    elif selected_key == _CREAR_NUEVO:
        is_creating_new_trip = True
        chat_enabled = True

    else:
        chat_trip = get_trip_by_id(trips, selected_key)
        if chat_trip:
            chat_enabled = True
            st.session_state.active_trip_id = chat_trip["id"]
        else:
            st.warning("El viaje seleccionado ya no existe. Selecciona otro.")

    # ─── Cargar/crear chat al cambiar viaje (RN-007) ───
    if chat_enabled and not is_creating_new_trip and chat_trip:
        prev_trip = st.session_state.get("_chat_prev_trip_id")
        if prev_trip != chat_trip["id"]:
            # Viaje cambio — limpiar drafts y cargar ultimo chat o crear uno nuevo
            _clear_drafts()
            latest = get_latest_chat_for_trip(user_id, chat_trip["id"])
            if latest:
                st.session_state.active_chat_id = latest["chat_id"]
            else:
                new_chat = create_chat(
                    user_id=user_id,
                    trip_id=chat_trip["id"],
                    title="Nueva conversacion",
                )
                st.session_state.active_chat_id = new_chat["chat_id"]
            st.session_state._chat_prev_trip_id = chat_trip["id"]
            st.session_state.user_chats = load_chats(user_id)

    elif chat_enabled and is_creating_new_trip:
        # Modo creacion: si no hay chat activo, crear uno sin trip_id
        if not st.session_state.get("active_chat_id"):
            new_chat = create_chat(
                user_id=user_id,
                trip_id=None,
                title="Nuevo viaje",
            )
            st.session_state.active_chat_id = new_chat["chat_id"]
            st.session_state.user_chats = load_chats(user_id)

    # ─── Header compacto con info del viaje + badges ───
    if chat_trip:
        dest = html.escape(chat_trip.get("destination", ""))
        dates = f"{chat_trip.get('start_date', '')} — {chat_trip.get('end_date', '')}"

        badges_html = ""
        if is_llm_active():
            badges_html += '<span class="tp-llm-indicator tp-llm-indicator--active">AI</span>'
        else:
            badges_html += '<span class="tp-llm-indicator tp-llm-indicator--basic">Básico</span>'
        if is_booking_active():
            badges_html += '<span class="tp-llm-indicator tp-llm-indicator--active">Hotels</span>'
        if is_flights_active():
            badges_html += '<span class="tp-llm-indicator tp-llm-indicator--active">Flights</span>'

        header_html = (
            '<div class="tp-chat-header">'
            '  <div class="tp-chat-header__info">'
            f'    <div class="tp-chat-header__destination">✈️ {dest}</div>'
            f'    <div class="tp-chat-header__dates">{dates}</div>'
            '  </div>'
            f'  <div class="tp-chat-header__badges">{badges_html}</div>'
            '</div>'
        )
        st.markdown(header_html, unsafe_allow_html=True)
    elif is_creating_new_trip:
        st.caption("Modo creacion de viaje — indica tu destino y fechas")

    # ─── Sidebar: lista de chats ───
    with st.sidebar:
        st.markdown('<div class="tp-chat-sidebar-title">Conversaciones</div>', unsafe_allow_html=True)

        # Búsqueda en historial
        search_query = st.text_input(
            "Buscar...",
            placeholder="Buscar chat...",
            label_visibility="collapsed",
            key="chat_search",
        )

        # Boton nuevo chat
        if chat_enabled:
            if st.button("+ Nuevo Chat", use_container_width=True, key="new_chat_btn"):
                new_chat = create_chat(
                    user_id=user_id,
                    trip_id=chat_trip["id"] if chat_trip else None,
                    title="Nueva conversacion",
                )
                st.session_state.active_chat_id = new_chat["chat_id"]
                st.session_state.user_chats = load_chats(user_id)
                st.rerun()

        st.divider()

        # Cargar chats del usuario
        if "user_chats" not in st.session_state:
            st.session_state.user_chats = load_chats(user_id)

        user_chats = st.session_state.user_chats
        active_chat_id = st.session_state.get("active_chat_id")

        # Filtrar chats por viaje seleccionado (si hay uno)
        if chat_trip:
            visible_chats = [c for c in user_chats if c.get("trip_id") == chat_trip["id"]]
        elif is_creating_new_trip:
            visible_chats = [c for c in user_chats if not c.get("trip_id")]
        else:
            visible_chats = user_chats

        # Aplicar filtro de búsqueda
        if search_query:
            visible_chats = [c for c in visible_chats if search_query.lower() in c.get("title", "").lower()]

        if not visible_chats:
            st.caption("No hay conversaciones para este viaje.")
        else:
            for chat in visible_chats:
                chat_id = chat["chat_id"]
                is_active = chat_id == active_chat_id

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
                            _clear_drafts()
                            st.session_state.active_chat_id = chat_id
                            st.rerun()
                    with btn_cols[1]:
                        if st.button(
                            "X",
                            key=f"del_{chat_id}",
                            help="Eliminar esta conversacion permanentemente",
                        ):
                            st.session_state._confirm_delete_chat = chat_id
                            st.rerun()

            # Confirmacion de eliminacion de chat
            if st.session_state.get("_confirm_delete_chat"):
                _del_id = st.session_state._confirm_delete_chat
                st.warning("Eliminar esta conversacion? Esta accion no se puede deshacer.")
                dc1, dc2 = st.columns(2)
                with dc1:
                    if st.button("Si, eliminar conversacion", key="confirm_del_chat", type="primary", help="Confirmar eliminacion permanente"):
                        delete_chat(_del_id, user_id=user_id)
                        if active_chat_id == _del_id:
                            _clear_drafts()
                            st.session_state.active_chat_id = None
                        st.session_state._confirm_delete_chat = None
                        st.session_state.user_chats = load_chats(user_id)
                        st.rerun()
                with dc2:
                    if st.button("Cancelar eliminacion", key="cancel_del_chat", help="No eliminar, mantener la conversacion"):
                        st.session_state._confirm_delete_chat = None
                        st.rerun()

    # ─── Area principal de chat (100% del ancho) ───
    if not chat_enabled:
        st.stop()

    # Obtener chat activo
    active_chat = None
    if active_chat_id:
        active_chat = get_chat_by_id(user_chats, active_chat_id)

    if not active_chat:
        st.info("Selecciona una conversacion o crea una nueva para comenzar.")
        st.stop()

    st.divider()

    # ─── Historial del chat activo ───
    history = active_chat.get("messages", [])

    # Paginación: mostrar solo últimos 30 mensajes
    MAX_VISIBLE_MESSAGES = 30
    if len(history) > MAX_VISIBLE_MESSAGES:
        hidden_count = len(history) - MAX_VISIBLE_MESSAGES
        if not st.session_state.get(f"_show_all_{active_chat_id}"):
            if st.button(f"⬆️ Cargar {hidden_count} mensajes anteriores", key="load_more_msgs", help="Mostrar mensajes más antiguos de esta conversación"):
                st.session_state[f"_show_all_{active_chat_id}"] = True
                st.rerun()
            history = history[-MAX_VISIBLE_MESSAGES:]

    # ─── Welcome screen premium para chat vacío ───
    if not history:
        if is_creating_new_trip:
            welcome_text = (
                "Vamos a crear un nuevo viaje. "
                "Indicame el destino al que te gustaria ir."
            )
            welcome_msg = {
                "role": "assistant",
                "type": "text",
                "content": welcome_text,
            }
            add_message(active_chat, welcome_msg)
            persist_chat(active_chat)
            st.session_state.user_chats = load_chats(user_id)
            history = active_chat["messages"]
        else:
            dest = chat_trip.get("destination", "tu destino") if chat_trip else "tu destino"
            dates_info = ""
            if chat_trip:
                dates_info = f'{chat_trip.get("start_date", "")} — {chat_trip.get("end_date", "")}'

            welcome_html = (
                '<div class="tp-chat-welcome">'
                '  <div class="tp-chat-welcome__icon">✈️</div>'
                f'  <div class="tp-chat-welcome__title">Tu agente de viajes personal</div>'
                f'  <div class="tp-chat-welcome__subtitle">Viaje a {html.escape(dest)}</div>'
                f'  <div class="tp-chat-welcome__trip-info">{html.escape(dates_info)}</div>'
                '</div>'
            )
            st.markdown(welcome_html, unsafe_allow_html=True)

            # Quick actions como botones en grid de 3 columnas
            if chat_trip and not is_creating_new_trip:
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("🏨 Buscar hotel", use_container_width=True, key=f"qa_hotel_{active_chat_id}"):
                        st.session_state[f"_quick_action_{active_chat_id}"] = f"Buscar hoteles en {dest}"
                        st.rerun()
                with c2:
                    if st.button("✈️ Buscar vuelos", use_container_width=True, key=f"qa_flights_{active_chat_id}"):
                        st.session_state[f"_quick_action_{active_chat_id}"] = f"Buscar vuelos desde Montevideo a {dest}"
                        st.rerun()
                with c3:
                    if st.button("🎯 Actividades", use_container_width=True, key=f"qa_activity_{active_chat_id}"):
                        st.session_state[f"_quick_action_{active_chat_id}"] = "Agregar una actividad para el dia 1"
                        st.rerun()
                c4, c5, c6 = st.columns(3)
                with c4:
                    if st.button("🍽️ Restaurante", use_container_width=True, key=f"qa_food_{active_chat_id}"):
                        st.session_state[f"_quick_action_{active_chat_id}"] = "Agregar un restaurante para almorzar el dia 1"
                        st.rerun()
                with c5:
                    if st.button("📋 Sugerir plan", use_container_width=True, key=f"qa_plan_{active_chat_id}"):
                        st.session_state[f"_quick_action_{active_chat_id}"] = "Que me sugeris para el primer dia?"
                        st.rerun()
                with c6:
                    if st.button("💰 Gastos", use_container_width=True, key=f"qa_expense_{active_chat_id}"):
                        st.session_state[f"_quick_action_{active_chat_id}"] = "Quiero registrar un gasto"
                        st.rerun()

            # Agregar mensaje de bienvenida al historial para que el chat no quede vacío
            if chat_trip:
                welcome_text = (
                    f"Estoy listo para ayudarte con tu viaje a **{chat_trip['destination']}**. "
                    "Puedo ayudarte a planificar actividades, buscar hoteles, "
                    "organizar el itinerario y mas."
                )
            else:
                welcome_text = (
                    "Soy tu asistente de viajes. "
                    "Puedo ayudarte a planificar viajes, buscar hoteles, "
                    "organizar actividades y mas."
                )
            welcome_msg = {
                "role": "assistant",
                "type": "text",
                "content": welcome_text,
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

            elif msg_type == "flight_results":
                render_flight_results(msg["content"])

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
                                f"Viaje creado: **{new_trip['name']}** a {new_trip['destination']} "
                                f"({new_trip['start_date']} — {new_trip['end_date']})"
                            )
                            msg["result"] = result_msg
                            st.session_state.trips = trips
                            # Limpiar draft de creacion
                            st.session_state.pop("_trip_creation_draft", None)
                            # Actualizar selector al nuevo viaje
                            st.session_state.chat_selected_trip_id = new_trip["id"]
                            st.session_state._chat_prev_trip_id = new_trip["id"]
                            add_message(active_chat, {
                                "role": "assistant",
                                "type": "text",
                                "content": (
                                    f"{result_msg}\n\n"
                                    "El viaje ya esta activo. Puedes verlo en **Mis Viajes** "
                                    "o empezar a planificar aqui mismo."
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
                        # Limpiar drafts si existian
                        st.session_state.pop("_trip_creation_draft", None)
                        st.session_state.pop("_item_creation_draft", None)
                        add_message(active_chat, {
                            "role": "assistant",
                            "type": "text",
                            "content": "Entendido, he cancelado la accion.",
                        })
                        persist_chat(active_chat)
                        st.session_state.user_chats = load_chats(user_id)
                        st.rerun()

    # ─── Input del usuario ───
    # Verificar si hay quick-action pendiente
    _quick_action_key = f"_quick_action_{active_chat_id}"
    quick_action_input = st.session_state.pop(_quick_action_key, None)

    user_input = st.chat_input("Escribí tu mensaje al asistente de viajes...") or quick_action_input
    if user_input:
        # Capturar historial ANTES de agregar el mensaje actual
        # (el mensaje actual se pasa por separado como 'message' a process_message)
        chat_history = active_chat.get("messages", [])

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
            rename_chat(active_chat["chat_id"], new_title, user_id=user_id)

        with st.spinner("El asistente esta procesando tu solicitud..."):
            trip_creation_draft = st.session_state.get("_trip_creation_draft")
            item_creation_draft = st.session_state.get("_item_creation_draft")
            response = process_message(
                user_input, chat_trip,
                user_id=user_id,
                chat_id=active_chat["chat_id"],
                trip_creation_draft=trip_creation_draft,
                item_creation_draft=item_creation_draft,
                chat_history=chat_history,
            )

        # Manejar draft de creacion de viaje en la respuesta
        if "_trip_creation_draft" in response:
            draft_value = response.pop("_trip_creation_draft")
            if draft_value is None:
                st.session_state.pop("_trip_creation_draft", None)
            else:
                st.session_state["_trip_creation_draft"] = draft_value

        # Manejar draft de creacion de item en la respuesta
        if "_item_creation_draft" in response:
            draft_value = response.pop("_item_creation_draft")
            if draft_value is None:
                st.session_state.pop("_item_creation_draft", None)
            else:
                st.session_state["_item_creation_draft"] = draft_value

        add_message(active_chat, response)
        persist_chat(active_chat)
        st.session_state.user_chats = load_chats(user_id)
        st.rerun()

except Exception as e:
    st.error("Ocurrió un error en el chat. Por favor, intentá de nuevo.")
    with st.expander("Detalles técnicos", expanded=False):
        st.code(str(e))
    if st.button("Reintentar", help="Recargar la pagina del chat"):
        st.rerun()
