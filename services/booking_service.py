"""Servicio de busqueda de hoteles via RapidAPI — Booking.com (DataCrawler)."""

import os
import re
import time
import logging
from typing import Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# ─── Configuracion ───
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = os.environ.get("RAPIDAPI_BOOKING_HOST", "booking-com15.p.rapidapi.com")

# Whitelist de dominios permitidos para llamadas API
_ALLOWED_HOSTS = frozenset({
    "booking-com15.p.rapidapi.com",
    RAPIDAPI_HOST,
})

# Cache simple en memoria {key: {data, ts}}
_cache: dict = {}
_CACHE_TTL = 3600  # 1 hora


def _validate_api_host(host: str) -> bool:
    """Valida que el host esté en la whitelist de dominios permitidos."""
    return host in _ALLOWED_HOSTS


def _sanitize_query_param(value: str) -> str:
    """Sanitiza un parámetro de query que proviene de input del usuario."""
    # Remover caracteres de control y limitar longitud
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', str(value))
    return sanitized[:200].strip()


def _validate_dest_id(dest_id: str) -> bool:
    """Valida que dest_id sea alfanumérico (puede incluir guión/negativo)."""
    return bool(re.match(r'^-?[a-zA-Z0-9_]+$', dest_id))


def _validate_date(date_str: str) -> bool:
    """Valida formato de fecha YYYY-MM-DD."""
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', date_str))


def _headers() -> dict:
    return {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }


def _cache_get(key: str):
    if key in _cache:
        entry = _cache[key]
        if time.time() - entry["ts"] < _CACHE_TTL:
            return entry["data"]
        del _cache[key]
    return None


def _cache_set(key: str, data):
    _cache[key] = {"data": data, "ts": time.time()}


def _make_cache_key(prefix: str, **kwargs) -> str:
    parts = sorted(f"{k}={v}" for k, v in kwargs.items() if v)
    return f"{prefix}:{'|'.join(parts)}"


# ─── API Calls (DataCrawler booking-com15) ───

def search_destinations(query: str) -> list[dict]:
    """Busca destinos en Booking.com por nombre.

    Endpoint: GET /api/v1/hotels/searchDestination?query=...
    Retorna lista de dicts con dest_id (city_ufi), name, country.
    """
    if not RAPIDAPI_KEY:
        return []

    if not _validate_api_host(RAPIDAPI_HOST):
        logger.error("Host no permitido: %s", RAPIDAPI_HOST)
        return []

    query = _sanitize_query_param(query)
    if not query:
        return []

    ck = _make_cache_key("dest", query=query)
    cached = _cache_get(ck)
    if cached is not None:
        return cached

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                f"https://{RAPIDAPI_HOST}/api/v1/hotels/searchDestination",
                headers=_headers(),
                params={"query": query},
            )
            resp.raise_for_status()
            raw = resp.json()

        # DataCrawler devuelve {data: [...]} o directamente [...]
        items = raw.get("data", raw) if isinstance(raw, dict) else raw
        if not isinstance(items, list):
            items = []

        results = []
        for item in items:
            # city_ufi es el dest_id en DataCrawler
            dest_id = str(
                item.get("city_ufi")
                or item.get("dest_id")
                or ""
            )
            if not dest_id:
                continue

            results.append({
                "dest_id": dest_id,
                "dest_type": item.get("dest_type", "city"),
                "name": item.get("name", ""),
                "region": item.get("region", ""),
                "country": item.get("country", ""),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
            })

        _cache_set(ck, results[:5])
        return results[:5]

    except Exception as e:
        logger.warning("Error buscando destinos en Booking.com: %s", e)
        return []


