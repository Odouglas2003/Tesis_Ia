from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import logging
from datetime import datetime, timezone
import sys
import os
import hashlib
import json
from ..database import get_db
from pymongo.database import Database


PROJECT_ROOT_FOR_TEAMS_CONFIG = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
if PROJECT_ROOT_FOR_TEAMS_CONFIG not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_FOR_TEAMS_CONFIG)

try:
    from config import Config
except ImportError as e:
    print(
        f"ERROR CRITICO [app/routers/teams.py]: No se pudieron importar dependencias: {e}"
    )
    raise

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/teams", tags=["Teams Management"])


class PositionRequest(BaseModel):
    position_id: str = Field(..., example="req-frontend-1")
    role: str = Field(..., example="Frontend Developer")
    seniority: str = Field(..., example="Senior")
    technologies: List[str] = Field(
        default_factory=list, example=["React", "TypeScript"]
    )
    assigned_hours_needed: int = Field(..., ge=0, example=40)
    quantity: int = Field(..., ge=1, example=1)
    suggestedId: Optional[str] = Field(
        None,
        description="Opcional: _id del colaborador sugerido por el usuario.",
        example="685c124105eff4780cf1271a",
    )


class RequestDetails(BaseModel):
    request_date: str = Field(..., example="2025-07-01")
    start_date: str = Field(..., example="2025-08-01")
    budget: Optional[float] = Field(
        None, gt=0, description="Presupuesto total para la solicitud (opcional)."
    )
    objective: Optional[str] = Field(
        None, description="Descripción del proyecto o la solicitud."
    )


class SimpleTeamRequest(BaseModel):
    request_details: RequestDetails
    positions_requested: List[PositionRequest] = Field(..., min_length=1)


class CandidateResponse(BaseModel):
    id: str
    name: str
    score: float
    score_details: Dict[str, float]
    is_user_suggestion: bool = Field(False)
    suggestion_analysis: Optional[str] = None
    suggested_by_ia: bool = Field(False)
    availability_message: str
    known_technologies: List[str] = Field(
        default_factory=list,
        description="Lista de tecnologías que conoce el candidato.",
    )
    missing_data_warnings: List[str] = Field(default_factory=list)


class PositionResponse(BaseModel):
    position_id: str
    role_requested: str
    seniority_requested: str
    technologies_requested: List[str] = Field(
        default_factory=list,
        description="Las tecnologías que se solicitaron para este puesto.",
    )
    candidates: List[CandidateResponse]
    vacancy_needed: bool
    vacancy_message: Optional[str] = None


class BudgetResponse(BaseModel):
    total_requested: Optional[float]
    total_assigned: float
    remaining: Optional[float]


class SimpleTeamResponse(BaseModel):
    request_id: str
    response_date: str
    budget_details: BudgetResponse
    positions: List[PositionResponse]


def create_request_hash(positions: List[PositionRequest]) -> str:
    try:
        positions_dict = [
            p.model_dump(exclude={"suggestedId", "position_id"}) for p in positions
        ]
        positions_str = json.dumps(positions_dict, sort_keys=True)
        return hashlib.sha256(positions_str.encode("utf-8")).hexdigest()
    except Exception as e:
        logger.warning(f"No se pudo generar el hash de la solicitud: {e}")
        return f"hash-error-{datetime.now(timezone.utc).timestamp()}"


@router.post(
    "/recommend_positions",
    response_model=SimpleTeamResponse,
    summary="Recomendar candidatos (usando motor pre-cargado)",
    description="Utiliza el motor de IA Singleton. Si el motor aún se está inicializando, devolverá un error 503.",
)
async def recommend_for_positions(
    request: Request, request_data: SimpleTeamRequest, db: Database = Depends(get_db)
):
    logger.info(
        "--- INICIO Endpoint /api/teams/recommend_positions (Modo Singleton) ---"
    )
    if Config.DEBUG_MODE:
        logger.debug(f"Request data: {request_data.model_dump_json(indent=2)}")

    try:

        if not getattr(request.app.state, "recommendation_engine", None):
            logger.warning(
                "Petición recibida pero el motor aún no está disponible. Devolviendo 503."
            )
            raise HTTPException(
                status_code=503,
                detail="El motor de IA todavía se está inicializando o no pudo cargarse. Por favor, inténtelo de nuevo en unos momentos.",
            )

        engine = request.app.state.recommendation_engine
        if engine is None:
            logger.error(
                "FATAL: El motor está marcado como listo ('engine_is_ready') pero es None."
            )
            raise HTTPException(
                status_code=500, detail="Error interno crítico en el servicio de IA."
            )

        logger.info("Generando recomendaciones con la instancia Singleton del motor...")
        result_from_engine = engine.recommend_for_positions_v2(
            positions_requested=request_data.positions_requested,
            budget=request_data.request_details.budget,
            project_description=request_data.request_details.objective,
            db=db,
        )

        try:
            logger.info("Guardando asignaciones exitosas en el historial...")
            history_collection = db["recommendation_history"]
            history_documents_to_insert = []
            request_hash = create_request_hash(request_data.positions_requested)

            for position_response in result_from_engine.get("positions", []):
                if position_response.get("candidates") and not position_response.get(
                    "vacancy_needed"
                ):
                    assigned_candidate = position_response["candidates"][0]

                    history_doc = {
                        "recommendation_date": datetime.now(timezone.utc),
                        "assigned_candidate_id": assigned_candidate.get("id"),
                        "assigned_candidate_name": assigned_candidate.get("name"),
                        "position_id_requested": position_response.get("position_id"),
                        "role_requested": position_response.get("role_requested"),
                        "original_request_hash": request_hash,
                    }
                    history_documents_to_insert.append(history_doc)

            if history_documents_to_insert:
                history_collection.insert_many(history_documents_to_insert)
                logger.info(
                    f"Se guardaron {len(history_documents_to_insert)} asignaciones en el historial."
                )
        except Exception as e:
            logger.error(
                f"Error al guardar el historial de recomendaciones: {e}", exc_info=True
            )

        result_from_engine["request_id"] = (
            f"req-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        )
        result_from_engine["response_date"] = datetime.now(timezone.utc).isoformat()

        logger.info("--- FIN Endpoint /api/teams/recommend_positions ---")
        return result_from_engine

    except HTTPException:

        raise

    except ValueError as ve:
        logger.exception("Error de validación al procesar la recomendación.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve)
        )

    except Exception as e:

        logger.exception(
            f"Error inesperado en el endpoint recommend_for_positions: {e}"
        )
        raise HTTPException(
            status_code=500, detail="Error interno al procesar la recomendación."
        )
