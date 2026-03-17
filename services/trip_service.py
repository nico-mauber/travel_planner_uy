"""Servicio de gestión de viajes — CRUD, sincronización — Supabase backend."""

import uuid
from datetime import date
from typing import Optional

from config.settings import TripStatus, ItemStatus, DEMO_USER_ID


# ─── Helpers de conversión DB → dict ───

def _row_to_item(row: dict) -> dict:
    """Convierte un row de itinerary_items de Supabase a dict de la app."""
    return {
        "id": row["id"],
        "trip_id": row["trip_id"],
        "name": row.get("name", ""),
        "item_type": row.get("item_type", "actividad"),
        "day": int(row.get("day", 1)),
        "end_day": row.get("end_day"),
        "start_time": str(row.get("start_time", "00:00"))[:5],  # TIME → "HH:MM"
        "end_time": str(row.get("end_time", "00:00"))[:5],
        "status": row.get("status", "pendiente"),
        "location": row.get("location", ""),
        "address": row.get("address", ""),
        "notes": row.get("notes", ""),
        "cost_estimated": float(row.get("cost_estimated") or 0.0),
        "cost_real": float(row.get("cost_real") or 0.0),
        "booking_url": row.get("booking_url", ""),
        "provider": row.get("provider", ""),
    }


def _row_to_trip(row: dict, items: list, expenses: list = None) -> dict:
    """Convierte un row de trips de Supabase a dict de la app."""
    # start_date y end_date pueden venir como date o string
    start_date = str(row.get("start_date", ""))[:10]
    end_date = str(row.get("end_date", ""))[:10]

    return {
        "id": row["id"],
        "user_id": row.get("user_id", ""),
        "name": row.get("name", ""),
        "destination": row.get("destination", ""),
        "start_date": start_date,
        "end_date": end_date,
        "status": row.get("status", TripStatus.PLANNING.value),
        "budget_total": float(row.get("budget_total") or 0.0),
        "items": items,
        "expenses": expenses or [],
        "notes": row.get("notes", ""),
    }


def _item_to_row(item: dict) -> dict:
    """Convierte un dict de item de la app a row para Supabase."""
    return {
        "id": item["id"],
        "trip_id": item.get("trip_id", ""),
        "name": item.get("name", ""),
        "item_type": item.get("item_type", "actividad"),
        "day": int(item.get("day", 1)),
        "end_day": item.get("end_day"),
        "start_time": item.get("start_time", "00:00"),
        "end_time": item.get("end_time", "00:00"),
        "status": item.get("status", "pendiente"),
        "location": item.get("location", ""),
        "address": item.get("address", ""),
        "notes": item.get("notes", ""),
        "cost_estimated": float(item.get("cost_estimated", 0.0)),
        "cost_real": float(item.get("cost_real", 0.0)),
        "booking_url": item.get("booking_url", ""),
        "provider": item.get("provider", ""),
    }


# ─── Funciones principales ───

def load_trips(user_id: Optional[str] = None) -> list:
    """Carga viajes desde Supabase, filtrados por user_id.

    Retorna lista vacia si el usuario no tiene viajes.
    """
    from services.supabase_client import get_supabase_client
    from services.auth_service import ensure_user_exists

    uid = user_id or DEMO_USER_ID
    ensure_user_exists(uid)
    sb = get_supabase_client()

    # Cargar viajes del usuario
    trips_result = sb.table("trips").select("*").eq("user_id", uid).execute()
    trip_rows = trips_result.data or []

    if not trip_rows:
        return []

    # Cargar items de todos los viajes del usuario
    trip_ids = [r["id"] for r in trip_rows]
    items_result = sb.table("itinerary_items").select("*").in_("trip_id", trip_ids).execute()
    all_items = items_result.data or []

    # Agrupar items por trip_id
    items_by_trip = {}
    for item_row in all_items:
        tid = item_row["trip_id"]
        if tid not in items_by_trip:
            items_by_trip[tid] = []
        items_by_trip[tid].append(_row_to_item(item_row))

    # Cargar expenses de todos los viajes del usuario
    from services.expense_service import _row_to_expense
    expenses_result = sb.table("expenses").select("*").in_("trip_id", trip_ids).execute()
    all_expenses = expenses_result.data or []

    # Agrupar expenses por trip_id
    expenses_by_trip = {}
    for exp_row in all_expenses:
        tid = exp_row["trip_id"]
        if tid not in expenses_by_trip:
            expenses_by_trip[tid] = []
        expenses_by_trip[tid].append(_row_to_expense(exp_row))

    # Construir lista de trips
    trips = []
    for trip_row in trip_rows:
        trip_items = items_by_trip.get(trip_row["id"], [])
        trip_expenses = expenses_by_trip.get(trip_row["id"], [])
        trips.append(_row_to_trip(trip_row, trip_items, trip_expenses))

    return trips


