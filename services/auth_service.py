"""Servicio de autenticacion y gestion de usuarios — Supabase backend."""

import sys
import uuid
from datetime import datetime
from typing import Optional

import streamlit as st

from config.settings import DEMO_USER_ID

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


def get_or_create_user(email: str, name: str, picture: str = "") -> dict:
    """Busca usuario por email; si no existe, lo crea con user-{hex8}. Persiste en Supabase."""
    from services.supabase_client import get_supabase_client

    sb = get_supabase_client()
    now = datetime.now().isoformat()

    # Buscar por email
    result = sb.table("users").select("*").eq("email", email).execute()
    if result.data:
        user = result.data[0]
        # Actualizar last_login
        sb.table("users").update({"last_login": now}).eq("user_id", user["user_id"]).execute()
        user["last_login"] = now
        return user

    # Crear nuevo usuario
    new_user = {
        "user_id": f"user-{uuid.uuid4().hex[:8]}",
        "email": email,
        "name": name,
        "picture": picture,
        "created_at": now,
        "last_login": now,
    }
    sb.table("users").insert(new_user).execute()
    return new_user


def ensure_user_exists(user_id: str) -> None:
    """Asegura que un user_id exista en la tabla users (para el usuario demo u otros)."""
    from services.supabase_client import get_supabase_client

    sb = get_supabase_client()
    result = sb.table("users").select("user_id").eq("user_id", user_id).execute()
    if not result.data:
        now = datetime.now().isoformat()
        sb.table("users").insert({
            "user_id": user_id,
            "email": f"{user_id}@demo.local",
            "name": "Usuario Demo",
            "picture": "",
            "created_at": now,
            "last_login": now,
        }).execute()


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
