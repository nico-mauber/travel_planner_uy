"""Perfil y Preferencias del Viajero (REQ-UI-007)."""

import streamlit as st
from services.profile_service import save_profile


try:
    st.title("👤 Perfil y Preferencias")
    st.markdown(
        "Configura tus preferencias de viaje para que el agente personalice "
        "sus sugerencias."
    )
    st.markdown("---")

    profile = st.session_state.get("user_profile", {})

    with st.form("profile_form"):
        tab_aloj, tab_food, tab_style, tab_budget, tab_transport = st.tabs([
            "🏨 Alojamiento",
            "🍽️ Alimentación",
            "🎯 Estilo de viaje",
            "💰 Presupuesto",
            "✈️ Transporte",
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
                placeholder="Ej: maní, mariscos...",
            )

        with tab_style:
            travel_styles = st.multiselect(
                "Estilo de viaje preferido",
                options=[
                    "Aventura", "Relax", "Cultural", "Gastronómico",
                    "Familiar", "Romántico", "Mochilero", "Lujo",
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
                "Aerolíneas preferidas",
                value=profile.get("preferred_airlines", ""),
                placeholder="Ej: LATAM, Iberia, United...",
            )

        submitted = st.form_submit_button("💾 Guardar preferencias", type="primary")

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
                if save_profile(new_profile):
                    st.session_state.user_profile = new_profile
                    st.success("✅ Preferencias guardadas correctamente.")
                else:
                    st.error("Error al guardar las preferencias. Intenta de nuevo.")

except Exception as e:
    st.error(f"Error al cargar el perfil: {e}")
    if st.button("🔄 Reintentar"):
        st.rerun()