def _insert_trip_to_db(sb, trip: dict) -> None:
    """Inserta un viaje completo (trip + items) en Supabase."""
    trip_row = {
        "id": trip["id"],
        "user_id": trip.get("user_id", DEMO_USER_ID),
        "name": trip.get("name", ""),
        "destination": trip.get("destination", ""),
        "start_date": trip.get("start_date"),
        "end_date": trip.get("end_date"),
        "status": trip.get("status", TripStatus.PLANNING.value),
        "budget_total": float(trip.get("budget_total", 0.0)),
        "notes": trip.get("notes", ""),
    }
    sb.table("trips").upsert(trip_row, on_conflict="id").execute()

    items = trip.get("items", [])
    for item in items:
        row = _item_to_row(item)
        sb.table("itinerary_items").upsert(row, on_conflict="id").execute()


def create_trip(trips: list, name: str, destination: str,
                start_date: str, end_date: str, user_id: Optional[str] = None) -> dict:
    """Crea un nuevo viaje en planificación. Persiste en Supabase."""
    from services.supabase_client import get_supabase_client
    from services.auth_service import ensure_user_exists

    _uid = user_id or DEMO_USER_ID
    ensure_user_exists(_uid)

    trip = {
        "id": f"trip-{uuid.uuid4().hex[:8]}",
        "user_id": _uid,
        "name": name,
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "status": TripStatus.PLANNING.value,
        "budget_total": 0.0,
        "items": [],
        "expenses": [],
        "notes": "",
    }
    trips.append(trip)

    sb = get_supabase_client()
    _insert_trip_to_db(sb, trip)
    return trip


def delete_trip(trips: list, trip_id: str, user_id: Optional[str] = None) -> bool:
    """Elimina un viaje (solo si está en planificación y pertenece al usuario). CASCADE elimina items."""
    from services.supabase_client import get_supabase_client

    for i, trip in enumerate(trips):
        if trip["id"] == trip_id:
            # Verificar ownership si se proporcionó user_id
            if user_id and trip.get("user_id") and trip["user_id"] != user_id:
                return False
            if trip["status"] == TripStatus.PLANNING.value:
                trips.pop(i)
                sb = get_supabase_client()
                sb.table("trips").delete().eq("id", trip_id).execute()
                return True
    return False


def update_trip_statuses(trips: list) -> bool:
    """Actualiza automáticamente estados según fechas. Persiste cambios en Supabase."""
    from services.supabase_client import get_supabase_client

    changed = False
    today = date.today()
    sb = get_supabase_client()

    for trip in trips:
        start = date.fromisoformat(trip["start_date"])
        end = date.fromisoformat(trip["end_date"])
        current = trip["status"]

        if current == TripStatus.COMPLETED.value:
            continue

        new_status = None
        if today > end and current != TripStatus.COMPLETED.value:
            new_status = TripStatus.COMPLETED.value
        elif start <= today <= end and current in (
            TripStatus.CONFIRMED.value, TripStatus.PLANNING.value
        ):
            new_status = TripStatus.IN_PROGRESS.value

        if new_status:
            trip["status"] = new_status
            sb.table("trips").update({"status": new_status}).eq("id", trip["id"]).execute()
            changed = True

    return changed


def get_trip_by_id(trips: list, trip_id: str) -> Optional[dict]:
    """Obtiene un viaje por ID."""
    for trip in trips:
        if trip["id"] == trip_id:
            return trip
    return None


