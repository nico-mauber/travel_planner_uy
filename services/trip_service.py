"""Servicio de gestión de viajes — CRUD, sincronización, fuente de verdad."""

import json
import os
import uuid
from datetime import date, timedelta
from typing import List, Optional

from config.settings import TripStatus, ItemStatus, ItemType
from data.sample_data import get_sample_trips, get_sample_chat_histories

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
TRIPS_FILE = os.path.join(DATA_DIR, "trips.json")


def load_trips() -> list:
    """Carga viajes desde JSON. Si está vacío, carga datos de ejemplo."""
    try:
        with open(TRIPS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data:
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    # Cargar datos de ejemplo y persistir
    sample = get_sample_trips()
    save_trips(sample)
    return sample


def save_trips(trips: list) -> None:
    """Persiste viajes en JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TRIPS_FILE, "w", encoding="utf-8") as f:
        json.dump(trips, f, ensure_ascii=False, indent=2)


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


def create_trip(trips: list, name: str, destination: str,
                start_date: str, end_date: str) -> dict:
    """Crea un nuevo viaje en planificación."""
    trip = {
        "id": f"trip-{uuid.uuid4().hex[:8]}",
        "name": name,
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "status": TripStatus.PLANNING.value,
        "budget_total": 0.0,
        "items": [],
        "notes": "",
    }
    trips.append(trip)
    save_trips(trips)
    return trip


def delete_trip(trips: list, trip_id: str) -> bool:
    """Elimina un viaje (solo si está en planificación)."""
    for i, trip in enumerate(trips):
        if trip["id"] == trip_id:
            if trip["status"] == TripStatus.PLANNING.value:
                trips.pop(i)
                save_trips(trips)
                return True
    return False


def update_trip_statuses(trips: list) -> None:
    """Actualiza automáticamente estados según fechas."""
    today = date.today()
    for trip in trips:
        start = date.fromisoformat(trip["start_date"])
        end = date.fromisoformat(trip["end_date"])
        current = trip["status"]

        if current == TripStatus.COMPLETED.value:
            continue

        if today > end and current != TripStatus.COMPLETED.value:
            trip["status"] = TripStatus.COMPLETED.value
        elif start <= today <= end and current in (
            TripStatus.CONFIRMED.value, TripStatus.PLANNING.value
        ):
            trip["status"] = TripStatus.IN_PROGRESS.value


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
    """Agrupa items por día y los ordena cronológicamente."""
    groups = {}
    for item in items:
        day = item["day"]
        if day not in groups:
            groups[day] = []
        groups[day].append(item)

    for day in groups:
        groups[day].sort(key=lambda x: x["start_time"])

    return dict(sorted(groups.items()))


def accept_suggestion(trip: dict, item_id: str) -> bool:
    """Cambia un item sugerido a pendiente."""
    for item in trip["items"]:
        if item["id"] == item_id and item["status"] == ItemStatus.SUGGESTED.value:
            item["status"] = ItemStatus.PENDING.value
            return True
    return False


def discard_suggestion(trip: dict, item_id: str) -> bool:
    """Elimina un item sugerido."""
    for i, item in enumerate(trip["items"]):
        if item["id"] == item_id and item["status"] == ItemStatus.SUGGESTED.value:
            trip["items"].pop(i)
            return True
    return False


def add_item_to_trip(trip: dict, item: dict) -> None:
    """Agrega un item al viaje."""
    trip["items"].append(item)
    recalculate_budget(trip)


def remove_item_from_trip(trip: dict, item_id: str) -> bool:
    """Elimina un item del viaje por ID."""
    for i, item in enumerate(trip["items"]):
        if item["id"] == item_id:
            trip["items"].pop(i)
            recalculate_budget(trip)
            return True
    return False


def recalculate_budget(trip: dict) -> None:
    """Recalcula el presupuesto total del viaje (excluye sugeridos)."""
    total = 0.0
    for item in trip["items"]:
        if item["status"] != ItemStatus.SUGGESTED.value:
            total += item.get("cost_estimated", 0.0)
    trip["budget_total"] = total


def sync_trip_changes(trips: list, trip: dict) -> None:
    """Sincroniza cambios: recalcula presupuesto, persiste en JSON."""
    recalculate_budget(trip)
    # Actualizar el trip en la lista
    for i, t in enumerate(trips):
        if t["id"] == trip["id"]:
            trips[i] = trip
            break
    save_trips(trips)


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
