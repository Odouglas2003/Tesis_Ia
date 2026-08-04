import logging
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
import json
import ast
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from langchain_community.vectorstores import FAISS
from pymongo.database import Database as SyncDatabase
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent

# --- CONFIGURACIÓN ---
router = APIRouter(prefix="/chat", tags=["Asistente de Chat"])
logger = logging.getLogger(__name__)
SENSITIVE_FIELDS = ["dni", "honorarios", "password", "sueldo", "address", "token"]


# --- MODELOS Y DEPENDENCIAS ---
class ChatRequest(BaseModel):
    query: str = Field(...)
    chat_history: Optional[List[dict]] = Field(default_factory=list)


def get_sync_db(request: Request) -> SyncDatabase:
    logger.info(
        f"🔍 Estado de sync_mongo_db: {hasattr(request.app.state, 'sync_mongo_db')}"
    )
    if hasattr(request.app.state, "sync_mongo_db"):
        logger.info(
            f"🔍 Valor de sync_mongo_db: {request.app.state.sync_mongo_db is not None}"
        )

    if (
        not hasattr(request.app.state, "sync_mongo_db")
        or request.app.state.sync_mongo_db is None
    ):
        logger.error("❌ ERROR: sync_mongo_db no está disponible durante la request")
        raise HTTPException(
            status_code=503,
            detail="Conexión síncrona a la base de datos no está disponible.",
        )
    return request.app.state.sync_mongo_db


def get_vectorstore(request: Request) -> FAISS:
    logger.info(
        f"🔍 Estado de faiss_vectorstore: {hasattr(request.app.state, 'faiss_vectorstore')}"
    )
    if hasattr(request.app.state, "faiss_vectorstore"):
        logger.info(
            f"🔍 Valor de faiss_vectorstore: {request.app.state.faiss_vectorstore is not None}"
        )

    if (
        not hasattr(request.app.state, "faiss_vectorstore")
        or request.app.state.faiss_vectorstore is None
    ):
        logger.error("❌ ERROR: faiss_vectorstore no está disponible")
        # Crear vectorstore vacío on-demand
        try:
            from langchain_openai import OpenAIEmbeddings

            embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
            empty_vectorstore = FAISS.from_texts(
                ["Documentación no disponible"], embeddings_model
            )
            return empty_vectorstore
        except Exception as e:
            logger.error(f"Error creando vectorstore vacío: {e}")
            raise HTTPException(status_code=503, detail="VectorStore no disponible")

    return request.app.state.faiss_vectorstore


