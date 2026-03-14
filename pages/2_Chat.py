"""Chat con el Agente (REQ-UI-002, REQ-UI-003)."""

import streamlit as st

from services.trip_service import get_active_trip, create_trip, sync_trip_changes, save_trips
from services.agent_service import process_message, apply_confirmed_action, is_llm_active
from components.chat_widget import render_rich_card, render_confirmation


try:
    trips = st.session_state.trips
    active_trip_id = st.session_state.get("active_trip_id")
    trip = get_active_trip(trips, active_trip_id)

    st.title("💬 Chat con el Agente")

    # Indicador de modo
    if is_llm_active():
        st.caption("🤖 Asistente IA (Gemini)")
    else:
        st.caption("💡 Asistente básico (sin LLM)")

    if trip:
        st.caption(f"Viaje activo: **{trip['name']}** — {trip['destination']}")
    else:
        st.caption("Sin viaje activo — puedes crear uno desde aquí")

    st.markdown("---")

    # ─── Historial de chat ───
    chat_histories = st.session_state.chat_histories
    trip_id = trip["id"] if trip else "__no_trip__"

    if trip_id not in chat_histories:
        chat_histories[trip_id] = []
        # Mensaje de bienvenida
        if trip:
            chat_histories[trip_id].append({
                "role": "assistant",
                "type": "text",
                "content": (
                    f"¡Hola! Estoy listo para ayudarte con tu viaje a "
                    f"{trip['destination']}. ¿En qué puedo ayudarte?"
                ),
            })
        else:
            chat_histories[trip_id].append({
                "role": "assistant",
                "type": "text",
                "content": (
                    "¡Hola! Soy tu asistente de viajes. "
                    "Dime a dónde te gustaría viajar para empezar a planificar. "
                    'Por ejemplo: "Quiero viajar a París".'
                ),
            })

    history = chat_histories[trip_id]

    # ─── Renderizar mensajes ───
    for i, msg in enumerate(history):
        role = msg.get("role", "assistant")
        msg_type = msg.get("type", "text")

        with st.chat_message(role):
            if msg_type == "text":
                st.markdown(msg["content"])

            elif msg_type == "card":
                st.markdown("He encontrado esta opción para ti:")
                render_rich_card(msg["content"])

            elif msg_type == "confirmation":
                action_data = msg["content"]
                # Verificar si ya fue procesada
                if msg.get("processed"):
                    st.markdown(f"*{action_data.get('summary', '')}* — {msg.get('result', '')}")
                else:
                    result = render_confirmation(action_data, i)
                    if result == "confirm":
                        if action_data.get("action") == "create_trip":
                            details = action_data.get("details", {})
                            new_trip = create_trip(
                                trips,
                                name=details.get("name", "Nuevo viaje"),
                                destination=details.get("destination", "Sin destino"),
                                start_date="2026-05-01",
                                end_date="2026-05-07",
                            )
                            st.session_state.active_trip_id = new_trip["id"]
                            msg["processed"] = True
                            msg["result"] = "✅ Viaje creado"
                            # Crear historial para el nuevo viaje
                            chat_histories[new_trip["id"]] = [{
                                "role": "assistant",
                                "type": "text",
                                "content": (
                                    f"¡Perfecto! He creado tu viaje a {new_trip['destination']}. "
                                    "¿Qué te gustaría planificar primero?"
                                ),
                            }]
                            st.session_state.trips = trips
                        elif trip:
                            result_msg = apply_confirmed_action(
                                action_data, trip, trips
                            )
                            msg["processed"] = True
                            msg["result"] = result_msg
                            st.session_state.trips = trips
                            # Agregar mensaje de resultado
                            history.append({
                                "role": "assistant",
                                "type": "text",
                                "content": result_msg,
                            })
                        st.rerun()

                    elif result == "cancel":
                        msg["processed"] = True
                        msg["result"] = "❌ Cancelado por el usuario"
                        history.append({
                            "role": "assistant",
                            "type": "text",
                            "content": "Entendido, he cancelado la acción. ¿En qué más puedo ayudarte?",
                        })
                        st.rerun()

    # ─── Input del usuario ───
    if user_input := st.chat_input("Escribe tu mensaje..."):
        # Agregar mensaje del usuario
        history.append({
            "role": "user",
            "type": "text",
            "content": user_input,
        })

        with st.spinner("El asistente está procesando tu solicitud..."):
            response = process_message(user_input, trip)

        history.append(response)
        st.rerun()

except Exception as e:
    st.error(f"Error en el chat: {e}")
    if st.button("🔄 Reintentar"):
        st.rerun()
