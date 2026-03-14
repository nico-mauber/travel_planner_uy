"""Servicio de gestión de perfil de usuario."""

import json
import os

from data.sample_data import get_sample_profile

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")


def load_profile() -> dict:
    """Carga perfil desde JSON. Si está vacío, carga datos de ejemplo."""
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data:
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    sample = get_sample_profile()
    save_profile(sample)
    return sample


def save_profile(profile: dict) -> bool:
    """Persiste perfil en JSON. Retorna True si exitoso."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False
