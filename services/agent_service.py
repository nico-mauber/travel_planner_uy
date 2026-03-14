"""Servicio del agente — LLM (Gemini) con fallback a pattern matching mock."""

import os
import uuid
import re
from typing import Optional

from config.settings import ItemType, ItemStatus

# ─── Detectar si el LLM está disponible ───
_USE_LLM = bool(os.environ.get("GOOGLE_API_KEY"))

if _USE_LLM:
    try:
        from services.llm_agent_service import process_message_llm, LLM_AVAILABLE
        _USE_LLM = LLM_AVAILABLE
    except ImportError:
        _USE_LLM = False


def is_llm_active() -> bool:
    """Retorna True si el LLM está activo."""
    return _USE_LLM


def process_message(message: str, trip: Optional[dict] = None) -> dict:
    """Procesa un mensaje del usuario. Usa LLM si disponible, sino mock.

    Retorna dict con:
      - role: "assistant"
      - type: "text" | "card" | "confirmation"
      - content: str (texto) o dict (datos de tarjeta/confirmación)
    """
    msg = message.lower().strip()

    # ─── Acciones que SIEMPRE pasan por el mock (requieren confirmación UI) ───

    # Sin viaje activo — crear viaje
    if trip is None:
        match = re.search(r"viajar\s+a\s+(.+?)(?:\s+en\s+|\s*$)", msg)
        if match:
            destination = match.group(1).strip().title()
            return {
                "role": "assistant",
                "type": "confirmation",
                "content": {
                    "action": "create_trip",
                    "summary": f"Crear nuevo viaje a {destination}",
                    "details": {
                        "destination": destination,
                        "name": f"Viaje a {destination}",
                    },
                },
            }

    # Agregar item — siempre confirmación
    if trip and any(w in msg for w in ["agregar", "añadir", "agrega", "añade"]):
        return _add_item_response(msg, trip)

    # Eliminar item — siempre confirmación
    if trip and any(w in msg for w in ["eliminar", "quitar", "elimina", "quita", "borrar"]):
        return _remove_item_response(msg, trip)

    # ─── Para todo lo demás, usar LLM si disponible ───
    if _USE_LLM:
        try:
            import streamlit as st
            user_profile = st.session_state.get("user_profile")
            return process_message_llm(message, trip, user_profile)
        except Exception:
            pass  # Fallback al mock

    # ─── Fallback: pattern matching mock ───
    return _mock_process_message(msg, trip)


def _mock_process_message(msg: str, trip: Optional[dict]) -> dict:
    """Procesamiento mock por pattern matching."""
    if trip is None:
        return {
            "role": "assistant",
            "type": "text",
            "content": (
                "¡Hola! Soy tu asistente de viajes. "
                "Para empezar, dime a dónde te gustaría viajar. "
                'Por ejemplo: "Quiero viajar a París en mayo".'
            ),
        }

    if any(w in msg for w in ["vuelo", "volar", "avión", "avion"]):
        return _flight_response(trip)

    if any(w in msg for w in ["hotel", "alojamiento", "hospedaje", "hostel"]):
        return _hotel_response(trip)

    if any(w in msg for w in ["actividad", "visitar", "conocer", "museo", "tour"]):
        return _activity_response(trip)

    if any(w in msg for w in ["restaurante", "comer", "cenar", "almorzar", "comida"]):
        return _food_response(trip)

    if any(w in msg for w in ["presupuesto", "costo", "precio", "cuánto", "cuanto"]):
        return _budget_response(trip)

    if any(w in msg for w in ["clima", "tiempo", "temperatura"]):
        return _weather_response(trip)

    if any(w in msg for w in ["hola", "hi", "buenas", "buen dia", "buenos dias"]):
        return {
            "role": "assistant",
            "type": "text",
            "content": (
                f"¡Hola! Estoy aquí para ayudarte con tu viaje a "
                f"{trip['destination']}. Puedo buscar vuelos, hoteles, "
                f"actividades, restaurantes, o modificar tu itinerario. "
                f"¿En qué te puedo ayudar?"
            ),
        }

    return {
        "role": "assistant",
        "type": "text",
        "content": (
            f"Entiendo. Estoy trabajando en tu viaje a {trip['destination']}. "
            "Puedo ayudarte con:\n"
            "- Buscar **vuelos** o **alojamiento**\n"
            "- Sugerir **actividades** o **restaurantes**\n"
            "- **Agregar** o **eliminar** items del itinerario\n"
            "- Consultar **presupuesto** o **clima**\n\n"
            "¿Qué te gustaría hacer?"
        ),
    }


def _flight_response(trip: dict) -> dict:
    dest = trip["destination"]
    return {
        "role": "assistant",
        "type": "card",
        "content": {
            "card_type": "flight",
            "name": f"Vuelo directo a {dest}",
            "provider": "LATAM Airlines",
            "price": 650.0,
            "departure": "08:00",
            "arrival": "14:30",
            "duration": "6h 30m",
            "notes": f"Vuelo directo Montevideo → {dest}",
        },
    }


