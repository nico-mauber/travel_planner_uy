"""Script de migración: lee los JSON locales e inserta en Supabase.

Ejecutar desde la raíz del proyecto:
    python scripts/migrate_to_supabase.py

Requiere que el schema ya esté creado en Supabase (scripts/schema.sql)
y que .env tenga SUPABASE_URL y SUPABASE_SERVICE_KEY.
"""

import json
import os
import sys

# Agregar raíz del proyecto al path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT_DIR, ".env"))

from services.supabase_client import get_supabase_client

DATA_DIR = os.path.join(ROOT_DIR, "data")


def _load_json(filename: str):
    """Carga un archivo JSON del directorio data/."""
    path = os.path.join(DATA_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  [SKIP] {filename}: {e}")
        return None


def migrate_users():
    """Migra usuarios desde data/users.json."""
    print("\n--- Migrando usuarios ---")
    data = _load_json("users.json")
    if not data or not isinstance(data, list):
        print("  No hay usuarios para migrar.")
        return

    sb = get_supabase_client()
    for user in data:
        row = {
            "user_id": user["user_id"],
            "email": user.get("email", ""),
            "name": user.get("name", ""),
            "picture": user.get("picture", ""),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login"),
        }
        sb.table("users").upsert(row, on_conflict="user_id").execute()
        print(f"  [OK] Usuario {row['user_id']} ({row['email']})")


def migrate_profiles():
    """Migra perfiles desde data/profiles.json."""
    print("\n--- Migrando perfiles ---")
    data = _load_json("profiles.json")
    if not data or not isinstance(data, dict):
        print("  No hay perfiles para migrar.")
        return

    sb = get_supabase_client()
    for user_id, profile in data.items():
        if not isinstance(profile, dict):
            continue
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
        print(f"  [OK] Perfil de {user_id}")


def migrate_trips():
    """Migra viajes e items desde data/trips.json."""
    print("\n--- Migrando viajes e items ---")
    data = _load_json("trips.json")
    if not data or not isinstance(data, list):
        print("  No hay viajes para migrar.")
        return

    sb = get_supabase_client()

    # Asegurar que el user_id existe en la tabla users
    user_ids_seen = set()

    for trip in data:
        user_id = trip.get("user_id", "user-demo0001")

        # Crear usuario si no existe
        if user_id not in user_ids_seen:
            sb.table("users").upsert(
                {"user_id": user_id, "email": f"{user_id}@demo.local", "name": user_id},
                on_conflict="user_id",
            ).execute()
            user_ids_seen.add(user_id)

        # Insertar trip (sin items)
        trip_row = {
            "id": trip["id"],
            "user_id": user_id,
            "name": trip.get("name", ""),
            "destination": trip.get("destination", ""),
            "start_date": trip.get("start_date"),
            "end_date": trip.get("end_date"),
            "status": trip.get("status", "en_planificacion"),
            "budget_total": float(trip.get("budget_total", 0.0)),
            "notes": trip.get("notes", ""),
        }
        sb.table("trips").upsert(trip_row, on_conflict="id").execute()
        print(f"  [OK] Viaje {trip['id']}: {trip.get('name', '')}")

        # Insertar items
        items = trip.get("items", [])
        for item in items:
            item_row = {
                "id": item["id"],
                "trip_id": trip["id"],
                "name": item.get("name", ""),
                "item_type": item.get("item_type", "actividad"),
                "day": int(item.get("day", 1)),
                "start_time": item.get("start_time", "00:00"),
                "end_time": item.get("end_time", "00:00"),
                "status": item.get("status", "pendiente"),
                "location": item.get("location", ""),
                "address": item.get("address", ""),
                "notes": item.get("notes", ""),
                "cost_estimated": float(item.get("cost_estimated", 0.0)),
                "cost_real": float(item.get("cost_real", 0.0)),
                "booking_url": item.get("booking_url", ""),
                "provider": item.get("provider", ""),
            }
            sb.table("itinerary_items").upsert(item_row, on_conflict="id").execute()
        print(f"       {len(items)} items migrados")


def migrate_chats():
    """Migra chats y mensajes desde data/chats.json."""
    print("\n--- Migrando chats ---")
    data = _load_json("chats.json")
    if not data or not isinstance(data, list):
        print("  No hay chats para migrar.")
        return

    sb = get_supabase_client()
    for chat in data:
        chat_row = {
            "chat_id": chat["chat_id"],
            "user_id": chat.get("user_id", "user-demo0001"),
            "trip_id": chat.get("trip_id"),
            "title": chat.get("title", "Nueva conversacion"),
            "created_at": chat.get("created_at"),
            "last_activity_at": chat.get("last_activity_at"),
        }
        # trip_id puede ser None si el viaje fue eliminado
        if chat_row["trip_id"]:
            # Verificar que el trip existe
            check = sb.table("trips").select("id").eq("id", chat_row["trip_id"]).execute()
            if not check.data:
                chat_row["trip_id"] = None

        sb.table("chats").upsert(chat_row, on_conflict="chat_id").execute()
        print(f"  [OK] Chat {chat['chat_id']}: {chat.get('title', '')}")

        # Insertar mensajes
        messages = chat.get("messages", [])
        for idx, msg in enumerate(messages):
            content = msg.get("content", "")
            # JSONB: si content es string, envolver en JSON
            if isinstance(content, str):
                content_jsonb = json.dumps(content)
            else:
                content_jsonb = json.dumps(content)

            msg_row = {
                "chat_id": chat["chat_id"],
                "role": msg.get("role", "assistant"),
                "msg_type": msg.get("type", "text"),
                "content": content,  # supabase-py maneja la serialización JSONB
                "processed": msg.get("processed", False),
                "result": msg.get("result"),
                "sort_order": idx,
            }
            sb.table("chat_messages").insert(msg_row).execute()
        print(f"       {len(messages)} mensajes migrados")


def migrate_feedbacks():
    """Migra feedbacks desde data/feedbacks.json."""
    print("\n--- Migrando feedbacks ---")
    data = _load_json("feedbacks.json")
    if not data or not isinstance(data, dict):
        print("  No hay feedbacks para migrar.")
        return

    sb = get_supabase_client()
    for trip_id, feedback in data.items():
        if not isinstance(feedback, dict):
            continue

        # Verificar que el trip existe
        check = sb.table("trips").select("id").eq("id", trip_id).execute()
        if not check.data:
            print(f"  [SKIP] Feedback para trip {trip_id} — viaje no encontrado")
            continue

        row = {
            "trip_id": trip_id,
            "overall_rating": int(feedback.get("overall_rating", 0)),
            "comment": feedback.get("comment", ""),
            "item_feedbacks": feedback.get("item_feedbacks", []),
            "skipped": feedback.get("skipped", False),
        }
        sb.table("feedbacks").upsert(row, on_conflict="trip_id").execute()
        print(f"  [OK] Feedback para trip {trip_id}")


def main():
    print("=" * 60)
    print("  MIGRACION JSON → SUPABASE")
    print("=" * 60)

    try:
        sb = get_supabase_client()
        print("\n[OK] Conexion a Supabase exitosa")
    except Exception as e:
        print(f"\n[ERROR] No se pudo conectar a Supabase: {e}")
        sys.exit(1)

    migrate_users()
    migrate_profiles()
    migrate_trips()
    migrate_chats()
    migrate_feedbacks()

    print("\n" + "=" * 60)
    print("  MIGRACION COMPLETADA")
    print("=" * 60)


if __name__ == "__main__":
    main()
