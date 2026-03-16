"""Enums, constantes y colores globales del proyecto Trip Planner."""

from enum import Enum


class TripStatus(str, Enum):
    PLANNING = "en_planificacion"
    CONFIRMED = "confirmado"
    IN_PROGRESS = "en_curso"
    COMPLETED = "completado"


class ItemStatus(str, Enum):
    CONFIRMED = "confirmado"
    PENDING = "pendiente"
    SUGGESTED = "sugerido"


class ItemType(str, Enum):
    ACTIVITY = "actividad"
    TRANSFER = "traslado"
    ACCOMMODATION = "alojamiento"
    FOOD = "comida"
    FLIGHT = "vuelo"
    EXTRA = "extra"


class BudgetCategory(str, Enum):
    FLIGHTS = "vuelos"
    ACCOMMODATION = "alojamiento"
    ACTIVITIES = "actividades"
    FOOD = "comidas"
    TRANSPORT = "transporte_local"
    EXTRAS = "extras"


# Colores por tipo de item (calendario y UI)
# Alineados con design tokens WCAG AAA (config/styles/tokens.py)
ITEM_TYPE_COLORS = {
    ItemType.ACTIVITY: "#56D364",     # --tp-accent-green
    ItemType.TRANSFER: "#8B949E",     # --tp-accent-gray
    ItemType.ACCOMMODATION: "#58A6FF",  # --tp-accent-blue
    ItemType.FOOD: "#FFA657",         # --tp-accent-orange
    ItemType.FLIGHT: "#FF7B72",       # --tp-accent-red
    ItemType.EXTRA: "#BC8CFF",        # --tp-accent-purple
}

# Colores por categoria de presupuesto
# Consistentes con ITEM_TYPE_COLORS para coherencia visual
BUDGET_CATEGORY_COLORS = {
    BudgetCategory.FLIGHTS: "#FF7B72",     # --tp-accent-red
    BudgetCategory.ACCOMMODATION: "#58A6FF",  # --tp-accent-blue
    BudgetCategory.ACTIVITIES: "#56D364",   # --tp-accent-green
    BudgetCategory.FOOD: "#FFA657",         # --tp-accent-orange
    BudgetCategory.TRANSPORT: "#8B949E",    # --tp-accent-gray
    BudgetCategory.EXTRAS: "#BC8CFF",       # --tp-accent-purple
}

# Iconos por tipo de item
ITEM_TYPE_ICONS = {
    ItemType.ACTIVITY: "🎯",
    ItemType.TRANSFER: "🚕",
    ItemType.ACCOMMODATION: "🏨",
    ItemType.FOOD: "🍽️",
    ItemType.FLIGHT: "✈️",
    ItemType.EXTRA: "📦",
}

# Iconos por estado
STATUS_ICONS = {
    ItemStatus.CONFIRMED: "✅",
    ItemStatus.PENDING: "⏳",
    ItemStatus.SUGGESTED: "💡",
}

# Labels en español
TRIP_STATUS_LABELS = {
    TripStatus.PLANNING: "En planificación",
    TripStatus.CONFIRMED: "Confirmado",
    TripStatus.IN_PROGRESS: "En curso",
    TripStatus.COMPLETED: "Completado",
}

ITEM_TYPE_LABELS = {
    ItemType.ACTIVITY: "Actividad",
    ItemType.TRANSFER: "Traslado",
    ItemType.ACCOMMODATION: "Alojamiento",
    ItemType.FOOD: "Comida",
    ItemType.FLIGHT: "Vuelo",
    ItemType.EXTRA: "Extra",
}

BUDGET_CATEGORY_LABELS = {
    BudgetCategory.FLIGHTS: "Vuelos",
    BudgetCategory.ACCOMMODATION: "Alojamiento",
    BudgetCategory.ACTIVITIES: "Actividades",
    BudgetCategory.FOOD: "Comidas",
    BudgetCategory.TRANSPORT: "Transporte local",
    BudgetCategory.EXTRAS: "Extras",
}

# Constantes de autenticacion
DEMO_USER_ID = "user-demo0001"

# Mapeo de ItemType a BudgetCategory
ITEM_TYPE_TO_BUDGET = {
    ItemType.ACTIVITY: BudgetCategory.ACTIVITIES,
    ItemType.TRANSFER: BudgetCategory.TRANSPORT,
    ItemType.ACCOMMODATION: BudgetCategory.ACCOMMODATION,
    ItemType.FOOD: BudgetCategory.FOOD,
    ItemType.FLIGHT: BudgetCategory.FLIGHTS,
    ItemType.EXTRA: BudgetCategory.EXTRAS,
}
