"""Estilos responsive para la aplicacion Trip Planner.

Media queries organizadas por breakpoint para adaptar el layout
de Streamlit a diferentes tamanios de pantalla. Enfoque en hacer
que st.columns se comporte responsive via flex-wrap.
"""


def get_responsive_css() -> str:
    """Retorna CSS con media queries responsive."""
    return """
/* ==========================================================================
   RESPONSIVE — Media queries para layout adaptativo
   ==========================================================================
   Breakpoints:
     < 480px  — Mobile pequenio
     < 768px  — Mobile / Tablet vertical
     < 1024px — Tablet horizontal
     >= 1440px — Desktop grande
     >= 2560px — Ultra-wide
   ========================================================================== */

/* ── Ultra-wide (>= 2560px) — Centrar contenido con margenes generosos ── */
@media screen and (min-width: 2560px) {
  [data-testid="stAppViewContainer"] > section > div {
    max-width: 1800px;
    margin-left: auto;
    margin-right: auto;
  }
}

/* ── Desktop grande (>= 1440px) — Max-width para legibilidad ── */
@media screen and (min-width: 1440px) {
  .block-container {
    max-width: 1200px;
  }
}

/* ── Tablet (< 1024px) — Sidebar mas angosta, columnas flexibles ── */
@media screen and (max-width: 1023px) {
  [data-testid="stSidebar"] {
    min-width: 220px;
    max-width: 260px;
  }

  /* Columnas de Streamlit: permitir wrap para 3+ columnas */
  [data-testid="stHorizontalBlock"] {
    flex-wrap: wrap;
    gap: var(--tp-space-3);
  }

  /* Columnas internas: minimo 45% para que se muestren 2 por fila */
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    min-width: calc(50% - var(--tp-space-3));
    flex-grow: 1;
  }
}

/* ── Mobile / Tablet vertical (< 768px) — Columnas apiladas ── */
@media screen and (max-width: 767px) {
  /* Forzar columnas a apilar verticalmente */
  [data-testid="stHorizontalBlock"] {
    flex-wrap: wrap;
  }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    min-width: 100%;
    flex-basis: 100%;
  }

  /* Metrics: stack vertical */
  [data-testid="stMetric"] {
    padding: var(--tp-space-3);
  }

  /* Reducir padding general del contenedor */
  .block-container {
    padding-left: var(--tp-space-3);
    padding-right: var(--tp-space-3);
  }

  /* Tabs: scroll horizontal si no caben */
  .stTabs [data-baseweb="tab-list"] {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
  }
  .stTabs [data-baseweb="tab"] {
    white-space: nowrap;
    flex-shrink: 0;
  }
}

/* ── Mobile pequenio (< 480px) — Ajustes finos ── */
@media screen and (max-width: 479px) {
  /* Sidebar: forzar colapso por defecto */
  [data-testid="stSidebar"] {
    min-width: 0;
  }

  /* Tipografia ligeramente mas compacta */
  [data-testid="stMarkdown"] h1 {
    font-size: var(--tp-text-2xl);
  }
  [data-testid="stMarkdown"] h2 {
    font-size: var(--tp-text-xl);
  }

  /* Botones: full width */
  .stButton > button {
    width: 100%;
    justify-content: center;
  }

  /* Active trip box: padding reducido */
  .tp-active-trip-box {
    padding: var(--tp-space-2);
  }

  /* Cards: padding reducido */
  .tp-card {
    padding: var(--tp-space-3);
  }
}
"""
