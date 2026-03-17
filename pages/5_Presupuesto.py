"""Presupuesto (REQ-UI-006)."""

import streamlit as st

from config.settings import (
    BudgetCategory, BUDGET_CATEGORY_LABELS, BUDGET_CATEGORY_COLORS,
    ITEM_TYPE_ICONS, ItemType, TripStatus,
)
from services.trip_service import get_active_trip, get_trip_by_id
from services.budget_service import calculate_budget_summary, has_real_costs
from components.budget_charts import render_donut_chart, render_comparison_bars


try:
    trips = st.session_state.trips

    st.title("Presupuesto")

    # ─── Selector de viaje ───
    active_statuses = [TripStatus.PLANNING.value, TripStatus.CONFIRMED.value, TripStatus.IN_PROGRESS.value]
    available_trips = [t for t in trips if t["status"] in active_statuses]

    if not available_trips:
        st.info("No hay viajes activos. Ve a **Mis Viajes** para crear uno.")
        if st.button("Ir a Mis Viajes", type="primary", help="Navegar a la pagina de gestion de viajes"):
            st.switch_page("pages/7_Mis_Viajes.py")
        st.stop()

    trip_options = {t["id"]: f"{t['name']} — {t['destination']}" for t in available_trips}

    current_active = st.session_state.get("active_trip_id")
    default_keys = list(trip_options.keys())
    default_idx = default_keys.index(current_active) if current_active in default_keys else 0

    selected_trip_id = st.selectbox(
        "Selecciona un viaje",
        options=default_keys,
        format_func=lambda k: trip_options[k],
        index=default_idx,
        key="budget_trip_selector",
    )

    st.session_state.active_trip_id = selected_trip_id
    trip = get_trip_by_id(trips, selected_trip_id)

    if not trip:
        st.warning("No se pudo cargar el viaje seleccionado.")
        st.stop()

    st.caption(f"**{trip['name']}** — {trip['destination']}")

    items = trip.get("items", [])
    expenses = trip.get("expenses", [])
    budget = calculate_budget_summary(items, expenses)

    # ─── Fila 1: Metrica principal ───
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Presupuesto total",
            f"USD {budget['total_estimated']:,.0f}",
            help="Suma de costos estimados de items + gastos directos",
        )
    with col2:
        if budget["total_real"] > 0:
            diff = budget["total_real"] - budget["total_estimated"]
            st.metric(
                "Gasto real",
                f"USD {budget['total_real']:,.0f}",
                delta=f"USD {diff:,.0f}",
                delta_color="inverse",
                help="Gasto real registrado. El delta muestra la diferencia respecto al estimado",
            )
        else:
            st.metric(
                "Gasto real", "Sin datos",
                help="Aun no hay gastos reales registrados para este viaje",
            )
    with col3:
        total_expenses = budget.get("total_expenses", 0.0)
        if total_expenses > 0:
            st.metric(
                "Gastos directos",
                f"USD {total_expenses:,.0f}",
                help="Total de gastos registrados directamente (no items del itinerario)",
            )
        else:
            items_count = sum(
                len(cat_data["items"]) for cat_data in budget["by_category"].values()
            )
            st.metric(
                "Items contabilizados", items_count,
                help="Cantidad de items con costo incluidos en el presupuesto (excluye sugeridos)",
            )

    st.divider()

    if (not items and not expenses) or budget["total_estimated"] == 0:
        st.info("No hay items ni gastos con costos para mostrar el presupuesto.")
        st.stop()

    # ─── Fila 2: Donut + Tabla ───
    col_chart, col_table = st.columns(2)

    with col_chart:
        st.subheader("Distribucion por categoria")
        render_donut_chart(budget)

    with col_table:
        st.subheader("Desglose")
        table_data = []
        for cat in BudgetCategory:
            cat_data = budget["by_category"][cat.value]
            if cat_data["estimated"] > 0 or cat_data["real"] > 0:
                diff = cat_data["real"] - cat_data["estimated"] if cat_data["real"] > 0 else 0
                table_data.append({
                    "Categoria": BUDGET_CATEGORY_LABELS[cat],
                    "Estimado (USD)": cat_data["estimated"],
                    "Real (USD)": cat_data["real"] if cat_data["real"] > 0 else float("nan"),
                    "Diferencia": diff if cat_data["real"] > 0 else float("nan"),
                })

        if table_data:
            import pandas as pd
            df = pd.DataFrame(table_data)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Categoria": st.column_config.TextColumn("Categoria"),
                    "Estimado (USD)": st.column_config.NumberColumn(
                        "Estimado (USD)",
                        format="$ %.0f",
                        help="Costo estimado de todos los items en esta categoria",
                    ),
                    "Real (USD)": st.column_config.NumberColumn(
                        "Real (USD)",
                        format="$ %.0f",
                        help="Gasto real registrado en esta categoria",
                    ),
                    "Diferencia": st.column_config.NumberColumn(
                        "Diferencia",
                        format="$ %+.0f",
                        help="Diferencia entre gasto real y estimado (positivo = sobrecosto)",
                    ),
                },
            )

            # Totales
            total_line = f"**Total estimado: USD {budget['total_estimated']:,.0f}**"
            if budget["total_real"] > 0:
                real_formatted = f"{budget['total_real']:,.0f}"
                total_line += f" | Real: USD {real_formatted}"
            st.markdown(total_line)

    # ─── Fila 3: Barras comparativas ───
    if has_real_costs(items):
        st.divider()
        st.subheader("Comparacion: estimado vs. real")
        render_comparison_bars(budget)

    # ─── Fila 4: Drill-down por categoría ───
    st.divider()
    st.subheader("Detalle por categoria")

    for cat in BudgetCategory:
        cat_data = budget["by_category"][cat.value]
        cat_items = cat_data["items"]
        cat_expenses = cat_data.get("expenses", [])
        if not cat_items and not cat_expenses:
            continue

        color = BUDGET_CATEGORY_COLORS[cat]
        n_items = len(cat_items)
        n_expenses = len(cat_expenses)
        exp_suffix = f" + {n_expenses} gasto{'s' if n_expenses != 1 else ''}" if n_expenses else ""
        with st.expander(
            f"{BUDGET_CATEGORY_LABELS[cat]} — USD {cat_data['estimated']:,.0f} estimado ({n_items} item{'s' if n_items != 1 else ''}{exp_suffix})"
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
            if cat_expenses:
                st.caption("Gastos directos:")
                for exp in cat_expenses:
                    st.markdown(
                        f"💰 **{exp['name']}** — USD {exp['amount']:,.0f}"
                    )

except Exception as e:
    st.error(f"Error al cargar el presupuesto: {e}")
    if st.button("Reintentar", help="Recargar la pagina de presupuesto"):
        st.rerun()
