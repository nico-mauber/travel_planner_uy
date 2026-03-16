"""Servicio de retroalimentación post-viaje — Supabase backend."""


def save_feedback(trip_id: str, feedback: dict, user_id: str = None) -> bool:
    """Guarda feedback para un viaje en Supabase (upsert por trip_id).

    Si user_id es proporcionado, verifica que el viaje pertenezca al usuario.
    """
    from services.supabase_client import get_supabase_client

    try:
        sb = get_supabase_client()

        # Verificar ownership del viaje
        if user_id:
            trip_result = sb.table("trips").select("user_id").eq("id", trip_id).execute()
            if not trip_result.data or trip_result.data[0].get("user_id") != user_id:
                return False

        row = {
            "trip_id": trip_id,
            "overall_rating": int(feedback.get("overall_rating", 0)),
            "comment": feedback.get("comment", ""),
            "item_feedbacks": feedback.get("item_feedbacks", []),
            "skipped": feedback.get("skipped", False),
        }
        sb.table("feedbacks").upsert(row, on_conflict="trip_id").execute()
        return True
    except Exception:
        return False


def has_feedback(trip_id: str) -> bool:
    """Verifica si un viaje tiene feedback en Supabase."""
    from services.supabase_client import get_supabase_client

    try:
        sb = get_supabase_client()
        result = sb.table("feedbacks").select("trip_id").eq("trip_id", trip_id).execute()
        return bool(result.data)
    except Exception:
        return False


def get_feedback(trip_id: str) -> dict:
    """Obtiene feedback de un viaje desde Supabase."""
    from services.supabase_client import get_supabase_client

    try:
        sb = get_supabase_client()
        result = sb.table("feedbacks").select("*").eq("trip_id", trip_id).execute()
        if result.data:
            row = result.data[0]
            return {
                "trip_id": row["trip_id"],
                "overall_rating": row.get("overall_rating", 0),
                "comment": row.get("comment", ""),
                "item_feedbacks": row.get("item_feedbacks", []),
                "skipped": row.get("skipped", False),
            }
    except Exception:
        pass
    return {}


def has_pending_feedback(trips: list) -> bool:
    """Verifica si hay viajes completados sin feedback."""
    from config.settings import TripStatus

    for trip in trips:
        if trip["status"] == TripStatus.COMPLETED.value and not has_feedback(trip["id"]):
            return True
    return False


def get_trips_pending_feedback(trips: list) -> list:
    """Retorna viajes completados sin feedback."""
    from config.settings import TripStatus

    return [
        t for t in trips
        if t["status"] == TripStatus.COMPLETED.value and not has_feedback(t["id"])
    ]
