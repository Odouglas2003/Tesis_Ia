from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "software-team-builder-ai-engine",
        "version": "1.0.0",
    }


@router.get("/health")  # Opcional: también responde en /health
async def health_check_short():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
