"""Perfil y Preferencias del Viajero (REQ-UI-007, REQ-CL-001)."""

import streamlit as st
from services.profile_service import save_profile

if "trips" not in st.session_state:
    st.switch_page("app.py")
from services.auth_service import get_current_user_id


try:
    st.title("Perfil y preferencias")
    st.markdown('<div class="tp-breadcrumb">🏠 Dashboard  ›  👤 Perfil</div>', unsafe_allow_html=True)
    st.info("✨ Tus preferencias ayudan al asistente a hacer sugerencias personalizadas. Cuanto más completes, mejores recomendaciones recibirás.")
    st.divider()

    user_id = get_current_user_id()

    # ─── Info del usuario autenticado (read-only) ───
    current_user = st.session_state.get("current_user")
    if current_user:
        st.header("Cuenta")
        user_name = current_user.get("name", "Usuario")
        info_cols = st.columns([0.15, 0.85])
        with info_cols[0]:
            picture = current_user.get("picture", "")
            if picture:
                st.image(picture, width=60, caption=f"Foto de {user_name}")
        with info_cols[1]:
            st.markdown(f"**{user_name}**")
            st.markdown(f"Email: {current_user.get('email', '')}")
        st.divider()

    # ─── Preferencias editables ───
    st.header("Preferencias de viaje")
    profile = st.session_state.get("user_profile", {})

    with st.form("profile_form"):
        tab_aloj, tab_food, tab_style, tab_budget, tab_transport = st.tabs([
            "Alojamiento",
            "Alimentacion",
            "Estilo de viaje",
            "Presupuesto",
            "Transporte",
        ])

        with tab_aloj:
            accommodation = st.multiselect(
                "Tipo de alojamiento preferido",
                options=["Hotel", "Hostel", "Apartamento", "Resort", "Camping", "Casa rural"],
                default=profile.get("accommodation_types", []),
            )
            hotel_chains = st.text_area(
                "Cadenas hoteleras preferidas",
                value=profile.get("preferred_hotel_chains", ""),
                placeholder="Ej: Marriott, Hilton, Ibis...",
            )

        with tab_food:
            food_restrictions = st.multiselect(
                "Restricciones alimentarias",
                options=[
                    "Sin gluten", "Vegetariano", "Vegano", "Sin lactosa",
                    "Kosher", "Halal", "Sin mariscos",
                ],
                default=profile.get("food_restrictions", []),
            )
            allergies = st.text_input(
                "Alergias",
                value=profile.get("allergies", ""),
                placeholder="Ej: mani, mariscos...",
            )

        with tab_style:
            travel_styles = st.multiselect(
                "Estilo de viaje preferido",
                options=[
                    "Aventura", "Relax", "Cultural", "Gastronomico",
                    "Familiar", "Romantico", "Mochilero", "Lujo",
                ],
                default=profile.get("travel_styles", []),
            )

        with tab_budget:
            daily_budget = st.number_input(
                "Presupuesto diario habitual (USD)",
                min_value=0.0,
                max_value=10000.0,
                value=float(profile.get("daily_budget", 0.0)),
                step=10.0,
            )

        with tab_transport:
            airlines = st.text_area(
                "Aerolineas preferidas",
                value=profile.get("preferred_airlines", ""),
                placeholder="Ej: LATAM, Iberia, United...",
            )

        submitted = st.form_submit_button(
            "Guardar preferencias",
            type="primary",
            help="Guardar todos los cambios realizados en tus preferencias de viaje",
        )

        if submitted:
            if daily_budget < 0:
                st.error("El presupuesto diario no puede ser negativo.")
            else:
                new_profile = {
                    "accommodation_types": accommodation,
                    "food_restrictions": food_restrictions,
                    "allergies": allergies,
                    "travel_styles": travel_styles,
                    "daily_budget": daily_budget,
                    "preferred_airlines": airlines,
                    "preferred_hotel_chains": hotel_chains,
                }
                if save_profile(new_profile, user_id=user_id):
                    st.session_state.user_profile = new_profile
                    st.toast("✅ Preferencias guardadas correctamente")
                else:
                    st.error("❌ Error al guardar las preferencias. Intentá de nuevo.")

except Exception as e:
    st.error(f"Error al cargar el perfil: {e}")
    if st.button("Reintentar", help="Recargar la pagina de perfil"):
        st.rerun()
