"""Presupuesto (REQ-UI-006)."""

import streamlit as st

from config.settings import (
    BudgetCategory, BUDGET_CATEGORY_LABELS, BUDGET_CATEGORY_COLORS,
    ITEM_TYPE_ICONS, ItemType,
)
from services.trip_service import get_active_trip
from services.budget_service import calculate_budget_summary, has_real_costs
from components.budget_charts import render_donut_chart, render_comparison_bars


try:
    trips = st.session_state.trips
    trip = get_active_trip(trips, st.session_state.get("active_trip_id"))

    st.title("💰 Presupuesto")

    if not trip:
        st.info("No hay viaje activo. Ve a **Mis Viajes** para seleccionar o crear uno.")
        if st.button("🌍 Ir a Mis Viajes", type="primary"):
            st.switch_page("pages/7_Mis_Viajes.py")
        st.stop()

    st.caption(f"**{trip['name']}** — {trip['destination']}")

    items = trip.get("items", [])
    budget = calculate_budget_summary(items)

    # ─── Fila 1: Métrica principal ───
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Presupuesto estimado", f"USD {budget['total_estimated']:,.0f}")
    with col2:
        if budget["total_real"] > 0:
            diff = budget["total_real"] - budget["total_estimated"]
            st.metric(
                "Gasto real",
                f"USD {budget['total_real']:,.0f}",
                delta=f"USD {diff:,.0f}",
                delta_color="inverse",
            )
        else:
            st.metric("Gasto real", "Sin datos")
    with col3:
        items_count = sum(
            len(cat_data["items"]) for cat_data in budget["by_category"].values()
        )
        st.metric("Items contabilizados", items_count)

    st.markdown("---")

    if not items or budget["total_estimated"] == 0:
        st.info("No hay items con costos para mostrar el presupuesto.")
        st.stop()

    # ─── Fila 2: Donut + Tabla ───
    col_chart, col_table = st.columns(2)

    with col_chart:
        st.subheader("Distribución por categoría")
        render_donut_chart(budget)

    with col_table:
        st.subheader("Desglose")
        table_data = []
        for cat in BudgetCategory:
            cat_data = budget["by_category"][cat.value]
            if cat_data["estimated"] > 0 or cat_data["real"] > 0:
                diff = cat_data["real"] - cat_data["estimated"] if cat_data["real"] > 0 else 0
                table_data.append({
                    "Categoría": BUDGET_CATEGORY_LABELS[cat],
                    "Estimado (USD)": f"{cat_data['estimated']:,.0f}",
                    "Real (USD)": f"{cat_data['real']:,.0f}" if cat_data["real"] > 0 else "—",
                    "Diferencia": f"{diff:+,.0f}" if cat_data["real"] > 0 else "—",
                })

        if table_data:
            st.dataframe(
                table_data,
                use_container_width=True,
                hide_index=True,
            )

            # Totales
            total_line = f"**Total estimado: USD {budget['total_estimated']:,.0f}**"
            if budget["total_real"] > 0:
                real_formatted = f"{budget['total_real']:,.0f}"
                total_line += f" | Real: USD {real_formatted}"
            st.markdown(total_line)

    # ─── Fila 3: Barras comparativas ───
    if has_real_costs(items):
        st.markdown("---")
        st.subheader("📊 Comparación estimado vs. real")
        render_comparison_bars(budget)

    # ─── Fila 4: Drill-down por categoría ───
    st.markdown("---")
    st.subheader("📂 Detalle por categoría")

    for cat in BudgetCategory:
        cat_data = budget["by_category"][cat.value]
        cat_items = cat_data["items"]
        if not cat_items:
            continue

        color = BUDGET_CATEGORY_COLORS[cat]
        with st.expander(
            f"{BUDGET_CATEGORY_LABELS[cat]} — USD {cat_data['estimated']:,.0f} estimado"
        ):
            for item in cat_items:
                icon = ITEM_TYPE_ICONS.get(ItemType(item["item_type"]), "📦")
                real_str = (
                    f" | Real: USD {item['cost_real']:,.0f}"
                    if item.get("cost_real", 0) > 0
                    else ""
                )
                st.markdown(
                    f"{icon} **{item['name']}** — "
                    f"Est: USD {item.get('cost_estimated', 0):,.0f}{real_str}"
                )

except Exception as e:
    st.error(f"Error al cargar el presupuesto: {e}")
    if st.button("🔄 Reintentar"):
        st.rerun()
