# software-team-builder/app/routers/system.py
from fastapi import APIRouter, Depends, HTTPException, Request
import logging
import pandas as pd
from pymongo import MongoClient
from config import Config

from ..dependencies import get_recommendation_engine
from ..recommendation_engine import SoftwareTeamRecommender

# Importar Config para la cadena de conexión
import sys
import os

PROJECT_ROOT_FOR_SYSTEM_CONFIG = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
if PROJECT_ROOT_FOR_SYSTEM_CONFIG not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_FOR_SYSTEM_CONFIG)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/system", tags=["System Management"])


@router.post(
    "/refresh-data", summary="Refrescar los datos del motor de IA desde MongoDB"
)
async def refresh_ia_data(
    request: Request,  # Usamos Request para acceder a app.state directamente
    engine: SoftwareTeamRecommender = Depends(get_recommendation_engine),
):
    """
    Este endpoint fuerza al motor de IA a recargar todos los datos de las colecciones
    'collaborator' y 'projects' desde MongoDB.
    Debe ser llamado por el backend de RUBIK después de realizar cambios en los datos.
    """
    logger.info("--- INICIO Endpoint /api/system/refresh-data ---")

    # El engine ya está disponible a través de la dependencia, que lo obtiene de app.state

    client = None
    try:
        logger.info("Conectando a MongoDB para recargar los datos...")
        client = MongoClient(
            Config.MONGO_DB_CONNECTION_STRING, serverSelectionTimeoutMS=5000
        )
        db = client[Config.MONGO_DB_NAME]

        collaborators_data = list(
            db[Config.MONGO_COLLABORATOR_COLLECTION_NAME].find({})
        )
        projects_data = list(db[Config.MONGO_PROJECT_COLLECTION_NAME].find({}))

        logger.info(
            f"Datos recargados: {len(collaborators_data)} colaboradores, {len(projects_data)} proyectos."
        )

        if not collaborators_data:
            raise HTTPException(
                status_code=500,
                detail="No se encontraron datos de colaboradores en la base de datos durante el refresco.",
            )

        df_collaborators = pd.DataFrame(collaborators_data)
        df_projects = pd.DataFrame(projects_data) if projects_data else pd.DataFrame()

        # Llamar al nuevo método de refresco en la instancia del motor existente
        success = engine.refresh_data(df_collaborators, df_projects)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="El motor de IA no pudo refrescar los datos. Revisa los logs.",
            )

        # Opcional: Actualizar la instancia en app.state (aunque ya modificamos la existente)
        # request.app.state.recommendation_engine = engine

        logger.info("--- FIN Endpoint /api/system/refresh-data ---")
        return {
            "status": "success",
            "message": "Los datos del motor de IA han sido actualizados.",
        }

    except Exception as e:
        logger.exception("Error durante el refresco de datos.")
        raise HTTPException(
            status_code=500, detail=f"Error interno al refrescar los datos: {str(e)}"
        )
    finally:
        if client:
            client.close()
