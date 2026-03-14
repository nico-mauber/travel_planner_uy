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
ITEM_TYPE_COLORS = {
    ItemType.ACTIVITY: "#4CAF50",
    ItemType.TRANSFER: "#9E9E9E",
    ItemType.ACCOMMODATION: "#2196F3",
    ItemType.FOOD: "#FF9800",
    ItemType.FLIGHT: "#E91E63",
    ItemType.EXTRA: "#9C27B0",
}

# Colores por categoría de presupuesto
BUDGET_CATEGORY_COLORS = {
    BudgetCategory.FLIGHTS: "#E91E63",
    BudgetCategory.ACCOMMODATION: "#2196F3",
    BudgetCategory.ACTIVITIES: "#4CAF50",
    BudgetCategory.FOOD: "#FF9800",
    BudgetCategory.TRANSPORT: "#9E9E9E",
    BudgetCategory.EXTRAS: "#9C27B0",
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

# Mapeo de ItemType a BudgetCategory
ITEM_TYPE_TO_BUDGET = {
    ItemType.ACTIVITY: BudgetCategory.ACTIVITIES,
    ItemType.TRANSFER: BudgetCategory.TRANSPORT,
    ItemType.ACCOMMODATION: BudgetCategory.ACCOMMODATION,
    ItemType.FOOD: BudgetCategory.FOOD,
    ItemType.FLIGHT: BudgetCategory.FLIGHTS,
    ItemType.EXTRA: BudgetCategory.EXTRAS,
}
