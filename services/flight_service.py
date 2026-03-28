"""Servicio de busqueda de vuelos — SerpAPI (Google Flights) + fast-flights fallback."""

import os
import re
import time
import logging
import unicodedata
from typing import Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

# ─── Deteccion de backends disponibles ───

# Backend 1: SerpAPI (primario — API REST estable, datos reales de Google Flights)
_SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")
_SERPAPI_AVAILABLE = bool(_SERPAPI_KEY)

# Backend 2: fast-flights (fallback — scraper directo de Google Flights, sin API key)
_FAST_FLIGHTS_AVAILABLE = False
try:
    from fast_flights import (
        FlightData,
        Passengers,
        get_flights as _ff_get_flights,
    )
    _FAST_FLIGHTS_AVAILABLE = True
except ImportError:
    pass

# Whitelist de dominios permitidos para llamadas API (SerpAPI fallback)
_ALLOWED_HOSTS = frozenset({
    "serpapi.com",
})

# Cache simple en memoria {key: {data, ts}}
_cache: dict = {}
_CACHE_TTL = 1800  # 30 min

# ─── Mapeo de clases de cabina ───

_SEAT_MAP = {
    "economy": "economy",
    "premium_economy": "premium-economy",
    "business": "business",
    "first": "first",
}

# ─── Helpers ───