def _hotel_response(trip: dict) -> dict:
    dest = trip["destination"]
    return {
        "role": "assistant",
        "type": "card",
        "content": {
            "card_type": "hotel",
            "name": f"Hotel Boutique {dest.split(',')[0]}",
            "provider": "Booking.com",
            "price": 120.0,
            "location": f"Centro de {dest.split(',')[0]}",
            "rating": "4.5 ★",
            "notes": "Habitación doble con desayuno incluido",
        },
    }


def _activity_response(trip: dict) -> dict:
    dest = trip["destination"]
    return {
        "role": "assistant",
        "type": "card",
        "content": {
            "card_type": "activity",
            "name": f"Tour cultural por {dest.split(',')[0]}",
            "provider": "GetYourGuide",
            "price": 35.0,
            "duration": "3 horas",
            "location": f"Centro histórico de {dest.split(',')[0]}",
            "notes": "Tour guiado en español — incluye entradas a monumentos principales",
        },
    }


def _food_response(trip: dict) -> dict:
    dest = trip["destination"]
    return {
        "role": "assistant",
        "type": "card",
        "content": {
            "card_type": "food",
            "name": f"Restaurante típico de {dest.split(',')[0]}",
            "provider": "TripAdvisor",
            "price": 30.0,
            "location": f"Zona gastronómica de {dest.split(',')[0]}",
            "rating": "4.3 ★",
            "notes": "Cocina local auténtica — reservas recomendadas",
        },
    }


def _add_item_response(msg: str, trip: dict) -> dict:
    return {
        "role": "assistant",
        "type": "confirmation",
        "content": {
            "action": "add_item",
            "summary": "Agregar actividad al itinerario",
            "details": {
                "name": "Nueva actividad",
                "item_type": ItemType.ACTIVITY.value,
                "day": 1,
                "start_time": "10:00",
                "end_time": "12:00",
                "cost_estimated": 25.0,
                "location": trip["destination"].split(",")[0],
            },
        },
    }


def _remove_item_response(msg: str, trip: dict) -> dict:
    # Intentar encontrar qué item quiere eliminar
    items = trip.get("items", [])
    if items:
        last_item = items[-1]
        return {
            "role": "assistant",
            "type": "confirmation",
            "content": {
                "action": "remove_item",
                "summary": f"Eliminar '{last_item['name']}' del itinerario",
                "details": {
                    "item_id": last_item["id"],
                    "item_name": last_item["name"],
                },
            },
        }
    return {
        "role": "assistant",
        "type": "text",
        "content": "No hay items en el itinerario para eliminar.",
    }


def _budget_response(trip: dict) -> dict:
    total = sum(
        item.get("cost_estimated", 0)
        for item in trip.get("items", [])
        if item.get("status") != ItemStatus.SUGGESTED.value
    )
    return {
        "role": "assistant",
        "type": "text",
        "content": (
            f"El presupuesto estimado total de tu viaje a {trip['destination']} "
            f"es de **USD {total:,.0f}**.\n\n"
            "Puedes ver el desglose completo en la sección de Presupuesto."
        ),
    }


def _weather_response(trip: dict) -> dict:
    from services.weather_service import get_weather
    weather = get_weather(trip["destination"])
    return {
        "role": "assistant",
        "type": "text",
        "content": (
            f"{weather['icon']} **Clima en {trip['destination']}**\n\n"
            f"Temperatura: {weather['temp_min']}°C — {weather['temp_max']}°C\n"
            f"Condición: {weather['condition']}\n"
            f"{weather['description']}"
        ),
    }


def apply_confirmed_action(action: dict, trip: dict, trips: list) -> str:
    """Aplica una acción confirmada por el usuario. Retorna mensaje de resultado."""
    from services.trip_service import sync_trip_changes, create_trip

    action_type = action.get("action")
    details = action.get("details", {})

    if action_type == "add_item":
        new_item = {
            "id": f"item-{uuid.uuid4().hex[:8]}",
            "trip_id": trip["id"],
            "name": details.get("name", "Item sin nombre"),
            "item_type": details.get("item_type", ItemType.ACTIVITY.value),
            "day": details.get("day", 1),
            "start_time": details.get("start_time", "10:00"),
            "end_time": details.get("end_time", "12:00"),
            "status": ItemStatus.PENDING.value,
            "location": details.get("location", ""),
            "address": details.get("address", ""),
            "notes": details.get("notes", ""),
            "cost_estimated": details.get("cost_estimated", 0.0),
            "cost_real": 0.0,
            "booking_url": "",
            "provider": details.get("provider", ""),
        }
        trip["items"].append(new_item)
        sync_trip_changes(trips, trip)
        return f"✅ Se agregó '{new_item['name']}' al Día {new_item['day']} del itinerario."

    elif action_type == "remove_item":
        item_id = details.get("item_id")
        item_name = details.get("item_name", "item")
        for i, item in enumerate(trip["items"]):
            if item["id"] == item_id:
                trip["items"].pop(i)
                sync_trip_changes(trips, trip)
                return f"✅ Se eliminó '{item_name}' del itinerario."
        return "❌ No se encontró el item a eliminar."

    elif action_type == "create_trip":
        # Esto se maneja de forma especial en el chat
        return "✅ Viaje creado exitosamente."

    return "❌ Acción no reconocida."
