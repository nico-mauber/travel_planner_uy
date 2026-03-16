"""Graficos de presupuesto con Plotly.

Usa el template y colores del design system (config/styles/plotly_theme.py)
para mantener coherencia visual con el resto de la aplicacion.
Labels mejorados con formato de moneda y porcentaje, anotaciones de
diferencia en barras comparativas.
"""

import plotly.graph_objects as go
import streamlit as st

from config.settings import BUDGET_CATEGORY_COLORS, BUDGET_CATEGORY_LABELS, BudgetCategory
from config.styles.plotly_theme import get_plotly_base_layout, get_plotly_template, get_bar_colors


def render_donut_chart(budget_summary: dict) -> None:
    """Renderiza grafico donut de distribucion por categoria.

    Mejoras sobre la version base:
    - Labels con categoria + monto USD + porcentaje
    - Hover con formato de moneda
    - Borde sutil entre segmentos
    """
    by_cat = budget_summary["by_category"]

    labels = []
    values = []
    colors = []
    custom_text = []

    total = 0
    for cat in BudgetCategory:
        estimated = by_cat[cat.value]["estimated"]
        if estimated > 0:
            total += estimated

    for cat in BudgetCategory:
        estimated = by_cat[cat.value]["estimated"]
        if estimated > 0:
            label = BUDGET_CATEGORY_LABELS[cat]
            labels.append(label)
            values.append(estimated)
            colors.append(BUDGET_CATEGORY_COLORS[cat])
            # Texto personalizado: nombre + monto
            custom_text.append(f"{label}<br>USD {estimated:,.0f}")

    if not values:
        st.info("No hay datos de presupuesto para mostrar.")
        return

    base_layout = get_plotly_base_layout()

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(
            colors=colors,
            line=dict(
                color="#0F1419",  # --tp-bg-primary, borde entre segmentos
                width=2,
            ),
        ),
        text=custom_text,
        textinfo="text+percent",
        textposition="outside",
        textfont=dict(size=12),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Monto: USD %{value:,.0f}<br>"
            "Porcentaje: %{percent}<br>"
            "<extra></extra>"
        ),
        # Anotacion central
        title=dict(
            text=f"<b>USD {total:,.0f}</b><br><span style='font-size:11px'>Total estimado</span>",
            font=dict(size=14, color="#F0F2F4"),
        ),
    )])

    fig.update_layout(
        showlegend=False,
        height=380,
        **base_layout,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_comparison_bars(budget_summary: dict) -> None:
    """Renderiza barras agrupadas estimado vs real.

    Mejoras sobre la version base:
    - Anotaciones de diferencia porcentual entre estimado y real
    - Formato de ejes USD con separador de miles
    - Hover mejorado con formato de moneda
    """
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

    base_layout = get_plotly_base_layout()
    template = get_plotly_template()
    est_color, real_color = get_bar_colors()

    fig = go.Figure(data=[
        go.Bar(
            name="Estimado",
            x=categories,
            y=estimated,
            marker_color=est_color,
            hovertemplate="<b>%{x}</b><br>Estimado: USD %{y:,.0f}<extra></extra>",
        ),
        go.Bar(
            name="Real",
            x=categories,
            y=real,
            marker_color=real_color,
            hovertemplate="<b>%{x}</b><br>Real: USD %{y:,.0f}<extra></extra>",
        ),
    ])

    # Anotaciones de diferencia porcentual
    annotations = []
    for i, (est_val, real_val) in enumerate(zip(estimated, real)):
        if est_val > 0 and real_val > 0:
            diff_pct = ((real_val - est_val) / est_val) * 100
            max_val = max(est_val, real_val)
            # Color segun si es sobre o bajo presupuesto
            if diff_pct > 0:
                ann_color = "#FF7B72"  # --tp-accent-red
                ann_text = f"+{diff_pct:.0f}%"
            elif diff_pct < 0:
                ann_color = "#56D364"  # --tp-accent-green
                ann_text = f"{diff_pct:.0f}%"
            else:
                ann_color = "#8B949E"  # --tp-accent-gray
                ann_text = "0%"
            annotations.append(dict(
                x=categories[i],
                y=max_val,
                text=ann_text,
                showarrow=False,
                font=dict(size=11, color=ann_color, weight=600),
                yshift=15,
            ))

    # Aplicar layout base y luego propiedades especificas
    fig.update_layout(
        **base_layout,
        barmode="group",
        height=380,
        xaxis=template["layout"]["xaxis"],
        yaxis={
            **template["layout"]["yaxis"],
            "title": "USD",
            "tickformat": "$,.0f",
            "tickprefix": "",
        },
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font={"color": "#B8BFC6"},  # --tp-text-secondary
            bgcolor="rgba(0,0,0,0)",
        ),
        annotations=annotations,
    )

    st.plotly_chart(fig, use_container_width=True)
