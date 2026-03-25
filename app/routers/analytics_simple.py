from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from pymongo.database import Database
from app.database import get_db


router = APIRouter(prefix="/analytics", tags=["analytics"])

SENSITIVE_FIELDS = {"password", "dni", "token", "honorarios", "sueldo", "address"}


def sanitize(
    x: Union[Dict[str, Any], List[Any], Any],
) -> Union[Dict[str, Any], List[Any], Any]:
    if isinstance(x, dict):
        return {k: sanitize(v) for k, v in x.items() if k not in SENSITIVE_FIELDS}
    if isinstance(x, list):
        return [sanitize(i) for i in x]
    if isinstance(x, ObjectId):
        return str(x)
    if isinstance(x, datetime):
        return x.isoformat()
    return x


def get_sync_db() -> Any:
    try:
        return get_db()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo DB: {e}")


class NLQueryRequest(BaseModel):
    query: str
    limit: int = 50


class NLQueryResponse(BaseModel):
    intent: str
    collection: Optional[str] = None
    filter: Optional[Dict[str, Any]] = None
    results: Optional[List[Dict[str, Any]]] = None
    count: Optional[int] = None
    report: Optional[Dict[str, Any]] = None


def inject_active_softdelete(match_filter: Dict[str, Any]) -> Dict[str, Any]:
    soft = {
        "$or": [
            {"delete_at": {"$exists": False}},
            {"delete_at": None},
            {"delete_at": ""},
            {"deleted_at": {"$exists": False}},
            {"deleted_at": None},
            {"deleted_at": ""},
        ]
    }
    if not match_filter:
        return soft
    if "$and" in match_filter:
        return {"$and": [*match_filter["$and"], soft]}
    return {"$and": [match_filter, soft]}


@router.post("/query", response_model=NLQueryResponse)
def run_query(payload: NLQueryRequest, db: Database = Depends(get_sync_db)):

    raise HTTPException(
        status_code=400,
        detail="Consulta no reconocida por las reglas simples. Decime la frase exacta y la agrego.",
    )
