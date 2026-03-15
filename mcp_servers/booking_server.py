"""MCP Server para busqueda de hoteles en Booking.com via RapidAPI (DataCrawler).

Uso standalone:
    python mcp_servers/booking_server.py

Requiere RAPIDAPI_KEY en .env o variable de entorno.
"""

import sys
import os

# Agregar el directorio raiz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP

from services.booking_service import (
    search_destinations,
    search_hotels,
    is_booking_available,
)

mcp = FastMCP("booking-hotel-search")


@mcp.tool()
def buscar_destinos(query: str) -> list[dict]:
    """Busca destinos en Booking.com por nombre de ciudad o region.

    Args:
        query: Nombre de la ciudad o destino (ej: "Montevideo", "Paris", "Tokyo")

    Returns:
        Lista de destinos con dest_id, nombre y pais.
    """
    if not is_booking_available():
        return [{"error": "RAPIDAPI_KEY no configurada. Configura la variable de entorno."}]
    results = search_destinations(query)
    if not results:
        return [{"info": f"No se encontraron destinos para '{query}'"}]
    return results


@mcp.tool()
def buscar_hoteles(
    dest_id: str,
    checkin: str,
    checkout: str,
    adults: int = 2,
    search_type: str = "CITY",
    rooms: int = 1,
    limit: int = 5,
    currency: str = "USD",
) -> list[dict]:
    """Busca hoteles disponibles en Booking.com para un destino y fechas.

    Args:
        dest_id: ID del destino (el city_ufi de buscar_destinos)
        checkin: Fecha de check-in en formato YYYY-MM-DD
        checkout: Fecha de check-out en formato YYYY-MM-DD
        adults: Numero de adultos (default 2)
        search_type: Tipo de busqueda: CITY, REGION, LANDMARK, DISTRICT
        rooms: Numero de habitaciones (default 1)
        limit: Maximo de resultados a retornar (default 5)
        currency: Codigo de moneda (default USD)

    Returns:
        Lista de hoteles con nombre, precio, rating, direccion.
    """
    if not is_booking_available():
        return [{"error": "RAPIDAPI_KEY no configurada"}]
    results = search_hotels(
        dest_id, checkin, checkout, adults,
        search_type, rooms, limit, currency,
    )
    if not results:
        return [{"info": "No se encontraron hoteles para los criterios dados"}]
    return results


if __name__ == "__main__":
    mcp.run(transport="stdio")
