import logging
import os
import certifi
import openai

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import pandas as pd


from pymongo import MongoClient
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


from app.routers import health, teams, chat, faiss_update, analytics
from config import Config
from app.recommendation_engine import (
    SoftwareTeamRecommender,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("--- INICIO: Evento de Arranque de FastAPI ---")

    app.state.faiss_vectorstore = None
    app.state.sync_mongo_db = None
    app.state.mongo_client = None
    app.state.recommendation_engine = None
    app.state.engine_is_ready = False

    try:
        openai.api_key = Config.OPENAI_API_KEY
        openai_enabled = bool(Config.OPENAI_API_KEY)

        docs_path = "./docs"
        if not openai_enabled:
            logger.warning(
                "OPENAI_API_KEY no configurada. Se omite la carga del vectorstore y /chat quedara no disponible."
            )
        elif os.path.exists(docs_path):
            loader = DirectoryLoader(
                docs_path,
                glob="**/*.md",
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"},
            )
            documents = loader.load()
            if documents:
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1500, chunk_overlap=200
                )
                splits = text_splitter.split_documents(documents)
                embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
                app.state.faiss_vectorstore = FAISS.from_documents(
                    splits, embeddings_model
                )
                logger.info(
                    ">>> ÉXITO: VectorStore de FAISS creado desde documentación."
                )
            else:
                logger.warning(f"ADVERTENCIA: Carpeta '{docs_path}' vacía.")
        else:
            logger.warning(f"ADVERTENCIA: La carpeta '{docs_path}' no existe.")

        mongo_kwargs = {"serverSelectionTimeoutMS": 10000}
        connection_string = Config.MONGO_DB_CONNECTION_STRING or ""
        connection_string_lower = connection_string.lower()
        if connection_string.startswith("mongodb+srv://") or any(
            flag in connection_string_lower for flag in ("tls=true", "ssl=true")
        ):
            mongo_kwargs["tlsCAFile"] = certifi.where()

        mongo_client = MongoClient(
            Config.MONGO_DB_CONNECTION_STRING,
            **mongo_kwargs,
        )
        mongo_client.admin.command("ping")
        app.state.mongo_client = mongo_client
        app.state.sync_mongo_db = mongo_client[Config.MONGO_DB_NAME]
        logger.info(
            f">>> ÉXITO: Conexión a MongoDB (DB: '{Config.MONGO_DB_NAME}') establecida."
        )

        logger.info("Cargando datos para el motor de recomendación Singleton...")
        db = app.state.sync_mongo_db

        collaborators_data = list(
            db[Config.MONGO_COLLABORATOR_COLLECTION_NAME].find({})
        )
        projects_data = list(db[Config.MONGO_PROJECT_COLLECTION_NAME].find({}))

        if not collaborators_data:
            logger.error(
                "FATAL: No se encontraron datos de colaboradores para inicializar el motor. El servicio /teams no funcionará."
            )

        else:
            df_collaborators = pd.DataFrame(collaborators_data)
            df_projects = (
                pd.DataFrame(projects_data) if projects_data else pd.DataFrame()
            )

            logger.info("Creando instancia Singleton del motor (esto puede tardar)...")
            recommendation_engine_instance = SoftwareTeamRecommender(
                df_collaborators, df_projects
            )
            app.state.recommendation_engine = recommendation_engine_instance

            app.state.engine_is_ready = True  #
            logger.info(">>> ÉXITO: Motor de recomendación Singleton creado y listo.")

        try:
            openai.api_key = Config.OPENAI_API_KEY
            if not openai.api_key:
                raise ValueError("OPENAI_API_KEY está vacía.")
            logger.info("✅ OpenAI: Configuración de API Key cargada.")
        except Exception as e:
            logger.error(f"❌ OpenAI: Error en la configuración de la API Key - {e}")

    except Exception as e:
        logger.critical(
            f"FATAL: El arranque de la aplicación falló. Error: {e}", exc_info=True
        )

    yield

    logger.info("--- INICIO: Evento de Apagado de FastAPI ---")
    if app.state.mongo_client:
        app.state.mongo_client.close()
        logger.info("Conexión a MongoDB cerrada.")
    logger.info("--- FIN: Apagado completado. ---")

    logger.info("Apagando la aplicación...")


startup_lifespan = lifespan

