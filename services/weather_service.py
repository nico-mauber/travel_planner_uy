"""Servicio de clima mock por destino."""


WEATHER_DATA = {
    "Tokio, Japón": {
        "temp_min": 15,
        "temp_max": 22,
        "condition": "Parcialmente nublado",
        "icon": "⛅",
        "description": "Primavera en Tokio — temporada de cerezos en flor",
    },
    "Barcelona, España": {
        "temp_min": 18,
        "temp_max": 25,
        "condition": "Soleado",
        "icon": "☀️",
        "description": "Clima mediterráneo agradable para pasear",
    },
    "Lima, Perú": {
        "temp_min": 20,
        "temp_max": 28,
        "condition": "Nublado parcial",
        "icon": "🌤️",
        "description": "Verano limeño — días cálidos con garúa ocasional",
    },
}

DEFAULT_WEATHER = {
    "temp_min": 15,
    "temp_max": 25,
    "condition": "Variable",
    "icon": "🌤️",
    "description": "Datos climáticos no disponibles para este destino",
}


def get_weather(destination: str) -> dict:
    """Obtiene datos climáticos mock para un destino."""
    return WEATHER_DATA.get(destination, DEFAULT_WEATHER)
