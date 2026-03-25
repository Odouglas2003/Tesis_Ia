# ============================================
# 📁 app/routers/faiss_update.py
# ============================================

from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from pymongo import MongoClient
import pandas as pd
import logging
import os
from app.recommendation_engine import SoftwareTeamRecommender
from app.services.data_processing import DataProcessor
from config import Config


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/faiss", tags=["FAISS Update"])


class UpdateRequest(BaseModel):
    """
    Payload para actualizar el índice FAISS.
    Si item_id es None, se reindexa toda la colección.
    """

    # item_id: str | None = None
    item_id: Optional[str] = None


@router.post("/update")
async def update_faiss_index(data: UpdateRequest):
    """
    Regenera el índice FAISS en base a los datos actuales de MongoDB.
    - Si item_id es None, reindexa toda la colección de colaboradores.
    - Si item_id tiene valor, en esta versión igual reindexa todo para asegurar consistencia.
    """
    try:
        # 1️⃣ Conexión a MongoDB
        mongo_client = MongoClient(
            Config.MONGO_DB_CONNECTION_STRING, serverSelectionTimeoutMS=5000
        )
        db = mongo_client[Config.MONGO_DB_NAME]
        collab_coll = db[Config.MONGO_EMPLOYEES_COLLECTION_NAME]

        # Por ahora reindexamos todo aunque llegue item_id (más simple y consistente)
        query = {"_id": data.item_id} if data.item_id else {}
        collaborators = list(collab_coll.find(query))
        if not collaborators:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron colaboradores para reindexar.",
            )

        # 2️⃣ Convertir a DataFrame y preprocesar
        df = pd.DataFrame(collaborators)
        if "_id" in df.columns:
            df["_id"] = df["_id"].astype(str)

        logger.info(
            f"⚡ {len(df)} documentos cargados desde MongoDB para reindexación."
        )

        recommender = SoftwareTeamRecommender(df)
        processor = DataProcessor(
            recommender.df_employees.copy(), recommender_instance=recommender
        )

        # 3️⃣ Generar descripciones y embeddings
        descriptions = processor.generate_text_descriptions()
        if not descriptions:
            raise HTTPException(
                status_code=500,
                detail="No se pudieron generar descripciones para embeddings.",
            )

        models_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", Config.MODELS_SUBDIR
        )
        os.makedirs(models_dir, exist_ok=True)
        faiss_path = os.path.join(models_dir, Config.EMBEDDINGS_FILE_NAME)

        index = processor.generate_faiss_index(descriptions, save_path=faiss_path)
        if index is None or index.ntotal == 0:
            raise HTTPException(
                status_code=500, detail="Falló la creación del índice FAISS."
            )

        logger.info(
            f"✅ Índice FAISS actualizado con {index.ntotal} vectores en {faiss_path}"
        )
        return {"status": "ok", "vectors": index.ntotal, "path": faiss_path}

    except Exception as e:
        logger.exception("Error actualizando FAISS")
        raise HTTPException(status_code=500, detail=str(e))
