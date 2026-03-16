"""Template Plotly integrado con el design system Trip Planner.

Provee un template de layout Plotly con fondos transparentes,
colores del design system y tipografia consistente.
"""


# Colores para categorias de presupuesto (alineados con design tokens)
PLOTLY_COLORS = {
    "vuelos": "#FF7B72",       # --tp-accent-red
    "alojamiento": "#58A6FF",  # --tp-accent-blue
    "actividades": "#56D364",  # --tp-accent-green
    "comidas": "#FFA657",      # --tp-accent-orange
    "transporte_local": "#8B949E",  # --tp-accent-gray
    "extras": "#BC8CFF",       # --tp-accent-purple
}

# Colores para tipos de item (misma paleta para consistencia)
PLOTLY_ITEM_COLORS = {
    "actividad": "#56D364",    # --tp-accent-green
    "traslado": "#8B949E",     # --tp-accent-gray
    "alojamiento": "#58A6FF",  # --tp-accent-blue
    "comida": "#FFA657",       # --tp-accent-orange
    "vuelo": "#FF7B72",        # --tp-accent-red
    "extra": "#BC8CFF",        # --tp-accent-purple
}


def get_bar_colors() -> tuple:
    """Retorna tupla (estimated_color, real_color) para barras comparativas.

    Estimado: azul del design system.
    Real: verde del design system.
    """
    return ("#58A6FF", "#56D364")


def get_plotly_base_layout() -> dict:
    """Retorna propiedades de layout base (fondos, fuente, hover, margenes).

    Estas propiedades son seguras para aplicar a CUALQUIER tipo de chart
    (pie, bar, scatter, etc.) sin conflictos con configuraciones especificas.
    Para ejes y legend, usar get_plotly_template() que incluye todo.
    """
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {
            "color": "#F0F2F4",  # --tp-text-primary
            "family": (
                "-apple-system, BlinkMacSystemFont, 'Segoe UI', "
                "'Noto Sans', Helvetica, Arial, sans-serif"
            ),
            "size": 13,
        },
        "colorway": [
            "#58A6FF",  # blue
            "#56D364",  # green
            "#FFA657",  # orange
            "#FF7B72",  # red
            "#BC8CFF",  # purple
            "#E3B341",  # yellow
            "#8B949E",  # gray
        ],
        "hoverlabel": {
            "bgcolor": "#1A2027",      # --tp-bg-secondary
            "bordercolor": "#373E47",  # --tp-border-default
            "font": {
                "color": "#F0F2F4",    # --tp-text-primary
                "size": 13,
            },
        },
        "margin": {
            "t": 30,
            "b": 20,
            "l": 20,
            "r": 20,
        },
    }


def get_plotly_template() -> dict:
    """Retorna template Plotly completo consistente con el design system.

    Incluye propiedades base + ejes + legend + title.
    Usar para charts con ejes (bar, scatter, line).
    Para charts sin ejes (pie/donut), usar get_plotly_base_layout().

    - Fondos transparentes para integrarse con el dark theme de Streamlit.
    - Tipografia del sistema.
    - Colorway derivada de los design tokens.
    - Grids y ejes estilizados con los colores de borde del sistema.
    """
    base = get_plotly_base_layout()
    base.update({
        "title": {
            "font": {
                "color": "#F0F2F4",
                "size": 16,
            },
        },
        "xaxis": {
            "gridcolor": "#373E47",    # --tp-border-default
            "linecolor": "#373E47",
            "tickcolor": "#545D68",    # --tp-border-emphasis
            "tickfont": {"color": "#B8BFC6"},  # --tp-text-secondary
            "zerolinecolor": "#373E47",
            "showgrid": True,
            "gridwidth": 1,
        },
        "yaxis": {
            "gridcolor": "#373E47",
            "linecolor": "#373E47",
            "tickcolor": "#545D68",
            "tickfont": {"color": "#B8BFC6"},
            "zerolinecolor": "#373E47",
            "showgrid": True,
            "gridwidth": 1,
        },
        "legend": {
            "font": {"color": "#B8BFC6"},
            "bgcolor": "rgba(0,0,0,0)",
            "bordercolor": "rgba(0,0,0,0)",
        },
    })
    return {"layout": base}
