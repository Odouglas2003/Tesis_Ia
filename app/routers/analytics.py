from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from pymongo.database import Database

from app.database import get_db
from app.services.ia_logic import extract_entities


router = APIRouter(prefix="/analytics", tags=["analytics"])


SENSITIVE_FIELDS = {"password", "dni", "token", "honorarios", "sueldo", "address"}


def sanitize(x: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    if isinstance(x, dict):
        if "_id" in x and isinstance(x["_id"], ObjectId):
            x["_id"] = str(x["_id"])
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
    limit: int = 100


class NLQueryResponse(BaseModel):
    intent: str
    collection: Optional[str] = None
    filter: Optional[Dict[str, Any]] = None
    results: Optional[List[Dict[str, Any]]] = None
    count: Optional[int] = None


@router.post("/query", response_model=NLQueryResponse)
def run_query(payload: NLQueryRequest, db: Database = Depends(get_sync_db)):
    text = (payload.query or "").strip()
    limit = max(1, min(payload.limit, 200))
    is_count_query = (
        "cuántos" in text.lower()
        or "cuantos" in text.lower()
        or "cantidad" in text.lower()
    )

    if not text:
        raise HTTPException(
            status_code=400, detail="El campo 'query' no puede estar vacío."
        )

    ia_output = extract_entities(text)

    if not ia_output or "collection" not in ia_output or "query" not in ia_output:
        raise HTTPException(
            status_code=400,
            detail="La IA no pudo interpretar la consulta. Intenta ser más claro.",
        )

    collection_name = ia_output.get("collection")
    query_type = ia_output.get("query_type")
    query_body = ia_output.get("query")

    if not collection_name or not query_type or query_body is None:
        raise HTTPException(
            status_code=500,
            detail="Error interno: La respuesta de la IA no tiene el formato esperado.",
        )

    coll = db[collection_name]
    try:
        if query_type == "aggregate":
            pipeline = query_body
            print(f"--- Ejecutando PIPELINE de la IA: {pipeline} ---")

            if is_count_query:
                count_pipeline = pipeline + [{"$count": "total"}]
                result = list(coll.aggregate(count_pipeline))
                count = result[0]["total"] if result else 0
                return NLQueryResponse(
                    intent="count", collection=collection_name, count=count
                )
            else:
                results = list(coll.aggregate(pipeline + [{"$limit": limit}]))
                return NLQueryResponse(
                    intent="find", collection=collection_name, results=sanitize(results)
                )

        elif query_type == "find":
            db_filter = query_body
            projection = ia_output.get("projection", None)

            print(f"--- Ejecutando FILTER de la IA: {db_filter} ---")
            print(f"--- Con PROJECTION: {projection} ---")

            if is_count_query:
                count = coll.count_documents(db_filter)
                return NLQueryResponse(
                    intent="count",
                    collection=collection_name,
                    filter=db_filter,
                    count=count,
                )
            else:

                results = list(coll.find(db_filter, projection, limit=limit))
                return NLQueryResponse(
                    intent="find",
                    collection=collection_name,
                    filter=db_filter,
                    results=sanitize(results),
                )

        else:

            return NLQueryResponse(
                intent="find", collection=collection_name, results=[]
            )

    except Exception as e:
        print(f"Error al ejecutar la consulta en MongoDB: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos al ejecutar la consulta generada.",
        )
