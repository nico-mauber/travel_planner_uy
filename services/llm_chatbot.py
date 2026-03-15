"""Chatbot LLM para Trip Planner — LangGraph + Gemini.
Adaptado del multiuser_chat_system con dominio de viajes."""

import sqlite3
from typing import Optional, Dict, Any

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage, trim_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

from services.memory_manager import TripMemoryManager, MemoryState
from config.llm_config import DEFAULT_MODEL, DEFAULT_TEMPERATURE


class TripChatbot:
    """Chatbot de planificación de viajes con memoria vectorial (singleton)."""

    _instance: Optional["TripChatbot"] = None

    @classmethod
    def get_instance(cls) -> "TripChatbot":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.memory_manager = TripMemoryManager()
        self.llm = ChatGoogleGenerativeAI(
            model=DEFAULT_MODEL,
            temperature=DEFAULT_TEMPERATURE,
        )

        self.system_template = """Eres un asistente de planificación de viajes experto, amigable y proactivo.

Personalidad:
- Ayudas a planificar viajes: vuelos, hoteles, actividades, restaurantes, presupuesto
- Recuerdas preferencias del usuario de conversaciones anteriores
- Das sugerencias concretas con precios estimados cuando es posible
- Respondes siempre en español
- Eres conciso pero informativo

{memory_context}

{trip_context}

{user_profile_context}

INSTRUCCIONES:
- Responde en texto plano o markdown. NO generes JSON ni formatos estructurados.
- Si el usuario pide agregar algo al itinerario, sugiérelo en texto y el usuario lo confirmará desde la interfaz.
- Si el usuario pregunta por precios, da estimaciones razonables.
- Si mencionan un destino específico, da información real y útil sobre ese lugar.
- Si no hay viaje activo, pregunta a dónde quieren viajar.
"""

        self.message_trimmer = trim_messages(
            strategy="last",
            max_tokens=4000,
            token_counter=self.llm,
            start_on="human",
            include_system=True,
        )

        self.app = self._create_app()

    def _create_app(self):
        """Crea el pipeline LangGraph con 4 nodos."""
        workflow = StateGraph(state_schema=MemoryState)

        def memory_retrieval_node(state):
            messages = state.get("messages", [])
            if not messages:
                return {"vector_memories": []}
            last_user_message = None
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_user_message = msg
                    break
            if not last_user_message:
                return {"vector_memories": []}
            _user_id = state.get("user_id")
            relevant = self.memory_manager.search_vector_memory(
                last_user_message.content, user_id=_user_id
            )
            return {"vector_memories": relevant}

        def context_optimization_node(state):
            messages = state.get("messages", [])
            trimmed = self.message_trimmer.invoke(messages)
            return {"messages": trimmed}

        def response_generation_node(state):
            messages = state.get("messages", [])
            vector_memories = state.get("vector_memories", [])
            trip_context_str = state.get("trip_context") or ""
            user_profile = state.get("user_profile") or {}

            if not messages:
                return {"messages": []}

            # Contexto de memorias
            memory_context = ""
            if vector_memories:
                parts = ["Información que recuerdas del usuario:"]
                for mem in vector_memories:
                    parts.append(f"- {mem}")
                memory_context = "\n".join(parts)

            # Contexto del viaje activo
            trip_context = ""
            if trip_context_str:
                trip_context = f"VIAJE ACTIVO:\n{trip_context_str}"

            # Contexto del perfil
            profile_context = ""
            if user_profile:
                profile_parts = ["PERFIL DEL USUARIO:"]
                for k, v in user_profile.items():
                    if v:
                        profile_parts.append(f"- {k}: {v}")
                if len(profile_parts) > 1:
                    profile_context = "\n".join(profile_parts)

            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_template.format(
                    memory_context=memory_context,
                    trip_context=trip_context,
                    user_profile_context=profile_context,
                )),
                MessagesPlaceholder(variable_name="messages"),
            ])

            chain = prompt | self.llm
            response = chain.invoke({"messages": messages})
            return {"messages": response}

        def memory_extraction_node(state):
            messages = state.get("messages", [])
            last_extraction = state.get("last_memory_extraction")
            last_user_message = None
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    last_user_message = msg
                    break
            if not last_user_message:
                return {}
            if last_extraction != last_user_message.content:
                _user_id = state.get("user_id")
                self.memory_manager.extract_and_store_memories(
                    last_user_message.content, user_id=_user_id
                )
                return {"last_memory_extraction": last_user_message.content}
            return {}

        workflow.add_node("memory_retrieval", memory_retrieval_node)
        workflow.add_node("context_optimization", context_optimization_node)
        workflow.add_node("response_generation", response_generation_node)
        workflow.add_node("memory_extraction", memory_extraction_node)

        workflow.add_edge(START, "memory_retrieval")
        workflow.add_edge("memory_retrieval", "context_optimization")
        workflow.add_edge("context_optimization", "response_generation")
        workflow.add_edge("response_generation", "memory_extraction")
        workflow.add_edge("memory_extraction", END)

        db_path = self.memory_manager.langgraph_db_path
        conn = sqlite3.connect(db_path, check_same_thread=False)
        checkpointer = SqliteSaver(conn)

        return workflow.compile(checkpointer=checkpointer)

    def chat(self, message: str, trip: Optional[dict] = None,
             user_profile: Optional[dict] = None,
             user_id: str = "demo", chat_id: str = "default") -> dict:
        """Envía mensaje y retorna respuesta en formato Trip Planner.

        Retorna: {role: "assistant", type: "text", content: str}
        """
        try:
            config = {"configurable": {"thread_id": f"trip_chat_{user_id}_{chat_id}"}}

            # Serializar contexto del viaje
            trip_context = ""
            if trip:
                items = trip.get("items", [])
                confirmed = sum(1 for i in items if i.get("status") == "confirmado")
                pending = sum(1 for i in items if i.get("status") == "pendiente")
                suggested = sum(1 for i in items if i.get("status") == "sugerido")

                trip_context = (
                    f"Destino: {trip.get('destination', 'No definido')}\n"
                    f"Nombre: {trip.get('name', '')}\n"
                    f"Fechas: {trip.get('start_date', '?')} a {trip.get('end_date', '?')}\n"
                    f"Estado: {trip.get('status', '')}\n"
                    f"Presupuesto total: USD {trip.get('budget_total', 0):.0f}\n"
                    f"Items: {len(items)} total ({confirmed} confirmados, "
                    f"{pending} pendientes, {suggested} sugeridos)"
                )

            result = self.app.invoke(
                {
                    "messages": [HumanMessage(content=message)],
                    "trip_context": trip_context,
                    "user_profile": user_profile or {},
                    "user_id": user_id,
                },
                config,
            )

            messages = result.get("messages", [])
            if not messages:
                return {
                    "role": "assistant",
                    "type": "text",
                    "content": "No se recibió respuesta del asistente. Intenta de nuevo.",
                }

            response_text = messages[-1].content

            return {
                "role": "assistant",
                "type": "text",
                "content": response_text,
            }

        except Exception as e:
            return {
                "role": "assistant",
                "type": "text",
                "content": f"Error del asistente IA: {str(e)}. Intenta de nuevo.",
            }
