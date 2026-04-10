# software-team-builder/config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # --- Configuración General de la API ---
    API_TITLE = os.getenv("API_TITLE", "Team Builder Backend API")
    API_VERSION = "5.3.0"
    API_DESCRIPTION = "API para recomendar candidatos para una lista de posiciones, con opción de sugerir un candidato preferido."
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "True").lower() == "true"
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
    PYTHON_VERSION = os.getenv("PYTHON_VERSION", "3.9")

    # --- Configuración de Conexiones ---
    MONGO_DB_CONNECTION_STRING = os.getenv(
        "MONGO_DB_CONNECTION_STRING"
    )  # ← Sin valor por defecto
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "rubik_test")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # ← Sin valor por defecto

    # --- CONSTANTES (no variables de entorno) ---
    MONGO_COLLABORATOR_COLLECTION_NAME = "collaborator"
    MONGO_PROJECT_COLLECTION_NAME = "projects"

    # --- Configuración del Motor de Recomendación ---
    NLP_MODEL_NAME = "es_core_news_sm"
    MAX_CANDIDATES_PER_ROLE = 3

    # --- Pesos para el Scoring ---
    W_TECH_SCORE = 40.0
    W_SENIORITY_MATCH_BONUS = 25.0
    W_PERFORMANCE_SCORE = 20.0
    W_AVAILABILITY_SCORE = 15.0
    W_SUGGESTED_CANDIDATE_BONUS = 10.0
