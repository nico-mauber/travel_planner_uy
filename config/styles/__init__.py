"""Modulo de estilos del design system Trip Planner.

Exporta get_global_css() que combina tokens, estilos base y responsive
en un unico string CSS listo para inyectar en Streamlit.
"""

from config.styles.tokens import get_tokens_css
from config.styles.base import get_base_css
from config.styles.responsive import get_responsive_css


def get_global_css() -> str:
    """Combina todos los CSS del design system en un unico string.

    Orden de cascada:
    1. Tokens (custom properties en :root)
    2. Base (overrides de Streamlit + clases utilitarias)
    3. Responsive (media queries)
    """
    return get_tokens_css() + get_base_css() + get_responsive_css()