# --- SERVICIO DE HERRAMIENTAS GENÉRICAS ---
class AgentToolsService:
    def __init__(self, sync_db: SyncDatabase):
        self.db = sync_db

    def _sanitize_output(self, data: any) -> any:
        if isinstance(data, dict):
            return {
                k: self._sanitize_output(v)
                for k, v in data.items()
                if k not in SENSITIVE_FIELDS
            }
        if isinstance(data, list):
            return [self._sanitize_output(item) for item in data]
        if isinstance(data, ObjectId):
            return str(data)
        if isinstance(data, datetime):
            return data.isoformat()
        return data

    def _regex_filter(self, value: str) -> dict:
        return {"$regex": re.escape(value.strip()), "$options": "i"}

    def find_collaborator_by_name(self, full_name: str, limit: int = 5) -> str:
        """Busca colaboradores sin depender del orden entre nombre y apellido."""
        tokens = [token for token in re.split(r"\s+", full_name.strip()) if token]
        if not tokens:
            return "Ingresá al menos una parte del nombre o apellido."

        name_filter = {
            "$and": [
                {
                    "$or": [
                        {"first_name": self._regex_filter(token)},
                        {"last_name": self._regex_filter(token)},
                    ]
                }
                for token in tokens
            ]
        }
        try:
            documents = list(self.db["collaborator"].find(name_filter).limit(limit))
            if not documents:
                return f"No se encontraron colaboradores que coincidan con '{full_name}'."
            return json.dumps(
                self._sanitize_output(documents), ensure_ascii=False, indent=2
            )
        except Exception as e:
            logger.error("Error buscando colaborador por nombre: %s", e)
            return "Error al buscar el colaborador por nombre."

    def _string_filter_value(self, filter_query: dict, field: str) -> Optional[str]:
        value = filter_query.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    def _build_collaborator_name_fallback_filter(
        self, filter_query: dict
    ) -> Optional[dict]:
        first_name = self._string_filter_value(filter_query, "first_name")
        last_name = self._string_filter_value(filter_query, "last_name")

        if not first_name and not last_name:
            return None

        other_filters = {
            key: value
            for key, value in filter_query.items()
            if key not in {"first_name", "last_name"}
        }

        if first_name and last_name:
            name_filter = {
                "$or": [
                    {
                        "$and": [
                            {"first_name": self._regex_filter(first_name)},
                            {"last_name": self._regex_filter(last_name)},
                        ]
                    },
                    {
                        "$and": [
                            {"first_name": self._regex_filter(last_name)},
                            {"last_name": self._regex_filter(first_name)},
                        ]
                    },
                ]
            }
        else:
            name = first_name or last_name
            name_filter = {
                "$or": [
                    {"first_name": self._regex_filter(name)},
                    {"last_name": self._regex_filter(name)},
                ]
            }

        if other_filters:
            return {"$and": [other_filters, name_filter]}
        return name_filter

    def get_schema(self, collection_names_str: str = "") -> str:
        """Indispensable para ver los nombres exactos de las colecciones y sus campos antes de hacer una consulta."""
        try:
            if not collection_names_str or not collection_names_str.strip():
                collection_names = self.db.list_collection_names()
            else:
                collection_names = [
                    name.strip() for name in collection_names_str.split(",")
                ]

            schema_description = "Esquemas de la Base de Datos:\n"
            for name in collection_names:
                if name.startswith("system."):
                    continue
                sample_doc = self.db[name].find_one({}, {"_id": 0})
                if sample_doc:
                    sanitized_sample = self._sanitize_output(sample_doc)
                    fields = {
                        key: str(type(value).__name__)
                        for key, value in sanitized_sample.items()
                    }
                    schema_description += f"\n--- Colección: '{name}' ---\nCampos: {list(fields.keys())}\n"
            return (
                schema_description
                if len(schema_description) > 50
                else "No se encontraron colecciones con datos."
            )
        except Exception as e:
            return f"Error al obtener el esquema: {str(e)}"

    def count_documents(self, collection_name: str) -> int:
        """Cuenta el número total de documentos en CUALQUIER colección especificada."""
        logger.info(f"Contando documentos en: {collection_name}")
        try:
            return self.db[collection_name].count_documents({})
        except Exception as e:
            logger.error(
                f"Error en count_documents para la colección '{collection_name}': {e}"
            )
            return -1

    def find_documents(
        self, collection_name: str, filter_query_str: str, limit: int = 5
    ) -> str:
        """Busca documentos en CUALQUIER colección usando un filtro. Devuelve una lista de resultados."""
        logger.info(f"Buscando en '{collection_name}' con filtro: {filter_query_str}")
        try:
            filter_query = ast.literal_eval(filter_query_str)
            documents = list(self.db[collection_name].find(filter_query).limit(limit))
            used_fallback = False
            fallback_filter = None

            if (
                not documents
                and collection_name == "collaborator"
                and isinstance(filter_query, dict)
            ):
                fallback_filter = self._build_collaborator_name_fallback_filter(
                    filter_query
                )
                if fallback_filter:
                    logger.info(
                        "Sin resultados exactos. Reintentando busqueda flexible de colaborador con filtro: %s",
                        fallback_filter,
                    )
                    documents = list(
                        self.db[collection_name].find(fallback_filter).limit(limit)
                    )
                    used_fallback = True
            if not documents:
                if fallback_filter:
                    return (
                        f"No se encontraron documentos en la coleccion '{collection_name}' "
                        f"con el filtro {filter_query_str}. Tambien se probo una busqueda "
                        "flexible por first_name/last_name en ambos ordenes."
                    )
                return f"No se encontraron documentos en la colección '{collection_name}' con el filtro {filter_query_str}."
            result = json.dumps(
                self._sanitize_output(documents), ensure_ascii=False, indent=2
            )
            if used_fallback:
                return (
                    "Coincidencias encontradas usando busqueda flexible por "
                    f"nombre/apellido:\n{result}"
                )
            return result
        except Exception as e:
            logger.error(f"Error en find_documents: {e}")
            return "Error al ejecutar la búsqueda. Verifica el nombre de la colección y la sintaxis del filtro."


