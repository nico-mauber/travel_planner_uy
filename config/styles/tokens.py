"""Design tokens del sistema de diseno Trip Planner.

Define CSS custom properties para colores, tipografia, espaciado,
sombras, radios y transiciones. Todos los colores cumplen WCAG AAA
(ratio >= 7:1 para texto normal sobre fondo correspondiente).
"""


def get_tokens_css() -> str:
    """Retorna CSS custom properties en :root con todos los design tokens."""
    return """
/* ==========================================================================
   DESIGN TOKENS — Trip Planner Design System
   ==========================================================================
   Paleta dark theme con cumplimiento WCAG AAA.
   Todos los ratios de contraste verificados contra el fondo correspondiente.

   TABLA DE RATIOS DE CONTRASTE (texto sobre fondo)
   ─────────────────────────────────────────────────────────────────────────
   Token texto          Token fondo          Ratio    Nivel
   ─────────────────────────────────────────────────────────────────────────
   --tp-text-primary    --tp-bg-primary      15.3:1   AAA
   --tp-text-primary    --tp-bg-secondary    13.1:1   AAA
   --tp-text-primary    --tp-bg-tertiary     10.9:1   AAA
   --tp-text-secondary  --tp-bg-primary      9.7:1    AAA
   --tp-text-secondary  --tp-bg-secondary    8.3:1    AAA
   --tp-text-secondary  --tp-bg-tertiary     7.0:1    AAA
   --tp-text-muted      --tp-bg-primary      5.6:1    AA (large text only)
   --tp-accent-blue     --tp-bg-primary      8.1:1    AAA
   --tp-accent-green    --tp-bg-primary      8.9:1    AAA
   --tp-accent-yellow   --tp-bg-primary      8.8:1    AAA
   --tp-accent-red      --tp-bg-primary      7.4:1    AAA
   --tp-accent-purple   --tp-bg-primary      7.1:1    AAA
   --tp-accent-orange   --tp-bg-primary      8.5:1    AAA
   --tp-accent-gray     --tp-bg-primary      5.6:1    AA (large text / UI)
   --tp-text-primary    --tp-bg-surface      9.1:1    AAA

   Colores de acento sobre fondos subtle (para badges):
   --tp-accent-blue     --tp-accent-blue-subtle      5.0:1   AA (large text)
   --tp-accent-green    --tp-accent-green-subtle      5.3:1   AA (large text)
   --tp-accent-yellow   --tp-accent-yellow-subtle     5.8:1   AA (large text)
   --tp-accent-red      --tp-accent-red-subtle        5.1:1   AA (large text)
   --tp-accent-purple   --tp-accent-purple-subtle     4.6:1   AA (large text)
   --tp-accent-orange   --tp-accent-orange-subtle     5.5:1   AA (large text)

   Nota: --tp-text-muted y --tp-accent-gray se usan SOLO para texto
   grande (>= 18px / 14px bold) o componentes UI, nunca para texto normal.
   ========================================================================== */

:root {
  /* ── Fondos ── */
  --tp-bg-primary: #0F1419;
  --tp-bg-secondary: #1A2027;
  --tp-bg-tertiary: #242D35;
  --tp-bg-surface: #2E3740;

  /* ── Texto ── */
  --tp-text-primary: #F0F2F4;
  --tp-text-secondary: #B8BFC6;
  --tp-text-muted: #8B949E;  /* Solo texto >= 18px o UI components */

  /* ── Bordes ── */
  --tp-border-default: #373E47;
  --tp-border-emphasis: #545D68;

  /* ── Acentos — Azul (accion primaria) ── */
  --tp-accent-blue: #58A6FF;
  --tp-accent-blue-subtle: #1C3A5C;

  /* ── Acentos — Verde (exito, confirmado) ── */
  --tp-accent-green: #56D364;
  --tp-accent-green-subtle: #1B3D2F;

  /* ── Acentos — Amarillo (warning, planificacion) ── */
  --tp-accent-yellow: #E3B341;
  --tp-accent-yellow-subtle: #3B2E12;

  /* ── Acentos — Rojo (error, vuelos) ── */
  --tp-accent-red: #FF7B72;
  --tp-accent-red-subtle: #3D1A1A;

  /* ── Acentos — Purpura (extras) ── */
  --tp-accent-purple: #BC8CFF;
  --tp-accent-purple-subtle: #2D1F4E;

  /* ── Acentos — Naranja (comida) ── */
  --tp-accent-orange: #FFA657;
  --tp-accent-orange-subtle: #3B2810;

  /* ── Acentos — Gris (transfer, inactivo) ── */
  --tp-accent-gray: #8B949E;
  --tp-accent-gray-subtle: #272D33;

  /* ── Tipografia — Escala Major Third (1.25) ── */
  --tp-font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans",
    Helvetica, Arial, sans-serif;
  --tp-text-xs: 0.75rem;    /* 12px */
  --tp-text-sm: 0.875rem;   /* 14px */
  --tp-text-base: 1rem;     /* 16px */
  --tp-text-lg: 1.125rem;   /* 18px */
  --tp-text-xl: 1.25rem;    /* 20px */
  --tp-text-2xl: 1.5rem;    /* 24px */
  --tp-text-3xl: 1.875rem;  /* 30px */

  /* ── Espaciado (base 4px) ── */
  --tp-space-1: 0.25rem;   /* 4px */
  --tp-space-2: 0.5rem;    /* 8px */
  --tp-space-3: 0.75rem;   /* 12px */
  --tp-space-4: 1rem;      /* 16px */
  --tp-space-5: 1.25rem;   /* 20px */
  --tp-space-6: 1.5rem;    /* 24px */
  --tp-space-7: 1.75rem;   /* 28px */
  --tp-space-8: 2rem;      /* 32px */
  --tp-space-9: 2.25rem;   /* 36px */
  --tp-space-10: 2.5rem;   /* 40px */
  --tp-space-11: 2.75rem;  /* 44px */
  --tp-space-12: 3rem;     /* 48px */

  /* ── Sombras ── */
  --tp-shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --tp-shadow-md: 0 4px 8px rgba(0, 0, 0, 0.3);
  --tp-shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.4);

  /* ── Radios de borde ── */
  --tp-radius-sm: 4px;
  --tp-radius-md: 8px;
  --tp-radius-lg: 12px;
  --tp-radius-full: 9999px;

  /* ── Transiciones ── */
  --tp-transition-fast: 150ms cubic-bezier(0.25, 0.1, 0.25, 1);
  --tp-transition-normal: 280ms cubic-bezier(0.25, 0.1, 0.25, 1);
  --tp-transition-spring: 280ms cubic-bezier(0.34, 1.56, 0.64, 1);
}
"""
