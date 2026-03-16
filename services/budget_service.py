"""Servicio de cálculos de presupuesto."""

from config.settings import (
    BudgetCategory, ItemStatus, ItemType,
    ITEM_TYPE_TO_BUDGET, BUDGET_CATEGORY_LABELS,
)


def calculate_budget_summary(items: list) -> dict:
    """Calcula resumen de presupuesto por categoría.
    Items 'sugerido' NO se contabilizan (RN-002 REQ-UI-006)."""
    by_category = {}
    for cat in BudgetCategory:
        by_category[cat.value] = {
            "label": BUDGET_CATEGORY_LABELS[cat],
            "estimated": 0.0,
            "real": 0.0,
            "items": [],
        }

    total_estimated = 0.0
    total_real = 0.0

    for item in items:
        if item.get("status") == ItemStatus.SUGGESTED.value:
            continue

        item_type_str = item.get("item_type", "extra")
        try:
            item_type = ItemType(item_type_str)
            budget_cat = ITEM_TYPE_TO_BUDGET.get(item_type, BudgetCategory.EXTRAS)
        except ValueError:
            budget_cat = BudgetCategory.EXTRAS

        cost_est = item.get("cost_estimated", 0.0)
        cost_real = item.get("cost_real", 0.0)

        by_category[budget_cat.value]["estimated"] += cost_est
        by_category[budget_cat.value]["real"] += cost_real
        by_category[budget_cat.value]["items"].append(item)

        total_estimated += cost_est
        total_real += cost_real

    return {
        "total_estimated": total_estimated,
        "total_real": total_real,
        "by_category": by_category,
    }


def has_real_costs(items: list) -> bool:
    """Verifica si hay costos reales registrados."""
    return any(item.get("cost_real", 0.0) > 0 for item in items
               if item.get("status") != ItemStatus.SUGGESTED.value)


def calculate_planning_progress(items: list) -> float:
    """Calcula el progreso de planificación (0.0 a 1.0)."""
    non_suggested = [i for i in items if i.get("status") != ItemStatus.SUGGESTED.value]
    if not non_suggested:
        return 0.0
    confirmed = [i for i in non_suggested if i.get("status") == ItemStatus.CONFIRMED.value]
    return len(confirmed) / len(non_suggested)
