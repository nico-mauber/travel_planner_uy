"""Servicio de gestion de conversaciones multiples."""

import json
import os
import uuid
from datetime import datetime
from typing import Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CHATS_FILE = os.path.join(DATA_DIR, "chats.json")


def _load_all_chats() -> list:
    """Carga todos los chats desde JSON."""
    try:
        with open(CHATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return []


def save_chats(chats: list) -> None:
    """Persiste todos los chats en JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CHATS_FILE, "w", encoding="utf-8") as f:
        json.dump(chats, f, ensure_ascii=False, indent=2)


def load_chats(user_id: str) -> list:
    """Carga chats de un usuario, ordenados por last_activity_at desc."""
    all_chats = _load_all_chats()
    user_chats = [c for c in all_chats if c.get("user_id") == user_id]
    user_chats.sort(key=lambda c: c.get("last_activity_at", ""), reverse=True)
    return user_chats


def create_chat(user_id: str, trip_id: Optional[str] = None,
                title: str = "Nueva conversacion") -> dict:
    """Crea un nuevo chat. ID formato chat-{hex8}."""
    now = datetime.now().isoformat()
    new_chat = {
        "chat_id": f"chat-{uuid.uuid4().hex[:8]}",
        "user_id": user_id,
        "trip_id": trip_id,
        "title": title,
        "created_at": now,
        "last_activity_at": now,
        "messages": [],
    }
    all_chats = _load_all_chats()
    all_chats.append(new_chat)
    save_chats(all_chats)
    return new_chat


def get_chat_by_id(chats: list, chat_id: str) -> Optional[dict]:
    """Busca un chat por ID en una lista de chats."""
    for chat in chats:
        if chat["chat_id"] == chat_id:
            return chat
    return None


def delete_chat(chat_id: str, user_id: str = None) -> bool:
    """Elimina un chat por ID. Verifica ownership si user_id proporcionado."""
    all_chats = _load_all_chats()
    for i, chat in enumerate(all_chats):
        if chat["chat_id"] == chat_id:
            if user_id and chat.get("user_id") != user_id:
                return False  # No pertenece al usuario
            all_chats.pop(i)
            save_chats(all_chats)
            return True
    return False


def rename_chat(chat_id: str, new_title: str) -> bool:
    """Renombra un chat. Retorna True si exitoso."""
    all_chats = _load_all_chats()
    for chat in all_chats:
        if chat["chat_id"] == chat_id:
            chat["title"] = new_title
            save_chats(all_chats)
            return True
    return False


def add_message(chat: dict, message: dict) -> None:
    """Agrega un mensaje al chat y actualiza last_activity_at."""
    chat["messages"].append(message)
    chat["last_activity_at"] = datetime.now().isoformat()


def persist_chat(chat: dict) -> None:
    """Persiste un chat individual actualizandolo en el archivo global."""
    all_chats = _load_all_chats()
    for i, c in enumerate(all_chats):
        if c["chat_id"] == chat["chat_id"]:
            all_chats[i] = chat
            save_chats(all_chats)
            return
    # Si no existe, agregarlo
    all_chats.append(chat)
    save_chats(all_chats)


def auto_generate_title(first_message: str) -> str:
    """Genera titulo automatico a partir del primer mensaje (~50 chars)."""
    clean = first_message.strip()
    if len(clean) <= 50:
        return clean
    return clean[:47] + "..."