def get_active_trip(trips: list, active_trip_id: Optional[str]) -> Optional[dict]:
    """Obtiene el viaje activo. Prioridad: active_trip_id > en planificación > próximo confirmado."""
    if active_trip_id:
        trip = get_trip_by_id(trips, active_trip_id)
        if trip:
            return trip

    # Buscar viaje en planificación
    planning = [t for t in trips if t["status"] == TripStatus.PLANNING.value]
    if planning:
        return planning[0]

    # Buscar próximo confirmado
    confirmed = [t for t in trips if t["status"] == TripStatus.CONFIRMED.value]
    if confirmed:
        confirmed.sort(key=lambda t: t["start_date"])
        return confirmed[0]

    # Buscar en curso
    in_progress = [t for t in trips if t["status"] == TripStatus.IN_PROGRESS.value]
    if in_progress:
        return in_progress[0]

    return None


def sort_trips(trips: list) -> list:
    """Ordena viajes: en curso → próximos (asc) → completados (desc)."""
    in_progress = [t for t in trips if t["status"] == TripStatus.IN_PROGRESS.value]
    planning = [t for t in trips if t["status"] == TripStatus.PLANNING.value]
    confirmed = [t for t in trips if t["status"] == TripStatus.CONFIRMED.value]
    completed = [t for t in trips if t["status"] == TripStatus.COMPLETED.value]

    planning.sort(key=lambda t: t["start_date"])
    confirmed.sort(key=lambda t: t["start_date"])
    completed.sort(key=lambda t: t["start_date"], reverse=True)

    return in_progress + planning + confirmed + completed


def filter_trips_by_status(trips: list, status: Optional[str] = None) -> list:
    """Filtra viajes por estado. None = todos."""
    if status is None or status == "Todos":
        return trips
    return [t for t in trips if t["status"] == status]


def group_items_by_day(items: list) -> dict:
    """Agrupa items por dia y los ordena cronologicamente.

    Items con end_day aparecen en todos los dias que abarcan.
    """
    groups = {}
    for item in items:
        start_day = item["day"]
        end_day = item.get("end_day") or start_day
        for d in range(start_day, end_day + 1):
            if d not in groups:
                groups[d] = []
            groups[d].append(item)

    for day in groups:
        groups[day].sort(key=lambda x: x["start_time"])

    return dict(sorted(groups.items()))


def accept_suggestion(trip: dict, item_id: str) -> bool:
    """Cambia un item sugerido a pendiente. Persiste en Supabase."""
    from services.supabase_client import get_supabase_client

    for item in trip["items"]:
        if item["id"] == item_id and item["status"] == ItemStatus.SUGGESTED.value:
            item["status"] = ItemStatus.PENDING.value
            sb = get_supabase_client()
            sb.table("itinerary_items").update(
                {"status": ItemStatus.PENDING.value}
            ).eq("id", item_id).execute()
            return True
    return False


def discard_suggestion(trip: dict, item_id: str) -> bool:
    """Elimina un item sugerido. Borra de Supabase."""
    from services.supabase_client import get_supabase_client

    for i, item in enumerate(trip["items"]):
        if item["id"] == item_id and item["status"] == ItemStatus.SUGGESTED.value:
            trip["items"].pop(i)
            sb = get_supabase_client()
            sb.table("itinerary_items").delete().eq("id", item_id).execute()
            return True
    return False


def add_item_to_trip(trip: dict, item: dict) -> None:
    """Agrega un item al viaje. Persiste en Supabase."""
    from services.supabase_client import get_supabase_client

    trip["items"].append(item)
    sb = get_supabase_client()
    sb.table("itinerary_items").upsert(_item_to_row(item), on_conflict="id").execute()
    # budget_total se recalcula por el trigger
    _refresh_trip_budget(sb, trip)


def remove_item_from_trip(trip: dict, item_id: str) -> bool:
    """Elimina un item del viaje por ID. Borra de Supabase."""
    from services.supabase_client import get_supabase_client

    for i, item in enumerate(trip["items"]):
        if item["id"] == item_id:
            trip["items"].pop(i)
            sb = get_supabase_client()
            sb.table("itinerary_items").delete().eq("id", item_id).execute()
            # budget_total se recalcula por el trigger
            _refresh_trip_budget(sb, trip)
            return True
    return False