# --- MODELOS DE ARGUMENTOS ---
class SearchDocsArgs(BaseModel):
    consulta: str = Field(
        description="La pregunta o tema a buscar en la documentación."
    )


class CountArgs(BaseModel):
    collection_name: str = Field(
        description="El nombre exacto de la colección a contar (ej. 'collaborator', 'projects')."
    )


class FindArgs(BaseModel):
    collection_name: str = Field(
        description="El nombre exacto de la colección donde buscar (ej. 'collaborator', 'projects')."
    )
    filter_query_str: str = Field(
        description="Un filtro de MongoDB en formato de string de diccionario Python. Para colaboradores, usa first_name y last_name; si no hay resultado exacto, se prueba una busqueda flexible por nombre/apellido. Ejemplo: \"{'first_name': 'Luciana'}\""
    )
    limit: int = Field(default=5, description="Número máximo de resultados a devolver.")


class CollaboratorNameArgs(BaseModel):
    full_name: str = Field(
        description="Nombre, apellido o nombre completo escrito en cualquier orden."
    )
    limit: int = Field(default=5, description="Número máximo de resultados a devolver.")


# --- ENDPOINT DEL CHAT ---
@router.post("/")
async def chat_endpoint(
    chat_request: ChatRequest,
    sync_db: SyncDatabase = Depends(get_sync_db),
    vectorstore: FAISS = Depends(get_vectorstore),
):
    try:
        logger.info(f"📨 Request recibida en /chat: {chat_request.query}")
        logger.info("✅ Paso 1: Request llegó al endpoint /chat")

        # Verificar dependencias
        if sync_db is None:
            logger.error("❌ sync_db es None")
            return {"answer": "Error: Base de datos no disponible"}

        logger.info("✅ Paso 2: Dependencias verificadas")

        # Inicializar servicio
        try:
            service = AgentToolsService(sync_db)
            logger.info("✅ Paso 3: AgentToolsService creado")
        except Exception as e:
            logger.error(f"❌ Error creando AgentToolsService: {e}", exc_info=True)
            return {"answer": "Error inicializando servicio de herramientas"}

        # Definir función de búsqueda
        def search_docs(consulta: str) -> str:
            try:
                if vectorstore is None:
                    return "La documentación no está disponible en este momento."
                docs = vectorstore.similarity_search(consulta, k=1)
                if not docs:
                    return "No encontré información sobre eso en la documentación."
                return docs[0].page_content
            except Exception as e:
                logger.error(f"❌ Error en search_docs: {e}")
                return f"Ocurrió un error al consultar la documentación: {e}"

        # Crear herramientas
        try:
            tools = [
                StructuredTool.from_function(
                    func=search_docs,
                    name="buscar_en_documentacion",
                    args_schema=SearchDocsArgs,
                    description="Útil para responder preguntas conceptuales sobre el sistema 'Software Team Builder'.",
                ),
                StructuredTool.from_function(
                    func=service.get_schema,
                    name="obtener_esquema_db",
                    description="Indispensable para ver los nombres exactos de las colecciones y sus campos antes de hacer una consulta de datos.",
                ),
                StructuredTool.from_function(
                    func=service.count_documents,
                    name="contar_documentos",
                    args_schema=CountArgs,
                    description="Útil para contar el número total de documentos en una colección (ej. 'collaborator', 'projects').",
                ),
                StructuredTool.from_function(
                    func=service.find_documents,
                    name="buscar_documentos",
                    args_schema=FindArgs,
                    description="Útil para buscar uno o más documentos en una colección usando un filtro.",
                ),
                StructuredTool.from_function(
                    func=service.find_collaborator_by_name,
                    name="buscar_colaborador_por_nombre",
                    args_schema=CollaboratorNameArgs,
                    description="Busca un colaborador por nombre o apellido en cualquier orden. Es la herramienta obligatoria para preguntas como 'quién es Quiroga Martin'.",
                ),
            ]
            logger.info("✅ Paso 4: Tools creadas correctamente")
        except Exception as e:
            logger.error(f"❌ Error creando tools: {e}", exc_info=True)
            return {"answer": "Error configurando herramientas de IA"}

        # Inicializar LLM
        try:
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, max_tokens=500)
            logger.info("✅ Paso 5: LLM inicializado (gpt-3.5-turbo)")
        except Exception as e:
            logger.error(f"❌ Error inicializando LLM: {e}", exc_info=True)
            return {"answer": "Error con servicio de OpenAI"}

        # Crear agente
        try:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """Eres el asistente de IA de Software Team Builder, el sistema desarrollado para esta tesis.
                        Su objetivo es ayudar a gestionar colaboradores y proyectos, analizar perfiles y recomendar
                        equipos de trabajo adecuados según roles, tecnologías, experiencia y presupuesto.
                        **INSTRUCCIONES CRÍTICAS:**
                     1. Para buscar colaboradores/personas, usa SIEMPRE la colección 'collaborator'
                     2. La colección 'people' es de otro sistema y NO contiene datos actuales
                     3. Tu primer paso es SIEMPRE usar 'obtener_esquema_db' para ver la estructura
                     4. Para colaboradores: buscar en colección 'collaborator' con campos 'first_name' y 'last_name'
                     5. Los usuarios pueden escribir "apellido nombre" o solo una parte del nombre; no asumas que el primer token siempre es first_name.
                     6. Si preguntan quién es una persona o buscan un colaborador por nombre, usa PRIMERO 'buscar_colaborador_por_nombre' con el nombre completo tal como lo escribió el usuario.

                    📋 **Colecciones principales:**
                     - 'collaborator': Colaboradores actuales del sistema
                     - 'projects': Proyectos
                     - 'people': ❌ NO USAR - Datos obsoletos de otro sistema

                     Responde siempre en español. Eres conciso y te basas únicamente en la
                     información que te proporcionan tus herramientas.""",
                    ),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("user", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ]
            )

            agent = create_openai_tools_agent(llm, tools, prompt)
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3,
                max_execution_time=30,
            )
            logger.info("✅ Paso 6: Agente creado correctamente")

        except Exception as e:
            logger.error(f"❌ Error creando agente: {e}", exc_info=True)
            return {"answer": "Error configurando agente de IA"}

        # Ejecutar agente
        try:
            logger.info("✅ Paso 7: Ejecutando agente...")
            response = await agent_executor.ainvoke(
                {
                    "input": chat_request.query,
                    "chat_history": chat_request.chat_history or [],
                }
            )
            final_answer = response.get("output", "No pude generar una respuesta.")
            logger.info("✅ Paso 8: Agente ejecutado exitosamente")
            return {"answer": final_answer}

        except Exception as e:
            logger.error(f"❌ Error ejecutando agente: {e}", exc_info=True)
            return {
                "answer": "Lo siento, tuve un problema al procesar tu pregunta. Por favor intenta de nuevo."
            }

    except Exception as e:
        logger.critical(f"💥 ERROR CRÍTICO NO MANEJADO en /chat: {e}", exc_info=True)
        return {
            "answer": "Error interno del servidor. Por favor contacta al administrador."
        }