def _strip_accents(s: str) -> str:
    """Elimina acentos/diacriticos de un string (ej: Brasília → Brasilia)."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


# ─── Base de datos de aeropuertos (airportsdata: 7800+ aeropuertos) ───

def _build_airport_index() -> dict[str, str]:
    """Construye indice invertido city_normalized → IATA desde airportsdata.

    Incluye aliases manuales para nombres en espanol y variantes comunes
    que no estan en el dataset (ej: "manaos", "cdmx", "londres").
    """
    try:
        import airportsdata
        raw = airportsdata.load("IATA")
    except ImportError:
        logger.warning("airportsdata no instalado. Usando indice vacio.")
        raw = {}

    # Overrides curados: aeropuertos principales de ciudades ambiguas + nombres en espanol.
    # Estos tienen PRIORIDAD sobre el dataset (que puede tener aeropuertos menores primero).
    _OVERRIDES = {
        # Ciudades con multiples aeropuertos — forzar el principal
        "montevideo": "MVD", "buenos aires": "EZE", "roma": "FCO",
        "rome": "FCO", "lima": "LIM", "manila": "MNL", "paris": "CDG",
        "london": "LHR", "new york": "JFK", "moscow": "SVO",
        "sao paulo": "GRU", "rio de janeiro": "GIG", "houston": "IAH",
        "chicago": "ORD", "washington": "IAD", "san francisco": "SFO",
        "tokyo": "NRT", "osaka": "KIX", "seoul": "ICN", "shanghai": "PVG",
        "beijing": "PEK", "milan": "MXP", "stockholm": "ARN",
        # Destinos turisticos con nombre diferente en el dataset
        "bali": "DPS", "ushuaia": "USH", "machu picchu": "CUZ",
        "punta cana": "PUJ", "playa del carmen": "CUN",
        "riviera maya": "CUN", "costa amalfitana": "NAP",
        # Espanol y variantes no presentes en el dataset
        "manaos": "MAO", "cdmx": "MEX", "ciudad de mexico": "MEX",
        "londres": "LHR", "viena": "VIE", "atenas": "ATH", "praga": "PRG",
        "varsovia": "WAW", "copenhague": "CPH", "estocolmo": "ARN",
        "bruselas": "BRU", "bucarest": "OTP", "edimburgo": "EDI",
        "niza": "NCE", "marsella": "MRS", "venecia": "VCE", "napoles": "NAP",
        "estambul": "IST", "nueva york": "JFK", "nueva delhi": "DEL",
        "pekin": "PEK", "tokio": "NRT", "singapur": "SIN", "seul": "ICN",
        "el cairo": "CAI", "johannesburgo": "JNB", "ciudad del cabo": "CPT",
        "la habana": "HAV", "punta del este": "PDP", "santiago de chile": "SCL",
        "san jose costa rica": "SJO", "cordoba argentina": "COR",
        "salvador bahia": "SSA", "lisboa": "LIS", "sevilla": "SVQ",
        "malaga": "AGP", "bilbao": "BIO",
    }

    # 1. Empezar con overrides curados (prioridad maxima)
    index: dict[str, str] = dict(_OVERRIDES)

    # 2. Rellenar desde dataset (solo ciudades que NO estan en overrides)
    for iata, info in raw.items():
        city = info.get("city", "")
        if not city:
            continue
        normalized = _strip_accents(city.strip().lower())
        if normalized not in index:
            index[normalized] = iata

    logger.info("[flights] Indice de aeropuertos construido: %d entradas", len(index))
    return index


# Inicializar indice al importar el modulo (una sola vez)
_AIRPORT_INDEX = _build_airport_index()


def _sanitize_query_param(value: str) -> str:
    """Sanitiza un parametro de query que proviene de input del usuario."""
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', str(value))
    return sanitized[:200].strip()


def _validate_date(date_str: str) -> bool:
    """Valida formato de fecha YYYY-MM-DD."""
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', date_str))


def _validate_iata(code: str) -> bool:
    """Valida que sea un codigo IATA (2-4 letras mayusculas)."""
    return bool(re.match(r'^[A-Z]{2,4}$', code))


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


def get_airport_code(city_name: str) -> str:
    """Mapea nombre de ciudad a codigo IATA usando base de datos de 7800+ aeropuertos.

    Normaliza acentos (Brasília → brasilia → BSB).
    Busca exacto, luego parcial (substring).
    Si no encuentra, retorna el string en mayusculas como fallback.
    """
    if not city_name:
        return ""
    normalized = _strip_accents(city_name.strip().lower())
    # Busqueda exacta
    if normalized in _AIRPORT_INDEX:
        return _AIRPORT_INDEX[normalized]
    # Si ya parece un codigo IATA, retornarlo en mayusculas
    upper = _strip_accents(city_name.strip().upper())
    if _validate_iata(upper):
        return upper
    # Busqueda parcial (primera coincidencia)
    for key, code in _AIRPORT_INDEX.items():
        if normalized in key or key in normalized:
            return code
    return upper


def _parse_price(price_str: str) -> float:
    """Extrae valor numerico de un string de precio (ej: '$450', 'US$1,234')."""
    if not price_str:
        return 0.0
    cleaned = re.sub(r'[^\d.,]', '', str(price_str))
    # Manejar formato con coma como separador de miles
    if ',' in cleaned and '.' in cleaned:
        cleaned = cleaned.replace(',', '')
    elif ',' in cleaned:
        # Podria ser separador decimal o de miles
        parts = cleaned.split(',')
        if len(parts[-1]) == 2:
            cleaned = cleaned.replace(',', '.')
        else:
            cleaned = cleaned.replace(',', '')
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0


def _build_google_flights_url(
    origin: str, destination: str, departure_date: str,
    return_date: str = "", cabin_class: str = "economy",
    adults: int = 1,
) -> str:
    """Construye una URL de Google Flights para reservar."""
    base = "https://www.google.com/travel/flights"
    params = f"?q=Flights+from+{quote(origin)}+to+{quote(destination)}"
    params += f"+on+{departure_date}"
    if return_date:
        params += f"+return+{return_date}"
    return base + params


# ─── Busqueda via fast-flights (fallback) ───

def _search_fast_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str = "",
    adults: int = 1,
    cabin_class: str = "economy",
    max_results: int = 5,
) -> list[dict]:
    """Busqueda de vuelos usando fast-flights (scraper de Google Flights)."""
    if not _FAST_FLIGHTS_AVAILABLE:
        return []

    seat = _SEAT_MAP.get(cabin_class, "economy")

    # Construir solo ida (mas confiable en fast-flights)
    flight_data_list = [
        FlightData(
            date=departure_date,
            from_airport=origin,
            to_airport=destination,
        )
    ]

    result = None
    # Intentar primero round-trip si hay fecha de retorno, luego one-way como fallback
    trip_types = []
    if return_date:
        flight_data_rt = flight_data_list + [
            FlightData(
                date=return_date,
                from_airport=destination,
                to_airport=origin,
            )
        ]
        trip_types.append(("round-trip", flight_data_rt))
    trip_types.append(("one-way", flight_data_list))

    for trip_type, fd_list in trip_types:
        try:
            result = _ff_get_flights(
                flight_data=fd_list,
                trip=trip_type,
                passengers=Passengers(adults=adults),
                seat=seat,
            )
            if result and result.flights:
                logger.info("fast-flights %s: %d vuelos encontrados", trip_type, len(result.flights))
                break
            logger.info("fast-flights %s: sin resultados, intentando siguiente", trip_type)
            result = None
        except Exception as e:
            # fast-flights puede fallar si Google bloquea el scraping
            err_preview = str(e)[:120]
            logger.warning("fast-flights %s fallo: %s", trip_type, err_preview)
            result = None
            continue

    if result is None:
        return []

    flights = []
    for flight in (result.flights or [])[:max_results]:
        # Parsear stops (puede ser int, str numerico, "Unknown", o None)
        raw_stops = flight.stops
        try:
            stops = int(raw_stops) if raw_stops is not None else 0
        except (ValueError, TypeError):
            stops = 1 if raw_stops else 0  # Asumir 1 escala si es "Unknown"
        stop_text = "Directo" if stops == 0 else f"{stops} escala(s)"

        flights.append({
            "airline": flight.name or "",
            "flight_number": "",
            "departure_time": flight.departure or "",
            "arrival_time": flight.arrival or "",
            "duration": flight.duration or "",
            "stops": stops,
            "stop_details": stop_text,
            "price": _parse_price(flight.price),
            "price_raw": flight.price or "",
            "cabin_class": cabin_class,
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "booking_url": _build_google_flights_url(
                origin, destination, departure_date, return_date,
                cabin_class, adults,
            ),
            "is_best": flight.is_best,
            "arrival_time_ahead": flight.arrival_time_ahead or "",
            "delay": flight.delay or "",
            "_source": "fast-flights",
        })

    return flights


# ─── Busqueda via SerpAPI (fallback) ───

def _search_serpapi(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str = "",
    adults: int = 1,
    cabin_class: str = "economy",
    max_results: int = 5,
) -> list[dict]:
    """Busqueda de vuelos usando SerpAPI Google Flights endpoint."""
    api_key = os.environ.get("SERPAPI_KEY", "")
    if not api_key:
        return []

    try:
        import httpx
    except ImportError:
        logger.warning("httpx no disponible para SerpAPI fallback")
        return []

    # Mapeo de cabin class para SerpAPI
    serpapi_cabin_map = {
        "economy": "1",
        "premium_economy": "2",
        "business": "3",
        "first": "4",
    }
    cabin_code = serpapi_cabin_map.get(cabin_class, "1")

    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": departure_date,
        "adults": str(adults),
        "travel_class": cabin_code,
        "currency": "USD",
        "hl": "es",
        "api_key": api_key,
        "stops": "0",            # cualquier cantidad de escalas
        "deep_search": "true",   # carga completa (rutas con conexiones)
    }
    if return_date:
        params["return_date"] = return_date
        params["type"] = "1"  # round trip
    else:
        params["type"] = "2"  # one way

    ck = _make_cache_key(
        "serpapi_flights", origin=origin, destination=destination,
        departure_date=departure_date, return_date=return_date,
        adults=str(adults), cabin_class=cabin_class,
    )
    cached = _cache_get(ck)
    if cached is not None:
        return cached[:max_results]

    try:
        with httpx.Client(timeout=35) as client:
            resp = client.get(
                "https://serpapi.com/search",
                params=params,
            )
            resp.raise_for_status()
            raw = resp.json()
    except Exception as e:
        logger.warning("Error en SerpAPI Google Flights: %s", e)
        return []

    # Parsear resultados de SerpAPI
    best_flights = raw.get("best_flights", [])
    other_flights = raw.get("other_flights", [])
    all_results = best_flights + other_flights
    logger.info("[serpapi] Response keys: %s", list(raw.keys()))
    logger.info("[serpapi] best_flights=%d, other_flights=%d, total=%d",
                len(best_flights), len(other_flights), len(all_results))
    if not all_results:
        # Loguear mensaje de error de SerpAPI si existe
        error_msg = raw.get("error") or raw.get("search_information", {}).get("flight_results_state", "")
        logger.warning("[serpapi] Sin resultados. error=%s, raw_preview=%s",
                      error_msg, str(raw)[:500])

    flights = []
    for group in all_results[:max_results]:
        flight_legs = group.get("flights", [])
        if not flight_legs:
            continue

        first_leg = flight_legs[0]
        last_leg = flight_legs[-1]

        # Airline info
        airline = first_leg.get("airline", "")
        flight_number = first_leg.get("flight_number", "")

        # Times
        dep_time = first_leg.get("departure_airport", {}).get("time", "")
        arr_time = last_leg.get("arrival_airport", {}).get("time", "")

        # Duration
        total_duration = group.get("total_duration", 0)
        hours = total_duration // 60
        minutes = total_duration % 60
        duration_str = f"{hours}h {minutes}m" if total_duration else ""

        # Stops
        stops = len(flight_legs) - 1
        stop_details = "Directo"
        if stops > 0:
            layover_info = group.get("layovers", [])
            parts = []
            for layover in layover_info:
                lay_id = layover.get("id", "")  # código IATA si existe
                lay_name = layover.get("name", "")
                lay_dur = layover.get("duration", 0)
                lay_h = lay_dur // 60
                lay_m = lay_dur % 60
                # Usar código IATA si está disponible, sino abreviar nombre
                display_name = lay_id if lay_id else lay_name.split(",")[0].split("(")[0].strip()[:15]
                parts.append(f"{display_name} ({lay_h}h {lay_m}m)")
            stop_details = f"{stops} escala(s)"
            if parts:
                stop_details += ": " + ", ".join(parts)

        # Price
        price = float(group.get("price", 0) or 0)

        flights.append({
            "airline": airline,
            "flight_number": flight_number,
            "departure_time": dep_time,
            "arrival_time": arr_time,
            "duration": duration_str,
            "stops": stops,
            "stop_details": stop_details,
            "price": price,
            "price_raw": f"${price:.0f}" if price else "",
            "cabin_class": cabin_class,
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "booking_url": _build_google_flights_url(
                origin, destination, departure_date, return_date,
                cabin_class, adults,
            ),
            "is_best": group in best_flights,
            "arrival_time_ahead": "",
            "delay": "",
            "_source": "serpapi",
        })

    _cache_set(ck, flights)
    return flights[:max_results]


# ─── API Publica ───

def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str = "",
    adults: int = 1,
    cabin_class: str = "economy",
    max_results: int = 5,
) -> list[dict]:
    """Busca vuelos y retorna lista de resultados.

    Cada resultado es un dict con:
    - airline: str (nombre de aerolinea)
    - flight_number: str (si disponible)
    - departure_time: str (HH:MM)
    - arrival_time: str (HH:MM)
    - duration: str (ej: "12h 30m")
    - stops: int (0=directo, 1=una escala, etc.)
    - stop_details: str (ej: "Escala en Miami (2h)")
    - price: float (USD)
    - cabin_class: str
    - origin: str (codigo IATA)
    - destination: str (codigo IATA)
    - departure_date: str
    - return_date: str (si aplica)
    - booking_url: str (URL de Google Flights para reservar)

    Intenta primero con SerpAPI (API estable, datos reales de Google Flights).
    Si falla, usa fast-flights (scraper directo de Google Flights) como fallback.
    Si ninguno esta disponible, retorna lista vacia.
    """
    # Validar inputs
    origin = _sanitize_query_param(origin).upper()
    destination = _sanitize_query_param(destination).upper()

    if not origin or not destination:
        logger.warning("Origen o destino vacio: origin=%s, destination=%s", origin, destination)
        return []

    if not _validate_date(departure_date):
        logger.warning("Fecha de salida invalida: %s", departure_date)
        return []

    if return_date and not _validate_date(return_date):
        logger.warning("Fecha de retorno invalida: %s", return_date)
        return []

    if cabin_class not in _SEAT_MAP:
        cabin_class = "economy"

    adults = max(1, min(adults, 9))

    # Verificar cache (compartido entre backends)
    ck = _make_cache_key(
        "flights", origin=origin, destination=destination,
        departure_date=departure_date, return_date=return_date,
        adults=str(adults), cabin_class=cabin_class,
    )
    cached = _cache_get(ck)
    if cached is not None:
        return cached[:max_results]

    # Backend 1: SerpAPI (primario — API estable, datos reales)
    results = []
    serpapi_key = os.environ.get("SERPAPI_KEY", "")
    if serpapi_key:
        results = _search_serpapi(
            origin, destination, departure_date, return_date,
            adults, cabin_class, max_results,
        )

    # Backend 2: fast-flights (fallback — scraper directo)
    if not results and _FAST_FLIGHTS_AVAILABLE:
        results = _search_fast_flights(
            origin, destination, departure_date, return_date,
            adults, cabin_class, max_results,
        )

    if results:
        _cache_set(ck, results)

    return results[:max_results]


def search_flights_for_trip(
    trip: dict,
    origin: str = "",
    destination_city: str = "",
    origin_iata: str = "",
    dest_iata: str = "",
    max_results: int = 5,
) -> list[dict]:
    """Busca vuelos usando el contexto del viaje activo.

    Args:
        trip: dict del viaje con destination, start_date, end_date
        origin: ciudad de origen (extraida por el LLM)
        destination_city: ciudad con aeropuerto mas cercana al destino (extraida por el LLM)
        origin_iata: codigo IATA de origen extraido por el LLM (prioridad sobre lookup)
        dest_iata: codigo IATA de destino extraido por el LLM (prioridad sobre lookup)
        max_results: cantidad maxima de vuelos a retornar
    """
    if not origin and not origin_iata:
        return []

    # Prioridad: IATA del LLM > lookup por ciudad > fallback trip destination
    origin_code = origin_iata if origin_iata and _validate_iata(origin_iata) else get_airport_code(origin) if origin else ""
    dest_code = dest_iata if dest_iata and _validate_iata(dest_iata) else ""
    if not dest_code:
        dest_search = destination_city or trip.get("destination", "")
        dest_code = get_airport_code(dest_search) if dest_search else ""

    logger.info("[flights] origin='%s' iata_llm='%s' -> %s | dest_city='%s' iata_llm='%s' -> %s (trip='%s')",
                origin, origin_iata, origin_code, destination_city, dest_iata, dest_code,
                trip.get("destination", ""))

    departure_date = trip.get("start_date", "")
    return_date = trip.get("end_date", "")

    if not departure_date:
        return []

    return search_flights(
        origin=origin_code,
        destination=dest_code,
        departure_date=departure_date,
        return_date=return_date,
        max_results=max_results,
    )


def format_flights_as_cards(flights: list[dict]) -> list[dict]:
    """Convierte resultados de busqueda a formato de cards para el chat.

    Formato de salida (cada card):
    {
        "card_type": "flight",
        "name": "Vuelo EZE -> BCN",
        "provider": "Aerolineas Argentinas",
        "departure": "08:30",
        "arrival": "14:45",
        "duration": "12h 15m",
        "price": 450.0,
        "location": "EZE -> BCN",
        "notes": "Directo | Economica",
        "rating": None,
        "booking_url": "https://www.google.com/travel/flights/..."
    }
    """
    cards = []
    for f in flights:
        origin = f.get("origin", "")
        destination = f.get("destination", "")
        airline = f.get("airline", "")
        flight_num = f.get("flight_number", "")

        # Nombre de la card
        route = f"{origin} -> {destination}" if origin and destination else ""
        name = f"Vuelo {route}" if route else "Vuelo"
        if airline:
            name = f"{airline} ({route})" if route else airline

        # Notas: escalas + clase
        cabin_labels = {
            "economy": "Economica",
            "premium_economy": "Premium Economy",
            "business": "Business",
            "first": "Primera Clase",
        }
        cabin_label = cabin_labels.get(f.get("cabin_class", "economy"), "Economica")
        stop_text = f.get("stop_details", "")
        notes_parts = []
        if stop_text:
            notes_parts.append(stop_text)
        notes_parts.append(cabin_label)
        if flight_num:
            notes_parts.append(f"Vuelo {flight_num}")
        if f.get("arrival_time_ahead"):
            notes_parts.append(f"+{f['arrival_time_ahead']}")
        notes = " | ".join(notes_parts)

        # Precio formateado
        price = f.get("price", 0.0)
        price_display = f.get("price_raw", "")
        if not price_display and price:
            price_display = f"US${price:,.0f}"

        cards.append({
            "card_type": "flight",
            "name": name,
            "provider": airline,
            "departure": f.get("departure_time", ""),
            "arrival": f.get("arrival_time", ""),
            "duration": f.get("duration", ""),
            "price": price,
            "price_display": price_display,
            "location": route,
            "notes": notes,
            "rating": None,
            "booking_url": f.get("booking_url", ""),
            "is_best": f.get("is_best", False),
        })
    return cards


def is_flights_available() -> bool:
    """Verifica si el servicio de vuelos esta disponible.

    Retorna True si SerpAPI esta configurada O fast-flights esta instalado.
    """
    if os.environ.get("SERPAPI_KEY", ""):
        return True
    return _FAST_FLIGHTS_AVAILABLE
