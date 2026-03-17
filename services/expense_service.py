"""Servicio de gastos directos — CRUD de expenses no asociados a items del itinerario."""

import uuid
import logging
from typing import Optional

from config.settings import BudgetCategory

logger = logging.getLogger(__name__)

# Categorías válidas (valores del enum BudgetCategory)
_VALID_CATEGORIES = {cat.value for cat in BudgetCategory}


def _row_to_expense(row: dict) -> dict:
    """Convierte row de Supabase a dict de la app."""
    return {
        "id": row["id"],
        "trip_id": row["trip_id"],
        "name": row.get("name", ""),
        "category": row.get("category", "extras"),
        "amount": float(row.get("amount") or 0.0),
        "notes": row.get("notes", ""),
    }


def _expense_to_row(expense: dict) -> dict:
    """Convierte dict de la app a row para Supabase."""
    return {
        "id": expense["id"],
        "trip_id": expense.get("trip_id", ""),
        "name": expense.get("name", ""),
        "category": expense.get("category", "extras"),
        "amount": float(expense.get("amount", 0.0)),
        "notes": expense.get("notes", ""),
    }


def load_expenses(trip_id: str) -> list:
    """Carga gastos de un viaje desde Supabase."""
    from services.supabase_client import get_supabase_client

    try:
        sb = get_supabase_client()
        result = sb.table("expenses").select("*").eq("trip_id", trip_id).execute()
        return [_row_to_expense(row) for row in (result.data or [])]
    except Exception as e:
        logger.error("Error cargando expenses para trip %s: %s", trip_id, e)
        return []


def add_expense(trip: dict, name: str, category: str, amount: float,
                notes: str = "") -> dict:
    """Agrega un gasto al viaje. Persiste en Supabase. Retorna el expense dict."""
    from services.supabase_client import get_supabase_client

    # Validar categoría
    if category not in _VALID_CATEGORIES:
        category = BudgetCategory.EXTRAS.value

    expense = {
        "id": f"exp-{uuid.uuid4().hex[:8]}",
        "trip_id": trip["id"],
        "name": name,
        "category": category,
        "amount": float(amount),
        "notes": notes,
    }

    # Agregar a memoria
    if "expenses" not in trip:
        trip["expenses"] = []
    trip["expenses"].append(expense)

    # Persistir en Supabase
    try:
        sb = get_supabase_client()
        sb.table("expenses").upsert(_expense_to_row(expense), on_conflict="id").execute()
    except Exception as e:
        logger.error("Error persistiendo expense %s: %s", expense["id"], e)

    return expense


def update_expense(trip: dict, expense_id: str, updates: dict) -> Optional[dict]:
    """Actualiza campos de un gasto existente. Retorna expense actualizado o None."""
    from services.supabase_client import get_supabase_client

    expenses = trip.get("expenses", [])
    target = None
    for exp in expenses:
        if exp["id"] == expense_id:
            target = exp
            break

    if target is None:
        return None

    # Actualizar solo campos proporcionados
    for field in ("name", "category", "amount", "notes"):
        if field in updates:
            if field == "category" and updates[field] not in _VALID_CATEGORIES:
                updates[field] = BudgetCategory.EXTRAS.value
            if field == "amount":
                updates[field] = float(updates[field])
            target[field] = updates[field]

    # Persistir en Supabase
    try:
        sb = get_supabase_client()
        sb.table("expenses").upsert(_expense_to_row(target), on_conflict="id").execute()
    except Exception as e:
        logger.error("Error actualizando expense %s: %s", expense_id, e)

    return target


def remove_expense(trip: dict, expense_id: str) -> Optional[str]:
    """Elimina un gasto. Retorna nombre del gasto eliminado o None."""
    from services.supabase_client import get_supabase_client

    expenses = trip.get("expenses", [])
    for i, exp in enumerate(expenses):
        if exp["id"] == expense_id:
            removed_name = exp["name"]
            expenses.pop(i)

            # Eliminar de Supabase
            try:
                sb = get_supabase_client()
                sb.table("expenses").delete().eq("id", expense_id).execute()
            except Exception as e:
                logger.error("Error eliminando expense %s: %s", expense_id, e)

            return removed_name

    return None


def format_existing_expenses(trip: dict) -> str:
    """Formatea gastos existentes para contexto del LLM extractor."""
    expenses = trip.get("expenses", [])
    if not expenses:
        return "GASTOS EXISTENTES: ninguno"

    lines = ["GASTOS EXISTENTES (formato: [ID] Nombre | Categoría | Monto):"]
    for exp in expenses:
        lines.append(
            f"- [{exp['id']}] {exp['name']} | {exp['category']} | USD {exp['amount']:.2f}"
        )
    return "\n".join(lines)
