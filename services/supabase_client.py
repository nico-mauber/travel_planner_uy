"""Cliente Supabase — Singleton que lee credenciales de .env."""

import os
from typing import Optional

_client = None


def get_supabase_client():
    """Retorna el cliente Supabase (singleton). Requiere SUPABASE_URL y SUPABASE_SERVICE_KEY en .env."""
    global _client
    if _client is not None:
        return _client

    from supabase import create_client, Client

    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")

    if not url or not key:
        raise RuntimeError(
            "Faltan variables de entorno SUPABASE_URL y/o SUPABASE_SERVICE_KEY. "
            "Verificar el archivo .env"
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
