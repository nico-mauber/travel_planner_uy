"""Modelo y funciones de presupuesto."""

from dataclasses import dataclass
from typing import Dict, List

from config.settings import BudgetCategory, ItemStatus, ITEM_TYPE_TO_BUDGET


@dataclass
class BudgetSummary:
    total_estimated: float = 0.0
    total_real: float = 0.0
    by_category: Dict[str, Dict[str, float]] = None

    def __post_init__(self):
        if self.by_category is None:
            self.by_category = {}


def calculate_budget_from_items(items: list) -> BudgetSummary:
    """Calcula el resumen de presupuesto a partir de los items del itinerario.
    Items con estado 'sugerido' NO se contabilizan (RN-002 REQ-UI-006)."""
    summary = BudgetSummary()
    by_cat: Dict[str, Dict[str, float]] = {}

    for cat in BudgetCategory:
        by_cat[cat.value] = {"estimated": 0.0, "real": 0.0, "items": []}

    for item in items:
        if item.get("status") == ItemStatus.SUGGESTED.value:
            continue

        item_type = item.get("item_type", "extra")
        from config.settings import ItemType
        try:
            budget_cat = ITEM_TYPE_TO_BUDGET.get(
                ItemType(item_type), BudgetCategory.EXTRAS
            )
        except ValueError:
            budget_cat = BudgetCategory.EXTRAS

        cost_est = item.get("cost_estimated", 0.0)
        cost_real = item.get("cost_real", 0.0)

        by_cat[budget_cat.value]["estimated"] += cost_est
        by_cat[budget_cat.value]["real"] += cost_real
        by_cat[budget_cat.value]["items"].append(item)

        summary.total_estimated += cost_est
        summary.total_real += cost_real

    summary.by_category = by_cat
    return summary
