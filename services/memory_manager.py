"""Gestor de memoria vectorial para el Trip Planner.
Adaptado del multiuser_chat_system para usuario único y dominio de viajes."""

import logging
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from typing_extensions import TypedDict, Annotated

logger = logging.getLogger(__name__)

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from config.llm_config import LLM_DATA_DIR, MAX_VECTOR_RESULTS, DEFAULT_MODEL


class MemoryState(TypedDict):
    """Estado que combina mensajes de LangGraph con memoria vectorial."""
    messages: Annotated[List[BaseMessage], add_messages]
    vector_memories: List[str]
    user_profile: Dict[str, Any]
    last_memory_extraction: Optional[str]
    trip_context: Optional[str]
    user_id: Optional[str]


class ExtractedMemory(BaseModel):
    """Modelo para memoria extraída estructurada."""
    category: str = Field(description="Categoría: viaje, preferencias, personal, hechos_importantes")
    content: str = Field(description="Contenido de la memoria")
    importance: int = Field(description="Importancia del 0 al 5", ge=0, le=5)


class TripMemoryManager:
    """Gestor de memoria vectorial para usuario único del Trip Planner."""

    def __init__(self):
        self.data_dir = LLM_DATA_DIR
        os.makedirs(self.data_dir, exist_ok=True)
        self.chromadb_path = os.path.join(self.data_dir, "chromadb")
        self.langgraph_db_path = os.path.join(self.data_dir, "langgraph_memory.db")
        self._init_vector_db()
        self._init_extraction_system()

    def _init_vector_db(self):
        """Inicializa ChromaDB."""
        try:
            import chromadb

            logger.info("Inicializando ChromaDB (path=%s)", self.chromadb_path)
            self.client = chromadb.PersistentClient(path=self.chromadb_path)
            try:
                self.collection = self.client.get_collection("trip_planner_memories")
            except Exception:
                self.collection = self.client.create_collection("trip_planner_memories")
            logger.info("ChromaDB inicializado OK (collection count=%d)", self.collection.count())
        except Exception as e:
            logger.error("Error inicializando ChromaDB: %s", e, exc_info=True)
            self.collection = None

    def _init_extraction_system(self):
        """Inicializa el sistema de extracción de memorias orientado a viajes."""
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import PromptTemplate
            from langchain_core.output_parsers import PydanticOutputParser

            self.extraction_llm = ChatOpenAI(model=DEFAULT_MODEL, temperature=0)
            self.memory_parser = PydanticOutputParser(pydantic_object=ExtractedMemory)

            self.extraction_template = PromptTemplate(
                template="""Analiza el siguiente mensaje del usuario en el contexto de planificación de viajes
y determina si contiene información importante que deba recordarse.

Categorías disponibles:
- viaje: Destinos visitados o deseados, fechas de viaje, experiencias pasadas
- preferencias: Tipo de alojamiento preferido, aerolíneas favoritas, restricciones alimentarias, estilo de viaje
- personal: Nombre, idioma, país de residencia, presupuesto habitual
- hechos_importantes: Alergias, documentos, fechas importantes, limitaciones físicas

Mensaje del usuario: "{user_message}"

Si contiene información relevante para futuros viajes, extrae UNA memoria (la más importante).
Si no es relevante, responde con categoría "none".

{format_instructions}""",
                input_variables=["user_message"],
                partial_variables={"format_instructions": self.memory_parser.get_format_instructions()},
            )
            self.extraction_chain = self.extraction_template | self.extraction_llm | self.memory_parser
            logger.info("Sistema de extraccion de memorias inicializado OK")
        except Exception as e:
            logger.error("Error inicializando sistema de extraccion: %s", e, exc_info=True)
            self.extraction_chain = None

    # --- MEMORIA VECTORIAL ---

    def save_vector_memory(self, text: str, metadata: Optional[Dict] = None,
                           user_id: Optional[str] = None) -> str:
        """Guarda una memoria en ChromaDB. Retorna memory_id."""
        if not self.collection:
            return ""
        try:
            memory_id = str(uuid.uuid4())
            doc_metadata = metadata or {}
            doc_metadata.update({
                "timestamp": datetime.now().isoformat(),
                "memory_id": memory_id,
            })
            if user_id:
                doc_metadata["user_id"] = user_id
            self.collection.add(
                documents=[text],
                ids=[memory_id],
                metadatas=[doc_metadata],
            )
            return memory_id
        except Exception as e:
            logger.error("Error guardando memoria vectorial: %s", e)
            return ""

    def search_vector_memory(self, query: str, k: int = MAX_VECTOR_RESULTS,
                             user_id: Optional[str] = None) -> List[str]:
        """Busca memorias semánticamente similares. Retorna lista de textos.

        Si user_id se proporciona, filtra por usuario. Si es None, busca sin filtro
        (compatibilidad con memorias existentes sin user_id).
        """
        if not self.collection:
            return []
        try:
            count = self.collection.count()
            if count == 0:
                return []
            query_kwargs = {
                "query_texts": [query],
                "n_results": min(k, count),
            }
            if user_id:
                query_kwargs["where"] = {"user_id": user_id}
            results = self.collection.query(**query_kwargs)
            return results["documents"][0] if results["documents"] else []
        except Exception as e:
            logger.error("Error buscando memoria vectorial: %s", e)
            return []

    def get_all_vector_memories(self) -> List[Dict]:
        """Retorna todas las memorias almacenadas."""
        if not self.collection:
            return []
        try:
            results = self.collection.get()
            memories = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"]):
                    memories.append({
                        "id": results["ids"][i],
                        "content": doc,
                        "metadata": results["metadatas"][i] if results["metadatas"] else {},
                    })
            return memories
        except Exception as e:
            logger.error("Error obteniendo memorias vectoriales: %s", e)
            return []

    def extract_and_store_memories(self, user_message: str,
                                   user_id: Optional[str] = None) -> bool:
        """Extrae memorias del mensaje y las guarda si son relevantes."""
        if not self.extraction_chain:
            return self._extract_memories_manual(user_message, user_id=user_id)
        try:
            extracted = self.extraction_chain.invoke({"user_message": user_message})
            if extracted.category != "none" and extracted.importance >= 2:
                memory_id = self.save_vector_memory(
                    extracted.content,
                    {
                        "category": extracted.category,
                        "importance": extracted.importance,
                        "original_message": user_message[:200],
                    },
                    user_id=user_id,
                )
                return bool(memory_id)
            return False
        except Exception as e:
            logger.error("Error en extracción automática: %s", e)
            return self._extract_memories_manual(user_message, user_id=user_id)

    def _extract_memories_manual(self, user_message: str,
                                 user_id: Optional[str] = None) -> bool:
        """Fallback manual orientado a viajes."""
        message_lower = user_message.lower()
        memory_rules = [
            (
                ["prefiero", "me gusta", "favorito", "odio", "no me gusta"],
                "preferencias",
                f"Preferencia de viaje: {user_message}",
            ),
            (
                ["alergia", "alérgico", "no puedo comer", "intolerancia", "vegetariano", "vegano"],
                "personal",
                f"Restricción: {user_message}",
            ),
            (
                ["me llamo", "mi nombre", "vivo en", "soy de"],
                "personal",
                f"Info personal: {user_message}",
            ),
            (
                ["viajé a", "fui a", "visité", "conocí"],
                "viaje",
                f"Experiencia de viaje: {user_message}",
            ),
            (
                ["presupuesto", "gastar", "máximo"],
                "preferencias",
                f"Presupuesto: {user_message}",
            ),
        ]
        for phrases, category, memory_text in memory_rules:
            if any(phrase in message_lower for phrase in phrases):
                return bool(self.save_vector_memory(
                    memory_text, {"category": category}, user_id=user_id
                ))
        return False