def search_hotels(
    dest_id: str,
    checkin: str,
    checkout: str,
    adults: int = 2,
    search_type: str = "CITY",
    rooms: int = 1,
    limit: int = 5,
    currency: str = "USD",
) -> list[dict]:
    """Busca hoteles por dest_id y fechas.

    Endpoint: GET /api/v1/hotels/searchHotels
    """
    if not RAPIDAPI_KEY:
        return []

    if not _validate_api_host(RAPIDAPI_HOST):
        logger.error("Host no permitido: %s", RAPIDAPI_HOST)
        return []

    if not _validate_dest_id(dest_id):
        logger.warning("dest_id inválido: %s", dest_id)
        return []

    if not _validate_date(checkin) or not _validate_date(checkout):
        logger.warning("Fechas inválidas: checkin=%s, checkout=%s", checkin, checkout)
        return []

    ck = _make_cache_key(
        "hotels", dest_id=dest_id, checkin=checkin,
        checkout=checkout, adults=str(adults),
    )
    cached = _cache_get(ck)
    if cached is not None:
        return cached[:limit]

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                f"https://{RAPIDAPI_HOST}/api/v1/hotels/searchHotels",
                headers=_headers(),
                params={
                    "dest_id": dest_id,
                    "search_type": search_type,
                    "arrival_date": checkin,
                    "departure_date": checkout,
                    "adults": str(adults),
                    "room_qty": str(rooms),
                    "page_number": "1",
                    "currency_code": currency,
                    "languagecode": "es",
                    "units": "metric",
                },
            )
            resp.raise_for_status()
            raw = resp.json()

        # DataCrawler: {data: {hotels: [...]}}
        data = raw.get("data", raw) if isinstance(raw, dict) else {}
        hotel_list = []
        if isinstance(data, dict):
            hotel_list = data.get("hotels", [])
        elif isinstance(data, list):
            hotel_list = data

        results = []
        for entry in hotel_list:
            # DataCrawler anida los datos en entry.property
            prop = entry.get("property", entry)

            # Precio
            price = 0.0
            pb = prop.get("priceBreakdown", {})
            gross = pb.get("grossPrice", {})
            if isinstance(gross, dict):
                price = float(gross.get("value", 0) or 0)
            if not price:
                price = float(prop.get("price", 0) or 0)

            # Review
            review_score = float(prop.get("reviewScore", 0) or 0)
            review_word = prop.get("reviewScoreWord", "")
            review_count = int(prop.get("reviewCount", 0) or 0)

            # Fotos
            photo_urls = prop.get("photoUrls", [])
            photo_url = photo_urls[0] if photo_urls else ""

            # Estrellas
            stars = int(prop.get("propertyClass", 0) or prop.get("class", 0) or 0)

            # Nombre y ubicacion
            name = prop.get("name", "Hotel")
            city = prop.get("wishlistName", prop.get("city", ""))
            address = prop.get("address", "")

            # Checkin/checkout info
            checkin_info = prop.get("checkin", {})
            checkout_info = prop.get("checkout", {})

            results.append({
                "hotel_id": str(prop.get("id", entry.get("hotel_id", ""))),
                "name": name,
                "price": round(price, 2),
                "currency": currency,
                "review_score": review_score,
                "review_word": review_word,
                "review_count": review_count,
                "photo_url": photo_url,
                "stars": stars,
                "address": address,
                "city": city,
                "checkin": checkin,
                "checkout": checkout,
                "checkin_time": checkin_info.get("fromTime", ""),
                "checkout_time": checkout_info.get("untilTime", ""),
                "accessibility_label": entry.get("accessibilityLabel", ""),
            })

        _cache_set(ck, results)
        return results[:limit]

    except Exception as e:
        logger.warning("Error buscando hoteles en Booking.com: %s", e)
        return []


# ─── Funciones de alto nivel ───

def _clean_destination(destination: str) -> str:
    """Limpia el nombre del destino para busqueda: quita años, numeros sueltos, etc."""
    # Quitar años (4 digitos) y numeros sueltos
    cleaned = re.sub(r'\b\d{4}\b', '', destination)
    cleaned = re.sub(r'\b\d+\b', '', cleaned)
    # Quitar espacios multiples
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def search_hotels_for_trip(
    trip: dict,
    query: str = "",
    limit: int = 5,
) -> list[dict]:
    """Busca hoteles usando el contexto del viaje activo."""
    destination = trip.get("destination", "")
    if not destination:
        return []

    # Limpiar destino (quitar años, numeros) y tomar parte antes de la coma
    clean_dest = _clean_destination(destination)
    search_term = clean_dest.split(",")[0].strip()

    if not search_term:
        return []

    # Obtener dest_id
    destinations = search_destinations(search_term)
    if not destinations and "," in clean_dest:
        # Reintentar con nombre completo limpio
        destinations = search_destinations(clean_dest)
    if not destinations:
        return []

    dest = destinations[0]
    checkin = trip.get("start_date", "")
    checkout = trip.get("end_date", "")
    if not checkin or not checkout:
        return []

    return search_hotels(
        dest_id=dest["dest_id"],
        checkin=checkin,
        checkout=checkout,
        search_type=dest.get("dest_type", "CITY").upper(),
        limit=limit,
    )


def format_hotels_as_cards(hotels: list[dict]) -> list[dict]:
    """Convierte resultados de busqueda a formato de cards para el chat."""
    cards = []
    for h in hotels:
        stars = h.get("stars", 0)
        stars_str = "⭐" * stars if stars else ""
        review = h.get("review_score", 0)
        review_word = h.get("review_word", "")
        review_count = h.get("review_count", 0)
        review_str = ""
        if review:
            review_str = f"{review}/10 {review_word}"
            if review_count:
                review_str += f" ({review_count:,} resenas)"
        rating = f"{stars_str} {review_str}".strip()

        # Info de horarios
        notes_parts = []
        if h.get("checkin") and h.get("checkout"):
            notes_parts.append(f"{h['checkin']} → {h['checkout']}")
        if h.get("checkin_time"):
            notes_parts.append(f"Check-in desde {h['checkin_time']}")
        if h.get("checkout_time"):
            notes_parts.append(f"Check-out hasta {h['checkout_time']}")
        notes = " | ".join(notes_parts)

        # Construir URL de Booking.com para el hotel
        hotel_id = h.get("hotel_id", "")
        booking_url = f"https://www.booking.com/hotel/x/{hotel_id}.html" if hotel_id else ""

        cards.append({
            "card_type": "hotel",
            "name": h["name"],
            "provider": "Booking.com",
            "price": h.get("price", 0),
            "location": h.get("city", "") or h.get("address", ""),
            "rating": rating or None,
            "notes": notes,
            "photo_url": h.get("photo_url", ""),
            "booking_url": booking_url,
            "stars": h.get("stars", 0),
            "review_score": h.get("review_score", 0),
            "review_word": h.get("review_word", ""),
            "review_count": h.get("review_count", 0),
            "checkin_time": h.get("checkin_time", ""),
            "checkout_time": h.get("checkout_time", ""),
        })
    return cards


def is_booking_available() -> bool:
    """Verifica si el servicio de Booking.com esta configurado."""
    return bool(RAPIDAPI_KEY)
