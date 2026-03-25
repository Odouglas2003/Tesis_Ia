# app/dependencies.py
from fastapi import Request, HTTPException, status
import logging

try:
    from .recommendation_engine import SoftwareTeamRecommender
except (
    ImportError
):  # Fallback para type hint si hay problemas de importación circular o entorno
    SoftwareTeamRecommender = None
logger = logging.getLogger(__name__)  # app.dependencies logger


async def get_recommendation_engine(request: Request) -> SoftwareTeamRecommender:
    logger.debug("Dependencia get_recommendation_engine solicitada.")
    if (
        not hasattr(request.app.state, "recommendation_engine")
        or request.app.state.recommendation_engine is None
    ):
        logger.error(
            "Motor de recomendación NO encontrado o es None en app.state. Revisa el log de startup."
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de recomendación no disponible (error de inicialización o carga de datos).",
        )

    engine = request.app.state.recommendation_engine

    # Esta verificación es opcional si confías en la inicialización, pero no hace daño
    if SoftwareTeamRecommender and not isinstance(engine, SoftwareTeamRecommender):
        logger.error(
            f"Objeto en app.state.recommendation_engine no es SoftwareTeamRecommender. Tipo: {type(engine)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Error grave si el tipo es incorrecto
            detail="Error interno: Tipo incorrecto para el servicio de recomendación.",
        )
    logger.debug(
        "Instancia de motor de recomendación devuelta exitosamente por dependencia."
    )
    return engine