def recalculate_budget(trip: dict) -> None:
    """Recalcula el presupuesto total del viaje en memoria (excluye sugeridos)."""
    total = 0.0
    for item in trip["items"]:
        if item["status"] != ItemStatus.SUGGESTED.value:
            total += item.get("cost_estimated", 0.0)
    for exp in trip.get("expenses", []):
        total += exp.get("amount", 0.0)
    trip["budget_total"] = total


def _refresh_trip_budget(sb, trip: dict) -> None:
    """Lee el budget_total actualizado por el trigger de Supabase y lo refleja en el dict."""
    result = sb.table("trips").select("budget_total").eq("id", trip["id"]).execute()
    if result.data:
        trip["budget_total"] = float(result.data[0].get("budget_total") or 0.0)


def sync_trip_changes(trips: list, trip: dict, user_id: Optional[str] = None) -> None:
    """Sincroniza cambios del viaje a Supabase.

    - Recalcula presupuesto en memoria
    - Persiste trip y sus items en Supabase
    - Actualiza el trip en la lista de trips
    """
    from services.supabase_client import get_supabase_client

    recalculate_budget(trip)

    # Actualizar el trip en la lista en memoria
    for i, t in enumerate(trips):
        if t["id"] == trip["id"]:
            trips[i] = trip
            break

    sb = get_supabase_client()

    # Actualizar datos del trip
    trip_update = {
        "name": trip.get("name", ""),
        "destination": trip.get("destination", ""),
        "start_date": trip.get("start_date"),
        "end_date": trip.get("end_date"),
        "status": trip.get("status", TripStatus.PLANNING.value),
        "notes": trip.get("notes", ""),
    }
    sb.table("trips").update(trip_update).eq("id", trip["id"]).execute()

    # Sincronizar items: obtener IDs actuales en DB, comparar con los en memoria
    db_items_result = sb.table("itinerary_items").select("id").eq("trip_id", trip["id"]).execute()
    db_item_ids = {r["id"] for r in (db_items_result.data or [])}
    mem_item_ids = {item["id"] for item in trip.get("items", [])}

    # Eliminar items que ya no están en memoria
    removed_ids = db_item_ids - mem_item_ids
    for rid in removed_ids:
        sb.table("itinerary_items").delete().eq("id", rid).execute()

    # Upsert items actuales
    for item in trip.get("items", []):
        sb.table("itinerary_items").upsert(_item_to_row(item), on_conflict="id").execute()

    # Sincronizar expenses
    from services.expense_service import _expense_to_row
    db_expenses_result = sb.table("expenses").select("id").eq("trip_id", trip["id"]).execute()
    db_expense_ids = {r["id"] for r in (db_expenses_result.data or [])}
    mem_expense_ids = {exp["id"] for exp in trip.get("expenses", [])}

    # Eliminar expenses que ya no están en memoria
    removed_exp_ids = db_expense_ids - mem_expense_ids
    for rid in removed_exp_ids:
        sb.table("expenses").delete().eq("id", rid).execute()

    # Upsert expenses actuales
    for exp in trip.get("expenses", []):
        sb.table("expenses").upsert(_expense_to_row(exp), on_conflict="id").execute()

    # Refrescar budget_total desde el trigger
    _refresh_trip_budget(sb, trip)


def save_trips_for_user(user_trips: list, user_id: str) -> None:
    """Compatibilidad: persiste todos los viajes del usuario en Supabase.

    Reemplaza la lógica anterior de merge JSON. Ahora simplemente
    actualiza cada viaje en Supabase.
    """
    from services.supabase_client import get_supabase_client
    from services.auth_service import ensure_user_exists

    ensure_user_exists(user_id)
    sb = get_supabase_client()
    for trip in user_trips:
        if trip.get("user_id") == user_id:
            _insert_trip_to_db(sb, trip)


def get_transfer_info(item_a: dict, item_b: dict) -> Optional[dict]:
    """Genera info de traslado entre dos items con ubicaciones diferentes."""
    loc_a = item_a.get("location", "")
    loc_b = item_b.get("location", "")

    if not loc_a or not loc_b or loc_a == loc_b:
        return None

    return {
        "from": loc_a,
        "to": loc_b,
        "transport": "Metro / Taxi",
        "duration": "20 min",
        "cost_estimated": 5.0,
    }
