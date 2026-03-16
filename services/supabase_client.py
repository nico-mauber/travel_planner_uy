"""Cliente Supabase — Singleton que lee credenciales de .env o st.secrets (Cloud)."""

import os
from typing import Optional

_client = None


def _get_env_or_secret(key: str) -> str:
    """Lee una variable de os.environ (.env local) o st.secrets (Streamlit Cloud)."""
    val = os.environ.get(key, "")
    if val:
        return val
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
    except Exception:
        pass
    return val or ""


def get_supabase_client():
    """Retorna el cliente Supabase (singleton). Requiere SUPABASE_URL y SUPABASE_SERVICE_KEY."""
    global _client
    if _client is not None:
        return _client

    from supabase import create_client, Client

    url = _get_env_or_secret("SUPABASE_URL")
    key = _get_env_or_secret("SUPABASE_SERVICE_KEY")

    if not url or not key:
        raise RuntimeError(
            "Faltan SUPABASE_URL y/o SUPABASE_SERVICE_KEY. "
            "Configurar en .env (local) o en Streamlit Cloud Secrets (produccion)."
        )

    _client = create_client(url, key)
    return _client


def is_supabase_available() -> bool:
    """Verifica si Supabase esta configurado y accesible."""
    try:
        client = get_supabase_client()
        # Test de conectividad: query liviana
        client.table("users").select("user_id").limit(1).execute()
        return True
    except Exception:
        return False
