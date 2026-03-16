"""Configuración del LLM (OpenAI) y memoria vectorial."""

import os

# Directorios de datos del LLM
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LLM_DATA_DIR = os.path.join(BASE_DIR, "data", "llm_data")
os.makedirs(LLM_DATA_DIR, exist_ok=True)

# Configuración del modelo
DEFAULT_MODEL = "gpt-4.1-nano"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

# Configuración de memoria
MAX_VECTOR_RESULTS = 3
MEMORY_CATEGORIES = [
    "viaje",
    "preferencias",
    "personal",
    "hechos_importantes",
]
