"""Servicio de retroalimentación post-viaje."""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
FEEDBACK_FILE = os.path.join(DATA_DIR, "feedbacks.json")


def load_feedbacks() -> dict:
    """Carga feedbacks desde JSON. Clave = trip_id."""
    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_feedback(trip_id: str, feedback: dict) -> bool:
    """Guarda feedback para un viaje."""
    try:
        feedbacks = load_feedbacks()
        feedbacks[trip_id] = feedback
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(feedbacks, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def has_feedback(trip_id: str) -> bool:
    """Verifica si un viaje tiene feedback."""
    feedbacks = load_feedbacks()
    return trip_id in feedbacks


def get_feedback(trip_id: str) -> dict:
    """Obtiene feedback de un viaje."""
    feedbacks = load_feedbacks()
    return feedbacks.get(trip_id, {})


def has_pending_feedback(trips: list) -> bool:
    """Verifica si hay viajes completados sin feedback."""
    from config.settings import TripStatus
    feedbacks = load_feedbacks()
    for trip in trips:
        if trip["status"] == TripStatus.COMPLETED.value and trip["id"] not in feedbacks:
            return True
    return False


def get_trips_pending_feedback(trips: list) -> list:
    """Retorna viajes completados sin feedback."""
    from config.settings import TripStatus
    feedbacks = load_feedbacks()
    return [
        t for t in trips
        if t["status"] == TripStatus.COMPLETED.value and t["id"] not in feedbacks
    ]
