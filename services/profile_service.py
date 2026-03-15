"""Servicio de gestión de perfil de usuario."""

import json
import os
from typing import Optional

from data.sample_data import get_sample_profile
from config.settings import DEMO_USER_ID

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")


def _load_all_profiles() -> dict:
    """Carga todos los perfiles como dict keyed por user_id."""
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                # Detectar formato legacy (dict plano con keys de perfil, no user_ids)
                if "accommodation_types" in data or "travel_styles" in data:
                    migrated = {DEMO_USER_ID: data}
                    _save_all_profiles(migrated)
                    return migrated
                # Formato nuevo (keyed por user_id)
                return data
            if isinstance(data, list):
                # Formato legacy (lista) — no deberia ocurrir, pero manejar
                return {DEMO_USER_ID: data[0]} if data else {}
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {}


def _save_all_profiles(profiles: dict) -> bool:
    """Persiste todos los perfiles en JSON."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def load_profile(user_id: Optional[str] = None) -> dict:
    """Carga perfil para un user_id. Si no existe, carga datos de ejemplo."""
    uid = user_id or DEMO_USER_ID
    all_profiles = _load_all_profiles()

    if uid in all_profiles and all_profiles[uid]:
        return all_profiles[uid]

    # Crear perfil de ejemplo para este usuario
    sample = get_sample_profile()
    all_profiles[uid] = sample
    _save_all_profiles(all_profiles)
    return sample


def save_profile(profile: dict, user_id: Optional[str] = None) -> bool:
    """Persiste perfil para un user_id. Retorna True si exitoso."""
    uid = user_id or DEMO_USER_ID
    all_profiles = _load_all_profiles()
    all_profiles[uid] = profile
    return _save_all_profiles(all_profiles)