app = FastAPI(lifespan=lifespan)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("--- INICIO: Evento de Arranque de FastAPI ---")

    app.state.faiss_vectorstore = None
    app.state.sync_mongo_db = None
    app.state.mongo_client = None
    app.state.recommendation_engine = None
    app.state.engine_is_ready = False

    try:

        docs_path = "./docs"
        if os.path.exists(docs_path):
            loader = DirectoryLoader(
                docs_path,
                glob="**/*.md",
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"},
            )
            documents = loader.load()
            if documents:
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1500, chunk_overlap=200
                )
                splits = text_splitter.split_documents(documents)
                embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
                app.state.faiss_vectorstore = FAISS.from_documents(
                    splits, embeddings_model
                )
                logger.info(
                    ">>> ÉXITO: VectorStore de FAISS creado desde documentación."
                )
            else:
                logger.warning(f"ADVERTENCIA: Carpeta '{docs_path}' vacía.")
                embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
                app.state.faiss_vectorstore = FAISS.from_texts(
                    ["Documentación no disponible"], embeddings_model
                )
        else:
            logger.warning(f"ADVERTENCIA: La carpeta '{docs_path}' no existe.")
            embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
            app.state.faiss_vectorstore = FAISS.from_texts(
                ["Documentación no disponible"], embeddings_model
            )

        mongo_client = MongoClient(
            Config.MONGO_DB_CONNECTION_STRING,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=10000,
        )
        mongo_client.admin.command("ping")
        app.state.mongo_client = mongo_client
        app.state.sync_mongo_db = mongo_client[Config.MONGO_DB_NAME]
        logger.info(
            f">>> ÉXITO: Conexión a MongoDB (DB: '{Config.MONGO_DB_NAME}') establecida."
        )

        logger.info("Cargando datos para el motor de recomendación Singleton...")
        db = app.state.sync_mongo_db

        collaborators_data = list(
            db[Config.MONGO_COLLABORATOR_COLLECTION_NAME].find({})
        )
        projects_data = list(db[Config.MONGO_PROJECT_COLLECTION_NAME].find({}))

        if not collaborators_data:
            logger.error(
                "FATAL: No se encontraron datos de colaboradores para inicializar el motor. La aplicación no funcionará correctamente."
            )
        else:
            df_collaborators = pd.DataFrame(collaborators_data)
            df_projects = (
                pd.DataFrame(projects_data) if projects_data else pd.DataFrame()
            )
            logger.info(
                "Creando instancia Singleton del motor (esto puede tardar varios segundos)..."
            )
            recommendation_engine_instance = SoftwareTeamRecommender(
                df_collaborators, df_projects
            )
            app.state.recommendation_engine = recommendation_engine_instance
            logger.info(">>> ÉXITO: Motor de recomendación Singleton creado y listo.")

        try:
            openai.api_key = Config.OPENAI_API_KEY
            if not openai.api_key:
                raise ValueError("OPENAI_API_KEY está vacía.")
            logger.info("✅ OpenAI: Configuración de API Key cargada.")
        except Exception as e:
            logger.error(f"❌ OpenAI: Error en la configuración de la API Key - {e}")

    except Exception as e:
        logger.critical(
            f"FATAL: El arranque de la aplicación falló. Error: {e}", exc_info=True
        )

    yield

    logger.info("--- INICIO: Evento de Apagado de FastAPI ---")
    if app.state.mongo_client:
        app.state.mongo_client.close()
        logger.info("Conexión a MongoDB cerrada.")
    logger.info("--- FIN: Apagado completado. ---")


app = FastAPI(
    title="Motor de IA de Software Team Builder",
    description="Motor de IA para recomendaciones y chat analítico.",
    version="12.0.0 (Estable)",
    lifespan=startup_lifespan,
)


app.include_router(health.router)
app.include_router(teams.router)
app.include_router(chat.router)
app.include_router(faiss_update.router)
app.include_router(analytics.router)
logger.info("Router '/api/teams' registrado.")
logger.info("Router '/chat' registrado.")


@app.middleware("http")
async def log_all_requests(request: Request, call_next):
    logger.info(f"🌐 Request recibida: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"📤 Response: {response.status_code}")
    return response


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Motor de IA de Software Team Builder (v12 Estable) funcionando correctamente."}
