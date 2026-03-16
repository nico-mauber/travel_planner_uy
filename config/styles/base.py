"""Estilos base y overrides de widgets Streamlit.

Aplica el design system sobre los componentes nativos de Streamlit
y define clases utilitarias propias con prefijo tp-.
"""


def get_base_css() -> str:
    """Retorna CSS con overrides de Streamlit y clases utilitarias tp-."""
    return """
/* ==========================================================================
   BASE STYLES — Overrides de Streamlit + Clases utilitarias tp-
   ========================================================================== */

/* ── Skip link para accesibilidad (teclado) ── */
.tp-skip-link {
  position: absolute;
  top: -100%;
  left: var(--tp-space-4);
  z-index: 10000;
  padding: var(--tp-space-2) var(--tp-space-4);
  background: var(--tp-bg-primary);
  color: var(--tp-text-primary) !important;
  border: 2px solid var(--tp-accent-blue);
  border-radius: var(--tp-radius-md);
  font-weight: 600;
  font-size: var(--tp-text-sm);
  text-decoration: none !important;
  transition: top var(--tp-transition-fast);
}
.tp-skip-link:focus {
  top: var(--tp-space-4);
  outline: 2px solid var(--tp-accent-blue);
  outline-offset: 2px;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background-color: var(--tp-bg-secondary);
  border-right: 1px solid var(--tp-border-default);
}
[data-testid="stSidebar"] [data-testid="stMarkdown"] {
  color: var(--tp-text-primary);
}

/* ── Botones generales ── */
.stButton > button {
  padding: var(--tp-space-2) var(--tp-space-4);
  border-radius: var(--tp-radius-md);
  font-size: var(--tp-text-sm);
  font-weight: 500;
  font-family: var(--tp-font-family);
  border: 1px solid var(--tp-border-default);
  background-color: var(--tp-bg-tertiary);
  color: var(--tp-text-primary);
  cursor: pointer;
  min-height: 44px; /* Touch target minimo Apple HIG */
  transition: transform var(--tp-transition-spring),
              box-shadow var(--tp-transition-normal),
              background-color var(--tp-transition-fast),
              border-color var(--tp-transition-fast);
}
.stButton > button:hover {
  transform: translateY(-1px);
  box-shadow: var(--tp-shadow-md);
  background-color: var(--tp-bg-surface);
  border-color: var(--tp-border-emphasis);
}
.stButton > button:active {
  transform: translateY(0);
  box-shadow: var(--tp-shadow-sm);
}
.stButton > button:focus-visible {
  outline: 2px solid var(--tp-accent-blue);
  outline-offset: 2px;
}

/* ── Botones primarios ──
   Ratio de contraste: #0F1419 sobre #58A6FF = 8.1:1 (AAA) */
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
  background-color: var(--tp-accent-blue);
  color: var(--tp-bg-primary);
  border-color: var(--tp-accent-blue);
  font-weight: 600;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
  background-color: #6FB8FF; /* Azul mas claro para hover */
  border-color: #6FB8FF;
  color: var(--tp-bg-primary);
}

/* ── Selectbox / Multiselect ── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
  background-color: var(--tp-bg-tertiary);
  border-color: var(--tp-border-default);
  border-radius: var(--tp-radius-md);
  color: var(--tp-text-primary);
}
[data-testid="stSelectbox"] > div > div:focus-within,
[data-testid="stMultiSelect"] > div > div:focus-within {
  border-color: var(--tp-accent-blue);
  box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.2);
}

/* ── Expanders ── */
[data-testid="stExpander"] {
  border: 1px solid var(--tp-border-default);
  border-radius: var(--tp-radius-md);
  background-color: var(--tp-bg-secondary);
}
[data-testid="stExpander"] summary {
  color: var(--tp-text-primary);
  font-weight: 500;
}
[data-testid="stExpander"] summary:focus-visible {
  outline: 2px solid var(--tp-accent-blue);
  outline-offset: 2px;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  border-bottom: 1px solid var(--tp-border-default);
  gap: 0;
}
.stTabs [data-baseweb="tab"] {
  color: var(--tp-text-secondary);
  padding: var(--tp-space-2) var(--tp-space-4);
  min-height: 44px;
  border-bottom: 2px solid transparent;
  transition: color var(--tp-transition-fast),
              border-color var(--tp-transition-fast);
}
.stTabs [data-baseweb="tab"]:hover {
  color: var(--tp-text-primary);
}
.stTabs [aria-selected="true"] {
  color: var(--tp-accent-blue);
  border-bottom-color: var(--tp-accent-blue);
}
.stTabs [data-baseweb="tab"]:focus-visible {
  outline: 2px solid var(--tp-accent-blue);
  outline-offset: -2px;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
  background-color: var(--tp-bg-secondary);
  padding: var(--tp-space-4);
  border-radius: var(--tp-radius-md);
  box-shadow: var(--tp-shadow-sm);
  border: 1px solid var(--tp-border-default);
}
[data-testid="stMetric"] label {
  color: var(--tp-text-secondary);
  font-size: var(--tp-text-sm);
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
  color: var(--tp-text-primary);
  font-weight: 600;
}
[data-testid="stMetric"] [data-testid="stMetricDelta"] svg {
  width: 14px;
  height: 14px;
}

/* ── Progress bar ── */
[data-testid="stProgress"] > div > div > div {
  background-color: var(--tp-accent-blue);
}
[data-testid="stProgress"] > div > div {
  background-color: var(--tp-bg-tertiary);
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
  border-radius: var(--tp-radius-lg);
  padding: var(--tp-space-3) var(--tp-space-4);
  margin-bottom: var(--tp-space-2);
}
/* Mensaje del usuario */
[data-testid="stChatMessage"][data-testid*="user"],
[data-testid="stChatMessage"]:has(.stChatMessageUser) {
  background-color: var(--tp-bg-tertiary);
}
/* Mensaje del asistente */
[data-testid="stChatMessage"][data-testid*="assistant"],
[data-testid="stChatMessage"]:has(.stChatMessageAssistant) {
  background-color: var(--tp-bg-secondary);
}

/* ── Chat input ── */
[data-testid="stChatInput"] > div {
  border-color: var(--tp-border-default);
  background-color: var(--tp-bg-tertiary);
  border-radius: var(--tp-radius-md);
}
[data-testid="stChatInput"] > div:focus-within {
  border-color: var(--tp-accent-blue);
  box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.2);
}
[data-testid="stChatInput"] textarea {
  color: var(--tp-text-primary);
}

/* ── Form inputs (text_input, number_input, text_area, date_input) ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea,
.stDateInput > div > div > input {
  background-color: var(--tp-bg-tertiary);
  border: 1px solid var(--tp-border-default);
  border-radius: var(--tp-radius-md);
  color: var(--tp-text-primary);
  padding: var(--tp-space-2) var(--tp-space-3);
  min-height: 44px;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stDateInput > div > div > input:focus {
  border-color: var(--tp-accent-blue);
  box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.2);
  outline: none;
}

/* ── Dataframes ── */
[data-testid="stDataFrame"] thead th {
  background-color: var(--tp-bg-tertiary);
  color: var(--tp-text-secondary);
  font-weight: 600;
}

/* ── Focus visible global — interactivos ── */
a:focus-visible,
input:focus-visible,
textarea:focus-visible,
select:focus-visible,
[tabindex]:focus-visible {
  outline: 2px solid var(--tp-accent-blue);
  outline-offset: 2px;
}

/* ── Dividers ── */
[data-testid="stHorizontalRule"],
hr {
  border-color: var(--tp-border-default);
}

/* ==========================================================================
   CLASES UTILITARIAS tp-
   ========================================================================== */

/* ── Status badges ──
   Cada variante usa fondo subtle + texto de acento para legibilidad.
   Ratios verificados en tokens.py (>= 4.5:1 para large text en badges). */
.tp-status-badge {
  display: inline-block;
  padding: 2px var(--tp-space-3);
  border-radius: var(--tp-radius-full);
  font-size: var(--tp-text-sm);
  font-weight: 500;
  line-height: 1.5;
  letter-spacing: 0.01em;
  white-space: nowrap;
}
/* En planificacion — amarillo */
.tp-status-badge--planning {
  background-color: var(--tp-accent-yellow-subtle);
  color: var(--tp-accent-yellow);
}
/* Confirmado — verde */
.tp-status-badge--confirmed {
  background-color: var(--tp-accent-green-subtle);
  color: var(--tp-accent-green);
}
/* En curso — azul */
.tp-status-badge--in-progress {
  background-color: var(--tp-accent-blue-subtle);
  color: var(--tp-accent-blue);
}
/* Completado — gris */
.tp-status-badge--completed {
  background-color: var(--tp-accent-gray-subtle);
  color: var(--tp-accent-gray);
}

/* ── Active trip box (sidebar) ── */
.tp-active-trip-box {
  background-color: var(--tp-bg-tertiary);
  padding: var(--tp-space-3);
  border-radius: var(--tp-radius-md);
  border-left: 4px solid var(--tp-accent-blue);
  margin-bottom: var(--tp-space-3);
  color: var(--tp-text-primary);
  line-height: 1.6;
}
.tp-active-trip-box strong {
  color: var(--tp-text-primary);
  font-size: var(--tp-text-base);
}

/* ── Transfer block ── */
.tp-transfer-block {
  background-color: var(--tp-bg-secondary);
  padding: var(--tp-space-2) var(--tp-space-4);
  border-radius: var(--tp-radius-md);
  border-left: 3px solid var(--tp-accent-gray);
  margin: var(--tp-space-1) 0;
  color: var(--tp-text-secondary);
  font-size: var(--tp-text-sm);
}

/* ── Suggested item ── */
.tp-suggested-item {
  border: 2px dashed var(--tp-accent-orange);
  opacity: 0.85;
  border-radius: var(--tp-radius-md);
}

/* ── Evento de calendario fallback ──
   Usado en la vista alternativa del Cronograma cuando streamlit-calendar
   no esta disponible. border-left-color se setea inline por tipo de item. */
.tp-calendar-event {
  padding: var(--tp-space-2) var(--tp-space-3);
  margin: var(--tp-space-1) 0;
  border-radius: var(--tp-radius-sm);
  background-color: var(--tp-bg-secondary);
  border-left: 4px solid var(--tp-accent-gray);
  color: var(--tp-text-primary);
  font-size: var(--tp-text-sm);
  line-height: 1.5;
}
.tp-calendar-event i {
  color: var(--tp-text-secondary);
}
.tp-calendar-event b {
  color: var(--tp-text-primary);
}

/* ── Card generica con hover lift ── */
.tp-card {
  background-color: var(--tp-bg-secondary);
  border: 1px solid var(--tp-border-default);
  border-radius: var(--tp-radius-md);
  padding: var(--tp-space-4);
  transition: transform var(--tp-transition-spring),
              box-shadow var(--tp-transition-normal),
              border-color var(--tp-transition-fast);
}
.tp-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--tp-shadow-md);
  border-color: var(--tp-border-emphasis);
}

/* ==========================================================================
   COMPONENT STYLES — Estilos especificos para componentes reutilizables
   ========================================================================== */

/* ── Rich card (chat_widget) ── */
.tp-rich-card {
  background-color: var(--tp-bg-secondary);
  border: 1px solid var(--tp-border-default);
  border-radius: var(--tp-radius-md);
  padding: var(--tp-space-4);
  display: flex;
  gap: var(--tp-space-4);
  align-items: flex-start;
  transition: border-color var(--tp-transition-fast),
              box-shadow var(--tp-transition-normal);
}
.tp-rich-card:hover {
  border-color: var(--tp-border-emphasis);
  box-shadow: var(--tp-shadow-sm);
}
.tp-rich-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  min-width: 48px;
  border-radius: var(--tp-radius-full);
  background-color: var(--tp-bg-tertiary);
  font-size: var(--tp-text-xl);
  line-height: 1;
}
.tp-rich-card__body {
  flex: 1;
  min-width: 0;
}
.tp-rich-card__name {
  font-size: var(--tp-text-base);
  font-weight: 600;
  color: var(--tp-text-primary);
  margin: 0 0 var(--tp-space-1) 0;
  line-height: 1.4;
}
.tp-rich-card__provider {
  font-size: var(--tp-text-xs);
  color: var(--tp-text-muted);
  margin-bottom: var(--tp-space-2);
}
.tp-rich-card__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--tp-space-1) var(--tp-space-4);
  margin-bottom: var(--tp-space-2);
}
.tp-rich-card__detail {
  font-size: var(--tp-text-sm);
  color: var(--tp-text-secondary);
  line-height: 1.5;
}
.tp-rich-card__price {
  font-size: var(--tp-text-lg);
  font-weight: 700;
  color: var(--tp-accent-green);
  line-height: 1.4;
}
.tp-rich-card__price--high {
  color: var(--tp-accent-orange);
}
.tp-rich-card__rating {
  font-size: var(--tp-text-sm);
  color: var(--tp-accent-yellow);
  letter-spacing: 0.05em;
}
.tp-rich-card__notes {
  font-size: var(--tp-text-sm);
  color: var(--tp-text-muted);
  font-style: italic;
  margin-top: var(--tp-space-1);
  line-height: 1.5;
}

/* ── Hotel results header ── */
.tp-hotel-header {
  display: flex;
  align-items: center;
  gap: var(--tp-space-3);
  margin-bottom: var(--tp-space-3);
}
.tp-hotel-header__count {
  font-size: var(--tp-text-lg);
  font-weight: 600;
  color: var(--tp-text-primary);
}
.tp-hotel-header__badge {
  display: inline-block;
  padding: 2px var(--tp-space-2);
  border-radius: var(--tp-radius-full);
  background-color: var(--tp-accent-blue-subtle);
  color: var(--tp-accent-blue);
  font-size: var(--tp-text-xs);
  font-weight: 500;
}
.tp-hotel-separator {
  border: none;
  border-top: 1px solid var(--tp-border-default);
  margin: var(--tp-space-3) 0;
}
.tp-hotel-credit {
  font-size: var(--tp-text-xs);
  color: var(--tp-text-muted);
  text-align: center;
  padding-top: var(--tp-space-2);
  border-top: 1px solid var(--tp-border-default);
}

/* ── Confirmation dialog ── */
.tp-confirmation {
  background-color: var(--tp-bg-secondary);
  border-radius: var(--tp-radius-md);
  padding: var(--tp-space-4);
  border: 1px solid var(--tp-border-default);
  border-left: 4px solid var(--tp-accent-blue);
  animation: tp-slide-in 280ms cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tp-confirmation--delete {
  border-left-color: var(--tp-accent-red);
}
.tp-confirmation--add {
  border-left-color: var(--tp-accent-green);
}
.tp-confirmation__header {
  display: flex;
  align-items: center;
  gap: var(--tp-space-2);
  margin-bottom: var(--tp-space-3);
}
.tp-confirmation__icon {
  font-size: var(--tp-text-xl);
}
.tp-confirmation__title {
  font-size: var(--tp-text-base);
  font-weight: 600;
  color: var(--tp-text-primary);
}
.tp-confirmation__details {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--tp-space-3) 0;
}
.tp-confirmation__details li {
  font-size: var(--tp-text-sm);
  color: var(--tp-text-secondary);
  padding: var(--tp-space-1) 0;
  border-bottom: 1px solid var(--tp-border-default);
  line-height: 1.5;
}
.tp-confirmation__details li:last-child {
  border-bottom: none;
}
.tp-confirmation__details strong {
  color: var(--tp-text-primary);
  font-weight: 500;
}

@keyframes tp-slide-in {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── Itinerary item enhanced ── */
.tp-itinerary-badge {
  display: inline-block;
  padding: 1px var(--tp-space-2);
  border-radius: var(--tp-radius-full);
  font-size: var(--tp-text-xs);
  font-weight: 500;
  line-height: 1.6;
  vertical-align: middle;
  margin-left: var(--tp-space-1);
}
.tp-itinerary-badge--time {
  background-color: var(--tp-bg-surface);
  color: var(--tp-text-secondary);
}
.tp-itinerary-badge--status {
  background-color: var(--tp-accent-green-subtle);
  color: var(--tp-accent-green);
}
.tp-itinerary-badge--pending {
  background-color: var(--tp-accent-yellow-subtle);
  color: var(--tp-accent-yellow);
}
.tp-itinerary-badge--suggested {
  background-color: var(--tp-accent-orange-subtle);
  color: var(--tp-accent-orange);
}
.tp-itinerary-notes {
  background-color: var(--tp-bg-tertiary);
  border-left: 3px solid var(--tp-accent-blue);
  padding: var(--tp-space-2) var(--tp-space-3);
  border-radius: 0 var(--tp-radius-sm) var(--tp-radius-sm) 0;
  font-size: var(--tp-text-sm);
  color: var(--tp-text-secondary);
  line-height: 1.5;
  margin-top: var(--tp-space-2);
}
.tp-itinerary-cost-diff {
  font-size: var(--tp-text-xs);
  font-weight: 500;
  padding: 1px var(--tp-space-2);
  border-radius: var(--tp-radius-full);
  display: inline-block;
}
.tp-itinerary-cost-diff--over {
  background-color: var(--tp-accent-red-subtle);
  color: var(--tp-accent-red);
}
.tp-itinerary-cost-diff--under {
  background-color: var(--tp-accent-green-subtle);
  color: var(--tp-accent-green);
}

/* ── Transfer block enhanced ── */
.tp-transfer-block__arrow {
  display: inline-block;
  color: var(--tp-accent-gray);
  margin: 0 var(--tp-space-1);
  font-weight: 700;
}
.tp-transfer-chip {
  display: inline-block;
  padding: 1px var(--tp-space-2);
  border-radius: var(--tp-radius-full);
  background-color: var(--tp-bg-tertiary);
  font-size: var(--tp-text-xs);
  color: var(--tp-text-secondary);
  margin-left: var(--tp-space-2);
}

/* ── Trip card enhanced ── */
.tp-trip-card {
  background-color: var(--tp-bg-secondary);
  border: 1px solid var(--tp-border-default);
  border-radius: var(--tp-radius-md);
  padding: var(--tp-space-4);
  transition: transform var(--tp-transition-spring),
              box-shadow var(--tp-transition-normal),
              border-color var(--tp-transition-fast);
}
.tp-trip-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--tp-shadow-md);
  border-color: var(--tp-border-emphasis);
}
.tp-trip-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--tp-space-3);
}
.tp-trip-card__name {
  font-size: var(--tp-text-xl);
  font-weight: 600;
  color: var(--tp-text-primary);
  margin: 0;
  line-height: 1.3;
}
.tp-trip-card__info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--tp-space-2);
  margin-bottom: var(--tp-space-3);
}
.tp-trip-card__detail {
  font-size: var(--tp-text-sm);
  color: var(--tp-text-secondary);
  line-height: 1.5;
}
.tp-trip-card__detail strong {
  color: var(--tp-text-primary);
}
.tp-trip-card__budget {
  font-size: var(--tp-text-lg);
  font-weight: 600;
  color: var(--tp-accent-green);
}

/* ── Alert banner enhanced ── */
.tp-alert {
  display: flex;
  align-items: center;
  gap: var(--tp-space-3);
  padding: var(--tp-space-3) var(--tp-space-4);
  border-radius: var(--tp-radius-md);
  background-color: var(--tp-bg-secondary);
  border: 1px solid var(--tp-border-default);
  border-left: 4px solid var(--tp-accent-blue);
  margin-bottom: var(--tp-space-2);
  animation: tp-slide-in 280ms cubic-bezier(0.25, 0.1, 0.25, 1);
}
.tp-alert--warning {
  border-left-color: var(--tp-accent-yellow);
}
.tp-alert--error {
  border-left-color: var(--tp-accent-red);
}
.tp-alert--info {
  border-left-color: var(--tp-accent-blue);
}
.tp-alert__icon {
  font-size: var(--tp-text-xl);
  flex-shrink: 0;
}
.tp-alert__message {
  flex: 1;
  font-size: var(--tp-text-sm);
  color: var(--tp-text-primary);
  line-height: 1.5;
}

/* ==========================================================================
   REDUCED MOTION — Desactivar todas las animaciones
   ========================================================================== */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  .stButton > button:hover,
  .tp-card:hover,
  .tp-trip-card:hover {
    transform: none;
  }
}
"""
