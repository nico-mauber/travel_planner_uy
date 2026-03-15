"""Gráficos de presupuesto con Plotly."""

import plotly.graph_objects as go
import streamlit as st

from config.settings import BUDGET_CATEGORY_COLORS, BUDGET_CATEGORY_LABELS, BudgetCategory


def render_donut_chart(budget_summary: dict) -> None:
    """Renderiza gráfico donut de distribución por categoría."""
    by_cat = budget_summary["by_category"]

    labels = []
    values = []
    colors = []

    for cat in BudgetCategory:
        estimated = by_cat[cat.value]["estimated"]
        if estimated > 0:
            labels.append(BUDGET_CATEGORY_LABELS[cat])
            values.append(estimated)
            colors.append(BUDGET_CATEGORY_COLORS[cat])

    if not values:
        st.info("No hay datos de presupuesto para mostrar.")
        return

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker_colors=colors,
        textinfo="label+percent",
        textposition="outside",
    )])

    fig.update_layout(
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20),
        height=350,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E0E0E0",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_comparison_bars(budget_summary: dict) -> None:
    """Renderiza barras agrupadas estimado vs real."""
    by_cat = budget_summary["by_category"]

    categories = []
    estimated = []
    real = []

    for cat in BudgetCategory:
        est = by_cat[cat.value]["estimated"]
        rl = by_cat[cat.value]["real"]
        if est > 0 or rl > 0:
            categories.append(BUDGET_CATEGORY_LABELS[cat])
            estimated.append(est)
            real.append(rl)

    if not categories:
        return

    fig = go.Figure(data=[
        go.Bar(
            name="Estimado",
            x=categories,
            y=estimated,
            marker_color="#1E88E5",
        ),
        go.Bar(
            name="Real",
            x=categories,
            y=real,
            marker_color="#43A047",
        ),
    ])

    fig.update_layout(
        barmode="group",
        margin=dict(t=30, b=20, l=20, r=20),
        height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_title="USD",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E0E0E0",
    )

    st.plotly_chart(fig, use_container_width=True)
