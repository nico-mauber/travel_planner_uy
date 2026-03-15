"""Servicio de gestión de perfil de usuario — Supabase backend."""

from typing import Optional

from config.settings import DEMO_USER_ID

_EMPTY_PROFILE = {
    "accommodation_types": [],
    "food_restrictions": [],
    "allergies": "",
    "travel_styles": [],
    "daily_budget": 0.0,
    "preferred_airlines": "",
    "preferred_hotel_chains": "",
}


def load_profile(user_id: Optional[str] = None) -> dict:
    """Carga perfil para un user_id desde Supabase. Si no existe, crea uno vacio."""
    from services.supabase_client import get_supabase_client
    from services.auth_service import ensure_user_exists

    uid = user_id or DEMO_USER_ID
    sb = get_supabase_client()

    result = sb.table("profiles").select("*").eq("user_id", uid).execute()
    if result.data:
        row = result.data[0]
        return {
            "accommodation_types": row.get("accommodation_types") or [],
            "food_restrictions": row.get("food_restrictions") or [],
            "allergies": row.get("allergies") or "",
            "travel_styles": row.get("travel_styles") or [],
            "daily_budget": float(row.get("daily_budget") or 0.0),
            "preferred_airlines": row.get("preferred_airlines") or "",
            "preferred_hotel_chains": row.get("preferred_hotel_chains") or "",
        }

    # No existe: crear perfil vacio
    ensure_user_exists(uid)
    _upsert_profile(sb, uid, _EMPTY_PROFILE)
    return dict(_EMPTY_PROFILE)


def save_profile(profile: dict, user_id: Optional[str] = None) -> bool:
    """Persiste perfil para un user_id en Supabase. Retorna True si exitoso."""
    from services.supabase_client import get_supabase_client
    from services.auth_service import ensure_user_exists

    uid = user_id or DEMO_USER_ID
    sb = get_supabase_client()
    ensure_user_exists(uid)
    try:
        _upsert_profile(sb, uid, profile)
        return True
    except Exception:
        return False


def _upsert_profile(sb, user_id: str, profile: dict) -> None:
    """Upsert de perfil en Supabase."""
    row = {
        "user_id": user_id,
        "accommodation_types": profile.get("accommodation_types", []),
        "food_restrictions": profile.get("food_restrictions", []),
        "allergies": profile.get("allergies", ""),
        "travel_styles": profile.get("travel_styles", []),
        "daily_budget": float(profile.get("daily_budget", 0.0)),
        "preferred_airlines": profile.get("preferred_airlines", ""),
        "preferred_hotel_chains": profile.get("preferred_hotel_chains", ""),
    }
    sb.table("profiles").upsert(row, on_conflict="user_id").execute()
