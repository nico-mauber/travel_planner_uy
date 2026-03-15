"""Servicio de autenticacion y gestion de usuarios."""

import json
import os
import sys
import uuid
from datetime import datetime
from typing import Optional

import streamlit as st

from config.settings import DEMO_USER_ID

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# Verificar si Authlib esta disponible al importar el modulo
_AUTHLIB_AVAILABLE = False
try:
    import authlib  # noqa: F401
    _AUTHLIB_AVAILABLE = True
except Exception:
    pass

# Diagnostico: que Python esta ejecutando la app
_PYTHON_EXECUTABLE = sys.executable


def is_auth_enabled() -> bool:
    """Verifica si las credenciales OAuth estan configuradas y Authlib esta instalado."""
    if not _AUTHLIB_AVAILABLE:
        return False
    try:
        secrets = st.secrets
        return bool(
            secrets.get("auth", {}).get("google", {}).get("client_id")
        )
    except Exception:
        return False


def load_users() -> list:
    """Carga usuarios desde JSON."""
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return []


def save_users(users: list) -> None:
    """Persiste usuarios en JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def get_or_create_user(email: str, name: str, picture: str = "") -> dict:
    """Busca usuario por email; si no existe, lo crea con user-{hex8}."""
    users = load_users()
    for user in users:
        if user["email"] == email:
            user["last_login"] = datetime.now().isoformat()
            save_users(users)
            return user

    new_user = {
        "user_id": f"user-{uuid.uuid4().hex[:8]}",
        "email": email,
        "name": name,
        "picture": picture,
        "created_at": datetime.now().isoformat(),
        "last_login": datetime.now().isoformat(),
    }
    users.append(new_user)
    save_users(users)
    return new_user


def get_current_user_id() -> str:
    """Retorna el user_id del usuario actual, o DEMO_USER_ID si no hay auth."""
    current_user = st.session_state.get("current_user")
    if current_user:
        return current_user.get("user_id", DEMO_USER_ID)
    return DEMO_USER_ID


def require_auth() -> None:
    """Guard de autenticacion. Si auth habilitada y no logueado, muestra login y st.stop()."""
    if not is_auth_enabled():
        return

    if st.session_state.get("current_user"):
        return

    # Verificar si el usuario ya esta autenticado via st.user
    user_info = getattr(st, "user", None)
    if user_info and getattr(user_info, "is_logged_in", False):
        user_data = get_or_create_user(
            email=getattr(user_info, "email", ""),
            name=getattr(user_info, "name", ""),
            picture=getattr(user_info, "picture", ""),
        )
        st.session_state.current_user = user_data
        return

    # No autenticado — mostrar pantalla de login
    st.markdown("## Bienvenido a Trip Planner")
    st.markdown("Inicia sesion para acceder a tus viajes y planificaciones.")
    st.login("google")
    st.stop()
