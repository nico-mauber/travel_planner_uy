"""Servicio de gestion de conversaciones multiples — Supabase backend."""

import uuid
from datetime import datetime
from typing import Optional


def load_chats(user_id: str) -> list:
    """Carga chats de un usuario desde Supabase, ordenados por last_activity_at desc."""
    from services.supabase_client import get_supabase_client

    sb = get_supabase_client()
    result = sb.table("chats").select("*").eq("user_id", user_id).order(
        "last_activity_at", desc=True
    ).execute()

    chats = []
    for row in (result.data or []):
        chat = _row_to_chat(row)
        # Cargar mensajes de este chat
        msgs_result = sb.table("chat_messages").select("*").eq(
            "chat_id", row["chat_id"]
        ).order("sort_order").execute()
        chat["messages"] = [_row_to_message(m) for m in (msgs_result.data or [])]
        chats.append(chat)

    return chats


def create_chat(user_id: str, trip_id: Optional[str] = None,
                title: str = "Nueva conversacion") -> dict:
    """Crea un nuevo chat. Persiste en Supabase."""
    from services.supabase_client import get_supabase_client

    now = datetime.now().isoformat()
    chat_id = f"chat-{uuid.uuid4().hex[:8]}"

    new_chat = {
        "chat_id": chat_id,
        "user_id": user_id,
        "trip_id": trip_id,
        "title": title,
        "created_at": now,
        "last_activity_at": now,
        "messages": [],
    }

    sb = get_supabase_client()
    chat_row = {
        "chat_id": chat_id,
        "user_id": user_id,
        "trip_id": trip_id,
        "title": title,
    }
    sb.table("chats").insert(chat_row).execute()
    return new_chat


def get_chat_by_id(chats: list, chat_id: str) -> Optional[dict]:
    """Busca un chat por ID en una lista de chats."""
    for chat in chats:
        if chat["chat_id"] == chat_id:
            return chat
    return None


def get_latest_chat_for_trip(user_id: str, trip_id: str) -> Optional[dict]:
    """Obtiene el chat mas reciente para un viaje especifico."""
    from services.supabase_client import get_supabase_client

    sb = get_supabase_client()
    result = sb.table("chats").select("*").eq("user_id", user_id).eq(
        "trip_id", trip_id
    ).order("last_activity_at", desc=True).limit(1).execute()

    if not result.data:
        return None

    chat = _row_to_chat(result.data[0])
    # Cargar mensajes
    msgs_result = sb.table("chat_messages").select("*").eq(
        "chat_id", chat["chat_id"]
    ).order("sort_order").execute()
    chat["messages"] = [_row_to_message(m) for m in (msgs_result.data or [])]
    return chat


def delete_chat(chat_id: str, user_id: str = None) -> bool:
    """Elimina un chat por ID. CASCADE elimina mensajes.

    Requiere user_id para verificar ownership. Si no se proporciona,
    se rechaza la operación por seguridad.
    """
    from services.supabase_client import get_supabase_client

    if not user_id:
        return False

    sb = get_supabase_client()

    # Verificar ownership
    result = sb.table("chats").select("user_id").eq("chat_id", chat_id).execute()
    if not result.data:
        return False
    if result.data[0].get("user_id") != user_id:
        return False

    sb.table("chats").delete().eq("chat_id", chat_id).execute()
    return True


def rename_chat(chat_id: str, new_title: str, user_id: str = None) -> bool:
    """Renombra un chat en Supabase. Verifica ownership si user_id es proporcionado."""
    from services.supabase_client import get_supabase_client

    try:
        sb = get_supabase_client()

        if user_id:
            result = sb.table("chats").select("user_id").eq("chat_id", chat_id).execute()
            if not result.data or result.data[0].get("user_id") != user_id:
                return False

        sb.table("chats").update({"title": new_title}).eq("chat_id", chat_id).execute()
        return True
    except Exception:
        return False


def add_message(chat: dict, message: dict) -> None:
    """Agrega un mensaje al chat en memoria y persiste en Supabase."""
    from services.supabase_client import get_supabase_client

    chat["messages"].append(message)
    now = datetime.now().isoformat()
    chat["last_activity_at"] = now

    sb = get_supabase_client()

    # Calcular sort_order
    sort_order = len(chat["messages"]) - 1

    # Preparar content para JSONB
    content = message.get("content", "")

    msg_row = {
        "chat_id": chat["chat_id"],
        "role": message.get("role", "assistant"),
        "msg_type": message.get("type", "text"),
        "content": content,  # supabase-py serializa a JSONB automáticamente
        "processed": message.get("processed", False),
        "result": message.get("result"),
        "sort_order": sort_order,
    }
    sb.table("chat_messages").insert(msg_row).execute()

    # Actualizar last_activity_at del chat
    sb.table("chats").update({"last_activity_at": now}).eq("chat_id", chat["chat_id"]).execute()


def persist_chat(chat: dict) -> None:
    """Persiste el estado actual de un chat en Supabase.

    Sincroniza mensajes: borra todos los existentes y re-inserta.
    Esto maneja correctamente cambios en mensajes (ej: processed=True).
    """
    from services.supabase_client import get_supabase_client

    sb = get_supabase_client()
    chat_id = chat["chat_id"]

    # Actualizar metadatos del chat
    sb.table("chats").update({
        "title": chat.get("title", "Nueva conversacion"),
        "last_activity_at": chat.get("last_activity_at", datetime.now().isoformat()),
    }).eq("chat_id", chat_id).execute()

    # Re-sincronizar mensajes: borrar y reinsertar
    sb.table("chat_messages").delete().eq("chat_id", chat_id).execute()

    for idx, msg in enumerate(chat.get("messages", [])):
        content = msg.get("content", "")
        msg_row = {
            "chat_id": chat_id,
            "role": msg.get("role", "assistant"),
            "msg_type": msg.get("type", "text"),
            "content": content,
            "processed": msg.get("processed", False),
            "result": msg.get("result"),
            "sort_order": idx,
        }
        sb.table("chat_messages").insert(msg_row).execute()


def auto_generate_title(first_message: str) -> str:
    """Genera titulo automatico a partir del primer mensaje (~50 chars)."""
    clean = first_message.strip()
    if len(clean) <= 50:
        return clean
    return clean[:47] + "..."


# ─── Helpers de conversión ───

def _row_to_chat(row: dict) -> dict:
    """Convierte un row de chats de Supabase a dict de la app."""
    return {
        "chat_id": row["chat_id"],
        "user_id": row.get("user_id", ""),
        "trip_id": row.get("trip_id"),
        "title": row.get("title", "Nueva conversacion"),
        "created_at": str(row.get("created_at", "")),
        "last_activity_at": str(row.get("last_activity_at", "")),
        "messages": [],  # se cargan por separado
    }


def _row_to_message(row: dict) -> dict:
    """Convierte un row de chat_messages de Supabase a dict de la app."""
    content = row.get("content", "")
    # JSONB: si viene como string JSON, dejarlo como está
    # Si es un dict/list, dejarlo como dict/list
    # El campo content en la app puede ser str (para text) o dict (para card/confirmation)

    msg = {
        "role": row.get("role", "assistant"),
        "type": row.get("msg_type", "text"),
        "content": content,
    }

    if row.get("processed"):
        msg["processed"] = True
    if row.get("result"):
        msg["result"] = row["result"]

    return msg
