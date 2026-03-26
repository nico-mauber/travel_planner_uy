"""Configuración del LLM (OpenAI) y memoria vectorial.

Valores sensibles se leen de variables de entorno (.env).
Defaults razonables para que funcione sin configuración explícita.
"""

import os

# Directorios de datos del LLM
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LLM_DATA_DIR = os.path.join(BASE_DIR, "data", "llm_data")
os.makedirs(LLM_DATA_DIR, exist_ok=True)

# Configuración del modelo (desde .env o defaults)
DEFAULT_MODEL = os.environ.get("LLM_DEFAULT_MODEL", "gpt-5-nano")
DEFAULT_TEMPERATURE = float(os.environ.get("LLM_DEFAULT_TEMPERATURE", "0.7"))
EXTRACTION_TEMPERATURE = float(os.environ.get("LLM_EXTRACTION_TEMPERATURE", "0"))
DEFAULT_EMBEDDING_MODEL = os.environ.get("LLM_EMBEDDING_MODEL", "text-embedding-3-small")

# Configuración de memoria
MAX_VECTOR_RESULTS = int(os.environ.get("LLM_MAX_VECTOR_RESULTS", "3"))
MEMORY_CATEGORIES = [
    "viaje",
    "preferencias",
    "personal",
    "hechos_importantes",
]
